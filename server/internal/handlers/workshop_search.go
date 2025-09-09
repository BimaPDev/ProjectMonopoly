// internal/handlers/workshop_search.go
package handlers

import (
	"encoding/json"
	"io"
	"log"
	"net/http"
	"strings"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
)

type searchReq struct {
	GroupID int32  `json:"group_id"`
	Q       string `json:"q"`     // primary
	Query   string `json:"query"` // alias
	Limit   int32  `json:"limit"`
}

type searchHit struct {
	DocumentID string `json:"document_id"`
	Page       int32  `json:"page"`
	Index      int32  `json:"chunk_index"`
	Snippet    string `json:"snippet"`
}

type searchResp struct {
	Query string      `json:"query"`
	Hits  []searchHit `json:"hits"`
}

func WorkshopSearchHandler(q *db.Queries) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// read body once for debugging
		raw, _ := io.ReadAll(r.Body)
		_ = r.Body.Close()

		var req searchReq
		if err := json.Unmarshal(raw, &req); err != nil {
			http.Error(w, "invalid json", http.StatusBadRequest)
			log.Printf("[search] bad json: %v body=%s", err, string(raw))
			return
		}
		query := strings.TrimSpace(req.Q)
		if query == "" {
			query = strings.TrimSpace(req.Query)
		}
		if query == "" || req.GroupID == 0 {
			http.Error(w, "missing q or group_id", http.StatusBadRequest)
			log.Printf("[search] missing fields: group_id=%d q='%s' alias='%s' body=%s",
				req.GroupID, req.Q, req.Query, string(raw))
			return
		}
		limit := req.Limit
		if limit <= 0 || limit > 20 {
			limit = 6
		}

		userID := ctxUserID(r)

		// 1) BM25/TS query
		rows, err := q.SearchChunks(r.Context(), db.SearchChunksParams{
			Q:       query,
			UserID:  int32(userID),
			GroupID: req.GroupID,
			N:       limit,
		})
		if err != nil {
			http.Error(w, "db error", http.StatusInternalServerError)
			log.Printf("[search] db error SearchChunks: %v", err)
			return
		}

		hits := make([]searchHit, 0, limit)

		if len(rows) > 0 {
			for _, rr := range rows {
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
			}
		} else {
			// 2) Trigram fuzzy fallback
			fz, err := q.FuzzyChunks(r.Context(), db.FuzzyChunksParams{
				Q:       query,
				UserID:  int32(userID),
				GroupID: req.GroupID,
				N:       limit,
			})
			if err != nil {
				http.Error(w, "db error", http.StatusInternalServerError)
				log.Printf("[search] db error FuzzyChunks: %v", err)
				return
			}
			for _, rr := range fz {
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
			}
		}

		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(searchResp{Query: query, Hits: hits})
	}
}