package handlers

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/sqlc-dev/pqtype"
)

// Create a new group
type CreateGroupRequest struct {
	UserID      int32  `json:"userID"`
	Name        string `json:"name"`
	Description string `json:"description"`
}

func CreateGroup(w http.ResponseWriter, r *http.Request, queries *db.Queries) {
	if r.Method != http.MethodPost {
		http.Error(w, "Invalid request method", http.StatusMethodNotAllowed)
		return
	}

	var req CreateGroupRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if req.UserID == 0 || req.Name == "" {
		http.Error(w, "Missing required fields", http.StatusBadRequest)
		return
	}

	group, err := queries.CreateGroup(r.Context(), db.CreateGroupParams{
		UserID:      req.UserID,
		Name:        req.Name,
		Description: sql.NullString{String: req.Description, Valid: req.Description != ""},
	})
	if err != nil {
		http.Error(w, "Failed to create group", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(group)
}

type groupResponse struct {
	ID          int32  `json:"ID"`
	Name        string `json:"name"`
	Description string `json:"description"`
}

func GetGroups(w http.ResponseWriter, r *http.Request, q *db.Queries) {

	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// 1. Grab as string and validate
	uidStr := r.URL.Query().Get("userID")
	if uidStr == "" {
		http.Error(w, "userID is required", http.StatusBadRequest)
		return
	}

	// 2. Parse to int
	uidInt, err := strconv.Atoi(uidStr)
	if err != nil {
		http.Error(w, "invalid userID", http.StatusBadRequest)
		return
	}
	userID := int32(uidInt) // 3. Convert to int32

	// 4. Call your generated query
	groups, err := q.ListGroupsByUser(r.Context(), userID)
	if err != nil {
		http.Error(w, "could not list groups", http.StatusInternalServerError)
		return
	}

	// map to clean JSON
	out := make([]groupResponse, 0, len(groups))
	for _, g := range groups {
		desc := ""
		if g.Description.Valid {
			desc = g.Description.String
		}
		out = append(out, groupResponse{
			ID:          g.ID,
			Name:        g.Name,
			Description: desc,
		})
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(out)
}

type AddGroupitem struct {
	groupID  int    `json:"groupID"`
	username string `json:"userName"`
	password string `json:"password"`
	platform string `json:"platform"`
}

func AddGroupItem(w http.ResponseWriter, r *http.Request, q *db.Queries) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req AddGroupitem
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Create the data JSON object
	dataJSON := map[string]string{
		"username": req.username,
		"password": req.password,
	}

	// Convert to JSON bytes
	dataBytes, err := json.Marshal(dataJSON)
	if err != nil {
		http.Error(w, "Error processing data", http.StatusInternalServerError)
		return
	}

	response, err := q.InsertGroupItemIfNotExists(r.Context(), db.InsertGroupItemIfNotExistsParams{
		GroupID:  int32(req.groupID),
		Platform: req.platform,
		Data: pqtype.NullRawMessage{
			RawMessage: dataBytes,
			Valid:      true,
		},
	})

	if err != nil {
		http.Error(w, fmt.Sprintf("Database error: %v", err), http.StatusInternalServerError)
		return
	}

	// Send success response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"id":      response.ID, // Adjust based on what your query returns
	})
}
