package handlers

import (
	"fmt"
	"net/http"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/BimaPDev/ProjectMonopoly/internal/utils"
	"github.com/gin-gonic/gin"
)

// RequestBody defines the expected input for the API
type RequestBody struct {
	SessionID string `json:"session_id"`
	VideoPath string `json:"video_path"`
	Caption   string `json:"caption"`
	Headless  bool   `json:"headless"`
}

// ResponseBody defines the structure of the API response
type ResponseBody struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
	Output  string `json:"output,omitempty"`
	Error   string `json:"error,omitempty"`
}

// TriggerPythonScript handles requests to trigger the Python script
func TriggerPythonScript(c *gin.Context) {
	// Parse request body
	var reqBody RequestBody
	if err := c.ShouldBindJSON(&reqBody); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid JSON payload"})
		return
	}

	// Validate input
	if err := utils.ValidateRequest(reqBody.SessionID, reqBody.VideoPath, reqBody.Caption); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Run the Python script
	output, err := utils.TikTokUpload(reqBody.SessionID, reqBody.VideoPath, reqBody.Caption, reqBody.Headless)
	if err != nil {
		c.JSON(http.StatusInternalServerError, ResponseBody{
			Success: false,
			Message: "Failed to execute Python script",
			Error:   err.Error(),
		})
		return
	}

	// Success response
	c.JSON(http.StatusOK, ResponseBody{
		Success: true,
		Message: "Python script executed successfully",
		Output:  output,
	})
}

// TriggerFollowersScript handles requests to trigger the followers Python script
func TriggerFollowersScript(c *gin.Context, queries *db.Queries) {
	// Call the GetFollowers function from utils
	utils.GetFollowers(c, queries)
}

// HealthCheck provides a simple health check endpoint
func HealthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"status": "ok"})
}

func TriggerAiScript(c *gin.Context) {
	// Define the request body structure
	var reqBody struct {
		Model string `json:"model"`
		Input string `json:"input"`
	}

	// Decode the JSON request body
	if err := c.ShouldBindJSON(&reqBody); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid JSON payload"})
		return
	}

	// Validate the input
	if reqBody.Model == "" || reqBody.Input == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Model and input fields are required"})
		return
	}

	// Call the TriggerModel function
	output, err := utils.TriggerModel(reqBody.Model, reqBody.Input)
	if err != nil {
		c.JSON(http.StatusInternalServerError, ResponseBody{
			Success: false,
			Message: fmt.Sprintf("Failed to execute %s model", reqBody.Model),
			Error:   err.Error(),
		})
		return
	}

	// Return the successful response
	c.JSON(http.StatusOK, ResponseBody{
		Success: true,
		Message: fmt.Sprintf("%s model executed successfully", reqBody.Model),
		Output:  output,
	})
}
