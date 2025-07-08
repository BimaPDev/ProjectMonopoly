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
	Description string `json:"description"`
	Name        string `json:"name"`
	UserID      int32  `json:"userID"`
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
	if queries == nil {
		http.Error(w, "Internal server error: queries is nil", http.StatusInternalServerError)
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
	GroupID  int    `json:"groupID"`
	Username string `json:"userName"`
	Password string `json:"password"`
	Platform string `json:"platform"`
}

func AddOrUpdateGroupItem(w http.ResponseWriter, r *http.Request, q *db.Queries) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req AddGroupitem
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Convert credentials to JSON
	dataJSON := map[string]string{
		"username": req.Username,
		"password": req.Password,
	}
	dataBytes, err := json.Marshal(dataJSON)
	if err != nil {
		http.Error(w, "Error processing data", http.StatusInternalServerError)
		return
	}

	// Try Insert (will do nothing if exists)
	_, err = q.InsertGroupItemIfNotExists(r.Context(), db.InsertGroupItemIfNotExistsParams{
		GroupID:  int32(req.GroupID),
		Platform: req.Platform,
		Data: pqtype.NullRawMessage{
			RawMessage: dataBytes,
			Valid:      true,
		},
	})
	if err != nil {
		http.Error(w, fmt.Sprintf("Insert error: %v", err), http.StatusInternalServerError)
		return
	}

	// Then force update anyway (safe, no-op if same)
	err = q.UpdateGroupItemData(r.Context(), db.UpdateGroupItemDataParams{
		GroupID:  int32(req.GroupID),
		Platform: req.Platform,
		Data:  json.RawMessage(dataBytes),
	})
	if err != nil {
		http.Error(w, fmt.Sprintf("Update error: %v", err), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
	fmt.Fprint(w, "Group item updated or inserted")
}

// GetGroupItems retrieves all items in a group
func GetGroupItems(w http.ResponseWriter, r *http.Request, q *db.Queries) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allwed", http.StatusBadRequest)
	}
	groupIDstr := r.URL.Query().Get("groupID")
	groupIDInt, err := strconv.Atoi(groupIDstr)
	if err != nil {
		http.Error(w, "Invalid groupID, could not convert", http.StatusBadRequest)
		return
	}
	groupID := int32(groupIDInt)
	items, err := q.GetGroupItemByGroupID(r.Context(), groupID)
	if err != nil {
		http.Error(w, "Failed to retrieve group items", http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(items)

}
