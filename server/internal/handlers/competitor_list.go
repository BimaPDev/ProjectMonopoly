package handlers

import (
	"encoding/json"
	"log"
	"net/http"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/BimaPDev/ProjectMonopoly/internal/utils"
)

func ListUserCompetitors(w http.ResponseWriter, r *http.Request, queries *db.Queries) {
	// TODO: Replace with real user session logic
	userID, err := utils.GetUserIDFromRequest(r)
    	if err != nil {
    		http.Error(w, "unauthorized", http.StatusUnauthorized)
    		return
    	}

	// Query DB
	competitors, err := queries.ListUserCompetitors(r.Context(), userID)
	if err != nil {
		log.Printf("❌ Failed to list user competitors: %v", err)
		http.Error(w, "Failed to fetch competitors", http.StatusInternalServerError)
		return
	}

	// Success
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(competitors)
}
