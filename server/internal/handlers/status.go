package handlers

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"

	"github.com/gin-gonic/gin"
)

// Python API URL
const pythonAPIURL = "http://localhost:5000"

func GetUserJobStatusHandler(c *gin.Context) {
	userID := c.Param("user_id")
	jobID := c.Param("job_id")

	// Connect to database
	db, err := sql.Open("postgres", "your_db_connection_string")
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Database connection error"})
		return
	}
	defer db.Close()

	// Ensure the job belongs to the user
	var storedUserID string
	err = db.QueryRow("SELECT user_id FROM upload_jobs WHERE id = $1", jobID).Scan(&storedUserID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Job not found"})
		return
	}

	if storedUserID != userID {
		c.JSON(http.StatusForbidden, gin.H{"error": "Unauthorized to view this job"})
		return
	}

	// Fetch job status from Python API
	pythonURL := fmt.Sprintf("%s/status/%s", pythonAPIURL, jobID)
	resp, err := http.Get(pythonURL)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to contact Python API"})
		return
	}
	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to read response"})
		return
	}

	var result map[string]interface{}
	if err := json.Unmarshal(body, &result); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Invalid JSON response"})
		return
	}

	// Return job status
	c.JSON(http.StatusOK, result)
}