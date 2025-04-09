package utils

import (
	"bytes"
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
	// Create a shared HTTP client with timeouts
	httpClient = &http.Client{
		Timeout: 30 * time.Second,
		Transport: &http.Transport{
			MaxIdleConns:        100,
			MaxIdleConnsPerHost: 100,
			IdleConnTimeout:     90 * time.Second,
		},
	}

	// Cache for JSON data
	jsonCache    = make(map[string]string)
	jsonCacheMux sync.RWMutex
)

// MainDeep reads a JSON file and uses it as context for AI responses.
// If a file is uploaded, its contents are read and appended to the user prompt.
func MainDeep(prompt string, uploadedFile *multipart.FileHeader) (string, error) {
	apiKey := "sk-2a0bb6456b094dddaca045fb70557ca2" // Get API key from environment variable
	if apiKey == "" {
		return "", fmt.Errorf("missing DEEPAPI_KEY environment variable")
	}

	jsonPath := "detailed_data.json"
	jsonData, err := getCachedJSON(jsonPath)
	if err != nil {
		return "", fmt.Errorf("failed to read JSON file: %v", err)
	}

	// Prepare the user content with file content if provided
	userContent := prompt
	if uploadedFile != nil {
		fileContent, err := readFileContent(uploadedFile)
		if err != nil {
			return "", err
		}
		userContent = fmt.Sprintf("%s\n\n[Attached File Contents]:\n%s", prompt, fileContent)
	}

	// Construct messages directly as a slice to avoid unnecessary manipulation
	messages := []map[string]interface{}{
		{
			"role": "system",
			"content": fmt.Sprintf(
				"You are a helpful assistant. GIVE SHORT AND CONSISE RESPONSE TO ANY QUESTIONS GIVEN. Use the following data as context for answering questions. "+
					"MAKE SURE TO RETURN OUTPUT IN Markdown format. Use marketing or normal formatting based on the request:\n%s",
				jsonData,
			),
		},
		{"role": "user", "content": userContent},
	}

	// Create request body
	requestBody := map[string]interface{}{
		"model":    "deepseek-chat",
		"messages": messages,
	}

	return makeAPIRequest(requestBody, apiKey)
}

// getCachedJSON retrieves JSON from cache or reads from file if not cached
func getCachedJSON(filePath string) (string, error) {
	// Check cache first
	jsonCacheMux.RLock()
	cached, exists := jsonCache[filePath]
	jsonCacheMux.RUnlock()

	if exists {
		return cached, nil
	}

	// If not in cache, read from file
	jsonCacheMux.Lock()
	defer jsonCacheMux.Unlock()

	// Check again in case another goroutine populated the cache
	if cached, exists := jsonCache[filePath]; exists {
		return cached, nil
	}

	data, err := os.ReadFile(filePath)
	if err != nil {
		return "", fmt.Errorf("failed to read file: %v", err)
	}

	var formattedJSON interface{}
	if err := json.Unmarshal(data, &formattedJSON); err != nil {
		return "", fmt.Errorf("failed to parse JSON: %v", err)
	}

	prettyJSON, err := json.MarshalIndent(formattedJSON, "", "  ")
	if err != nil {
		return "", fmt.Errorf("failed to format JSON: %v", err)
	}

	result := string(prettyJSON)
	jsonCache[filePath] = result
	return result, nil
}

// readFileContent reads the content of an uploaded file
func readFileContent(uploadedFile *multipart.FileHeader) (string, error) {
	file, err := uploadedFile.Open()
	if err != nil {
		return "", fmt.Errorf("failed to open uploaded file: %v", err)
	}
	defer file.Close()

	fileContent, err := io.ReadAll(file)
	if err != nil {
		return "", fmt.Errorf("failed to read file content: %v", err)
	}

	return string(fileContent), nil
}

// makeAPIRequest sends the request to the DeepSeek API
func makeAPIRequest(requestBody map[string]interface{}, apiKey string) (string, error) {
	// Convert request body to JSON
	jsonBody, err := json.Marshal(requestBody)
	if err != nil {
		return "", fmt.Errorf("failed to encode request body: %v", err)
	}

	// Create HTTP request
	req, err := http.NewRequest("POST", "https://api.deepseek.com/chat/completions", bytes.NewBuffer(jsonBody))
	if err != nil {
		return "", fmt.Errorf("failed to create HTTP request: %v", err)
	}

	// Set headers
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+apiKey)

	// Send request using the shared client
	resp, err := httpClient.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to send HTTP request: %v", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read response body: %v", err)
	}

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("API returned status %d: %s", resp.StatusCode, body)
	}

	return extractResponseContent(body)
}

// extractResponseContent extracts the content from API response
func extractResponseContent(responseBody []byte) (string, error) {
	var response map[string]interface{}
	if err := json.Unmarshal(responseBody, &response); err != nil {
		return "", fmt.Errorf("failed to parse response body: %v", err)
	}

	choices, ok := response["choices"].([]interface{})
	if !ok || len(choices) == 0 {
		return "", fmt.Errorf("invalid response format or no choices available")
	}

	choice, ok := choices[0].(map[string]interface{})
	if !ok {
		return "", fmt.Errorf("unexpected choice format")
	}

	message, ok := choice["message"].(map[string]interface{})
	if !ok {
		return "", fmt.Errorf("unexpected message format")
	}

	content, ok := message["content"].(string)
	if !ok {
		return "", fmt.Errorf("content is not a string")
	}

	return content, nil
}
