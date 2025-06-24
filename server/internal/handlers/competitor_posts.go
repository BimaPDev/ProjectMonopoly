package handlers

import (
	"database/sql"
	"encoding/json"
	"log"
	"net/http"
	"strconv"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/BimaPDev/ProjectMonopoly/internal/utils"
)

func ListVisibleCompetitorPosts(w http.ResponseWriter, r *http.Request, queries *db.Queries) {
	ctx := r.Context()

	// Step 1: Get user ID from context
	userID, err := utils.GetUserIDFromRequest(r)
	if err != nil {
		http.Error(w, "unauthorized", http.StatusUnauthorized)
		return
	}

	// Step 2: Try to get groupID from query param ?group_id=1
	groupIDStr := r.URL.Query().Get("group_id")

	var groupID sql.NullInt32
	if groupIDStr != "" {
		if gid, err := strconv.Atoi(groupIDStr); err == nil {
			groupID = sql.NullInt32{Int32: int32(gid), Valid: true}
		}
	} else {
		groupID = sql.NullInt32{Valid: false}
	}

	// Step 3: Run query
	posts, err := queries.ListVisibleCompetitorPosts(ctx, db.ListVisibleCompetitorPostsParams{
		UserID:  userID,
		GroupID: groupID,
	})
	if err != nil {
		log.Printf("❌ DB error: %v", err)
		http.Error(w, "failed to fetch posts", http.StatusInternalServerError)
		return
	}

	// Step 4: Return result
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(posts)
}
