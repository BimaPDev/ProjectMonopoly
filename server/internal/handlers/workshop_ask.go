// internal/handlers/workshop_ask.go
package handlers

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"
	"unicode"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
)

var citeRe = regexp.MustCompile(`\[p\.(\d+)\]`)

// ---------------- Conversation Memory (2h TTL, last 3 turns) ----------------

type pastTurn struct {
	Question string
	Answer   string
	Context  string
	Hits     []askHit
	At       time.Time
}

var convMem = struct {
	sync.Mutex
	M map[string][]pastTurn
}{M: make(map[string][]pastTurn)}

func memKey(userID, groupID int32) string {
	return fmt.Sprintf("%d:%d", userID, groupID)
}

func pushTurn(userID, groupID int32, t pastTurn) {
	convMem.Lock()
	defer convMem.Unlock()

	k := memKey(userID, groupID)
	h := append(convMem.M[k], t)

	// keep last 3 turns, drop >2h old
	cut := time.Now().Add(-2 * time.Hour)
	out := make([]pastTurn, 0, 3)
	for i := len(h) - 1; i >= 0 && len(out) < 3; i-- {
		if h[i].At.After(cut) {
			out = append(out, h[i])
		}
	}
	// reverse back to chronological
	for i, j := 0, len(out)-1; i < j; i, j = i+1, j-1 {
		out[i], out[j] = out[j], out[i]
	}
	convMem.M[k] = out
}

func getHistory(userID, groupID int32) []pastTurn {
	convMem.Lock()
	defer convMem.Unlock()
	return append([]pastTurn(nil), convMem.M[memKey(userID, groupID)]...)
}

// ---------------------------------------------------------------------------

type historyMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type askReq struct {
	GroupID      int32             `json:"group_id"`
	Question     string            `json:"question"`
	Limit        int32             `json:"limit"`
	Model        string            `json:"model"`
	Mode         string            `json:"mode"`          // "strict" | "opinion"
	AllowOutside bool              `json:"allow_outside"` // default false
	Output       string            `json:"output"`        // e.g. "bullet pros/cons", "one-page memo"
	Tone         string            `json:"tone"`          // e.g. "neutral", "confident"
	History      []historyMessage  `json:"history"`       // conversation history from client
}

type askHit struct {
	DocumentID string `json:"document_id"`
	Page       int32  `json:"page"`
	Index      int32  `json:"chunk_index"`
	Snippet    string `json:"snippet"`
}

type askResp struct {
	Answer string   `json:"answer"`
	Hits   []askHit `json:"hits"`
}

func envOr(k, d string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return d
}

func WorkshopAskHandler(q *db.Queries) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		userID := ctxUserID(r)

		var ar askReq
		if err := json.NewDecoder(r.Body).Decode(&ar); err != nil || ar.GroupID == 0 || strings.TrimSpace(ar.Question) == "" {
			http.Error(w, "bad request", http.StatusBadRequest)
			return
		}
		limit := ar.Limit
		if limit <= 0 || limit > 8 {
			limit = 6
		}

		ctx := r.Context()
		history := getHistory(int32(userID), ar.GroupID) // last ≤3 turns in past 2h

		// Exact search with full question
		rows, err := q.SearchChunks(ctx, db.SearchChunksParams{
			Q:       ar.Question,
			UserID:  int32(userID),
			GroupID: ar.GroupID,
			N:       limit,
		})
		if err != nil {
			fmt.Printf("SearchChunks error: %v\n", err)
		}
		fmt.Printf("SearchChunks results for '%s': %d rows (userID=%d, groupID=%d)\n", ar.Question, len(rows), userID, ar.GroupID)

		// Retry with concise query if empty
		if len(rows) == 0 {
			cq := conciseQuery(ar.Question)
			fmt.Printf("Retrying with concise query: '%s'\n", cq)
			if cq != "" && cq != strings.ToLower(ar.Question) {
				r2, _ := q.SearchChunks(ctx, db.SearchChunksParams{
					Q:       cq,
					UserID:  int32(userID),
					GroupID: ar.GroupID,
					N:       limit,
				})
				fmt.Printf("Concise query returned %d rows\n", len(r2))
				rows = append(rows, r2...)
			}
		}

		// Fuzzy fallback
		if len(rows) == 0 {
			fmt.Printf("Trying fuzzy search...\n")
			fz, _ := q.FuzzyChunks(ctx, db.FuzzyChunksParams{
				Q:       ar.Question,
				UserID:  int32(userID),
				GroupID: ar.GroupID,
				N:       limit,
			})
			fmt.Printf("Fuzzy search returned %d rows\n", len(fz))
			for _, r2 := range fz {
				rows = append(rows, db.SearchChunksRow{
					DocumentID: r2.DocumentID,
					Page:       r2.Page,
					ChunkIndex: r2.ChunkIndex,
					Content:    r2.Content,
				})
			}
		}

		fmt.Printf("Final row count after all searches: %d\n", len(rows))

		// Topic filter removed - not needed for indie games/marketing RAG
		// The vector search already returns relevant results

		// Build context + hits list
		hits := make([]askHit, 0, len(rows))
		var b strings.Builder

		// Short conversation transcript for continuity
		if len(history) > 0 {
			b.WriteString("Conversation so far:\n")
			for _, t := range history {
				prevAns := t.Answer
				if len(prevAns) > 400 {
					prevAns = prevAns[:400] + "..."
				}
				fmt.Fprintf(&b, "Q: %s\nA: %s\n\n", strings.TrimSpace(t.Question), strings.TrimSpace(prevAns))
			}
		}

		if len(rows) > 0 {
			b.WriteString("Context:\n")
			for i, rr := range rows {
				page := int32(0)
				if rr.Page.Valid {
					page = rr.Page.Int32
				}
				ctxChunk := rr.Content
				if len(ctxChunk) > 900 {
					ctxChunk = ctxChunk[:900] + "..."
				}
				fmt.Fprintf(&b, "[%d] (doc %s, p.%d)\n%s\n\n", i+1, rr.DocumentID.String(), page, ctxChunk)

				snip := rr.Content
				if len(snip) > 200 {
					snip = snip[:200] + "..."
				}
				hits = append(hits, askHit{
					DocumentID: rr.DocumentID.String(),
					Page:       page,
					Index:      rr.ChunkIndex,
					Snippet:    snip,
				})
			}
		} else if len(history) > 0 {
			// No fresh rows. Reuse prior Context block to keep thread alive.
			b.WriteString("Context:\n")
			lastCtx := history[len(history)-1].Context
			if strings.TrimSpace(lastCtx) == "" {
				b.WriteString("<none>\n")
			} else {
				b.WriteString(lastCtx + "\n")
			}
		}

		// Model + host
		model := orDefault(ar.Model, envOr("OLLAMA_MODEL", "gemma3:latest"))
		host := envOr("OLLAMA_HOST", "http://localhost:11434")

		// Modes
		mode := strings.ToLower(strings.TrimSpace(ar.Mode))
		if mode == "" {
			mode = "strict"
		}
		temp := 0.2
		if mode == "opinion" {
			temp = 0.7
		}

		// No-context handling
		var sys, user string
		hasClientHistory := len(ar.History) > 0

		// If client provides history, treat as conversational even without RAG context
		if len(rows) == 0 && len(history) == 0 && !hasClientHistory {
			if !ar.AllowOutside {
				w.Header().Set("Content-Type", "application/json")
				_ = json.NewEncoder(w).Encode(askResp{
					Answer: "No relevant context on this topic in your PDFs. Enable allow_outside or upload a relevant document.",
					Hits:   nil,
				})
				return
			}
			// allow outside: forbid fake cites
			sys = "There is no Context. Answer from general knowledge. Do NOT invent citations. Include an 'Assumptions' section."
			if mode == "opinion" {
				user = buildOpinionNoContext(ar)
			} else {
				user = "Question: " + ar.Question
			}
		} else if hasClientHistory && len(rows) == 0 && len(history) == 0 {
			// Client history exists but no RAG context - conversational mode
			if mode == "opinion" {
				sys = "You are a helpful AI assistant. Provide thoughtful recommendations and advice based on the conversation history and your general knowledge. Be practical and actionable."
				user = buildOpinionNoContext(ar)
			} else {
				sys = "You are a helpful AI assistant. Answer based on the conversation history and your general knowledge."
				user = "Question: " + ar.Question
			}
		} else {
			if mode == "opinion" {
				if hasClientHistory {
					sys = "You are a helpful AI assistant. When Context is available, cite it with [p.X]. Use conversation history to understand follow-up questions. Provide practical recommendations."
					user = buildContextOnly(b.String())
				} else {
					sys = "Write an opinionated analysis primarily from Context. Claims from Context MUST cite [p.X]. If you add outside knowledge, put it ONLY under 'Assumptions'."
					user = buildOpinionUserPrompt(b.String(), ar)
				}
			} else {
				if hasClientHistory {
					sys = "Answer using Context when available and cite [p.X]. Use conversation history to understand context. If information is missing, say you don't know."
					user = buildContextOnly(b.String())
				} else {
					sys = "Answer only from Context. Cite pages like [p.X]. If missing, say you don't know."
					user = buildStrictUserPrompt(b.String(), ar.Question)
				}
			}
		}

		ans, err := callOllamaWithOptions(ctx, host, model, sys, user, map[string]any{
			"temperature":    temp,
			"num_ctx":        8192,
			"repeat_penalty": 1.1,
			"top_p":          0.9,
			"min_p":          0.05,
			"seed":           13,
		}, ar.History)
		if err != nil {
			if len(rows) == 0 {
				ans = "No relevant context on this topic in your PDFs. Enable allow_outside or upload a relevant document."
			} else {
				ans = "Unable to generate a grounded answer."
			}
		}

		// Require numeric page citations when any Context existed (fresh or reused) and not opinion
		if (len(rows) > 0 || len(history) > 0) && citeRe.FindStringIndex(ans) == nil && mode != "opinion" {
			ans = "Unable to generate a grounded answer with page citations from your PDFs."
		}

		// Save turn to memory
		pushTurn(int32(userID), ar.GroupID, pastTurn{
			Question: ar.Question,
			Answer:   strings.TrimSpace(ans),
			Context:  b.String(),
			Hits:     hits,
			At:       time.Now(),
		})

		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(askResp{Answer: strings.TrimSpace(ans), Hits: hits})
	}
}

// -------------------- helpers --------------------

func buildStrictUserPrompt(contextBlock, question string) string {
	var b strings.Builder
	if strings.TrimSpace(contextBlock) != "" {
		b.WriteString(contextBlock)
	} else {
		b.WriteString("Context:\n<none>\n")
	}
	b.WriteString("Instructions: Use ONLY the Context above. If the answer is not present, say you don't know. Cite pages like [p.X].\n")
	b.WriteString("Question: " + question)
	return b.String()
}

func buildContextOnly(contextBlock string) string {
	var b strings.Builder
	if strings.TrimSpace(contextBlock) != "" {
		b.WriteString(contextBlock)
	} else {
		b.WriteString("Context:\n<none>\n")
	}
	b.WriteString("Instructions: Use the Context above to answer questions. Cite pages like [p.X] when referencing the context.\n")
	return b.String()
}

func buildOpinionUserPrompt(contextBlock string, ar askReq) string {
	var b strings.Builder
	if strings.TrimSpace(contextBlock) != "" {
		b.WriteString(contextBlock)
	} else {
		b.WriteString("Context:\n<none>\n")
	}
	output := orDefault(ar.Output, "short memo")
	tone := orDefault(ar.Tone, "neutral")
	b.WriteString("Task: Provide a recommendation with rationale.\n")
	fmt.Fprintf(&b, "Tone: %s\nOutput: %s\n", tone, output)
	fmt.Fprintf(&b, "Rules:\n- Prefer evidence from Context and cite [p.X].\n- allow_outside=%v. If you add outside knowledge, add a separate 'Assumptions' section.\n- If Context is insufficient and allow_outside=false, say you don’t know.\n", ar.AllowOutside)
	b.WriteString("Question: " + ar.Question)
	return b.String()
}

func buildOpinionNoContext(ar askReq) string {
	output := orDefault(ar.Output, "short memo")
	tone := orDefault(ar.Tone, "neutral")
	var b strings.Builder
	b.WriteString("Task: Provide a recommendation with rationale.\n")
	fmt.Fprintf(&b, "Tone: %s\nOutput: %s\n", tone, output)
	b.WriteString("Rules:\n- No citations allowed because there is no Context.\n- Add an 'Assumptions' section for any external facts or heuristics you use.\n")
	b.WriteString("Question: " + ar.Question)
	return b.String()
}

func callOllamaWithOptions(ctx context.Context, host, model, sys, user string, opts map[string]any, history []historyMessage) (string, error) {
	// Wake Ollama/model (handles idle unloads)
	_ = pingOllama(host, 10*time.Second)

	client := &http.Client{Timeout: ollamaTimeout()}

	// Build messages array with history
	messages := []map[string]string{
		{"role": "system", "content": sys},
	}

	// Add conversation history if provided
	if len(history) > 0 {
		// When we have history, we need to integrate context smartly
		// The history already contains the user's question, so we prepend context if available
		hasContext := user != "" && strings.Contains(user, "Context:")

		if hasContext {
			// Add context as initial user message
			messages = append(messages, map[string]string{
				"role":    "user",
				"content": user,
			})
		}

		// Add all conversation history
		for _, msg := range history {
			messages = append(messages, map[string]string{
				"role":    msg.Role,
				"content": msg.Content,
			})
		}
	} else {
		// No history, use traditional approach
		messages = append(messages, map[string]string{
			"role":    "user",
			"content": user,
		})
	}

	// Try /api/chat with retries/backoff
	body := map[string]any{
		"model":    model,
		"stream":   false,
		"options":  opts,
		"messages": messages,
	}
	b, _ := json.Marshal(body)

	var lastErr error
	for attempt := 1; attempt <= 3; attempt++ {
		req, _ := http.NewRequestWithContext(ctx, "POST", host+"/api/chat", bytes.NewReader(b))
		req.Header.Set("Content-Type", "application/json")
		resp, err := client.Do(req)
		if err == nil && resp != nil && resp.StatusCode == 200 {
			defer resp.Body.Close()
			var out struct {
				Message struct {
					Content string `json:"content"`
				} `json:"message"`
			}
			if json.NewDecoder(resp.Body).Decode(&out) == nil {
				return strings.TrimSpace(out.Message.Content), nil
			}
		} else {
			if resp != nil {
				resp.Body.Close()
			}
			lastErr = err
		}
		time.Sleep(time.Duration(attempt*2) * time.Second) // backoff
	}

	// Fallback /api/generate
	gen := map[string]any{
		"model":   model,
		"stream":  false,
		"options": opts,
		"prompt":  "System: " + sys + "\n\nUser: " + user,
	}
	gb, _ := json.Marshal(gen)
	req2, _ := http.NewRequestWithContext(ctx, "POST", host+"/api/generate", bytes.NewReader(gb))
	req2.Header.Set("Content-Type", "application/json")
	resp2, err2 := client.Do(req2)
	if err2 != nil {
		if lastErr != nil {
			return "", lastErr
		}
		return "", err2
	}
	defer resp2.Body.Close()
	if resp2.StatusCode != 200 {
		rb, _ := io.ReadAll(resp2.Body)
		return "", fmt.Errorf("ollama %d: %s", resp2.StatusCode, string(rb))
	}
	var gout struct {
		Response string `json:"response"`
	}
	if err := json.NewDecoder(resp2.Body).Decode(&gout); err != nil {
		return "", err
	}
	return strings.TrimSpace(gout.Response), nil
}

// configurable timeout (default 180s) to survive cold-start loads
func ollamaTimeout() time.Duration {
	if v := os.Getenv("OLLAMA_TIMEOUT_SEC"); v != "" {
		if n, err := strconv.Atoi(v); err == nil && n > 0 {
			return time.Duration(n) * time.Second
		}
	}
	return 180 * time.Second
}

// quick ping to wake Ollama/model
func pingOllama(host string, to time.Duration) error {
	c := &http.Client{Timeout: to}
	req, _ := http.NewRequest("GET", host+"/api/tags", nil)
	resp, err := c.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	return nil
}

func orDefault(s, d string) string {
	if strings.TrimSpace(s) == "" {
		return d
	}
	return s
}

func containsAnyFold(s string, subs ...string) bool {
	if len(subs) == 0 {
		return false
	}
	s = strings.ToLower(s)
	for _, t := range subs {
		t = strings.ToLower(strings.TrimSpace(t))
		if t == "" {
			continue
		}
		if strings.Contains(s, t) {
			return true
		}
	}
	return false
}



func conciseQuery(s string) string {
	s = strings.ToLower(s)
	// Extract key terms (longest words ≥4 chars) for better search matching
	toks := strings.FieldsFunc(s, func(r rune) bool {
		return !(unicode.IsLetter(r) || unicode.IsDigit(r))
	})
	sort.Slice(toks, func(i, j int) bool { return len(toks[i]) > len(toks[j]) })
	out := make([]string, 0, 3)
	seen := map[string]bool{}
	for _, w := range toks {
		if len(out) == 3 {
			break
		}
		if len(w) < 4 || seen[w] {
			continue
		}
		seen[w] = true
		out = append(out, w)
	}
	return strings.Join(out, " ")
}
