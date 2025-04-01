package utils

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
)

// MainDeep reads a JSON file and uses it as context for AI responses.
// If a file is uploaded, its contents are read and appended to the user prompt.
func MainDeep(prompt string, uploadedFile *multipart.FileHeader) (string, error) {
	apiKey := "sk-" // Get API key from environment variable
	if apiKey == "" {
		return "", fmt.Errorf("missing DEEPAPI_KEY environment variable")
	}

	jsonPath := "detailed_data.json"
	jsonData, err := readJSON(jsonPath)
	if err != nil {
		return "", fmt.Errorf("failed to read JSON file: %v", err)
	}

	systemPrompt := fmt.Sprintf(
		"You are a helpful assistant. GIVE SHORT AND CONSISE RESPONSE TO ANY QUESTIONS GIVEN. Use the following data as context for answering questions. "+
			"MAKE SURE TO RETURN OUTPUT IN Markdown format. Use marketing or normal formatting based on the request:\n%s",
		jsonData,
	)

	// Construct initial messages array
	messages := []map[string]interface{}{
		{"role": "system", "content": systemPrompt},
		{"role": "user", "content": prompt},
	}

	// Read and append file contents (if provided)
	if uploadedFile != nil {
		file, err := uploadedFile.Open()
		if err != nil {
			return "", fmt.Errorf("failed to open uploaded file: %v", err)
		}
		defer file.Close()

		fileContent, err := io.ReadAll(file)
		if err != nil {
			return "", fmt.Errorf("failed to read file content: %v", err)
		}

		// Append the file content as text to the user message
		messages[1]["content"] = fmt.Sprintf("%s\n\n[Attached File Contents]:\n%s", prompt, string(fileContent))
	}

	// Create request body
	requestBody := map[string]interface{}{
		"model":    "deepseek-chat",
		"messages": messages,
	}

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

	// Send request
	client := &http.Client{}
	resp, err := client.Do(req)
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

	// Parse response
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

func readJSON(filePath string) (string, error) {
	data, err := os.ReadFile(filePath)
	if err != nil {
		return "", fmt.Errorf("failed to read file: %v", err)
	}

	var formattedJSON interface{} // Change from map[string]interface{} to interface{}
	if err := json.Unmarshal(data, &formattedJSON); err != nil {
		return "", fmt.Errorf("failed to parse JSON: %v", err)
	}

	prettyJSON, err := json.MarshalIndent(formattedJSON, "", "  ")
	if err != nil {
		return "", fmt.Errorf("failed to format JSON: %v", err)
	}

	return string(prettyJSON), nil
}
