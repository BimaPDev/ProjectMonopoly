package handlers

import (
	"database/sql"
	"fmt"
	"log"
	"net/http"
	"strconv"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/BimaPDev/ProjectMonopoly/internal/utils"
	"github.com/gin-gonic/gin"
)

type CreateCompetitorRequest struct {
	Username string `json:"Username"`
	Platform string `json:"Platform"`
}

func CreateCompetitor(c *gin.Context, queries *db.Queries) {
	// Extract optional group ID from URL param
	var groupID *int32
	if gidStr := c.Param("groupID"); gidStr != "" {
		if gid, err := strconv.Atoi(gidStr); err == nil {
			tmp := int32(gid)
			groupID = &tmp
		}
	}

	currentUserID, err := utils.GetUserID(c)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
		return
	}

	// Parse request body
	var req CreateCompetitorRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid JSON body"})
		return
	}

	// Parse social input (@username or URL)
	parsed, err := utils.ParseSocialInput(req.Username, req.Platform)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": fmt.Sprintf("Failed to parse input: %v", err)})
		return
	}

	// Check if competitor already exists
	var competitor db.Competitor
	existing, err := queries.GetCompetitorByPlatformUsername(c.Request.Context(), db.GetCompetitorByPlatformUsernameParams{
		Platform: parsed.Platform,
		Lower:    parsed.Username,
	})
	if err == nil {
		competitor = existing
	} else {
		// Create new competitor if not found
		newComp, err := queries.CreateCompetitor(c.Request.Context(), db.CreateCompetitorParams{
			Platform:   parsed.Platform,
			Username:   parsed.Username,
			ProfileUrl: parsed.ProfileURL,
		})
		if err != nil {
			log.Printf("❌ Failed to create competitor: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create competitor"})
			return
		}
		competitor = newComp
	}

	// Convert groupID into sql.NullInt32
	var groupVal sql.NullInt32
	if groupID != nil {
		groupVal = sql.NullInt32{Int32: *groupID, Valid: true}
	} else {
		groupVal = sql.NullInt32{Valid: false}
	}

	// Set visibility
	visibility := "group"
	if !groupVal.Valid {
		visibility = "user"
	}

	// Link user to competitor
	err = queries.LinkUserToCompetitor(c.Request.Context(), db.LinkUserToCompetitorParams{
		UserID:       currentUserID,
		GroupID:      groupVal,
		CompetitorID: competitor.ID,
		Visibility:   visibility,
	})
	if err != nil {
		log.Printf("❌ Failed to link user to competitor: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to link competitor"})
		return
	}

	// Success response
	resp := map[string]interface{}{
		"message": "Competitor added",
		"competitor": map[string]interface{}{
			"id":           competitor.ID,
			"platform":     competitor.Platform,
			"username":     competitor.Username,
			"profile_url":  competitor.ProfileUrl,
			"last_checked": competitor.LastChecked,
		},
	}
	c.JSON(http.StatusOK, resp)

	// Trigger scraper in background
	go func() {
		if err := utils.TriggerWeeklyScraper(); err != nil {
			log.Printf("⚠️ Failed to trigger background scraper: %v", err)
		} else {
			log.Printf("🚀 Triggered background scraper for new competitor")
		}
	}()
}
