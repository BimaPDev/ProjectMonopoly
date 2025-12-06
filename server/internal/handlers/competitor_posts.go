package handlers

import (
	"database/sql"
	"log"
	"net/http"
	"strconv"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/BimaPDev/ProjectMonopoly/internal/utils"
	"github.com/gin-gonic/gin"
)

func ListVisibleCompetitorPosts(c *gin.Context, queries *db.Queries) {
	ctx := c.Request.Context()

	// Step 1: Get user ID from context
	userID, err := utils.GetUserID(c)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
		return
	}

	// Step 2: Try to get groupID from query param ?group_id=1
	groupIDStr := c.Query("group_id")

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
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to fetch posts"})
		return
	}

	// Step 4: Return result
	c.JSON(http.StatusOK, posts)
}
