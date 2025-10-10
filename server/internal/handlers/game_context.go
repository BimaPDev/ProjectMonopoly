package handlers

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"github.com/ledongthuc/pdf"
	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
)
type GameContextResponse struct {
	GameName             string `json:"game_name"`
	Description          string `json:"description"`
	TargetAudience       string `json:"target_audience"`
	KeyFeatures          string `json:"key_features"`
	Tone                 string `json:"tone"`
	UniqueSellingPoints  string `json:"unique_selling_points"`
}

type OllamaRequest struct {
	Model    string                   `json:"model"`
	Messages []map[string]interface{} `json:"messages"`
}

type OllamaResponse struct {
	Choices []struct {
		Message struct {
			Content string `json:"content"`
		} `json:"message"`
	} `json:"choices"`
}
func ExtractGameContext(w http.ResponseWriter, r *http.Request, queries *db.Queries){
	if r.Method != http.MethodPost{
		http.Error(w, fmt.Sprintf("Wrong method"), http.StatusBadRequest)
		return
	}
	
	setCORSHeaders(w)
	ollamaURL := os.Getenv("OLLAMA_URL")
	if ollamaURL == "" {
		ollamaURL = "http://localhost:11434/v1/chat/completions"
	}
	model := os.Getenv("OLLAMA_MODEL")
	if model == "" {
		model = "gemma3"
	}
	if err := r.ParseMultipartForm(10 << 20);
	err != nil{
		http.Error(w, fmt.Sprintf("Failed to parse form: %v", err), http.StatusBadRequest)
		return
	}
	var file *multipart.FileHeader
	if files :=r.MultipartForm.File["file"]; len(files) > 0{
		file = files[0]
	}else{
		http.Error(w, fmt.Sprintf("Failed to get file"), http.StatusBadRequest)
		return
	}
	ext := strings.ToLower(filepath.Ext(file.Filename))
	if ext != ".txt" && ext != ".pdf" {
		http.Error(w, "Only .txt and .pdf files are supported", http.StatusInternalServerError)
		return
	}
	var fc string
	var err error

	if ext == ".pdf" {
		fc, err = readPDFContent(file)
	} else {
		fc, err = readFileContent(file)
	}

	if err != nil{
		http.Error(w, fmt.Sprintf("Error reading file: %v", err), http.StatusInternalServerError)
		return
	}

	// Log first 500 chars of file content for debugging
	if len(fc) > 500 {
		fmt.Printf("File content preview (first 500 chars): %s\n", fc[:500])
	} else {
		fmt.Printf("File content: %s\n", fc)
	}
	prompt := fmt.Sprintf(`Extract marketing information about a game from the following document.

		Return a JSON object with these exact fields:
		- game_name: string
		- description: string (2-3 paragraphs)
		- target_audience: string
		- key_features: string
		- tone: string
		- unique_selling_points: string

		Example output:
		{
		"game_name": "Mystic Legends",
		"description": "Mystic Legends is an epic fantasy RPG that combines strategic combat with deep narrative choices. Players embark on a journey through a richly detailed world where every decision shapes the story. The game features a unique magic system that evolves based on player choices.",
		"target_audience": "Core gamers aged 18-35 who enjoy deep RPGs, fantasy settings, and narrative-driven experiences. Appeals to fans of games like The Witcher, Dragon Age, and Baldur's Gate.",
		"key_features": "• Dynamic magic system that evolves with player choices\n• Branching narrative with 50+ hours of content\n• Strategic real-time combat\n• Fully voiced companions with unique storylines\n• Player choices impact world state",
		"tone": "Epic and immersive, with a focus on adventure and discovery. Serious but accessible, emphasizing the weight of player decisions.",
		"unique_selling_points": "The only RPG where your magic abilities fundamentally change based on moral choices. Every playthrough offers a completely different magical experience."
		}

		Document text:
		%s

		Return ONLY the JSON object, no additional text.`, fc)
	message := []map[string]interface{}{
		{
			"role": "system",
			"content": "You are a marketing analyst specializing in video game marketing. You extract structured, marketing-relevant information from game documentation.",
		},
		{
			"role": "user",
			"content": prompt,
		},

	}
	ollamaReq := OllamaRequest{
		Model: model,
		Messages: message,
	}

	OLRequest, err := json.Marshal(ollamaReq)
	if err != nil{
		http.Error(w, fmt.Sprintf("Failed to marshal request %v", err), http.StatusInternalServerError)
		return
	}

	ollamaRes, err := http.Post(ollamaURL, "application/json", bytes.NewBuffer(OLRequest))
	if err != nil{
		http.Error(w, fmt.Sprintf("Error calling ollama api %v", err), http.StatusInternalServerError)
		return
	}
	defer ollamaRes.Body.Close()
	if ollamaRes.StatusCode != http.StatusOK{
		body, _ := io.ReadAll(ollamaRes.Body)
		http.Error(w, fmt.Sprintf("Ollama API error %v", string(body)), http.StatusInternalServerError)
		return
	}

	body, _ := io.ReadAll(ollamaRes.Body)
	
	var ollamaResp OllamaResponse
	err = json.Unmarshal(body, &ollamaResp)
	if err != nil{
		http.Error(w, fmt.Sprintf("Error unmarshalling ollama response %v", err), http.StatusInternalServerError)
		return
	}

	// Check if we got a valid response
	if len(ollamaResp.Choices) == 0 {
		http.Error(w, "No response from AI model", http.StatusInternalServerError)
		return
	}

	// Extract the JSON content from AI response
	aiContent := ollamaResp.Choices[0].Message.Content
	
	// Parse the AI's JSON response
	var gameContext GameContextResponse
	if err := json.Unmarshal([]byte(aiContent), &gameContext); err != nil {
		// Try to extract JSON from markdown code blocks if present
		aiContent = strings.TrimPrefix(aiContent, "```json\n")
		aiContent = strings.TrimSuffix(aiContent, "\n```")
		aiContent = strings.TrimSpace(aiContent)
		
		if err := json.Unmarshal([]byte(aiContent), &gameContext); err != nil {
			http.Error(w, fmt.Sprintf("Failed to parse AI response as JSON: %v\nContent: %s", err, aiContent), http.StatusInternalServerError)
			return
		}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(gameContext)

}
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

func readPDFContent(uploadedFile *multipart.FileHeader) (string, error) {
	f, err := uploadedFile.Open()
	if err != nil {
		return "", fmt.Errorf("failed to open PDF file: %v", err)
	}
	defer f.Close()

	data, err := io.ReadAll(f)
	if err != nil {
		return "", fmt.Errorf("failed to read PDF file: %v", err)
	}

	// Create a bytes reader from the data
	reader := bytes.NewReader(data)

	// Parse the PDF
	pdfReader, err := pdf.NewReader(reader, int64(len(data)))
	if err != nil {
		return "", fmt.Errorf("failed to parse PDF: %v", err)
	}

	// Extract text from all pages
	var textContent strings.Builder
	numPages := pdfReader.NumPage()

	for pageNum := 1; pageNum <= numPages; pageNum++ {
		page := pdfReader.Page(pageNum)
		if page.V.IsNull() {
			continue
		}

		text, err := page.GetPlainText(nil)
		if err != nil {
			fmt.Printf("Warning: failed to extract text from page %d: %v\n", pageNum, err)
			continue
		}

		textContent.WriteString(text)
		textContent.WriteString("\n")
	}

	result := textContent.String()
	if result == "" {
		return "", fmt.Errorf("no text content found in PDF")
	}

	return result, nil
}