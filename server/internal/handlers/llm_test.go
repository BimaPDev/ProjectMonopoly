// internal/handlers/llm_test.go
package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strings"
)

type LLMTestRequest struct {
	Prompt string `json:"prompt"`
}

type LLMTestResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
	Error   string `json:"error,omitempty"`
}

// TestLLMHandler allows testing the LLM with a simple text prompt
func TestLLMHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	setCORSHeaders(w)

	// Get Ollama configuration
	ollamaHost := strings.TrimSpace(os.Getenv("OLLAMA_HOST"))
	if ollamaHost == "" {
		ollamaHost = "http://ollama:11434"
	}
	ollamaHost = strings.TrimRight(ollamaHost, "/")
	for _, bad := range []string{"/v1", "/v1/", "/api", "/api/"} {
		ollamaHost = strings.TrimSuffix(ollamaHost, bad)
	}
	chatURL := ollamaHost + "/api/chat"

	model := strings.TrimSpace(os.Getenv("OLLAMA_MODEL"))
	if model == "" {
		model = "qwen2.5:3b-instruct"
	}

	// Parse request
	var req LLMTestRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(LLMTestResponse{
			Success: false,
			Error:   fmt.Sprintf("Failed to parse request: %v", err),
		})
		return
	}

	if strings.TrimSpace(req.Prompt) == "" {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(LLMTestResponse{
			Success: false,
			Error:   "Prompt cannot be empty",
		})
		return
	}

	// Call the LLM using the callOllama helper
	data, err := callOllama(chatURL, model, req.Prompt)
	if err != nil {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(LLMTestResponse{
			Success: false,
			Error:   fmt.Sprintf("LLM call failed: %v", err),
		})
		return
	}

	// Convert the map to a formatted JSON string for display
	responseBytes, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(LLMTestResponse{
			Success: false,
			Error:   fmt.Sprintf("Failed to format response: %v", err),
		})
		return
	}

	// Return success with the LLM response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(LLMTestResponse{
		Success: true,
		Message: string(responseBytes),
	})
}
