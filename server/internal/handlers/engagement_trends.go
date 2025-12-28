// internal/handlers/engagement_trends.go
package handlers

import (
	"database/sql"
	"net/http"
	"strconv"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/gin-gonic/gin"
)

// EngagementTrendPoint represents a single data point for the chart
type EngagementTrendPoint struct {
	Date          string  `json:"date"`
	PostCount     int64   `json:"post_count"`
	TotalLikes    int64   `json:"total_likes"`
	TotalComments int64   `json:"total_comments"`
	AvgEngagement float64 `json:"avg_engagement"`
}

// GetEngagementTrendsHandler returns daily engagement trends for the dashboard chart
func GetEngagementTrendsHandler(queries *db.Queries) gin.HandlerFunc {
	return func(c *gin.Context) {
		// Get user ID from context (set by auth middleware)
		userIDVal, exists := c.Get("userID")
		if !exists {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "User not authenticated"})
			return
		}
		userID, ok := userIDVal.(int32)
		if !ok {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Invalid user ID type"})
			return
		}

		// Parse query parameters
		groupIDStr := c.Query("group_id")
		daysStr := c.DefaultQuery("days", "7")

		var groupID sql.NullInt32
		if groupIDStr != "" {
			id, err := strconv.Atoi(groupIDStr)
			if err != nil {
				c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid group_id"})
				return
			}
			groupID = sql.NullInt32{Int32: int32(id), Valid: true}
		}

		days, err := strconv.Atoi(daysStr)
		if err != nil || (days != 7 && days != 30 && days != 90) {
			days = 7 // Default to 7 days
		}

		// Fetch trends from database
		trends, err := queries.GetDailyEngagementTrends(c.Request.Context(), db.GetDailyEngagementTrendsParams{
			UserID:  userID,
			GroupID: groupID,
			Column3: sql.NullString{String: strconv.Itoa(days), Valid: true},
		})
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch engagement trends"})
			return
		}

		// Transform to response format
		response := make([]EngagementTrendPoint, 0, len(trends))
		for _, t := range trends {
			response = append(response, EngagementTrendPoint{
				Date:          t.PostDate.Format("Jan 2"),
				PostCount:     t.PostCount,
				TotalLikes:    t.TotalLikes,
				TotalComments: t.TotalComments,
				AvgEngagement: t.AvgEngagement,
			})
		}

		c.JSON(http.StatusOK, response)
	}
}
