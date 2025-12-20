package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"strconv"
	"time"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	_ "github.com/lib/pq"
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

func main() {
	connStr := "user=root password=secret dbname=project_monopoly sslmode=disable"
	dbConn, err := sql.Open("postgres", connStr)
	if err != nil {
		log.Fatal(err)
	}
	defer dbConn.Close()

	queries := db.New(dbConn)
	ctx := context.Background()

	// Assuming user ID 1 for testing (from logs)
	userID := int32(1)

	competitors, err := queries.ListCompetitorsWithProfiles(ctx, userID)
	if err != nil {
		log.Fatalf("Failed to list competitors: %v", err)
	}

	result := make([]CompetitorWithProfiles, 0, len(competitors))
	for _, comp := range competitors {
		profiles, err := queries.GetProfileStats(ctx, comp.ID)
		if err != nil {
			log.Printf("Failed to get profiles: %v", err)
			profiles = []db.GetProfileStatsRow{}
		}

		profileResponses := make([]ProfileResponse, 0, len(profiles))
		var latestLastChecked time.Time
		hasLastChecked := false

		for _, p := range profiles {
			var lastChecked *string
			if p.LastChecked.Valid {
				t := p.LastChecked.Time.Format(time.RFC3339)
				lastChecked = &t
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

		var compLastChecked *string
		if hasLastChecked {
			t := latestLastChecked.Format(time.RFC3339)
			compLastChecked = &t
		} else if comp.LastChecked.Valid {
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

	jsonData, _ := json.MarshalIndent(result, "", "  ")
	fmt.Println(string(jsonData))
}
