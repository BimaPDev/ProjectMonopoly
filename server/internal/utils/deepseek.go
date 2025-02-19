package utils

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
)

// MainDeep reads a JSON file and uses it as the basis for the AI's responses.
func MainDeep(prompt string) (string, error) {
	apiKey := "sk-" // Ensure you set a valid API key
	if apiKey == "" {
		return "", fmt.Errorf("missing DEEPAPI_KEY environment variable")
	}

	jsonPath := "detailed_data.json"
	// Load and process the JSON file
	jsonData, err := readJSON(jsonPath)
	if err != nil {
		return "", fmt.Errorf("failed to read JSON file: %v", err)
	}

	// Summarize the JSON data for the system prompt
	systemPrompt := fmt.Sprintf("You are a helpful assistant. Use the following data as context for answering questions. MAKE SURE TO RETURN OUTPUT IN Markdown format, there are two marketing and normal and use whichever depending on what is asked:\n%s", jsonData)

	url := "https://api.deepseek.com/chat/completions"

	requestBody := map[string]interface{}{
		"model": "deepseek-chat",
		"messages": []map[string]string{
			{"role": "system", "content": systemPrompt},
			{"role": "user", "content": prompt},
		},
	}

	//request body to JSON
	jsonBody, err := json.Marshal(requestBody)
	if err != nil {
		return "", fmt.Errorf("failed to encode request body: %v", err)
	}

	// a new HTTP request
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonBody))
	if err != nil {
		return "", fmt.Errorf("failed to create HTTP request: %v", err)
	}

	// request headers
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+apiKey)

	// send the request using an HTTP client
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to send HTTP request: %v", err)
	}
	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read response body: %v", err)
	}

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("API returned status %d: %s", resp.StatusCode, body)
	}

	var response map[string]interface{}
	if err := json.Unmarshal(body, &response); err != nil {
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

// readJSON reads a JSON file and returns its contents as a string.
func readJSON(filePath string) (string, error) {
	// Open the JSON file
	file, err := os.Open(filePath)
	if err != nil {
		return "", fmt.Errorf("failed to open file: %v", err)
	}
	defer file.Close()

	// Read the file contents
	data, err := ioutil.ReadAll(file)
	if err != nil {
		return "", fmt.Errorf("failed to read JSON data: %v", err)
	}

	var formattedJSON map[string]interface{}
	if err := json.Unmarshal(data, &formattedJSON); err != nil {
		return "", fmt.Errorf("failed to parse JSON: %v", err)
	}

	prettyJSON, err := json.MarshalIndent(formattedJSON, "", "  ")
	if err != nil {
		return "", fmt.Errorf("failed to format JSON: %v", err)
	}

	return string(prettyJSON), nil
}

// func ChatDeep(prompt string) (string, error) {
// 	// Load API key from environment variables
// 	apiKey := "sk-"
// 	if apiKey == "" {
// 		return "", fmt.Errorf("missing DEEPAPI_KEY environment variable")
// 	}

// 	// DeepSeek API URL
// 	url := "https://api.deepseek.com/chat/completions"

// 	// Prepare the request body
// 	requestBody := map[string]interface{}{
// 		"model": "deepseek-chat", // Specify the model
// 		"messages": []map[string]string{
// 			{"role": "user", "content": prompt}, // User's prompt
// 		},
// 	}

// 	// Convert the request body to JSON
// 	jsonBody, err := json.Marshal(requestBody)
// 	if err != nil {
// 		return "", fmt.Errorf("failed to encode request body: %v", err)
// 	}

// 	// Create a new HTTP request
// 	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonBody))
// 	if err != nil {
// 		return "", fmt.Errorf("failed to create HTTP request: %v", err)
// 	}

// 	// Set headers
// 	req.Header.Set("Content-Type", "application/json")
// 	req.Header.Set("Authorization", "Bearer "+apiKey)

// 	// Send the request using an HTTP client
// 	client := &http.Client{}
// 	resp, err := client.Do(req)
// 	if err != nil {
// 		return "", fmt.Errorf("failed to send HTTP request: %v", err)
// 	}
// 	defer resp.Body.Close()

// 	// Check for a successful response
// 	if resp.StatusCode != http.StatusOK {
// 		body, _ := ioutil.ReadAll(resp.Body) // Read the body for error details
// 		return "", fmt.Errorf("API returned status %d: %s", resp.StatusCode, body)
// 	}

// 	// Parse the response body
// 	body, err := ioutil.ReadAll(resp.Body)
// 	if err != nil {
// 		return "", fmt.Errorf("failed to read response body: %v", err)
// 	}

// 	// Extract the content from the API response
// 	var response map[string]interface{}
// 	if err := json.Unmarshal(body, &response); err != nil {
// 		return "", fmt.Errorf("failed to parse response: %v", err)
// 	}

// 	// Assume the response contains a "choices" array with "message" content
// 	choices, ok := response["choices"].([]interface{})
// 	if !ok || len(choices) == 0 {
// 		return "", fmt.Errorf("invalid response format or no choices returned")
// 	}

// 	choice, ok := choices[0].(map[string]interface{})
// 	if !ok {
// 		return "", fmt.Errorf("unexpected choice format")
// 	}

// 	message, ok := choice["message"].(map[string]interface{})
// 	if !ok {
// 		return "", fmt.Errorf("unexpected message format")
// 	}

// 	content, ok := message["content"].(string)
// 	if !ok {
// 		return "", fmt.Errorf("response content is not a string")
// 	}

// 	return content, nil
// }
