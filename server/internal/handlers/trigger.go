package handlers

import (
	"encoding/json"
	"net/http"

	"github.com/BimaPDev/ProjectMonopoly/internal/utils"
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
func TriggerPythonScript(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")

	// Parse request body
	var reqBody RequestBody
	err := json.NewDecoder(r.Body).Decode(&reqBody)
	if err != nil {
		http.Error(w, "Invalid JSON payload", http.StatusBadRequest)
		return
	}

	// Validate input
	if err := utils.ValidateRequest(reqBody.SessionID, reqBody.VideoPath, reqBody.Caption); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// Run the Python script
	output, err := utils.RunPythonScript(reqBody.SessionID, reqBody.VideoPath, reqBody.Caption, reqBody.Headless)
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(ResponseBody{
			Success: false,
			Message: "Failed to execute Python script",
			Error:   err.Error(),
		})
		return
	}

	// Success response
	json.NewEncoder(w).Encode(ResponseBody{
		Success: true,
		Message: "Python script executed successfully",
		Output:  output,
	})
}

// HealthCheck provides a simple health check endpoint
func HealthCheck(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}
