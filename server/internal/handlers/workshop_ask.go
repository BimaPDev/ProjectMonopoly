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
	"strings"
	"time"
	"unicode"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
)

var citeRe = regexp.MustCompile(`\[p\.(\d+)\]`)

type askReq struct {
	GroupID      int32  `json:"group_id"`
	Question     string `json:"question"`
	Limit        int32  `json:"limit"`
	Model        string `json:"model"`
	Mode         string `json:"mode"`          // "strict" | "opinion"
	AllowOutside bool   `json:"allow_outside"` // default false
	Output       string `json:"output"`        // e.g. "bullet pros/cons", "one-page memo"
	Tone         string `json:"tone"`          // e.g. "neutral", "confident"
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

		// Exact search with full question
		rows, _ := q.SearchChunks(ctx, db.SearchChunksParams{
			Q:       ar.Question,
			UserID:  int32(userID),
			GroupID: ar.GroupID,
			N:       limit,
		})

		// Retry with concise query if empty
		if len(rows) == 0 {
			cq := conciseQuery(ar.Question)
			if cq != "" && cq != strings.ToLower(ar.Question) {
				r2, _ := q.SearchChunks(ctx, db.SearchChunksParams{
					Q:       cq,
					UserID:  int32(userID),
					GroupID: ar.GroupID,
					N:       limit,
				})
				rows = append(rows, r2...)
			}
		}

		// Fuzzy fallback
		if len(rows) == 0 {
			fz, _ := q.FuzzyChunks(ctx, db.FuzzyChunksParams{
				Q:       ar.Question,
				UserID:  int32(userID),
				GroupID: ar.GroupID,
				N:       limit,
			})
			for _, r2 := range fz {
				rows = append(rows, db.SearchChunksRow{
					DocumentID: r2.DocumentID,
					Page:       r2.Page,
					ChunkIndex: r2.ChunkIndex,
					Content:    r2.Content,
				})
			}
		}

		// Topic filter (non-destructive)
		if len(rows) > 0 {
			terms := topicTerms(ar.Question)
			filtered := make([]db.SearchChunksRow, 0, len(rows))
			for _, rr := range rows {
				if containsAnyFold(rr.Content, terms...) {
					filtered = append(filtered, rr)
				}
			}
			if len(filtered) > 0 {
				rows = filtered
			}
		}

		// Build context + hits list
		hits := make([]askHit, 0, len(rows))
		var b strings.Builder
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
		if len(rows) == 0 {
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
		} else {
			if mode == "opinion" {
				sys = "Write an opinionated analysis primarily from Context. Claims from Context MUST cite [p.X]. If you add outside knowledge, put it ONLY under 'Assumptions'."
				user = buildOpinionUserPrompt(b.String(), ar)
			} else {
				sys = "Answer only from Context. Cite pages like [p.X]. If missing, say you don’t know."
				user = buildStrictUserPrompt(b.String(), ar.Question)
			}
		}

		ans, err := callOllamaWithOptions(ctx, host, model, sys, user, map[string]any{
			"temperature":    temp,
			"num_ctx":        8192,
			"repeat_penalty": 1.1,
			"top_p":          0.9,
			"min_p":          0.05,
			"seed":           13,
		})
		if err != nil {
			if len(rows) == 0 {
				ans = "No relevant context on this topic in your PDFs. Enable allow_outside or upload a relevant document."
			} else {
				ans = "Unable to generate a grounded answer."
			}
		}

		// Require numeric page citations when context existed
		if len(rows) > 0 && citeRe.FindStringIndex(ans) == nil {
			ans = "Unable to generate a grounded answer with page citations from your PDFs."
		}

		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(askResp{Answer: strings.TrimSpace(ans), Hits: hits})
	}
}

func buildStrictUserPrompt(contextBlock, question string) string {
	var b strings.Builder
	if strings.TrimSpace(contextBlock) != "" {
		b.WriteString(contextBlock)
	} else {
		b.WriteString("Context:\n<none>\n")
	}
	b.WriteString("Instructions: Use ONLY the Context above. If the answer is not present, say you don’t know. Cite pages like [p.X].\n")
	b.WriteString("Question: " + question)
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

func callOllamaWithOptions(ctx context.Context, host, model, sys, user string, opts map[string]any) (string, error) {
	// Try /api/chat
	body := map[string]any{
		"model":   model,
		"stream":  false,
		"options": opts,
		"messages": []map[string]string{
			{"role": "system", "content": sys},
			{"role": "user", "content": user},
		},
	}
	b, _ := json.Marshal(body)
	req, _ := http.NewRequestWithContext(ctx, "POST", host+"/api/chat", bytes.NewReader(b))
	req.Header.Set("Content-Type", "application/json")
	resp, err := (&http.Client{Timeout: 60 * time.Second}).Do(req)
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
	resp2, err2 := (&http.Client{Timeout: 60 * time.Second}).Do(req2)
	if err2 != nil {
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

// helpers

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

func topicTerms(q string) []string {
	q = strings.ToLower(q)

	core := []string{
		"bridge", "cross", "minute", "minutes", "torch",
		"bubble", "sort", "swap", "heap",
		"locker", "doors", "divisors", "square",
		"dp", "dynamic programming", "recurrence",
	}
	found := make([]string, 0, 6)
	for _, t := range core {
		if strings.Contains(q, t) {
			found = append(found, t)
		}
	}
	if len(found) > 0 {
		return found
	}

	norm := strings.NewReplacer("-", " ", "_", " ").Replace(q)
	fields := strings.FieldsFunc(norm, func(r rune) bool {
		return !(r >= 'a' && r <= 'z' || r >= '0' && r <= '9')
	})
	sort.Slice(fields, func(i, j int) bool { return len(fields[i]) > len(fields[j]) })
	out := []string{}
	for _, w := range fields {
		if len(out) >= 3 {
			break
		}
		if len(w) >= 5 {
			out = append(out, w)
		}
	}
	return out
}

func conciseQuery(s string) string {
	s = strings.ToLower(s)
	phrases := []string{
		"bubble sort", "dynamic programming", "max heap", "locker doors",
	}
	for _, p := range phrases {
		if strings.Contains(s, p) {
			return p
		}
	}
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
