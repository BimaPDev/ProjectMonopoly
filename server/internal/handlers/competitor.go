package handlers

import (
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
	Input    string `json:"input"`
	Platform string `json:"platform"`
}

func CreateCompetitor(w http.ResponseWriter, r *http.Request, queries *db.Queries) {
	// Extract group ID from URL
	parts := strings.Split(r.URL.Path, "/")
	if len(parts) < 4 {
		http.Error(w, "Invalid path. Expected /api/groups/{group_id}/competitors", http.StatusBadRequest)
		return
	}

	groupIDStr := parts[3]
	groupID, err := strconv.Atoi(groupIDStr)
	if err != nil {
		http.Error(w, "Invalid group ID", http.StatusBadRequest)
		return
	}

	// Parse request body
	var req CreateCompetitorRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON body", http.StatusBadRequest)
		return
	}

	// Parse social input (e.g., @username or full URL)
	parsed, err := utils.ParseSocialInput(req.Input, req.Platform)
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to parse input: %v", err), http.StatusBadRequest)
		return
	}

	// Build params for DB insert
	params := db.CreateCompetitorParams{
		GroupID:    int32(groupID),
		Platform:   parsed.Platform,
		Username:   parsed.Username,
		ProfileUrl: parsed.ProfileURL,
	}

	// Insert into DB
	competitor, err := queries.CreateCompetitor(r.Context(), params)
	if err != nil {
		log.Printf("❌ DB error while creating competitor: %v", err)
		http.Error(w, "Failed to create competitor", http.StatusInternalServerError)
		return
	}

	// Success response
	resp := map[string]interface{}{
		"message":      "Competitor added",
		"competitor": map[string]interface{}{
			"id":          competitor.ID,
			"group_id":    competitor.GroupID,
			"platform":    competitor.Platform,
			"username":    competitor.Username,
			"profile_url": competitor.ProfileUrl,
			"created_at":  competitor.LastChecked,
		},
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}
