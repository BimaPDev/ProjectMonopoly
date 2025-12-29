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

	// Check if competitor already exists by platform and username
	var competitor db.Competitor
	var profileID string
	existing, err := queries.GetCompetitorByPlatformUsername(c.Request.Context(), db.GetCompetitorByPlatformUsernameParams{
		Platform: parsed.Platform,
		Lower:    parsed.Username,
	})
	if err == nil {
		competitor = existing
		// Get the profile for response (optional, just for profile_url)
		profile, profErr := queries.GetProfileByCompetitorAndPlatform(c.Request.Context(), db.GetProfileByCompetitorAndPlatformParams{
			CompetitorID: competitor.ID,
			Platform:     parsed.Platform,
		})
		if profErr == nil {
			profileID = profile.ID.String()
		}
	} else {
		// Create new competitor entity (just display_name)
		newComp, err := queries.CreateCompetitor(c.Request.Context(), sql.NullString{String: parsed.Username, Valid: true})
		if err != nil {
			log.Printf("❌ Failed to create competitor: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create competitor"})
			return
		}
		competitor = newComp

		// Create competitor profile with platform, handle, profile_url
		profile, err := queries.CreateCompetitorProfile(c.Request.Context(), db.CreateCompetitorProfileParams{
			CompetitorID: competitor.ID,
			Platform:     parsed.Platform,
			Handle:       parsed.Username,
			ProfileUrl:   sql.NullString{String: parsed.ProfileURL, Valid: parsed.ProfileURL != ""},
		})
		if err != nil {
			log.Printf("❌ Failed to create competitor profile: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create competitor profile"})
			return
		}
		profileID = profile.ID.String()
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

	// Success response - use new field names
	displayName := parsed.Username
	if competitor.DisplayName.Valid {
		displayName = competitor.DisplayName.String
	}

	resp := map[string]interface{}{
		"message": "Competitor added",
		"competitor": map[string]interface{}{
			"id":           competitor.ID,
			"platform":     parsed.Platform,
			"username":     parsed.Username,
			"display_name": displayName,
			"profile_url":  parsed.ProfileURL,
			"profile_id":   profileID,
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

// AddProfileToCompetitorRequest represents the request body for adding a profile
type AddProfileToCompetitorRequest struct {
	Handle   string `json:"handle"`
	Platform string `json:"platform"`
}

// AddProfileToCompetitor adds a new platform profile to an existing competitor
func AddProfileToCompetitor(c *gin.Context, queries *db.Queries) {
	// Get competitor ID from URL param
	competitorIDStr := c.Param("id")
	if competitorIDStr == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Competitor ID is required"})
		return
	}

	// Parse competitor ID as UUID
	competitorID, err := utils.ParseUUID(competitorIDStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid competitor ID format"})
		return
	}

	// Check user is authenticated
	_, err = utils.GetUserID(c)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
		return
	}

	// Parse request body
	var req AddProfileToCompetitorRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid JSON body"})
		return
	}

	// Validate required fields
	if req.Handle == "" || req.Platform == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "handle and platform are required"})
		return
	}

	// Parse social input (@username or URL)
	parsed, err := utils.ParseSocialInput(req.Handle, req.Platform)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": fmt.Sprintf("Failed to parse input: %v", err)})
		return
	}

	// Check if profile already exists for this competitor and platform
	existingProfile, err := queries.GetProfileByCompetitorAndPlatform(c.Request.Context(), db.GetProfileByCompetitorAndPlatformParams{
		CompetitorID: competitorID,
		Platform:     parsed.Platform,
	})
	if err == nil {
		// Profile already exists
		c.JSON(http.StatusConflict, gin.H{
			"error":      "Profile already exists for this platform",
			"profile_id": existingProfile.ID.String(),
		})
		return
	}

	// Create new competitor profile
	profile, err := queries.CreateCompetitorProfile(c.Request.Context(), db.CreateCompetitorProfileParams{
		CompetitorID: competitorID,
		Platform:     parsed.Platform,
		Handle:       parsed.Username,
		ProfileUrl:   sql.NullString{String: parsed.ProfileURL, Valid: parsed.ProfileURL != ""},
	})
	if err != nil {
		log.Printf("❌ Failed to create competitor profile: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create competitor profile"})
		return
	}

	log.Printf("✅ Added %s profile for competitor %s: @%s", parsed.Platform, competitorIDStr, parsed.Username)

	c.JSON(http.StatusOK, gin.H{
		"message": "Profile added successfully",
		"profile": map[string]interface{}{
			"id":          profile.ID.String(),
			"platform":    parsed.Platform,
			"handle":      parsed.Username,
			"profile_url": parsed.ProfileURL,
		},
	})

	// Trigger scraper in background
	go func() {
		if err := utils.TriggerWeeklyScraper(); err != nil {
			log.Printf("⚠️ Failed to trigger background scraper: %v", err)
		} else {
			log.Printf("🚀 Triggered background scraper for new profile")
		}
	}()
}
