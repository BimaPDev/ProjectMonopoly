package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/BimaPDev/ProjectMonopoly/internal/utils" // Adjust based on your actual module path
)

// DeepSeekHandler handles AI requests to DeepSeek.
func DeepSeekHandler(w http.ResponseWriter, r *http.Request) {
	// Only allow POST requests
	if r.Method != http.MethodPost {
		http.Error(w, "Invalid request method. Only POST is allowed.", http.StatusMethodNotAllowed)
		return
	}

	// Parse the request body to extract the prompt
	var requestBody struct {
		Prompt string `json:"prompt"`
	}
	if err := json.NewDecoder(r.Body).Decode(&requestBody); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// Validate the prompt
	if requestBody.Prompt == "" {
		http.Error(w, "Prompt cannot be empty", http.StatusBadRequest)
		return
	}

	// Call the MainDeep function in utils
	response, err := utils.MainDeep(requestBody.Prompt)
	if err != nil {
		http.Error(w, fmt.Sprintf("Error processing request: %v", err), http.StatusInternalServerError)
		return
	}

	// Respond with the AI's output
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"response": response})
}

func ChatDeepHandler(w http.ResponseWriter, r *http.Request) {
	// Only allow POST requests
	if r.Method != http.MethodPost {
		http.Error(w, "Only POST requests are allowed.", http.StatusMethodNotAllowed)
		return
	}

	// Parse the request body
	var requestBody struct {
		Prompt string `json:"prompt"`
	}
	if err := json.NewDecoder(r.Body).Decode(&requestBody); err != nil {
		http.Error(w, "Invalid JSON request body.", http.StatusBadRequest)
		return
	}

	// Validate the prompt
	if requestBody.Prompt == "" {
		http.Error(w, "Prompt cannot be empty.", http.StatusBadRequest)
		return
	}

	// Call ChatDeep to send the prompt and get the response
	response, err := utils.ChatDeep(requestBody.Prompt)
	if err != nil {
		http.Error(w, fmt.Sprintf("Error calling DeepSeek API: %v", err), http.StatusInternalServerError)
		return
	}

	// Send the response back to the client
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"response": response})
}