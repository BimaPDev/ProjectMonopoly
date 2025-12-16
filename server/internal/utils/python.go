package utils

import (
	"bytes"
	"database/sql"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/gin-gonic/gin"
)

// RunPythonScript executes the Python script with the provided arguments
func TikTokUpload(sessionID, videoPath, caption string, headless bool) (string, error) {
	// Get absolute video path
	absVideoPath, err := filepath.Abs(videoPath)
	if err != nil {
		return "", fmt.Errorf("failed to resolve video path: %v", err)
	}

	// Check if video file exists
	if _, err := os.Stat(absVideoPath); os.IsNotExist(err) {
		return "", fmt.Errorf("video file does not exist at path: %s", absVideoPath)
	}

	// Path to the Python script
	scriptPath := filepath.Join("python", "socialmedia", "tiktok.py")
	if _, err := os.Stat(scriptPath); os.IsNotExist(err) {
		return "", fmt.Errorf("Python script does not exist at path: %s", scriptPath)
	}

	// Detect Python command
	pythonCmd := DetectPythonCommand()

	// Build arguments
	args := []string{
		scriptPath,
		"--sessionid", sessionID,
		"--video", absVideoPath,
		"--caption", caption,
	}
	if headless {
		args = append(args, "--headless")
	}

	// Execute Python script
	var out bytes.Buffer
	var stderr bytes.Buffer
	cmd := exec.Command(pythonCmd, args...)
	cmd.Stdout = &out
	cmd.Stderr = &stderr

	err = cmd.Run()
	if err != nil {
		return "", fmt.Errorf("error executing Python script: %v\nStderr: %s", err, stderr.String())
	}

	return out.String(), nil
}

func GetFollowers(c *gin.Context, queries *db.Queries) {

	ctx := c.Request.Context()

	// Call the sqlc‐generated method: no parameters (just the context)
	latest, err := queries.GetFollowerByDate(ctx)
	if err != nil {
		if err == sql.ErrNoRows {
			c.JSON(http.StatusNotFound, gin.H{"error": "no follower history yet"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to fetch followers"})
		return
	}

	c.JSON(http.StatusOK, latest)
}

// DetectPythonCommand determines whether to use 'python' or 'python3'
func DetectPythonCommand() string {
	pythonCmd := "python"
	if _, err := exec.LookPath(pythonCmd); err != nil {
		pythonCmd = "python3"
		if _, err := exec.LookPath(pythonCmd); err != nil {
			panic("Neither 'python' nor 'python3' found in PATH")
		}
	}
	return pythonCmd
}

// TriggerModel executes a Python script based on the selected model
func TriggerModel(model, input string) (string, error) {
	// Define the script paths for each model
	modelScripts := map[string]string{
		"chatgpt":  filepath.Join("python", "models", "chatgpt.py"),
		"deepseek": filepath.Join("python", "models", "deepseek.py"),
	}

	// Ensure the requested model exists in the map
	scriptPath, exists := modelScripts[model]
	if !exists {
		return "", fmt.Errorf("invalid model: %s", model)
	}

	// Check if the Python script exists
	if _, err := os.Stat(scriptPath); os.IsNotExist(err) {
		return "", fmt.Errorf("Python script does not exist at path: %s", scriptPath)
	}

	// Detect Python command
	pythonCmd := DetectPythonCommand()

	// Build arguments
	args := []string{scriptPath, "--input", input}

	// Execute Python script
	var out bytes.Buffer
	var stderr bytes.Buffer
	cmd := exec.Command(pythonCmd, args...)
	cmd.Stdout = &out
	cmd.Stderr = &stderr

	err := cmd.Run()
	if err != nil {
		return "", fmt.Errorf("error executing %s script: %v\nStderr: %s", model, err, stderr.String())
	}

	return out.String(), nil
}

// TriggerWeeklyScraper executes the weekly scraper immediately
// This is useful when a new competitor is added
func TriggerWeeklyScraper() error {
	// Path to the Python script
	scriptPath := filepath.Join("python", "socialmedia", "weekly_scraper.py")
	if _, err := os.Stat(scriptPath); os.IsNotExist(err) {
		return fmt.Errorf("Python script does not exist at path: %s", scriptPath)
	}

	// Detect Python command
	pythonCmd := DetectPythonCommand()

	// Build arguments - run as main
	args := []string{scriptPath}

	// Execute Python script in background (don't wait for output)
	// We use exec.Command but then Start() instead of Run()
	cmd := exec.Command(pythonCmd, args...)

	// Create a log file for the scraper
	logFile, err := os.OpenFile("scraper_trigger.log", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err == nil {
		cmd.Stdout = logFile
		cmd.Stderr = logFile
		defer logFile.Close()
	}

	err = cmd.Start()
	if err != nil {
		return fmt.Errorf("error starting scraper script: %v", err)
	}

	// Release resources
	go func() {
		_ = cmd.Wait()
	}()

	return nil
}
