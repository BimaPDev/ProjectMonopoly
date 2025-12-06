// internal/handlers/workshop_search.go
package handlers

import (
	"log"
	"net/http"
	"strings"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/BimaPDev/ProjectMonopoly/internal/utils"
	"github.com/gin-gonic/gin"
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

func WorkshopSearchHandler(q *db.Queries) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req searchReq
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "invalid json"})
			return
		}
		query := strings.TrimSpace(req.Q)
		if query == "" {
			query = strings.TrimSpace(req.Query)
		}
		if query == "" || req.GroupID == 0 {
			c.JSON(http.StatusBadRequest, gin.H{"error": "missing q or group_id"})
			return
		}
		limit := req.Limit
		if limit <= 0 || limit > 20 {
			limit = 6
		}

		userID, err := utils.GetUserID(c)
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
			return
		}

		// 1) BM25/TS query
		rows, err := q.SearchChunks(c.Request.Context(), db.SearchChunksParams{
			Q:       query,
			UserID:  int32(userID),
			GroupID: req.GroupID,
			N:       limit,
		})
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "db error"})
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
			fz, err := q.FuzzyChunks(c.Request.Context(), db.FuzzyChunksParams{
				Q:       query,
				UserID:  int32(userID),
				GroupID: req.GroupID,
				N:       limit,
			})
			if err != nil {
				c.JSON(http.StatusInternalServerError, gin.H{"error": "db error"})
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

		c.JSON(http.StatusOK, searchResp{Query: query, Hits: hits})
	}
}
