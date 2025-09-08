package handlers

import (
	"encoding/json"
	"net/http"
	"strconv"
	"strings"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
)

type searchResp struct {
	Query    string      `json:"query"`
	Hits     []searchHit `json:"hits"`
	Fallback bool        `json:"fallback"`
}

type searchHit struct {
	DocumentID string `json:"document_id"`
	Page       int32  `json:"page"`
	Index      int32  `json:"chunk_index"`
	Snippet    string `json:"snippet"`
}

func WorkshopSearchHandler(q *db.Queries) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		userID := ctxUserID(r)

		qstr := strings.TrimSpace(r.URL.Query().Get("q"))
		gidStr := r.URL.Query().Get("group_id")
		limitStr := r.URL.Query().Get("limit")
		if qstr == "" || gidStr == "" {
			http.Error(w, "missing q or group_id", http.StatusBadRequest)
			return
		}
		gid64, _ := strconv.ParseInt(gidStr, 10, 32)
		limit := int32(10)
		if v, err := strconv.ParseInt(limitStr, 10, 32); err == nil && v > 0 && v <= 50 {
			limit = int32(v)
		}

		ctx := r.Context()
		rows, err := q.SearchChunks(ctx, db.SearchChunksParams{
			Q: qstr,             // query text
			UserID:  int32(userID),
			GroupID: int32(gid64),
			N: limit,
		})
		if err != nil {
			http.Error(w, "search failed", http.StatusInternalServerError)
			return
		}

		// fallback to fuzzy if no hits
		if len(rows) == 0 {
			fz, err := q.FuzzyChunks(ctx, db.FuzzyChunksParams{
    			Q:       qstr,
    			UserID:  int32(userID),
    			GroupID: int32(gid64),
    			N:       limit,
			})
			if err != nil {
				http.Error(w, "search failed", http.StatusInternalServerError)
				return
			}
			hits := make([]searchHit, 0, len(fz))
			for _, r2 := range fz {
				page := int32(0)
				if r2.Page.Valid {
					page = r2.Page.Int32
				}
				s := r2.Content
				if len(s) > 400 {
					s = s[:400] + "..."
				}
				hits = append(hits, searchHit{
					DocumentID: r2.DocumentID.String(),
					Page:       page,
					Index:      r2.ChunkIndex,
					Snippet:    s,
				})
			}
			writeJSON(w, searchResp{Query: qstr, Hits: hits, Fallback: true})
			return
		}

		hits := make([]searchHit, 0, len(rows))
		for _, r1 := range rows {
			page := int32(0)
			if r1.Page.Valid {
				page = r1.Page.Int32
			}
			s := r1.Content
			if len(s) > 400 {
				s = s[:400] + "..."
			}
			hits = append(hits, searchHit{
				DocumentID: r1.DocumentID.String(),
				Page:       page,
				Index:      r1.ChunkIndex,
				Snippet:    s,
			})
		}
		writeJSON(w, searchResp{Query: qstr, Hits: hits, Fallback: false})
	}
}

func writeJSON(w http.ResponseWriter, v any) {
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(v)
}
