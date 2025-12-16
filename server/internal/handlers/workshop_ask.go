// internal/handlers/workshop_ask.go
package handlers

import (
	"bytes"
	"context"
	"database/sql"
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
	"github.com/BimaPDev/ProjectMonopoly/internal/utils"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

var citeRe = regexp.MustCompile(`\[(p\.|CP)(\d+)\]`)

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
	GroupID      int32            `json:"group_id"`
	Question     string           `json:"question"`
	Limit        int32            `json:"limit"`
	Model        string           `json:"model"`
	Mode         string           `json:"mode"`          // "strict" | "opinion"
	AllowOutside bool             `json:"allow_outside"` // default false
	Output       string           `json:"output"`        // e.g. "bullet pros/cons", "one-page memo"
	Tone         string           `json:"tone"`          // e.g. "neutral", "confident"
	History      []historyMessage `json:"history"`       // conversation history from client
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

func WorkshopAskHandler(q *db.Queries) gin.HandlerFunc {
	return func(c *gin.Context) {
		userID, err := utils.GetUserID(c)
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
			return
		}

		var ar askReq
		if err := c.ShouldBindJSON(&ar); err != nil || ar.GroupID == 0 || strings.TrimSpace(ar.Question) == "" {
			c.JSON(http.StatusBadRequest, gin.H{"error": "bad request"})
			return
		}
		limit := ar.Limit
		if limit <= 0 || limit > 8 {
			limit = 6
		}

		ctx := c.Request.Context()
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

		// Search Competitor Posts
		compPosts, err := q.SearchCompetitorPosts(ctx, db.SearchCompetitorPostsParams{
			UserID:             int32(userID),
			GroupID:            sql.NullInt32{Int32: ar.GroupID, Valid: true},
			WebsearchToTsquery: ar.Question,
			Limit:              5,
		})
		if err != nil {
			fmt.Printf("SearchCompetitorPosts error: %v\n", err)
		} else {
			fmt.Printf("SearchCompetitorPosts found %d posts\n", len(compPosts))
		}

		// Fallback: if no posts found with search, try to identify competitor and get their recent posts
		if len(compPosts) == 0 {
			fmt.Printf("No posts found with search, trying competitor-specific fallback\n")

			// Try to extract competitor name from question
			mentionedCompetitor := extractCompetitorName(ar.Question)

			if mentionedCompetitor != "" {
				fmt.Printf("Detected competitor mention: %s\n", mentionedCompetitor)
				// Get all user's competitors to find a match
				userCompetitors, err := q.ListUserCompetitors(ctx, int32(userID))
				if err == nil {
					// Find competitor that matches the mentioned name (case-insensitive)
					var targetCompetitorID uuid.UUID
					foundMatch := false
					for _, comp := range userCompetitors {
						if containsAnyFold(comp.Username, mentionedCompetitor) {
							targetCompetitorID = comp.ID
							foundMatch = true
							fmt.Printf("Found matching competitor: %s (ID: %s)\n", comp.Username, targetCompetitorID.String())
							break
						}
					}

					// If we found a matching competitor, get their recent posts
					if foundMatch {
						allPosts, err := q.ListVisibleCompetitorPosts(ctx, db.ListVisibleCompetitorPostsParams{
							UserID:  int32(userID),
							GroupID: sql.NullInt32{Int32: ar.GroupID, Valid: true},
						})
						if err == nil {
							for _, post := range allPosts {
								if post.CompetitorID.Valid && post.CompetitorID.UUID == targetCompetitorID && len(compPosts) < 5 {
									compPosts = append(compPosts, db.SearchCompetitorPostsRow{
										ID:           post.ID,
										CompetitorID: post.CompetitorID,
										Platform:     post.Platform,
										PostID:       post.PostID,
										Content:      post.Content,
										PostedAt:     post.PostedAt,
										Engagement:   post.Engagement,
										CompetitorUsername: func() string {
											// Get the username from competitors list
											for _, c := range userCompetitors {
												if c.ID == targetCompetitorID {
													return c.Username
												}
											}
											return ""
										}(),
										Relevance: 0,
									})
								}
							}
							fmt.Printf("Found %d posts from mentioned competitor\n", len(compPosts))
						}
					}
				}
			}

			// If still no posts, fallback to any recent posts
			if len(compPosts) == 0 {
				fmt.Printf("No competitor-specific posts found, fetching any recent posts\n")
				recentPosts, err := q.GetRecentCompetitorPosts(ctx, db.GetRecentCompetitorPostsParams{
					UserID:  int32(userID),
					GroupID: sql.NullInt32{Int32: ar.GroupID, Valid: true},
					Limit:   5,
				})
				if err != nil {
					fmt.Printf("GetRecentCompetitorPosts error: %v\n", err)
				} else {
					fmt.Printf("GetRecentCompetitorPosts found %d posts\n", len(recentPosts))
					for _, rp := range recentPosts {
						compPosts = append(compPosts, db.SearchCompetitorPostsRow{
							ID:                 rp.ID,
							CompetitorID:       rp.CompetitorID,
							Platform:           rp.Platform,
							PostID:             rp.PostID,
							Content:            rp.Content,
							PostedAt:           rp.PostedAt,
							Engagement:         rp.Engagement,
							CompetitorUsername: rp.CompetitorUsername,
							Relevance:          0,
						})
					}
				}
			}
		}

		// Topic filter removed - not needed for indie games/marketing RAG
		// The vector search already returns relevant results

		// Build context + hits list
		hits := make([]askHit, 0, len(rows))
		var b strings.Builder

		// Add game context if available (FIRST, before anything else)
		gameCtx, gameCtxErr := q.GetGameContext(ctx, db.GetGameContextParams{
			UserID:  int32(userID),
			GroupID: sql.NullInt32{Int32: ar.GroupID, Valid: true},
		})
		if gameCtxErr == nil {
			b.WriteString("=== Game Information ===\n")

			// Basic info
			if gameCtx.GameTitle != "" {
				fmt.Fprintf(&b, "Title: %s\n", gameCtx.GameTitle)
			}
			if gameCtx.StudioName.Valid {
				fmt.Fprintf(&b, "Studio: %s\n", gameCtx.StudioName.String)
			}
			if gameCtx.GameSummary.Valid {
				fmt.Fprintf(&b, "Summary: %s\n", gameCtx.GameSummary.String)
			}

			// Technical details
			if len(gameCtx.Platforms) > 0 {
				fmt.Fprintf(&b, "Platforms: %v\n", gameCtx.Platforms)
			}
			if gameCtx.EngineTech.Valid {
				fmt.Fprintf(&b, "Engine/Tech: %s\n", gameCtx.EngineTech.String)
			}

			// Genre and style
			if gameCtx.PrimaryGenre.Valid {
				fmt.Fprintf(&b, "Genre: %s", gameCtx.PrimaryGenre.String)
				if gameCtx.Subgenre.Valid {
					fmt.Fprintf(&b, " (%s)", gameCtx.Subgenre.String)
				}
				b.WriteString("\n")
			}
			if gameCtx.KeyMechanics.Valid {
				fmt.Fprintf(&b, "Key Mechanics: %s\n", gameCtx.KeyMechanics.String)
			}
			if gameCtx.PlaytimeLength.Valid {
				fmt.Fprintf(&b, "Playtime: %s\n", gameCtx.PlaytimeLength.String)
			}
			if gameCtx.ArtStyle.Valid {
				fmt.Fprintf(&b, "Art Style: %s\n", gameCtx.ArtStyle.String)
			}
			if gameCtx.Tone.Valid {
				fmt.Fprintf(&b, "Tone: %s\n", gameCtx.Tone.String)
			}

			// Audience
			if gameCtx.IntendedAudience.Valid {
				fmt.Fprintf(&b, "Target Audience: %s\n", gameCtx.IntendedAudience.String)
			}
			if gameCtx.AgeRange.Valid {
				fmt.Fprintf(&b, "Age Range: %s\n", gameCtx.AgeRange.String)
			}
			if gameCtx.PlayerMotivation.Valid {
				fmt.Fprintf(&b, "Player Motivation: %s\n", gameCtx.PlayerMotivation.String)
			}
			if gameCtx.ComparableGames.Valid {
				fmt.Fprintf(&b, "Similar Games: %s\n", gameCtx.ComparableGames.String)
			}

			// Marketing
			if gameCtx.MarketingObjective.Valid {
				fmt.Fprintf(&b, "Marketing Goal: %s\n", gameCtx.MarketingObjective.String)
			}
			if gameCtx.KeyEventsDates.Valid {
				fmt.Fprintf(&b, "Key Events/Dates: %s\n", gameCtx.KeyEventsDates.String)
			}
			if gameCtx.CallToAction.Valid {
				fmt.Fprintf(&b, "Call to Action: %s\n", gameCtx.CallToAction.String)
			}

			// Restrictions
			if gameCtx.ContentRestrictions.Valid {
				fmt.Fprintf(&b, "Content Restrictions: %s\n", gameCtx.ContentRestrictions.String)
			}
			if gameCtx.CompetitorsToAvoid.Valid {
				fmt.Fprintf(&b, "Competitors to Avoid: %s\n", gameCtx.CompetitorsToAvoid.String)
			}
			if gameCtx.AdditionalInfo.Valid {
				fmt.Fprintf(&b, "Additional Info: %s\n", gameCtx.AdditionalInfo.String)
			}

			b.WriteString("\n")
		}

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
		}

		if len(compPosts) > 0 {
			b.WriteString("=== Competitor Posts ===\n")
			for i, cp := range compPosts {
				content := "No content"
				if cp.Content.Valid {
					content = cp.Content.String
				}
				if len(content) > 500 {
					content = content[:500] + "..."
				}
				postedAt := "Unknown date"
				if cp.PostedAt.Valid {
					postedAt = cp.PostedAt.Time.Format("2006-01-02")
				}

				// Cite as [CP1], [CP2] etc.
				fmt.Fprintf(&b, "[CP%d] %s (%s) @%s: %s\n\n",
					i+1, cp.Platform, postedAt, cp.CompetitorUsername, content)

				hits = append(hits, askHit{
					DocumentID: fmt.Sprintf("post:%s:%s", cp.Platform, cp.PostID),
					Page:       0,
					Index:      0,
					Snippet:    content,
				})
			}
		}

		if len(rows) == 0 && len(compPosts) == 0 && len(history) > 0 {
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
		if len(rows) == 0 && len(compPosts) == 0 && len(history) == 0 && !hasClientHistory {
			if !ar.AllowOutside {
				c.JSON(http.StatusOK, askResp{
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
		} else if hasClientHistory && len(rows) == 0 && len(compPosts) == 0 && len(history) == 0 {
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
			fmt.Printf("callOllamaWithOptions error: %v\n", err)
			if len(rows) == 0 && len(compPosts) == 0 {
				ans = fmt.Sprintf("No relevant context on this topic in your PDFs. Enable allow_outside or upload a relevant document. (Error: %v)", err)
			} else {
				ans = fmt.Sprintf("Unable to generate a grounded answer. Error: %v", err)
			}
		}
		fmt.Printf("DEBUG: ans='%s', err=%v\n", ans, err)

		// Require numeric page citations when any Context existed (fresh or reused) and not opinion
		if (len(rows) > 0 || len(compPosts) > 0 || len(history) > 0) && citeRe.FindStringIndex(ans) == nil && mode != "opinion" {
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

		c.JSON(http.StatusOK, askResp{Answer: strings.TrimSpace(ans), Hits: hits})
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
	b.WriteString("Instructions: Use ONLY the Context above. If the answer is not present, say you don't know. Cite pages like [p.X] or posts like [CPX].\n")
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
	b.WriteString("Instructions: Use the Context above to answer questions. Cite pages like [p.X] or posts like [CPX] when referencing the context.\n")
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
	fmt.Fprintf(&b, "Rules:\n- Prefer evidence from Context and cite [p.X] or [CPX].\n- allow_outside=%v. If you add outside knowledge, add a separate 'Assumptions' section.\n- If Context is insufficient and allow_outside=false, say you don’t know.\n", ar.AllowOutside)
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

			// Read body to debug
			bodyBytes, _ := io.ReadAll(resp.Body)
			fmt.Printf("DEBUG OLLAMA RAW: %s\n", string(bodyBytes))

			// Restore body for decoder (or just decode from bytes)
			var out struct {
				Message struct {
					Content string `json:"content"`
				} `json:"message"`
			}
			if json.Unmarshal(bodyBytes, &out) == nil {
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

// extractCompetitorName tries to extract a competitor name from the question
// This is a simple heuristic that looks for patterns like "like X's" or "from X"
func extractCompetitorName(question string) string {
	// Common patterns that might indicate a competitor mention:
	// "like Cbum's", "from Cbum", "Cbum's posts", etc.
	patterns := []string{
		`like\s+(\w+)'?s?`,      // "like Cbum's"
		`from\s+(\w+)`,          // "from Cbum"
		`@(\w+)`,                // "@cbum"
		`(\w+)'?s?\s+posts?`,    // "Cbum's posts"
		`(\w+)'?s?\s+content`,   // "Cbum's content"
		`style\s+of\s+(\w+)`,    // "style of Cbum"
		`similar\s+to\s+(\w+)`,  // "similar to Cbum"
	}

	for _, pattern := range patterns {
		re := regexp.MustCompile(`(?i)` + pattern)
		if matches := re.FindStringSubmatch(question); len(matches) > 1 {
			name := matches[1]
			// Filter out common words that aren't names
			commonWords := map[string]bool{
				"the": true, "this": true, "that": true, "their": true,
				"them": true, "these": true, "those": true, "my": true,
				"your": true, "his": true, "her": true, "its": true,
			}
			if !commonWords[strings.ToLower(name)] && len(name) > 2 {
				return name
			}
		}
	}
	return ""
}
