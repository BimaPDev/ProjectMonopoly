package handlers

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strings"
	"time"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
)

type askReq struct {
	GroupID  int32  `json:"group_id"`
	Question string `json:"question"`
	Limit    int32  `json:"limit"`
	Model    string `json:"model"`
}

type askResp struct {
	Answer string      `json:"answer"`
	Hits   []searchHit `json:"hits"`
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
			limit = 5
		}

		ctx := r.Context()
		rows, _ := q.SearchChunks(ctx, db.SearchChunksParams{
			Q: ar.Question,
			UserID:  int32(userID),
			GroupID: ar.GroupID,
			N:   limit,
		})
		if len(rows) == 0 {
			fz, _ := q.FuzzyChunks(ctx, db.FuzzyChunksParams{
    			Q: ar.Question,
				UserID:  int32(userID),
				GroupID: ar.GroupID,
				N:   limit,          // $4
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

		hits := make([]searchHit, 0, len(rows))
		var b strings.Builder
		for i, rr := range rows {
			page := int32(0)
			if rr.Page.Valid {
				page = rr.Page.Int32
			}

			snip := rr.Content
			if len(snip) > 200 {
				snip = snip[:200] + "..."
			}
			hits = append(hits, searchHit{
				DocumentID: rr.DocumentID.String(),
				Page:       page,
				Index:      rr.ChunkIndex,
				Snippet:    snip,
			})

			fmt.Fprintf(&b, "\n---\n# Chunk %d (p.%d)\n%s\n", i+1, page, rr.Content)
		}

		prompt := "Use only the context to answer concisely. If unknown, say you don't know.\n\nContext:\n" +
			b.String() + "\n\nQuestion: " + ar.Question

		model := ar.Model
		if model == "" {
			model = envOr("OLLAMA_MODEL", "llama3.1:8b")
		}
		host := envOr("OLLAMA_HOST", "http://localhost:11434")

		answer, err := callOllama(ctx, host, model, prompt)
		if err != nil {
			http.Error(w, "llm error", http.StatusBadGateway)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(askResp{Answer: answer, Hits: hits})
	}
}

func callOllama(ctx context.Context, host, model, prompt string) (string, error) {
	body := map[string]any{
		"model": model,
		"messages": []map[string]string{
			{"role": "system", "content": "You are a precise assistant. Cite page numbers if useful."},
			{"role": "user", "content": prompt},
		},
		"stream": false,
	}
	b, _ := json.Marshal(body)
	req, _ := http.NewRequestWithContext(ctx, "POST", host+"/api/chat", bytes.NewReader(b))
	req.Header.Set("Content-Type", "application/json")
	client := &http.Client{Timeout: 60 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	var out struct {
		Message struct {
			Content string `json:"content"`
		} `json:"message"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return "", err
	}
	return out.Message.Content, nil
}

func envOr(k, d string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return d
}
