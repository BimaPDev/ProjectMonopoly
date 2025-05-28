package handlers

import (
	"database/sql"
	"encoding/json"
	"log"
	"net/http"
	"strconv"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
)

type SocialTokenRequest struct {
	UserID  int32  `json:"user_id"`
	GroupID int32  `json:"group_id"`
	Type    string `json:"type"`  // 'tiktok', 'instagram', etc.
	Token   string `json:"token"` // whatever you're saving
}

func SaveSocialToken(w http.ResponseWriter, r *http.Request, queries *db.Queries) {
	if r.Method != http.MethodPost {
		http.Error(w, "Invalid request method", http.StatusMethodNotAllowed)
		return
	}

	var req SocialTokenRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if req.UserID == 0 || req.GroupID == 0 || req.Token == "" || req.Type == "" {
		http.Error(w, "Missing required fields", http.StatusBadRequest)
		return
	}

	// Step 1: Check group ownership
	group, err := queries.GetGroupByID(r.Context(), req.GroupID)
	if err != nil {
		http.Error(w, "Group not found", http.StatusNotFound)
		return
	}
	if group.UserID != req.UserID {
		http.Error(w, "You do not own this group", http.StatusForbidden)
		return
	}

	// Step 2: Marshal token
	jsonData, err := json.Marshal(map[string]string{
		"token": req.Token,
	})
	if err != nil {
		http.Error(w, "Failed to marshal token", http.StatusInternalServerError)
		return
	}

	// Step 3: Insert if not exists
	insertedRows, insertErr := queries.InsertGroupItemIfNotExists(r.Context(), db.InsertGroupItemIfNotExistsParams{
		GroupID: req.GroupID,
		Type:    sql.NullString{String: req.Type, Valid: req.Type != ""},
		Data:    jsonData,
	})
	if insertErr != nil {
		log.Println("InsertGroupItemIfNotExists ERROR:", insertErr) // 👈 add this
		http.Error(w, "Failed to insert group item", http.StatusInternalServerError)
		return
	}

	// Step 4: Always try to update (should always hit if insert failed due to conflict)
	updatedRows, updateErr := queries.UpdateGroupItemData(r.Context(), db.UpdateGroupItemDataParams{
		GroupID: req.GroupID,
		Type:    sql.NullString{String: req.Type, Valid: req.Type != ""},
		Data:    jsonData,
	})
	if updateErr != nil {
		http.Error(w, "Failed to update group item", http.StatusInternalServerError)
		return
	}

	// ✅ Bug check: Neither insert nor update did anything
	if insertedRows == 0 && updatedRows == 0 {
		http.Error(w, "Nothing was saved. Check if the group/type is valid.", http.StatusInternalServerError)
		return
	}

	// ✅ Success
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]string{
		"message": "Token saved successfully",
		"type":    req.Type,
	})
}

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
