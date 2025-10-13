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
	// Section 1: Basic Game Information
	GameTitle    string   `json:"game_title"`
	StudioName   string   `json:"studio_name"`
	GameSummary  string   `json:"game_summary"`
	Platforms    []string `json:"platforms"`
	EngineTech   string   `json:"engine_tech"`

	// Section 2: Core Identity
	PrimaryGenre    string `json:"primary_genre"`
	Subgenre        string `json:"subgenre"`
	KeyMechanics    string `json:"key_mechanics"`
	PlaytimeLength  string `json:"playtime_length"`
	ArtStyle        string `json:"art_style"`
	Tone            string `json:"tone"`

	// Section 3: Target Audience
	IntendedAudience  string `json:"intended_audience"`
	AgeRange          string `json:"age_range"`
	PlayerMotivation  string `json:"player_motivation"`
	ComparableGames   string `json:"comparable_games"`

	// Section 4: Marketing Goals
	MarketingObjective string `json:"marketing_objective"`
	KeyEventsDates     string `json:"key_events_dates"`
	CallToAction       string `json:"call_to_action"`

	// Section 5: Restrictions / Boundaries
	ContentRestrictions  string `json:"content_restrictions"`
	CompetitorsToAvoid   string `json:"competitors_to_avoid"`
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
	prompt := fmt.Sprintf(`Extract comprehensive marketing and game information from the following document.

Return a JSON object with these exact fields organized by section:

SECTION 1 - Basic Game Information:
- game_title: string (the official game title)
- studio_name: string (developer/studio name)
- game_summary: string (one-sentence summary)
- platforms: array of strings (e.g., ["PC", "Console", "Mobile"])
- engine_tech: string (game engine or tech stack)

SECTION 2 - Core Identity:
- primary_genre: string (main genre)
- subgenre: string (gameplay style or subgenre)
- key_mechanics: string (3-5 key features or mechanics, bullet-pointed)
- playtime_length: string (e.g., "short session", "mid-length campaign", "endless")
- art_style: string (visual style)
- tone: string (overall tone/mood)

SECTION 3 - Target Audience:
- intended_audience: string (who the game is for)
- age_range: string (target age range)
- player_motivation: string (what players get from the game)
- comparable_games: string (similar/comparable games)

SECTION 4 - Marketing Goals:
- marketing_objective: string (main marketing goal)
- key_events_dates: string (important dates or events)
- call_to_action: string (preferred CTA)

SECTION 5 - Restrictions/Boundaries:
- content_restrictions: string (content to avoid)
- competitors_to_avoid: string (competitors or topics to not mention)

Example output:
{
  "game_title": "Mystic Legends",
  "studio_name": "Epic Quest Studios",
  "game_summary": "An epic fantasy RPG where player choices shape a magical world.",
  "platforms": ["PC", "Console"],
  "engine_tech": "Unreal Engine 5",
  "primary_genre": "RPG",
  "subgenre": "Action RPG with narrative focus",
  "key_mechanics": "• Dynamic magic system\n• Branching narrative\n• Strategic combat\n• Player choice consequences",
  "playtime_length": "50+ hour campaign",
  "art_style": "Stylized realistic 3D",
  "tone": "Epic and immersive with serious themes",
  "intended_audience": "Core gamers who enjoy deep RPGs and fantasy settings",
  "age_range": "18-35",
  "player_motivation": "Mastery, exploration, narrative engagement",
  "comparable_games": "The Witcher 3, Dragon Age, Baldur's Gate 3",
  "marketing_objective": "Wishlist growth",
  "key_events_dates": "Demo release Q2 2024, Early Access Q4 2024",
  "call_to_action": "Add to Wishlist on Steam",
  "content_restrictions": "Avoid graphic violence depictions in marketing",
  "competitors_to_avoid": ""
}

Rules:
- If information is not in the document, use reasonable inferences
- If truly unknown, use empty string ""
- Keep all responses marketing-focused and actionable
- Ensure valid JSON format

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