package utils

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
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

func GetFollowers(w http.ResponseWriter, r *http.Request, queries *db.Queries) {

	ctx := r.Context()

	// Call the sqlc‐generated method: no parameters (just the context)
	latest, err := queries.GetFollowerByDate(ctx)
	if err != nil {
		if err == sql.ErrNoRows {
			http.Error(w, "no follower history yet", http.StatusNotFound)
			return
		}
		http.Error(w, "failed to fetch followers", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(latest); err != nil {
		http.Error(w, "failed to encode JSON", http.StatusInternalServerError)
		return
	}

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
