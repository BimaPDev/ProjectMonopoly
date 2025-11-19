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
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
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

// MainDeep retrieves game context from database and constructs an OpenAI-compatible
// chat payload, sending it to your local Ollama chat/completions endpoint.
func MainDeep(prompt string, userID int32, groupID *int32, uploadedFile *multipart.FileHeader, queries *db.Queries) (string, error) {
	// 1) Determine Ollama endpoint & model from env (with sensible defaults)
	ollamaURL := os.Getenv("OLLAMA_URL")
	if ollamaURL == "" {
		ollamaURL = "http://localhost:11434/v1/chat/completions"
	}
	model := os.Getenv("OLLAMA_MODEL")
	if model == "" {
		model = "gemma3"
	}

	// 2) Retrieve game context from database
	gameContextData, err := getGameContextData(userID, groupID, queries)
	if err != nil {
		// Log the error but continue - we can still answer without game context
		fmt.Printf("Warning: Could not retrieve game context: %v\n", err)
		gameContextData = "No game context available. Provide general indie game assistance."
	}
	fmt.Printf("Game context data: %s\n", gameContextData)

	// 3) Search RAG documents if groupID is available
	var ragDocuments string
	if groupID != nil && *groupID > 0 {
		ragDocs, err := searchRAGDocuments(userID, *groupID, prompt, queries)
		if err != nil {
			fmt.Printf("Warning: RAG search failed: %v\n", err)
			ragDocuments = ""
		} else if ragDocs != "" {
			ragDocuments = ragDocs
			fmt.Printf("Found RAG documents\n")
		} else {
			fmt.Printf("No relevant RAG documents found\n")
		}
	}

	// 4) Append uploaded file content if present
	userContent := prompt
	if uploadedFile != nil {
		fc, err := readFileContent(uploadedFile)
		if err != nil {
			return "", err
		}
		userContent = fmt.Sprintf("%s\n\nUploaded file contents:\n%s", userContent, fc)
	}
	fmt.Printf(">>> UserContent content:\n%s\n", userContent)

	// 5) Build comprehensive context for LLM
	systemContext := "You are a helpful assistant specialized in indie game marketing and development. Use any relevant information about indie games to answer. GIVE SHORT AND CONCISE RESPONSES.\n\n"
	systemContext += gameContextData

	if ragDocuments != "" {
		systemContext += "\n\n" + ragDocuments
		systemContext += "\nWhen using information from documents, cite the page number like [p.X]."
	}

	// 6) Build chat messages in OpenAI format
	messages := []map[string]interface{}{
		{
			"role":    "system",
			"content": systemContext,
		},
		{
			"role":    "user",
			"content": userContent,
		},
	}
	fmt.Printf(">>> Messages payload:\n%+v\n", messages)

	// 7) Build the request body
	requestBody := map[string]interface{}{
		"model":    model,
		"messages": messages,
		"stream":   false,
	}

	// 8) Send to Ollama and return the assistant's reply
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

// getGameContextData retrieves game context from database and formats it for the LLM.
// Priority: group context > user context
func getGameContextData(userID int32, groupID *int32, queries *db.Queries) (string, error) {
	ctx := context.Background()
	var gameContext db.GameContext
	var err error

	// Try to get group context first if groupID is provided
	if groupID != nil && *groupID > 0 {
		nullGroupID := sql.NullInt32{Int32: *groupID, Valid: true}
		gameContext, err = queries.GetGameContextByGroupID(ctx, nullGroupID)
		if err == nil {
			return formatGameContext(gameContext), nil
		}
		fmt.Printf("No group context found (group_id=%d), trying user context: %v\n", *groupID, err)
	}

	// Fall back to user context
	gameContext, err = queries.GetGameContextByUserID(ctx, userID)
	if err != nil {
		return "", fmt.Errorf("no game context found for user_id=%d: %v", userID, err)
	}

	return formatGameContext(gameContext), nil
}

// searchRAGDocuments searches workshop_chunks for relevant content based on the user's prompt
func searchRAGDocuments(userID int32, groupID int32, prompt string, queries *db.Queries) (string, error) {
	ctx := context.Background()

	// Search for top 6 relevant chunks
	chunks, err := queries.SearchChunks(ctx, db.SearchChunksParams{
		Q:       prompt,
		UserID:  userID,
		GroupID: groupID,
		N:       6, // Limit to 6 chunks
	})

	if err != nil {
		return "", fmt.Errorf("failed to search RAG documents: %v", err)
	}

	if len(chunks) == 0 {
		return "", nil // No chunks found, not an error
	}

	// Format chunks for LLM with page citations
	var builder strings.Builder
	builder.WriteString("=== RELEVANT DOCUMENTS ===\n\n")

	for i, chunk := range chunks {
		pageInfo := "unknown"
		if chunk.Page.Valid {
			pageInfo = fmt.Sprintf("%d", chunk.Page.Int32)
		}

		builder.WriteString(fmt.Sprintf("[%d] Page %s:\n%s\n\n",
			i+1,
			pageInfo,
			strings.TrimSpace(chunk.Content),
		))
	}

	builder.WriteString("======================\n")
	return builder.String(), nil
}

// formatGameContext converts a GameContext database record into a formatted string for the LLM
func formatGameContext(gc db.GameContext) string {
	var builder strings.Builder

	builder.WriteString("=== GAME CONTEXT ===\n\n")

	// Section 1: Basic Game Information
	builder.WriteString("## Basic Information\n")
	builder.WriteString(fmt.Sprintf("Game Title: %s\n", gc.GameTitle))
	if gc.StudioName.Valid {
		builder.WriteString(fmt.Sprintf("Studio: %s\n", gc.StudioName.String))
	}
	if gc.GameSummary.Valid {
		builder.WriteString(fmt.Sprintf("Summary: %s\n", gc.GameSummary.String))
	}
	if len(gc.Platforms) > 0 {
		builder.WriteString(fmt.Sprintf("Platforms: %s\n", strings.Join(gc.Platforms, ", ")))
	}
	if gc.EngineTech.Valid {
		builder.WriteString(fmt.Sprintf("Engine/Tech: %s\n", gc.EngineTech.String))
	}

	// Section 2: Core Identity
	builder.WriteString("\n## Core Identity\n")
	if gc.PrimaryGenre.Valid {
		builder.WriteString(fmt.Sprintf("Primary Genre: %s\n", gc.PrimaryGenre.String))
	}
	if gc.Subgenre.Valid {
		builder.WriteString(fmt.Sprintf("Subgenre: %s\n", gc.Subgenre.String))
	}
	if gc.KeyMechanics.Valid {
		builder.WriteString(fmt.Sprintf("Key Mechanics: %s\n", gc.KeyMechanics.String))
	}
	if gc.PlaytimeLength.Valid {
		builder.WriteString(fmt.Sprintf("Playtime: %s\n", gc.PlaytimeLength.String))
	}
	if gc.ArtStyle.Valid {
		builder.WriteString(fmt.Sprintf("Art Style: %s\n", gc.ArtStyle.String))
	}
	if gc.Tone.Valid {
		builder.WriteString(fmt.Sprintf("Tone: %s\n", gc.Tone.String))
	}

	// Section 3: Target Audience
	builder.WriteString("\n## Target Audience\n")
	if gc.IntendedAudience.Valid {
		builder.WriteString(fmt.Sprintf("Intended Audience: %s\n", gc.IntendedAudience.String))
	}
	if gc.AgeRange.Valid {
		builder.WriteString(fmt.Sprintf("Age Range: %s\n", gc.AgeRange.String))
	}
	if gc.PlayerMotivation.Valid {
		builder.WriteString(fmt.Sprintf("Player Motivation: %s\n", gc.PlayerMotivation.String))
	}
	if gc.ComparableGames.Valid {
		builder.WriteString(fmt.Sprintf("Comparable Games: %s\n", gc.ComparableGames.String))
	}

	// Section 4: Marketing Goals
	builder.WriteString("\n## Marketing Goals\n")
	if gc.MarketingObjective.Valid {
		builder.WriteString(fmt.Sprintf("Marketing Objective: %s\n", gc.MarketingObjective.String))
	}
	if gc.KeyEventsDates.Valid {
		builder.WriteString(fmt.Sprintf("Key Events/Dates: %s\n", gc.KeyEventsDates.String))
	}
	if gc.CallToAction.Valid {
		builder.WriteString(fmt.Sprintf("Call to Action: %s\n", gc.CallToAction.String))
	}

	// Section 5: Restrictions
	builder.WriteString("\n## Restrictions & Notes\n")
	if gc.ContentRestrictions.Valid {
		builder.WriteString(fmt.Sprintf("Content Restrictions: %s\n", gc.ContentRestrictions.String))
	}
	if gc.CompetitorsToAvoid.Valid {
		builder.WriteString(fmt.Sprintf("Competitors to Avoid: %s\n", gc.CompetitorsToAvoid.String))
	}
	if gc.AdditionalInfo.Valid {
		builder.WriteString(fmt.Sprintf("Additional Info: %s\n", gc.AdditionalInfo.String))
	}

	builder.WriteString("\n===================\n")
	return builder.String()
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
