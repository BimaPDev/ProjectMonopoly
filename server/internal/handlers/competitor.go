package handlers

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strconv"
	"strings"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/BimaPDev/ProjectMonopoly/internal/utils"
)

type CreateCompetitorRequest struct {
	Username string `json:"Username"`
	Platform string `json:"Platform"`
}

func CreateCompetitor(w http.ResponseWriter, r *http.Request, queries *db.Queries) {
	// Extract optional group ID from URL
	parts := strings.Split(r.URL.Path, "/")
	var groupID *int32
	if len(parts) >= 4 {
		if gid, err := strconv.Atoi(parts[3]); err == nil {
			tmp := int32(gid)
			groupID = &tmp
		}
	}

	currentUserID, err := utils.GetUserIDFromRequest(r)
	if err != nil {
		http.Error(w, "unauthorized", http.StatusUnauthorized)
		return
	}

	// Parse request body
	var req CreateCompetitorRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON body", http.StatusBadRequest)
		return
	}

	// Parse social input (@username or URL)
	parsed, err := utils.ParseSocialInput(req.Username, req.Platform)
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to parse input: %v", err), http.StatusBadRequest)
		return
	}

	// Check if competitor already exists
	var competitor db.Competitor
	existing, err := queries.GetCompetitorByPlatformUsername(r.Context(), db.GetCompetitorByPlatformUsernameParams{
		Platform: parsed.Platform,
		Username: parsed.Username,
	})
	if err == nil {
		competitor = existing
	} else {
		// Create new competitor if not found
		newComp, err := queries.CreateCompetitor(r.Context(), db.CreateCompetitorParams{
			Platform:   parsed.Platform,
			Username:   parsed.Username,
			ProfileUrl: parsed.ProfileURL,
		})
		if err != nil {
			log.Printf("❌ Failed to create competitor: %v", err)
			http.Error(w, "Failed to create competitor", http.StatusInternalServerError)
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
	err = queries.LinkUserToCompetitor(r.Context(), db.LinkUserToCompetitorParams{
		UserID:       currentUserID,
		GroupID:      groupVal,
		CompetitorID: competitor.ID,
		Visibility:   visibility,
	})
	if err != nil {
		log.Printf("❌ Failed to link user to competitor: %v", err)
		http.Error(w, "Failed to link competitor", http.StatusInternalServerError)
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
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}
