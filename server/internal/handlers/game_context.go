// internal/handlers/game_context.go
package handlers

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/ledongthuc/pdf"
)

// ---------------- Models ----------------

type GameContextRequest struct {
	GroupID *int32 `json:"group_id,omitempty"`
	GameTitle   string   `json:"game_title"`
	StudioName  string   `json:"studio_name"`
	GameSummary string   `json:"game_summary"`
	Platforms   []string `json:"platforms"`
	EngineTech  string   `json:"engine_tech"`
	PrimaryGenre   string `json:"primary_genre"`
	Subgenre       string `json:"subgenre"`
	KeyMechanics   string `json:"key_mechanics"`
	PlaytimeLength string `json:"playtime_length"`
	ArtStyle       string `json:"art_style"`
	Tone           string `json:"tone"`
	IntendedAudience string `json:"intended_audience"`
	AgeRange         string `json:"age_range"`
	PlayerMotivation string `json:"player_motivation"`
	ComparableGames  string `json:"comparable_games"`
	MarketingObjective string `json:"marketing_objective"`
	KeyEventsDates     string `json:"key_events_dates"`
	CallToAction       string `json:"call_to_action"`
	ContentRestrictions string `json:"content_restrictions"`
	CompetitorsToAvoid  string `json:"competitors_to_avoid"`
	AdditionalInfo		string `json:"additional_info"`
}

func toNullString(s string) sql.NullString {
	if strings.TrimSpace(s) == "" {
		return sql.NullString{Valid: false}
	}
	return sql.NullString{String: s, Valid: true}
}

// ---------------- DeepSeek API types ----------------

type deepseekChatRequest struct {
	Model       string                   `json:"model"`
	Messages    []map[string]string      `json:"messages"`
	Stream      bool                     `json:"stream"`
	Temperature float64                  `json:"temperature,omitempty"`
	MaxTokens   int                      `json:"max_tokens,omitempty"`
}

type deepseekChatResponse struct {
	ID      string `json:"id"`
	Object  string `json:"object"`
	Created int64  `json:"created"`
	Model   string `json:"model"`
	Choices []struct {
		Index   int `json:"index"`
		Message struct {
			Role    string `json:"role"`
			Content string `json:"content"`
		} `json:"message"`
		FinishReason string `json:"finish_reason"`
	} `json:"choices"`
	Usage struct {
		PromptTokens     int `json:"prompt_tokens"`
		CompletionTokens int `json:"completion_tokens"`
		TotalTokens      int `json:"total_tokens"`
	} `json:"usage"`
}

// WarmupDeepSeek makes a simple test call to verify API connectivity
func WarmupDeepSeek(apiKey, model string) error {
	reqBody := deepseekChatRequest{
		Model:       model,
		Stream:      false,
		Temperature: 0.1,
		MaxTokens:   10,
		Messages: []map[string]string{
			{"role": "user", "content": "Hi"},
		},
	}
	b, _ := json.Marshal(reqBody)

	client := &http.Client{Timeout: 30 * time.Second}
	req, err := http.NewRequest("POST", "https://api.deepseek.com/chat/completions", bytes.NewBuffer(b))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+apiKey)

	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		rb, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("DeepSeek warmup failed (%d): %s", resp.StatusCode, string(rb))
	}
	return nil
}

func SaveGameContext(w http.ResponseWriter, r *http.Request, queries *db.Queries) {
	if r.Method != http.MethodPost {
		http.Error(w, "Invalid request method", http.StatusMethodNotAllowed)
		return
	}
	userID, ok := r.Context().Value("userID").(int32)
	if !ok {
		http.Error(w, "User ID not found in context", http.StatusUnauthorized)
		return
	}
	var req GameContextRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	var groupID sql.NullInt32
	if req.GroupID != nil && *req.GroupID > 0 {
		groupID = sql.NullInt32{Int32: *req.GroupID, Valid: true}
	}

	response, err := queries.CreateGameContext(r.Context(), db.CreateGameContextParams{
		UserID:              userID,
		GroupID:             groupID,
		GameTitle:           req.GameTitle,
		StudioName:          toNullString(req.StudioName),
		GameSummary:         toNullString(req.GameSummary),
		Platforms:           req.Platforms,
		EngineTech:          toNullString(req.EngineTech),
		PrimaryGenre:        toNullString(req.PrimaryGenre),
		Subgenre:            toNullString(req.Subgenre),
		KeyMechanics:        toNullString(req.KeyMechanics),
		PlaytimeLength:      toNullString(req.PlaytimeLength),
		ArtStyle:            toNullString(req.ArtStyle),
		Tone:                toNullString(req.Tone),
		IntendedAudience:    toNullString(req.IntendedAudience),
		AgeRange:            toNullString(req.AgeRange),
		PlayerMotivation:    toNullString(req.PlayerMotivation),
		ComparableGames:     toNullString(req.ComparableGames),
		MarketingObjective:  toNullString(req.MarketingObjective),
		KeyEventsDates:      toNullString(req.KeyEventsDates),
		CallToAction:        toNullString(req.CallToAction),
		ContentRestrictions: toNullString(req.ContentRestrictions),
		CompetitorsToAvoid:  toNullString(req.CompetitorsToAvoid),
		AdditionalInfo:	     toNullString(req.AdditionalInfo),
	})
	if err != nil {
		http.Error(w, fmt.Sprintf("Could not save to database: %v", err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	_ = json.NewEncoder(w).Encode(response)
}

func ExtractGameContext(w http.ResponseWriter, r *http.Request, queries *db.Queries) {
	if r.Method != http.MethodPost {
		http.Error(w, "Wrong method", http.StatusBadRequest)
		return
	}
	setCORSHeaders(w)

	
	apiKey := "sk-"
	if apiKey == "" {
		http.Error(w, "DEEPSEEK_API_KEY not configured", http.StatusInternalServerError)
		return
	}

	model := strings.TrimSpace(os.Getenv("DEEPSEEK_MODEL"))
	if model == "" {
		model = "deepseek-chat"
	}

	if err := r.ParseMultipartForm(10 << 20); err != nil {
		http.Error(w, fmt.Sprintf("Failed to parse form: %v", err), http.StatusBadRequest)
		return
	}

	var file *multipart.FileHeader
	if files := r.MultipartForm.File["file"]; len(files) > 0 {
		file = files[0]
	} else {
		http.Error(w, "Failed to get file", http.StatusBadRequest)
		return
	}

	ext := strings.ToLower(filepath.Ext(file.Filename))
	if ext != ".txt" && ext != ".pdf" {
		http.Error(w, "Only .txt and .pdf files are supported", http.StatusBadRequest)
		return
	}

	var fc string
	var err error
	if ext == ".pdf" {
		fc, err = readPDFContent(file)
	} else {
		fc, err = readFileContent(file)
	}
	if err != nil {
		http.Error(w, fmt.Sprintf("Error reading file: %v", err), http.StatusInternalServerError)
		return
	}
	gameContext, err := extractInChunks(fc, apiKey, model)
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to extract game context: %v", err), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(gameContext)
}

type ChunkResult struct {
	Section string
	Data    map[string]interface{}
	Error   error
}

type chunkConfig struct {
	fields []string
	prompt string
	context string
}
// callDeepSeek makes a single call to DeepSeek API with the given prompt
func callDeepSeek(apiKey, model, prompt string) (map[string]interface{}, error) {
	messages := []map[string]string{
		{"role": "user", "content": prompt},
	}

	reqBody := deepseekChatRequest{
		Model:       model,
		Stream:      false,
		Temperature: 0.1,
		MaxTokens:   500,
		Messages:    messages,
	}
	b, _ := json.Marshal(reqBody)

	client := &http.Client{Timeout: 180 * time.Second}
	req, err := http.NewRequest("POST", "https://api.deepseek.com/chat/completions", bytes.NewBuffer(b))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %v", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+apiKey)

	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("LLM POST ERROR %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		rb, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("DeepSeek API error (%d): %s", resp.StatusCode, string(rb))
	}

	rb, _ := io.ReadAll(resp.Body)
	var deepseekResp deepseekChatResponse
	if err := json.Unmarshal(rb, &deepseekResp); err != nil {
		return nil, fmt.Errorf("failed to parse DeepSeek response: %v", err)
	}

	if len(deepseekResp.Choices) == 0 {
		return nil, fmt.Errorf("no choices returned from DeepSeek")
	}

	aiContent := strings.TrimSpace(deepseekResp.Choices[0].Message.Content)
	aiContent = strings.TrimPrefix(aiContent, "```json")
	aiContent = strings.TrimPrefix(aiContent, "```")
	aiContent = strings.TrimSuffix(aiContent, "```")
	aiContent = strings.TrimSpace(aiContent)

	var data map[string]interface{}
	if err := json.Unmarshal([]byte(aiContent), &data); err != nil {
		return nil, fmt.Errorf("failed to parse AI response as JSON: %v", err)
	}

	return data, nil
}

// mergeChunkData merges data from a chunk result into the target GameContextRequest
func mergeChunkData(target *GameContextRequest, source map[string]interface{}) {
	if v, ok := source["game_title"].(string); ok && v != "" {
		target.GameTitle = v
	}
	if v, ok := source["studio_name"].(string); ok && v != "" {
		target.StudioName = v
	}
	if v, ok := source["game_summary"].(string); ok && v != "" {
		target.GameSummary = v
	}
	if v, ok := source["platforms"].([]interface{}); ok && len(v) > 0 {
		platforms := make([]string, 0, len(v))
		for _, p := range v {
			if ps, ok := p.(string); ok && ps != "" {
				platforms = append(platforms, ps)
			}
		}
		if len(platforms) > 0 {
			target.Platforms = platforms
		}
	}
	if v, ok := source["engine_tech"].(string); ok && v != "" {
		target.EngineTech = v
	}
	if v, ok := source["primary_genre"].(string); ok && v != "" {
		target.PrimaryGenre = v
	}
	if v, ok := source["subgenre"].(string); ok && v != "" {
		target.Subgenre = v
	}
	if v, ok := source["key_mechanics"].(string); ok && v != "" {
		target.KeyMechanics = v
	}
	if v, ok := source["playtime_length"].(string); ok && v != "" {
		target.PlaytimeLength = v
	}
	if v, ok := source["art_style"].(string); ok && v != "" {
		target.ArtStyle = v
	}
	if v, ok := source["tone"].(string); ok && v != "" {
		target.Tone = v
	}
	if v, ok := source["intended_audience"].(string); ok && v != "" {
		target.IntendedAudience = v
	}
	if v, ok := source["age_range"].(string); ok && v != "" {
		target.AgeRange = v
	}
	if v, ok := source["player_motivation"].(string); ok && v != "" {
		target.PlayerMotivation = v
	}
	if v, ok := source["comparable_games"].(string); ok && v != "" {
		target.ComparableGames = v
	}
	if v, ok := source["marketing_objective"].(string); ok && v != "" {
		target.MarketingObjective = v
	}
	if v, ok := source["key_events_dates"].(string); ok && v != "" {
		target.KeyEventsDates = v
	}
	if v, ok := source["call_to_action"].(string); ok && v != "" {
		target.CallToAction = v
	}
	if v, ok := source["content_restrictions"].(string); ok && v != "" {
		target.ContentRestrictions = v
	}
	if v, ok := source["competitors_to_avoid"].(string); ok && v != "" {
		target.CompetitorsToAvoid = v
	}
}

// extractInChunks processes the document in semantic chunks using parallel LLM calls
func extractInChunks(fc string, apiKey string, model string) (*GameContextRequest, error) {
	format := `
			1. Basic Game Information
		Game Title: Official name
		Studio / Developer Name: Your studio or indie name
		One-Sentence Summary: Core appeal in one sentence (e.g., "A cozy farming sim about restoring a village")
		Platform(s): PC ☐ Console ☐ Mobile ☐ VR ☐ Other ☐
		Engine / Tech Used: (Optional) Unity, Unreal, Godot, etc.
		2. Core Identity
		Primary Genre: Racing, RPG, puzzle, strategy, etc.
		Subgenre: Roguelike deckbuilder, narrative puzzle, sandbox builder, etc.
		Key Mechanics (3 to 5): What players actually do (customizable cars, procedural levels, multiplayer, etc.)
		Playtime: Short sessions / mid-length campaign / endless
		Art Style / Tone: Pixel art, stylized 3D, comedic, noir, cozy, etc.
		3. Target Audience
		Intended Audience: Casual gamers, speedrunners, story enthusiasts, strategy fans, etc.
		Age Range: Kids / Teens / Young Adults / Adults / All Ages
		Player Motivation: Fun, relaxation, mastery, creativity, competition, story, achievement
		Comparable Games: "Like Stardew Valley meets Dark Souls"
		4. Marketing Goals
		Main Objective: Awareness ☐ Wishlist growth ☐ Demo downloads ☐ Retention ☐ Event promotion ☐
		Key Events/Dates: Demo release, launch date, festival submissions, etc.
		Call-to-Action: Add to Wishlist / Play demo / Join Discord / etc.
		5. Restrictions / Boundaries
		Content Restrictions: No mention of real-money gambling, avoid dark humor, etc.
		Topics to Avoid: Real-world casinos, violence, specific competitors, etc.
	`
	chunks := map[string]chunkConfig{
		"basic": {
			fields: []string{"game_title", "studio_name", "game_summary", "platforms", "engine_tech"},
			prompt: `Extract basic game info as JSON (use "" if missing): {"game_title":"","studio_name":"","game_summary":"","platforms":[],"engine_tech":""}`,
			context: format, 
		},
		"identity": {
			fields: []string{"primary_genre", "subgenre", "key_mechanics", "playtime_length", "art_style", "tone"},
			prompt: `Extract game identity as JSON (use "" if missing): {"primary_genre":"","subgenre":"","key_mechanics":"","playtime_length":"","art_style":"","tone":""}`,
			context: format,
		},
		"audience": {
			fields: []string{"intended_audience", "age_range", "player_motivation", "comparable_games"},
			prompt: `Extract target audience as JSON (use "" if missing): {"intended_audience":"","age_range":"","player_motivation":"","comparable_games":""}`,
			context: format,
		},
		"marketing": {
			fields: []string{"marketing_objective", "key_events_dates", "call_to_action", "content_restrictions", "competitors_to_avoid"},
			prompt: `Extract marketing info as JSON (use "" if missing): {"marketing_objective":"","key_events_dates":"","call_to_action":"","content_restrictions":"","competitors_to_avoid":""}`,
			context: format,
		},
	}


	results := make(chan ChunkResult, len(chunks))

	for section, config := range chunks {
		go func(sec string, cfg chunkConfig) {

			chunkContent := fc
			const maxPerChunk = 4000
			if len(chunkContent) > maxPerChunk {
				chunkContent = chunkContent[:maxPerChunk] + "..."
			}

			fullPrompt := fmt.Sprintf("%s\n\nDocument: %s\n\nJSON only:", cfg.prompt, chunkContent)

			data, err := callDeepSeek(apiKey, model, fullPrompt)
			results <- ChunkResult{Section: sec, Data: data, Error: err}
		}(section, config)
	}
	gameContext := &GameContextRequest{}
	var errors []string

	for i := 0; i < len(chunks); i++ {
		result := <-results
		if result.Error != nil {
			errors = append(errors, fmt.Sprintf("chunk %s failed: %v", result.Section, result.Error))
			continue
		}
		mergeChunkData(gameContext, result.Data)
	}

	if len(errors) > 0 {
		return nil, fmt.Errorf("chunk processing errors: %s", strings.Join(errors, "; "))
	}

	return gameContext, nil
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


	reader := bytes.NewReader(data)
	pdfReader, err := pdf.NewReader(reader, int64(len(data)))
	if err != nil {
		return "", fmt.Errorf("failed to parse PDF: %v", err)
	}

	var textContent strings.Builder
	numPages := pdfReader.NumPage()
	for pageNum := 1; pageNum <= numPages; pageNum++ {
		page := pdfReader.Page(pageNum)
		if page.V.IsNull() {
			continue
		}
		text, err := page.GetPlainText(nil)
		if err != nil {
			continue
		}
		textContent.WriteString(text)
		textContent.WriteString("\n")
	}
	out := textContent.String()
	if strings.TrimSpace(out) == "" {
		return "", fmt.Errorf("no text content found in PDF")
	}
	return out, nil
}
