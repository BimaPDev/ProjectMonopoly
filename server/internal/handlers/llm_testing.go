// internal/handlers/llm_testing.go
package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strings"
	"time"
)

type LLMTestRequest struct {
	Prompt string `json:"prompt"`
}

type LLMTestResponse struct {
	Success  bool   `json:"success"`
	Message  string `json:"message"`
	Duration string `json:"duration,omitempty"`
	Error    string `json:"error,omitempty"`
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

	// Start timer
	startTime := time.Now()

	// Call Ollama directly
	messages := []map[string]string{
		{"role": "user", "content": req.Prompt},
	}

	reqBody := map[string]interface{}{
		"model":    model,
		"stream":   false,
		"messages": messages,
		"options": map[string]interface{}{
			"num_ctx":        3072,
			"num_predict":    200,
			"temperature":    0.1,
			"top_p":          0.9,
			"repeat_penalty": 1.1,
		},
	}

	jsonData, _ := json.Marshal(reqBody)
	resp, err := http.Post(chatURL, "application/json", strings.NewReader(string(jsonData)))
	if err != nil {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(LLMTestResponse{
			Success: false,
			Error:   fmt.Sprintf("LLM call failed: %v", err),
		})
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(LLMTestResponse{
			Success: false,
			Error:   fmt.Sprintf("Ollama returned status code: %d", resp.StatusCode),
		})
		return
	}

	// Parse Ollama response
	var ollamaResp struct {
		Model   string `json:"model"`
		Message struct {
			Role    string `json:"role"`
			Content string `json:"content"`
		} `json:"message"`
		Done bool `json:"done"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&ollamaResp); err != nil {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusInternalServerError)
		json.NewEncoder(w).Encode(LLMTestResponse{
			Success: false,
			Error:   fmt.Sprintf("Failed to parse Ollama response: %v", err),
		})
		return
	}

	// Calculate duration
	elapsed := time.Since(startTime)

	// Return success with the LLM response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(LLMTestResponse{
		Success:  true,
		Message:  ollamaResp.Message.Content,
		Duration: elapsed.String(),
	})
}
