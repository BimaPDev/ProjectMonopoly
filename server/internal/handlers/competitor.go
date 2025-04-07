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

	var req CreateCompetitorRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON body", http.StatusBadRequest)
		return
	}

	parsed, err := utils.ParseSocialInput(req.Input, req.Platform)
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to parse input: %v", err), http.StatusBadRequest)
		return
	}

	params := db.CreateCompetitorParams{
		GroupID:    int32(groupID),
		Platform:   parsed.Platform,
		Username:   parsed.Username,
		ProfileUrl: parsed.ProfileURL,
	}

	err = queries.CreateCompetitor(r.Context(), params)
	if err != nil {
	log.Printf("❌ DB error while creating competitor: %v", err) // 👈 Add this
	http.Error(w, "Failed to create competitor", http.StatusInternalServerError)
	return
	}

	resp := map[string]string{
		"message":     "Competitor added",
		"profile_url": parsed.ProfileURL,
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}
