package handlers

import (
	"log"
	"net/http"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/BimaPDev/ProjectMonopoly/internal/utils"
	"github.com/gin-gonic/gin"
)

func ListUserCompetitors(c *gin.Context, queries *db.Queries) {
	// TODO: Replace with real user session logic
	userID, err := utils.GetUserID(c)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
		return
	}

	// Query DB
	competitors, err := queries.ListUserCompetitors(c.Request.Context(), userID)
	if err != nil {
		log.Printf("❌ Failed to list user competitors: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch competitors"})
		return
	}

	// Success
	c.JSON(http.StatusOK, competitors)
}
