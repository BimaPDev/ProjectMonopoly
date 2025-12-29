package handlers

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/gin-gonic/gin"
)

// Create a new group
type CreateGroupRequest struct {
	Description string `json:"description"`
	Name        string `json:"name"`
	UserID      int32  `json:"userID"`
}

func CreateGroup(c *gin.Context, queries *db.Queries) {
	var req CreateGroupRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid JSON"})
		return
	}

	if req.UserID == 0 || req.Name == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Missing required fields"})
		return
	}
	if queries == nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error: queries is nil"})
		return
	}

	group, err := queries.CreateGroup(c.Request.Context(), db.CreateGroupParams{
		UserID:      req.UserID,
		Name:        req.Name,
		Description: sql.NullString{String: req.Description, Valid: req.Description != ""},
	})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create group"})
		return
	}

	c.JSON(http.StatusOK, group)
}

type groupResponse struct {
	ID          int32  `json:"ID"`
	Name        string `json:"name"`
	Description string `json:"description"`
}

func GetGroups(c *gin.Context, q *db.Queries) {
	// 1. Grab as string and validate
	uidStr := c.Query("userID")
	if uidStr == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "userID is required"})
		return
	}

	// 2. Parse to int
	uidInt, err := strconv.Atoi(uidStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid userID"})
		return
	}
	userID := int32(uidInt) // 3. Convert to int32

	// 4. Call your generated query
	groups, err := q.ListGroupsByUser(c.Request.Context(), userID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "could not list groups"})
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

	c.JSON(http.StatusOK, out)
}

type AddGroupitem struct {
	GroupID  int    `json:"groupID"`
	Username string `json:"userName"`
	Password string `json:"password"`
	Platform string `json:"platform"`
}

func AddOrUpdateGroupItem(c *gin.Context, q *db.Queries) {
	var req AddGroupitem
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid JSON"})
		return
	}

	// Convert credentials to JSON
	dataJSON := map[string]string{
		"username": req.Username,
		"password": req.Password,
	}
	dataBytes, err := json.Marshal(dataJSON)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error processing data"})
		return
	}

	// Try Insert (will do nothing if exists)
	_, err = q.InsertGroupItemIfNotExists(c.Request.Context(), db.InsertGroupItemIfNotExistsParams{
		GroupID:  int32(req.GroupID),
		Platform: req.Platform,
		Data:     dataBytes,
	})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Insert error: %v", err)})
		return
	}

	// Then force update anyway (safe, no-op if same)
	err = q.UpdateGroupItemData(c.Request.Context(), db.UpdateGroupItemDataParams{
		GroupID:  int32(req.GroupID),
		Platform: req.Platform,
		Data:     json.RawMessage(dataBytes),
	})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Update error: %v", err)})
		return
	}

	c.String(http.StatusOK, "Group item updated or inserted")
}

// GetGroupItems retrieves all items in a group
func GetGroupItems(c *gin.Context, q *db.Queries) {
	groupIDstr := c.Query("groupID")
	groupIDInt, err := strconv.Atoi(groupIDstr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid groupID, could not convert"})
		return
	}
	groupID := int32(groupIDInt)
	items, err := q.GetGroupItemByGroupID(c.Request.Context(), groupID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve group items"})
		return
	}
	c.JSON(http.StatusOK, items)
}
