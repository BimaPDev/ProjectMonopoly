// internal/handlers/llm_provider.go
package handlers

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"
)

// LLMProvider defines the interface for LLM providers
type LLMProvider interface {
	Call(ctx context.Context, system, user string, opts map[string]any, history []historyMessage) (string, error)
	Name() string
}

// GetLLMProvider returns the appropriate LLM provider based on environment configuration
func GetLLMProvider() LLMProvider {
	provider := strings.ToLower(strings.TrimSpace(os.Getenv("LLM_PROVIDER")))

	switch provider {
	case "gemini":
		apiKey := os.Getenv("GEMINI_API_KEY")
		if apiKey == "" {
			fmt.Println("WARNING: LLM_PROVIDER=gemini but GEMINI_API_KEY is not set, falling back to Ollama")
			return NewOllamaProvider()
		}
		model := envOr("GEMINI_MODEL", "gemini-2.0-flash")
		return NewGeminiProvider(apiKey, model)
	default:
		return NewOllamaProvider()
	}
}

// ============================================================================
// Ollama Provider
// ============================================================================

type OllamaProvider struct {
	host  string
	model string
}

func NewOllamaProvider() *OllamaProvider {
	return &OllamaProvider{
		host:  envOr("OLLAMA_HOST", "http://localhost:11434"),
		model: envOr("OLLAMA_MODEL", "gemma3:latest"),
	}
}

func (p *OllamaProvider) Name() string {
	return "ollama"
}

func (p *OllamaProvider) Call(ctx context.Context, system, user string, opts map[string]any, history []historyMessage) (string, error) {
	return callOllamaWithOptions(ctx, p.host, p.model, system, user, opts, history)
}

// ============================================================================
// Gemini Provider
// ============================================================================

type GeminiProvider struct {
	apiKey string
	model  string
}

func NewGeminiProvider(apiKey, model string) *GeminiProvider {
	return &GeminiProvider{
		apiKey: apiKey,
		model:  model,
	}
}

func (p *GeminiProvider) Name() string {
	return "gemini"
}

func (p *GeminiProvider) Call(ctx context.Context, system, user string, opts map[string]any, history []historyMessage) (string, error) {
	return callGemini(ctx, p.apiKey, p.model, system, user, opts, history)
}

// callGemini makes a request to the Gemini API
func callGemini(ctx context.Context, apiKey, model, system, user string, opts map[string]any, history []historyMessage) (string, error) {
	// Gemini API endpoint
	url := fmt.Sprintf("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=%s", model, apiKey)

	fmt.Printf("DEBUG: Calling Gemini API with model: %s\n", model)

	// Build conversation contents
	contents := []map[string]any{}

	// Add conversation history if provided
	if len(history) > 0 {
		for _, msg := range history {
			role := msg.Role
			if role == "assistant" {
				role = "model"
			}
			contents = append(contents, map[string]any{
				"role": role,
				"parts": []map[string]string{
					{"text": msg.Content},
				},
			})
		}
	}

	// Add current user message
	contents = append(contents, map[string]any{
		"role": "user",
		"parts": []map[string]string{
			{"text": user},
		},
	})

	// Build request body with system instruction
	reqBody := map[string]any{
		"contents": contents,
		"systemInstruction": map[string]any{
			"parts": []map[string]string{
				{"text": system},
			},
		},
		"generationConfig": map[string]any{
			"temperature":     getFloat(opts, "temperature", 0.7),
			"topP":            getFloat(opts, "top_p", 0.9),
			"maxOutputTokens": getInt(opts, "max_tokens", 2048),
		},
	}

	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return "", fmt.Errorf("failed to marshal request: %w", err)
	}

	fmt.Printf("DEBUG: Gemini request body length: %d bytes\n", len(jsonData))

	// Create HTTP client
	client := &http.Client{Timeout: 180 * time.Second}

	// Execute request with retry
	var lastErr error
	for attempt := 1; attempt <= 3; attempt++ {
		// Create fresh request for each attempt (body is consumed after first read)
		req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewReader(jsonData))
		if err != nil {
			return "", fmt.Errorf("failed to create request: %w", err)
		}
		req.Header.Set("Content-Type", "application/json")

		fmt.Printf("DEBUG: Gemini API attempt %d\n", attempt)

		resp, err := client.Do(req)
		if err != nil {
			lastErr = fmt.Errorf("HTTP request failed: %w", err)
			fmt.Printf("DEBUG: Gemini HTTP error on attempt %d: %v, waiting 60s before retry...\n", attempt, err)
			time.Sleep(60 * time.Second)
			continue
		}

		bodyBytes, _ := io.ReadAll(resp.Body)
		resp.Body.Close()

		fmt.Printf("DEBUG: Gemini API response status: %d, body length: %d\n", resp.StatusCode, len(bodyBytes))

		if resp.StatusCode != 200 {
			lastErr = fmt.Errorf("gemini API error %d: %s", resp.StatusCode, string(bodyBytes))
			fmt.Printf("DEBUG: Gemini API error response: %s\n", string(bodyBytes))
			fmt.Printf("DEBUG: Waiting 60s before retry...\n")
			time.Sleep(60 * time.Second)
			continue
		}

		// Parse response
		var geminiResp struct {
			Candidates []struct {
				Content struct {
					Parts []struct {
						Text string `json:"text"`
					} `json:"parts"`
				} `json:"content"`
			} `json:"candidates"`
			Error struct {
				Code    int    `json:"code"`
				Message string `json:"message"`
				Status  string `json:"status"`
			} `json:"error"`
		}

		if err := json.Unmarshal(bodyBytes, &geminiResp); err != nil {
			fmt.Printf("DEBUG: Failed to parse Gemini response: %v\nBody: %s\n", err, string(bodyBytes))
			return "", fmt.Errorf("failed to parse Gemini response: %w", err)
		}

		// Check for error in response body
		if geminiResp.Error.Message != "" {
			return "", fmt.Errorf("gemini API error: %s (code: %d, status: %s)", geminiResp.Error.Message, geminiResp.Error.Code, geminiResp.Error.Status)
		}

		if len(geminiResp.Candidates) == 0 || len(geminiResp.Candidates[0].Content.Parts) == 0 {
			fmt.Printf("DEBUG: Empty candidates in Gemini response: %s\n", string(bodyBytes))
			return "", fmt.Errorf("empty response from Gemini")
		}

		result := strings.TrimSpace(geminiResp.Candidates[0].Content.Parts[0].Text)
		fmt.Printf("DEBUG: Gemini response received, length: %d chars\n", len(result))
		return result, nil
	}

	return "", fmt.Errorf("gemini request failed after retries: %w", lastErr)
}

// Helper functions for extracting typed values from options map
func getFloat(opts map[string]any, key string, defaultVal float64) float64 {
	if v, ok := opts[key]; ok {
		switch val := v.(type) {
		case float64:
			return val
		case float32:
			return float64(val)
		case int:
			return float64(val)
		}
	}
	return defaultVal
}

func getInt(opts map[string]any, key string, defaultVal int) int {
	if v, ok := opts[key]; ok {
		switch val := v.(type) {
		case int:
			return val
		case float64:
			return int(val)
		case float32:
			return int(val)
		}
	}
	return defaultVal
}
