package utils

import (
	"bytes"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"strings"
)

// MainDeep reads a CSV file and uses it as the basis for the AI's responses.
func MainDeep(prompt string) (string, error) {
	// Load API key from environment variables
	print("CALLED MAIN DEEP")
	apiKey := "sk-"
	if apiKey == "" {
		return "", fmt.Errorf("missing DEEPAPI_KEY environment variable")
	}
	csvPath := "data.csv"
	// Load and process the CSV file
	csvData, err := readCSV(csvPath)
	if err != nil {

		return "", fmt.Errorf("failed to read CSV file: %v", err)

	}

	// Summarize the CSV data for the system prompt
	systemPrompt := fmt.Sprintf("You are a helpful assistant. Use the following data as context for answering questions:\n%s", csvData)

	url := "https://api.deepseek.com/chat/completions"

	// Prepare the request body
	requestBody := map[string]interface{}{
		"model": "deepseek-chat", // Specify the model to use
		"messages": []map[string]string{
			{"role": "system", "content": systemPrompt},
			{"role": "user", "content": prompt}, // Use the provided prompt
		},
	}

	// Convert the request body to JSON
	jsonBody, err := json.Marshal(requestBody)
	if err != nil {
		return "", fmt.Errorf("failed to encode request body: %v", err)
	}

	// Create a new HTTP request
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonBody))
	if err != nil {
		return "", fmt.Errorf("failed to create HTTP request: %v", err)
	}

	// Set request headers
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+apiKey)

	// Send the request using an HTTP client
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to send HTTP request: %v", err)
	}
	defer resp.Body.Close()

	// Read the response body
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read response body: %v", err)
	}

	// Check for a successful response
	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("API returned status %d: %s", resp.StatusCode, body)
	}

	// Parse the response body and return the answer
	var response map[string]interface{}
	if err := json.Unmarshal(body, &response); err != nil {
		return "", fmt.Errorf("failed to parse response body: %v", err)
	}

	// Extract the AI's response from the response object
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

func readCSV(filePath string) (string, error) {

	// Open the CSV file
	file, err := os.Open(filePath)
	if err != nil {
		return "", fmt.Errorf("failed to open file: %v", err)
	}
	defer file.Close()

	// Create a CSV reader
	reader := csv.NewReader(file)

	// Read all records
	records, err := reader.ReadAll()
	if err != nil {
		return "", fmt.Errorf("failed to read CSV data: %v", err)
	}

	// Build a formatted string
	var sb strings.Builder
	sb.WriteString("Parsed CSV Data:\n")
	for i, record := range records {
		sb.WriteString(fmt.Sprintf("Record %d:\n", i+1))
		for j, field := range record {
			sb.WriteString(fmt.Sprintf("  Field %d: %s\n", j+1, field))
		}
		sb.WriteString("\n")
	}

	return sb.String(), nil
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
