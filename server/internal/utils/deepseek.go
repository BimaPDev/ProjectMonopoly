package utils

import (
	"bytes"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"strings"
)

// mainDeep reads a CSV file and uses it as the basis for the AI's responses.
func mainDeep(prompt string) (string, error) {
	// Load API key from environment variables
	apiKey := os.Getenv("DEEPAPI_KEY")
	if apiKey == "" {
		log.Fatal("Missing DEEPAPI_KEY environment variable")
	}

	// Load and process the CSV file
	csvData, err := readCSV("detailed_data.csv")
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

	// Assuming the response has a "choices" array and each choice has "message" content
	choices := response["choices"].([]interface{})
	if len(choices) > 0 {
		choice := choices[0].(map[string]interface{})
		message := choice["message"].(map[string]interface{})["content"].(string)
		return message, nil
	}

	return "", fmt.Errorf("no response from API")
}

// readCSV reads the contents of a CSV file and returns it as a formatted string.
func readCSV(filePath string) (string, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return "", err
	}
	defer file.Close()

	reader := csv.NewReader(file)
	records, err := reader.ReadAll()
	if err != nil {
		return "", err
	}

	// Format the CSV data into a string (e.g., as a table)
	var sb strings.Builder
	for _, record := range records {
		sb.WriteString(strings.Join(record, ", "))
		sb.WriteString("\n")
	}

	return sb.String(), nil
}
