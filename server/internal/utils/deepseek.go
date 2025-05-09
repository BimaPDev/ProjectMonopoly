package utils

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"sync"
	"time"
)

var (
	// Shared HTTP client with optimized timeouts and connection reuse
	httpClient = &http.Client{
		Timeout: 300 * time.Second,
		Transport: &http.Transport{
			MaxIdleConns:        100,
			MaxIdleConnsPerHost: 100,
			IdleConnTimeout:     90 * time.Second,
			ForceAttemptHTTP2:   true, // Enable HTTP/2 for better performance
		},
	}

	// In-memory cache for JSON file contents with TTL
	jsonCache      = make(map[string]cacheEntry)
	jsonCacheMux   sync.RWMutex
	cacheExpiry    = 15 * time.Minute
	initializeOnce sync.Once
)

type cacheEntry struct {
	content   string
	timestamp time.Time
}

// MainDeep reads your JSON context file (and any uploaded file),
// constructs an OpenAI-compatible chat payload, and sends it to your
// local Ollama chat/completions endpoint, defaulting to model "gemma".
func MainDeep(prompt string, uploadedFile *multipart.FileHeader) (string, error) {
	// Initialize cache on first call (run once)
	initializeOnce.Do(func() {
		go cacheCleaner()
		// Preload common JSON files in background
		go func() {
			_, _ = getCachedJSON("detailed_data.json")
		}()
	})

	// Create a context with timeout for the entire operation
	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()

	// 1) Determine Ollama endpoint & model from env (with sensible defaults)
	ollamaURL := getEnvOrDefault("OLLAMA_URL", "http://localhost:11434/v1/chat/completions")
	model := getEnvOrDefault("OLLAMA_MODEL", "gemma3")

	// 2) Load JSON data and process user content concurrently
	var jsonData, userContent string
	var jsonErr, fileErr error
	var wg sync.WaitGroup
	wg.Add(1)

	// Load JSON data in a goroutine
	go func() {
		defer wg.Done()
		jsonData, jsonErr = getCachedJSON("detailed_data.json")
	}()

	// Process uploaded file content if present
	userContent = prompt
	if uploadedFile != nil {
		wg.Add(1)
		go func() {
			defer wg.Done()
			var fc string
			fc, fileErr = readFileContent(uploadedFile)
			if fileErr == nil {
				userContent = fmt.Sprintf("%s\n\n[Attached File Contents]:\n%s", prompt, fc)
			}
		}()
	}

	// Wait for concurrent operations to complete
	wg.Wait()

	// Check for errors
	if jsonErr != nil {
		return "", fmt.Errorf("failed to read JSON file: %v", jsonErr)
	}
	if fileErr != nil {
		return "", fileErr
	}

	// 3) Build chat messages in OpenAI format
	messages := []map[string]interface{}{
		{
			"role": "system",
			"content": fmt.Sprintf(
				`You are an expert Instagram marketing strategist working at a high-performance social media agency that specializes in indie games and creative tech.

                    You already have access to pre-analyzed Instagram post data, including fields like:

                    username, likes, comments, followers, engagement_rate, hashtags, post_hour, ai_class, trend_score, caption, and ai_summary.

                    Your role is to provide data-driven answers and actionable insights based on this dataset. You are not guessing — you are reasoning from actual numbers.

                    You can help users:

                    Discover what types of posts work best (e.g., cinematic vs. promotional).

                    Suggest best times to post based on engagement and trend scores.

                    Recommend which hashtags to focus on or which ones to drop.

                    Evaluate the performance of specific usernames or posts.

                    Compare strategies between creators.

                    Suggest ways to increase reach, engagement, and follower growth.

                    You can summarize findings, explain why a post performed well or poorly, and offer creative ideas backed by the data.

                    ⚠️ Do not make up data. Only reason using what’s available.

                    🗣 If the user asks a question like "what’s the best time to post?" or "which hashtags are trending?", give them clear, structured, real answers from the dataset.`,
				jsonData,
			),
		},
		{
			"role":    "user",
			"content": userContent,
		},
	}

	// 4) Build the request body
	requestBody := map[string]interface{}{
		"model":    model,
		"messages": messages,
		// Add temperature to potentially speed up responses
		"temperature": 0.7,
		"stream":      false,
	}

	// 5) Send to Ollama with timeout context
	return makeAPIRequest(ctx, requestBody, ollamaURL)
}

// makeAPIRequest sends an OpenAI-style chat request to the given URL,
// and extracts the assistant's reply from the JSON response.
func makeAPIRequest(ctx context.Context, requestBody map[string]interface{}, apiURL string) (string, error) {
	jsonBody, err := json.Marshal(requestBody)
	if err != nil {
		return "", fmt.Errorf("failed to encode request body: %v", err)
	}

	req, err := http.NewRequestWithContext(ctx, "POST", apiURL, bytes.NewBuffer(jsonBody))
	if err != nil {
		return "", fmt.Errorf("failed to create HTTP request: %v", err)
	}
	req.Header.Set("Content-Type", "application/json")

	// Ollama v1 ignores the API key, but if you want to
	// pass one for compatibility:
	if apiKey := os.Getenv("OLLAMA_API_KEY"); apiKey != "" {
		req.Header.Set("Authorization", "Bearer "+apiKey)
	}

	// Add some timing for debugging purposes
	start := time.Now()
	resp, err := httpClient.Do(req)
	elapsed := time.Since(start)

	// Log the timing info if needed
	if os.Getenv("DEBUG") == "true" {
		fmt.Printf("API request took %v\n", elapsed)
	}

	if err != nil {
		return "", fmt.Errorf("HTTP request failed after %v: %v", elapsed, err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read response body: %v", err)
	}
	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("API returned status %d: %s", resp.StatusCode, body)
	}

	// Parse OpenAI-style response
	var out struct {
		Choices []struct {
			Message struct {
				Content string `json:"content"`
			} `json:"message"`
		} `json:"choices"`
	}
	if err := json.Unmarshal(body, &out); err != nil {
		return "", fmt.Errorf("invalid response format: %v", err)
	}
	if len(out.Choices) == 0 {
		return "", fmt.Errorf("no choices in response")
	}

	return out.Choices[0].Message.Content, nil
}

// getCachedJSON loads a JSON file from disk, pretty-prints it,
// and caches the result in memory with TTL.
func getCachedJSON(filePath string) (string, error) {
	// Check if we have a valid cached entry
	jsonCacheMux.RLock()
	if entry, ok := jsonCache[filePath]; ok {
		if time.Since(entry.timestamp) < cacheExpiry {
			jsonCacheMux.RUnlock()
			return entry.content, nil
		}
	}
	jsonCacheMux.RUnlock()

	jsonCacheMux.Lock()
	defer jsonCacheMux.Unlock()

	// Double-check in case it was cached during lock wait
	if entry, ok := jsonCache[filePath]; ok {
		if time.Since(entry.timestamp) < cacheExpiry {
			return entry.content, nil
		}
	}

	data, err := os.ReadFile(filePath)
	if err != nil {
		return "", fmt.Errorf("failed to read file: %v", err)
	}

	// Just use the raw data instead of pretty-printing if it's valid JSON
	if json.Valid(data) {
		jsonCache[filePath] = cacheEntry{
			content:   string(data),
			timestamp: time.Now(),
		}
		return string(data), nil
	}

	// Only pretty-print if necessary
	var pretty interface{}
	if err := json.Unmarshal(data, &pretty); err != nil {
		return "", fmt.Errorf("failed to parse JSON: %v", err)
	}
	out, err := json.MarshalIndent(pretty, "", "  ")
	if err != nil {
		return "", fmt.Errorf("failed to format JSON: %v", err)
	}

	jsonCache[filePath] = cacheEntry{
		content:   string(out),
		timestamp: time.Now(),
	}
	return string(out), nil
}

// readFileContent reads the entire contents of an uploaded multipart file.
func readFileContent(uploadedFile *multipart.FileHeader) (string, error) {
	f, err := uploadedFile.Open()
	if err != nil {
		return "", fmt.Errorf("failed to open uploaded file: %v", err)
	}
	defer f.Close()

	data, err := io.ReadAll(f)
	if err != nil {
		return "", fmt.Errorf("failed to read file content: %v", err)
	}
	return string(data), nil
}

// getEnvOrDefault gets an environment variable or returns default if not set
func getEnvOrDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// cacheCleaner periodically cleans expired items from the cache
func cacheCleaner() {
	ticker := time.NewTicker(5 * time.Minute)
	defer ticker.Stop()

	for range ticker.C {
		cleanCache()
	}
}

// cleanCache removes expired items from the JSON cache
func cleanCache() {
	jsonCacheMux.Lock()
	defer jsonCacheMux.Unlock()

	now := time.Now()
	for key, entry := range jsonCache {
		if now.Sub(entry.timestamp) > cacheExpiry {
			delete(jsonCache, key)
		}
	}
}
