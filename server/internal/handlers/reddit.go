package handlers

import (
	"context"
	"database/sql"
	"net/http"
	"strconv"
	"time"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/gin-gonic/gin"
)

// Response DTOs to convert sql.Null* types to plain values for JSON
type SourceResponse struct {
	ID        int32   `json:"id"`
	UserID    int32   `json:"user_id"`
	GroupID   *int32  `json:"group_id"`
	Type      string  `json:"type"`
	Value     string  `json:"value"`
	Subreddit *string `json:"subreddit"`
	Enabled   bool    `json:"enabled"`
	CreatedAt string  `json:"created_at"`
}

type ItemResponse struct {
	ID           int32   `json:"id"`
	SourceID     int32   `json:"source_id"`
	Subreddit    string  `json:"subreddit"`
	ExternalID   string  `json:"external_id"`
	ExternalURL  string  `json:"external_url"`
	Title        string  `json:"title"`
	Body         string  `json:"body"`
	Author       string  `json:"author"`
	Score        int32   `json:"score"`
	NumComments  int32   `json:"num_comments"`
	CreatedUTC   string  `json:"created_utc"`
	QualityScore float64 `json:"quality_score"`
}

type CardResponse struct {
	ID              int32    `json:"id"`
	Source          string   `json:"source"`
	ItemID          int32    `json:"item_id"`
	PlatformTargets []string `json:"platform_targets"`
	Niche           string   `json:"niche"`
	Tactic          string   `json:"tactic"`
	Confidence      float64  `json:"confidence"`
	CreatedAt       string   `json:"created_at"`
}

type AlertResponse struct {
	ID            int32   `json:"id"`
	SourceID      int32   `json:"source_id"`
	WindowStart   string  `json:"window_start"`
	WindowEnd     string  `json:"window_end"`
	Metric        string  `json:"metric"`
	CurrentValue  float64 `json:"current_value"`
	PreviousValue float64 `json:"previous_value"`
	Factor        float64 `json:"factor"`
	CreatedAt     string  `json:"created_at"`
}

// Helper functions
func nullStringToPtr(ns sql.NullString) *string {
	if ns.Valid {
		return &ns.String
	}
	return nil
}

func nullInt32ToPtr(ni sql.NullInt32) *int32 {
	if ni.Valid {
		return &ni.Int32
	}
	return nil
}

func nullStringValue(ns sql.NullString) string {
	if ns.Valid {
		return ns.String
	}
	return ""
}

func nullInt32Value(ni sql.NullInt32) int32 {
	if ni.Valid {
		return ni.Int32
	}
	return 0
}

func nullFloat64Value(nf sql.NullFloat64) float64 {
	if nf.Valid {
		return nf.Float64
	}
	return 0
}

func nullBoolValue(nb sql.NullBool) bool {
	if nb.Valid {
		return nb.Bool
	}
	return false
}

func nullTimeStr(nt sql.NullTime) string {
	if nt.Valid {
		return nt.Time.Format(time.RFC3339)
	}
	return ""
}

func toSourceResponse(s db.RedditSource) SourceResponse {
	return SourceResponse{
		ID:        s.ID,
		UserID:    s.UserID,
		GroupID:   nullInt32ToPtr(s.GroupID),
		Type:      s.Type,
		Value:     s.Value,
		Subreddit: nullStringToPtr(s.Subreddit),
		Enabled:   nullBoolValue(s.Enabled),
		CreatedAt: nullTimeStr(s.CreatedAt),
	}
}

func toItemResponse(item db.RedditItem) ItemResponse {
	return ItemResponse{
		ID:           item.ID,
		SourceID:     item.SourceID,
		Subreddit:    item.Subreddit,
		ExternalID:   item.ExternalID,
		ExternalURL:  item.ExternalUrl,
		Title:        nullStringValue(item.Title),
		Body:         nullStringValue(item.Body),
		Author:       nullStringValue(item.Author),
		Score:        nullInt32Value(item.Score),
		NumComments:  nullInt32Value(item.NumComments),
		CreatedUTC:   item.CreatedUtc.Format(time.RFC3339),
		QualityScore: nullFloat64Value(item.QualityScore),
	}
}

func toCardResponse(card db.StrategyCard) CardResponse {
	return CardResponse{
		ID:              card.ID,
		Source:          nullStringValue(card.Source),
		ItemID:          nullInt32Value(card.ItemID),
		PlatformTargets: card.PlatformTargets,
		Niche:           nullStringValue(card.Niche),
		Tactic:          nullStringValue(card.Tactic),
		Confidence:      nullFloat64Value(card.Confidence),
		CreatedAt:       nullTimeStr(card.CreatedAt),
	}
}

func toAlertResponse(alert db.RedditAlert) AlertResponse {
	return AlertResponse{
		ID:            alert.ID,
		SourceID:      alert.SourceID,
		WindowStart:   alert.WindowStart.Format(time.RFC3339),
		WindowEnd:     alert.WindowEnd.Format(time.RFC3339),
		Metric:        alert.Metric,
		CurrentValue:  alert.CurrentValue,
		PreviousValue: alert.PreviousValue,
		Factor:        alert.Factor,
		CreatedAt:     nullTimeStr(alert.CreatedAt),
	}
}

// getRedditUserID extracts the user ID from context (set by auth middleware as int32)
func getRedditUserID(c *gin.Context) (int32, bool) {
	userIDVal, exists := c.Get("userID")
	if !exists {
		return 0, false
	}
	switch v := userIDVal.(type) {
	case int32:
		return v, v != 0
	case int:
		return int32(v), v != 0
	case int64:
		return int32(v), v != 0
	default:
		return 0, false
	}
}

// CreateSourceHandler creates a new Reddit source
func CreateSourceHandler(q *db.Queries) gin.HandlerFunc {
	return func(c *gin.Context) {
		userID, ok := getRedditUserID(c)
		if !ok {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
			return
		}

		var req struct {
			GroupID   *int    `json:"group_id"`
			Type      string  `json:"type" binding:"required,oneof=subreddit keyword"`
			Value     string  `json:"value" binding:"required"`
			Subreddit *string `json:"subreddit"`
		}

		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		var groupID sql.NullInt32
		if req.GroupID != nil {
			groupID = sql.NullInt32{Int32: int32(*req.GroupID), Valid: true}
		}

		var subreddit sql.NullString
		if req.Subreddit != nil && *req.Subreddit != "" {
			subreddit = sql.NullString{String: *req.Subreddit, Valid: true}
		}

		params := db.CreateRedditSourceParams{
			UserID:    userID,
			GroupID:   groupID,
			Type:      req.Type,
			Value:     req.Value,
			Subreddit: subreddit,
		}

		source, err := q.CreateRedditSource(context.Background(), params)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create source: " + err.Error()})
			return
		}

		c.JSON(http.StatusOK, toSourceResponse(source))
	}
}

// ListSourcesHandler lists Reddit sources for the user
func ListSourcesHandler(q *db.Queries) gin.HandlerFunc {
	return func(c *gin.Context) {
		userID, _ := getRedditUserID(c)
		groupIDStr := c.Query("group_id")

		var groupID sql.NullInt32
		if groupIDStr != "" {
			if gid, err := strconv.Atoi(groupIDStr); err == nil {
				groupID = sql.NullInt32{Int32: int32(gid), Valid: true}
			}
		}

		params := db.ListRedditSourcesParams{
			UserID:  userID,
			GroupID: groupID,
		}

		sources, err := q.ListRedditSources(context.Background(), params)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to list sources"})
			return
		}

		// Convert to response DTOs
		result := make([]SourceResponse, len(sources))
		for i, s := range sources {
			result[i] = toSourceResponse(s)
		}

		c.JSON(http.StatusOK, result)
	}
}

// DeleteSourceHandler deletes a source if it belongs to the user
func DeleteSourceHandler(q *db.Queries) gin.HandlerFunc {
	return func(c *gin.Context) {
		userID, _ := getRedditUserID(c)
		sourceIDStr := c.Param("id")
		sourceID, err := strconv.Atoi(sourceIDStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid source ID"})
			return
		}

		err = q.DeleteRedditSource(context.Background(), db.DeleteRedditSourceParams{
			ID:     int32(sourceID),
			UserID: userID,
		})
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to delete source"})
			return
		}

		c.JSON(http.StatusOK, gin.H{"status": "deleted"})
	}
}

// ListItemsHandler lists Reddit items
func ListItemsHandler(q *db.Queries) gin.HandlerFunc {
	return func(c *gin.Context) {
		userID, _ := getRedditUserID(c)
		groupIDStr := c.Query("group_id")
		limitStr := c.DefaultQuery("limit", "50")
		offsetStr := c.DefaultQuery("offset", "0")

		limit, _ := strconv.Atoi(limitStr)
		offset, _ := strconv.Atoi(offsetStr)

		var groupID sql.NullInt32
		if groupIDStr != "" {
			if gid, err := strconv.Atoi(groupIDStr); err == nil {
				groupID = sql.NullInt32{Int32: int32(gid), Valid: true}
			}
		}

		params := db.ListRedditItemsParams{
			UserID:  userID,
			Limit:   int32(limit),
			Offset:  int32(offset),
			GroupID: groupID,
		}

		items, err := q.ListRedditItems(context.Background(), params)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to list items"})
			return
		}

		// Convert to response DTOs
		result := make([]ItemResponse, len(items))
		for i, item := range items {
			result[i] = toItemResponse(item)
		}

		c.JSON(http.StatusOK, result)
	}
}

// ListStrategyCardsHandler lists extracted strategy cards
func ListStrategyCardsHandler(q *db.Queries) gin.HandlerFunc {
	return func(c *gin.Context) {
		userID, _ := getRedditUserID(c)
		groupIDStr := c.Query("group_id")
		limitStr := c.DefaultQuery("limit", "50")
		offsetStr := c.DefaultQuery("offset", "0")

		limit, _ := strconv.Atoi(limitStr)
		offset, _ := strconv.Atoi(offsetStr)

		var groupID sql.NullInt32
		if groupIDStr != "" {
			if gid, err := strconv.Atoi(groupIDStr); err == nil {
				groupID = sql.NullInt32{Int32: int32(gid), Valid: true}
			}
		}

		params := db.ListStrategyCardsParams{
			UserID:  userID,
			Limit:   int32(limit),
			Offset:  int32(offset),
			GroupID: groupID,
		}

		cards, err := q.ListStrategyCards(context.Background(), params)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to list cards"})
			return
		}

		// Convert to response DTOs
		result := make([]CardResponse, len(cards))
		for i, card := range cards {
			result[i] = toCardResponse(card)
		}

		c.JSON(http.StatusOK, result)
	}
}

// ListAlertsHandler lists spike alerts
func ListAlertsHandler(q *db.Queries) gin.HandlerFunc {
	return func(c *gin.Context) {
		userID, _ := getRedditUserID(c)
		groupIDStr := c.Query("group_id")
		limitStr := c.DefaultQuery("limit", "50")
		offsetStr := c.DefaultQuery("offset", "0")

		limit, _ := strconv.Atoi(limitStr)
		offset, _ := strconv.Atoi(offsetStr)

		var groupID sql.NullInt32
		if groupIDStr != "" {
			if gid, err := strconv.Atoi(groupIDStr); err == nil {
				groupID = sql.NullInt32{Int32: int32(gid), Valid: true}
			}
		}

		params := db.ListRedditAlertsParams{
			UserID:  userID,
			Limit:   int32(limit),
			Offset:  int32(offset),
			GroupID: groupID,
		}

		alerts, err := q.ListRedditAlerts(context.Background(), params)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to list alerts"})
			return
		}

		// Convert to response DTOs
		result := make([]AlertResponse, len(alerts))
		for i, alert := range alerts {
			result[i] = toAlertResponse(alert)
		}

		c.JSON(http.StatusOK, result)
	}
}
