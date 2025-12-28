package handlers

import (
	"database/sql"
	"log"
	"net/http"
	"strconv"
	"time"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/BimaPDev/ProjectMonopoly/internal/utils"
	"github.com/gin-gonic/gin"
)

// ProfileResponse represents a profile with clean JSON values
type ProfileResponse struct {
	ID               string  `json:"id"`
	Platform         string  `json:"platform"`
	Handle           string  `json:"handle"`
	ProfileURL       string  `json:"profile_url"`
	Followers        int64   `json:"followers"`
	EngagementRate   float64 `json:"engagement_rate"`
	GrowthRate       float64 `json:"growth_rate"`
	PostingFrequency float64 `json:"posting_frequency"`
	LastChecked      *string `json:"last_checked"`
}

// CompetitorWithProfiles represents a competitor with all their profiles
type CompetitorWithProfiles struct {
	ID          string            `json:"id"`
	DisplayName string            `json:"display_name"`
	LastChecked *string           `json:"last_checked"`
	TotalPosts  int64             `json:"total_posts"`
	Profiles    []ProfileResponse `json:"profiles"`
}

// ListCompetitorsWithProfiles returns all competitors for the user with their profiles
func ListCompetitorsWithProfiles(c *gin.Context, queries *db.Queries) {
	ctx := c.Request.Context()

	userID, err := utils.GetUserID(c)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
		return
	}

	// Get group_id from query params (required for proper scoping)
	var groupID sql.NullInt32
	if groupIDStr := c.Query("group_id"); groupIDStr != "" {
		if gid, err := strconv.Atoi(groupIDStr); err == nil {
			groupID = sql.NullInt32{Int32: int32(gid), Valid: true}
		}
	}

	// Get all competitors for this user and group
	competitors, err := queries.ListCompetitorsWithProfiles(ctx, db.ListCompetitorsWithProfilesParams{
		UserID:  userID,
		GroupID: groupID,
	})
	if err != nil {
		log.Printf("❌ Failed to list competitors: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch competitors"})
		return
	}

	// For each competitor, fetch their profiles
	result := make([]CompetitorWithProfiles, 0, len(competitors))
	for _, comp := range competitors {
		profiles, err := queries.GetProfileStats(ctx, comp.ID)
		if err != nil {
			log.Printf("⚠️ Failed to get profiles for competitor %s: %v", comp.ID, err)
			profiles = []db.GetProfileStatsRow{}
		}

		// Convert profiles to clean response format and track latest last_checked
		profileResponses := make([]ProfileResponse, 0, len(profiles))
		var latestLastChecked time.Time
		hasLastChecked := false
		for _, p := range profiles {
			var lastChecked *string
			if p.LastChecked.Valid {
				t := p.LastChecked.Time.Format(time.RFC3339)
				lastChecked = &t
				// Track the most recent last_checked from all profiles
				if !hasLastChecked || p.LastChecked.Time.After(latestLastChecked) {
					latestLastChecked = p.LastChecked.Time
					hasLastChecked = true
				}
			}

			var followers int64
			if p.Followers.Valid {
				followers = p.Followers.Int64
			}

			var engagementRate, growthRate, postingFreq float64
			if p.EngagementRate.Valid {
				engagementRate, _ = strconv.ParseFloat(p.EngagementRate.String, 64)
			}
			if p.GrowthRate.Valid {
				growthRate, _ = strconv.ParseFloat(p.GrowthRate.String, 64)
			}
			if p.PostingFrequency.Valid {
				postingFreq, _ = strconv.ParseFloat(p.PostingFrequency.String, 64)
			}

			profileURL := ""
			if p.ProfileUrl.Valid {
				profileURL = p.ProfileUrl.String
			}

			profileResponses = append(profileResponses, ProfileResponse{
				ID:               p.ID.String(),
				Platform:         p.Platform,
				Handle:           p.Handle,
				ProfileURL:       profileURL,
				Followers:        followers,
				EngagementRate:   engagementRate,
				GrowthRate:       growthRate,
				PostingFrequency: postingFreq,
				LastChecked:      lastChecked,
			})
		}

		displayName := ""
		if comp.DisplayName.Valid {
			displayName = comp.DisplayName.String
		}

		// Use the most recent last_checked from profiles (this is what the scraper updates)
		var compLastChecked *string
		if hasLastChecked {
			t := latestLastChecked.Format(time.RFC3339)
			compLastChecked = &t
		} else if comp.LastChecked.Valid {
			// Fallback to competitor-level last_checked if no profile has one
			t := comp.LastChecked.Time.Format(time.RFC3339)
			compLastChecked = &t
		}

		var totalPosts int64
		if comp.TotalPosts.Valid {
			totalPosts = comp.TotalPosts.Int64
		}

		result = append(result, CompetitorWithProfiles{
			ID:          comp.ID.String(),
			DisplayName: displayName,
			LastChecked: compLastChecked,
			TotalPosts:  totalPosts,
			Profiles:    profileResponses,
		})
	}

	c.JSON(http.StatusOK, result)
}
