package handlers

import (
	"net/http"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/BimaPDev/ProjectMonopoly/internal/service"
	"github.com/gin-gonic/gin"
)

func CreateUserHandler(queries *db.Queries) gin.HandlerFunc {
	return func(c *gin.Context) {
		var input service.CreateUserInput
		if err := c.ShouldBindJSON(&input); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body"})
			return
		}

		user, err := service.CreateUser(queries, input)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusOK, user)
	}
}

type getUserIDRequest struct {
	Username string `json:"username"`
	Email    string `json:"email"`
}

type getUserIDResponse struct {
	ID int32 `json:"userID"`
}

// handler
func GetUserIDHandler(q *db.Queries) gin.HandlerFunc {
	type req struct{ Username, Email string }
	type resp struct {
		UserID int32 `json:"userID"`
	}
	return func(c *gin.Context) {
		var body req
		if err := c.ShouldBindJSON(&body); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "invalid JSON"})
			return
		}
		if body.Username == "" || body.Email == "" {
			c.JSON(http.StatusBadRequest, gin.H{"error": "username & email required"})
			return
		}
		id, err := q.GetUserIDByUsernameEmail(c.Request.Context(), db.GetUserIDByUsernameEmailParams{
			Username: body.Username, Email: body.Email,
		})
		if err != nil {
			c.JSON(http.StatusNotFound, gin.H{"error": "user not found"})
			return
		}
		c.JSON(http.StatusOK, resp{UserID: id})
	}
}
