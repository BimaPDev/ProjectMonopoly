package handlers

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
)

type TikTokSessionRequest struct {
	UserID    int32  `json:"user_id"`
	GroupID   int32  `json:"group_id"`
	SessionID string `json:"session_id"`
}

func TikTokSession(w http.ResponseWriter, r *http.Request, queries *db.Queries) {
	if r.Method != http.MethodPost {
		http.Error(w, "Invalid request method", http.StatusMethodNotAllowed)
		return
	}

	var req TikTokSessionRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if req.UserID == 0 || req.GroupID == 0 || req.SessionID == "" {
		http.Error(w, "Missing required fields: user_id, group_id, session_id", http.StatusBadRequest)
		return
	}

	// ✅ Step 1: Verify the group exists and is owned by the user
	group, err := queries.GetGroupByID(r.Context(), req.GroupID)
	if err != nil {
		fmt.Println("GetGroupByID ERROR:", err)
		if err == sql.ErrNoRows {
			http.Error(w, "Group not found", http.StatusNotFound)
			return
		}
		http.Error(w, "Failed to fetch group", http.StatusInternalServerError)
		return
	}
	if group.UserID != req.UserID {
		http.Error(w, "You do not own this group", http.StatusForbidden)
		return
	}

	// ✅ Step 2: Insert TikTok group_item if not exists
	err = queries.InsertTikTokGroupItemIfNotExists(r.Context(), db.InsertTikTokGroupItemIfNotExistsParams{
		GroupID: req.GroupID,
		Column2: req.SessionID,
	})
	if err != nil {
		fmt.Println("InsertTikTokGroupItemIfNotExists ERROR:", err)
		// Still continue to update to ensure data consistency
	}

	// ✅ Step 3: Update session ID in group_items (always run)
	err = queries.UpdateTikTokSessionID(r.Context(), db.UpdateTikTokSessionIDParams{
		GroupID: req.GroupID,
		Column2: req.SessionID,
	})
	if err != nil {
		fmt.Println("UpdateTikTokSessionID ERROR:", err)
		http.Error(w, "Failed to update TikTok session ID", http.StatusInternalServerError)
		return
	}

	// ✅ Step 4: Respond with success
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]string{
		"message":        "TikTok session saved successfully",
		"tiktok_session": req.SessionID,
		"group_id":       strconv.Itoa(int(req.GroupID)),
	})
}


// Create a new group
type CreateGroupRequest struct {
	UserID      int32  `json:"user_id"`
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

	fmt.Println("user_id =", req.UserID)
	fmt.Println("name =", req.Name)
	fmt.Println("description =", req.Description)

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

