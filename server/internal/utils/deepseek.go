// package utils

// import (
// 	"bytes"
// 	"encoding/json"
// 	"fmt"
// 	"io"
// 	"mime/multipart"
// 	"net/http"
// 	"os"
// 	"sync"
// 	"time"
// )

// var (
// 	// Shared HTTP client with sensible timeouts and connection reuse
// 	httpClient = &http.Client{
// 		Transport: &http.Transport{
// 			MaxIdleConns:        100,
// 			MaxIdleConnsPerHost: 100,
// 			IdleConnTimeout:     90 * time.Second,
// 		},
// 	}

// 	// Simple in-memory cache for JSON file contents
// 	jsonCache    = make(map[string]string)
// 	jsonCacheMux sync.RWMutex
// )

// // MainOllama reads your JSON context file (and any uploaded file),
// // constructs an OpenAI-compatible chat payload, and sends it to your
// // local Ollama chat/completions endpoint.
// func MainDeep(prompt string, uploadedFile *multipart.FileHeader) (string, error) {
// 	// 1) Determine Ollama endpoint & model from env (with sensible defaults)
// 	ollamaURL := os.Getenv("OLLAMA_URL")
// 	if ollamaURL == "" {
// 		ollamaURL = "http://localhost:11434/v1/chat/completions"
// 	}
// 	model := os.Getenv("OLLAMA_MODEL")
// 	if model == "" {
// 		model = "gemma3"
// 	}

// 	// 2) Load your cached JSON data
// 	jsonData, err := getCachedJSON("detailed_data.json")
// 	if err != nil {
// 		return "", fmt.Errorf("failed to read JSON file: %v", err)
// 	}
// 	fmt.Sprintf("JSON data: %s\n", jsonData)
// 	// 3) Append uploaded file content if present
// 	userContent := prompt
// 	if uploadedFile != nil {
// 		fc, err := readFileContent(uploadedFile)
// 		if err != nil {
// 			return "", err
// 		}
// 		userContent = fmt.Sprintf("%s\n\nUploaded file contents:\n%s", userContent, fc)
// 	}
// 	fmt.Printf(">>> UserContent content:\n%s\n", userContent)
// 	// 4) Build chat messages in OpenAI format
// 	messages := []map[string]interface{}{
// 		{
// 			"role": "system",
// 			"content": fmt.Sprintf(
// 				"You are a helpful assistant, the topic is related to indie games. Use any relevent information about indie games to answer. GIVE SHORT AND CONCISE RESPONSES. Use the following data as context:\n %s", jsonData),
// 		},
// 		{
// 			"role":    "user",
// 			"content": userContent,
// 		},
// 	}

// 	// 5) Build the request body
// 	requestBody := map[string]interface{}{
// 		"model":    model,
// 		"messages": messages,
// 		"stream":   false,
// 	}

// 	// 6) Send to Ollama and return the assistant's reply
// 	return makeAPIRequest(requestBody, ollamaURL)
// }

// // makeAPIRequest sends an OpenAI-style chat request to the given URL,
// // and extracts the assistant’s reply from the JSON response.
// func makeAPIRequest(requestBody map[string]interface{}, apiURL string) (string, error) {
// 	jsonBody, err := json.Marshal(requestBody)
// 	if err != nil {
// 		return "", fmt.Errorf("failed to encode request body: %v", err)
// 	}

// 	req, err := http.NewRequest("POST", apiURL, bytes.NewBuffer(jsonBody))
// 	if err != nil {
// 		return "", fmt.Errorf("failed to create HTTP request: %v", err)
// 	}
// 	req.Header.Set("Content-Type", "application/json")

// 	// Ollama v1 ignores the API key, but if you want to
// 	// pass one for compatibility:
// 	if apiKey := os.Getenv("OLLAMA_API_KEY"); apiKey != "" {
// 		req.Header.Set("Authorization", "Bearer "+apiKey)
// 	}

// 	resp, err := httpClient.Do(req)
// 	if err != nil {
// 		return "", fmt.Errorf("HTTP request failed: %v", err)
// 	}
// 	defer resp.Body.Close()

// 	body, err := io.ReadAll(resp.Body)
// 	if err != nil {
// 		return "", fmt.Errorf("failed to read response body: %v", err)
// 	}
// 	if resp.StatusCode != http.StatusOK {
// 		return "", fmt.Errorf("API returned status %d: %s", resp.StatusCode, body)
// 	}

// 	// Parse OpenAI-style response
// 	var out struct {
// 		Choices []struct {
// 			Message struct {
// 				Content string `json:"content"`
// 			} `json:"message"`
// 		} `json:"choices"`
// 	}
// 	if err := json.Unmarshal(body, &out); err != nil {
// 		return "", fmt.Errorf("invalid response format: %v", err)
// 	}
// 	if len(out.Choices) == 0 {
// 		return "", fmt.Errorf("no choices in response")
// 	}

// 	return out.Choices[0].Message.Content, nil
// }

// // getCachedJSON loads a JSON file from disk, pretty-prints it,
// // and caches the result in memory.
// func getCachedJSON(filePath string) (string, error) {
// 	jsonCacheMux.RLock()
// 	if cached, ok := jsonCache[filePath]; ok {
// 		jsonCacheMux.RUnlock()
// 		return cached, nil
// 	}
// 	jsonCacheMux.RUnlock()

// 	jsonCacheMux.Lock()
// 	defer jsonCacheMux.Unlock()
// 	if cached, ok := jsonCache[filePath]; ok {
// 		return cached, nil
// 	}

// 	data, err := os.ReadFile(filePath)
// 	if err != nil {
// 		return "", fmt.Errorf("failed to read file: %v", err)
// 	}

// 	var pretty interface{}
// 	if err := json.Unmarshal(data, &pretty); err != nil {
// 		return "", fmt.Errorf("failed to parse JSON: %v", err)
// 	}
// 	out, err := json.MarshalIndent(pretty, "", "  ")
// 	if err != nil {
// 		return "", fmt.Errorf("failed to format JSON: %v", err)
// 	}

// 	jsonCache[filePath] = string(out)
// 	return string(out), nil
// }

// // readFileContent reads the entire contents of an uploaded multipart file.
// func readFileContent(uploadedFile *multipart.FileHeader) (string, error) {
// 	f, err := uploadedFile.Open()
// 	if err != nil {
// 		return "", fmt.Errorf("failed to open uploaded file: %v", err)
// 	}
// 	defer f.Close()

// 	data, err := io.ReadAll(f)
// 	if err != nil {
// 		return "", fmt.Errorf("failed to read file content: %v", err)
// 	}
// 	return string(data), nil
// }

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
	// Shared HTTP client with sensible timeouts and connection reuse
	httpClient = &http.Client{
		Transport: &http.Transport{
			MaxIdleConns:        100,
			MaxIdleConnsPerHost: 100,
			IdleConnTimeout:     90 * time.Second,
		},
	}

	// Simple in-memory cache for JSON file contents
	jsonCache    = make(map[string]string)
	jsonCacheMux sync.RWMutex
)

// MainDeep reads your JSON context file (and any uploaded file),
// constructs an OpenAI-compatible chat payload, and sends it to your
// local Ollama chat/completions endpoint.
func MainDeep(prompt string, uploadedFile *multipart.FileHeader) (string, error) {
	// 1) Determine Ollama endpoint & model from env (with sensible defaults)
	ollamaURL := os.Getenv("OLLAMA_URL")
	if ollamaURL == "" {
		ollamaURL = "http://localhost:11434/v1/chat/completions"
	}
	model := os.Getenv("OLLAMA_MODEL")
	if model == "" {
		model = "gemma3"
	}

	// 2) Load your cached JSON data
	jsonData, err := getCachedJSON("detailed_data.json")
	if err != nil {
		return "", fmt.Errorf("failed to read JSON file: %v", err)
	}
	fmt.Printf("JSON data: %s\n", jsonData) // Added print statement

	// 3) Append uploaded file content if present
	userContent := prompt
	if uploadedFile != nil {
		fc, err := readFileContent(uploadedFile)
		if err != nil {
			return "", err
		}
		userContent = fmt.Sprintf("%s\n\nUploaded file contents:\n%s", userContent, fc)
	}
	fmt.Printf(">>> UserContent content:\n%s\n", userContent)

	// 4) Build chat messages in OpenAI format
	messages := []map[string]interface{}{
		{
			"role": "system",
			"content": fmt.Sprintf(
				"You are a helpful assistant, the topic is related to indie games. Use any relevent information about indie games to answer. GIVE SHORT AND CONCISE RESPONSES. Use the following data as context:\n %s", jsonData),
		},
		{
			"role":    "user",
			"content": userContent,
		},
	}
	fmt.Printf(">>> Messages payload:\n%+v\n", messages) // Added print statement

	// 5) Build the request body
	requestBody := map[string]interface{}{
		"model":    model,
		"messages": messages,
		"stream":   false,
	}

	// 6) Send to Ollama and return the assistant's reply
	return makeAPIRequest(requestBody, ollamaURL)
}

// makeAPIRequest sends an OpenAI-style chat request to the given URL,
// and extracts the assistant’s reply from the JSON response.
func makeAPIRequest(requestBody map[string]interface{}, apiURL string) (string, error) {
	jsonBody, err := json.Marshal(requestBody)
	if err != nil {
		return "", fmt.Errorf("failed to encode request body: %v", err)
	}
	fmt.Printf(">>> Request Body:\n%s\n", jsonBody) // Added print statement

	req, err := http.NewRequest("POST", apiURL, bytes.NewBuffer(jsonBody))
	if err != nil {
		return "", fmt.Errorf("failed to create HTTP request: %v", err)
	}
	req.Header.Set("Content-Type", "application/json")

	// Ollama v1 ignores the API key, but if you want to
	// pass one for compatibility:
	if apiKey := os.Getenv("OLLAMA_API_KEY"); apiKey != "" {
		req.Header.Set("Authorization", "Bearer "+apiKey)
	}

	resp, err := httpClient.Do(req)
	if err != nil {
		return "", fmt.Errorf("HTTP request failed: %v", err)
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
// and caches the result in memory.
func getCachedJSON(filePath string) (string, error) {
	jsonCacheMux.RLock()
	if cached, ok := jsonCache[filePath]; ok {
		jsonCacheMux.RUnlock()
		return cached, nil
	}
	jsonCacheMux.RUnlock()

	jsonCacheMux.Lock()
	defer jsonCacheMux.Unlock()
	if cached, ok := jsonCache[filePath]; ok {
		return cached, nil
	}

	data, err := os.ReadFile(filePath)
	if err != nil {
		return "", fmt.Errorf("failed to read file: %v", err)
	}

	var pretty interface{}
	if err := json.Unmarshal(data, &pretty); err != nil {
		return "", fmt.Errorf("failed to parse JSON: %v", err)
	}
	out, err := json.MarshalIndent(pretty, "", "  ")
	if err != nil {
		return "", fmt.Errorf("failed to format JSON: %v", err)
	}

	jsonCache[filePath] = string(out)
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
