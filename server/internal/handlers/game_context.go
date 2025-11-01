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
	// Identifiers
	GroupID *int32 `json:"group_id,omitempty"`

	// Section 1: Basic Game Information
	GameTitle   string   `json:"game_title"`
	StudioName  string   `json:"studio_name"`
	GameSummary string   `json:"game_summary"`
	Platforms   []string `json:"platforms"`
	EngineTech  string   `json:"engine_tech"`

	// Section 2: Core Identity
	PrimaryGenre   string `json:"primary_genre"`
	Subgenre       string `json:"subgenre"`
	KeyMechanics   string `json:"key_mechanics"`
	PlaytimeLength string `json:"playtime_length"`
	ArtStyle       string `json:"art_style"`
	Tone           string `json:"tone"`

	// Section 3: Target Audience
	IntendedAudience string `json:"intended_audience"`
	AgeRange         string `json:"age_range"`
	PlayerMotivation string `json:"player_motivation"`
	ComparableGames  string `json:"comparable_games"`

	// Section 4: Marketing Goals
	MarketingObjective string `json:"marketing_objective"`
	KeyEventsDates     string `json:"key_events_dates"`
	CallToAction       string `json:"call_to_action"`

	// Section 5: Restrictions / Boundaries
	ContentRestrictions string `json:"content_restrictions"`
	CompetitorsToAvoid  string `json:"competitors_to_avoid"`
}

func toNullString(s string) sql.NullString {
	if strings.TrimSpace(s) == "" {
		return sql.NullString{Valid: false}
	}
	return sql.NullString{String: s, Valid: true}
}

// ---------------- Ollama types ----------------

type ollamaChatRequest struct {
	Model    string              `json:"model"`
	Stream   bool                `json:"stream"`
	Options  map[string]any      `json:"options,omitempty"`
	Messages []map[string]string `json:"messages"`
}

type ollamaChatResponse struct {
	Model   string `json:"model"`
	Message struct {
		Role    string `json:"role"`
		Content string `json:"content"`
	} `json:"message"`
	Done bool `json:"done"`
}

// WarmupOllama pre-loads the model to avoid first-request timeout
func WarmupOllama(chatURL, model string) error {
	reqBody := ollamaChatRequest{
		Model:   model,
		Stream:  false,
		Options: map[string]any{"num_predict": 1},
		Messages: []map[string]string{
			{"role": "user", "content": "Hi"},
		},
	}
	b, _ := json.Marshal(reqBody)

	client := &http.Client{Timeout: 120 * time.Second}
	resp, err := client.Post(chatURL, "application/json", bytes.NewBuffer(b))
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	return nil
}

// ---------------- Handlers ----------------

func SaveGameContext(w http.ResponseWriter, r *http.Request, queries *db.Queries) {
	if r.Method != http.MethodPost {
		http.Error(w, "Invalid request method", http.StatusMethodNotAllowed)
		return
	}

	// Extract user_id from context (set by JWT middleware)
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

	// Convert group_id to sql.NullInt32
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
	// Reuse shared helper defined elsewhere in your package
	setCORSHeaders(w)

	// Base host (no /v1, no /api suffix here)
	ollamaHost := strings.TrimSpace(os.Getenv("OLLAMA_HOST"))
	if ollamaHost == "" {
		// Works inside Docker network (backend -> ollama)
		ollamaHost = "http://ollama:11434"
	}
	ollamaHost = strings.TrimRight(ollamaHost, "/")
	for _, bad := range []string{"/v1", "/v1/", "/api", "/api/"} {
		ollamaHost = strings.TrimSuffix(ollamaHost, bad)
	}
	chatURL := ollamaHost + "/api/chat"

	model := strings.TrimSpace(os.Getenv("OLLAMA_MODEL"))
	if model == "" {
		model = "qwen2.5:3b-instruct"
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

	// OPTIMIZED: Reduced from 8000 to 4000 for faster inference
	const maxDoc = 4000
	if len(fc) > maxDoc {
		fc = fc[:maxDoc] + "..."
	}

	// OPTIMIZED: Shorter, more efficient prompt
	prompt := fmt.Sprintf(`Extract game marketing info as JSON (use "" if missing):
{"game_title":"","studio_name":"","game_summary":"","platforms":[],"engine_tech":"","primary_genre":"","subgenre":"","key_mechanics":"","playtime_length":"","art_style":"","tone":"","intended_audience":"","age_range":"","player_motivation":"","comparable_games":"","marketing_objective":"","key_events_dates":"","call_to_action":"","content_restrictions":"","competitors_to_avoid":""}

Document: %s

JSON only:`, fc)

	// OPTIMIZED: Removed redundant system message
	messages := []map[string]string{
		{"role": "user", "content": prompt},
	}

	reqBody := ollamaChatRequest{
		Model:   model,
		Stream:  false,
		Options: map[string]any{
			"num_ctx":        3072, // OPTIMIZED: Reduced from 2048
			"num_predict":    200,  // OPTIMIZED: Reduced from 384
			"temperature":    0.1,  // OPTIMIZED: Lowered from 0.3
			"top_p":          0.9,
			"repeat_penalty": 1.1,
		},
		Messages: messages,
	}
	b, _ := json.Marshal(reqBody)

	client := &http.Client{Timeout: 180 * time.Second}
	resp, err := client.Post(chatURL, "application/json", bytes.NewBuffer(b))
	if err != nil {
		http.Error(w, fmt.Sprintf("Error calling Ollama: %v", err), http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		rb, _ := io.ReadAll(resp.Body)
		http.Error(w, fmt.Sprintf("Ollama API error (%d): %s", resp.StatusCode, string(rb)), http.StatusInternalServerError)
		return
	}

	rb, _ := io.ReadAll(resp.Body)
	var oc ollamaChatResponse
	if err := json.Unmarshal(rb, &oc); err != nil {
		http.Error(w, fmt.Sprintf("Failed to parse Ollama response: %v\nRaw: %s", err, string(rb)), http.StatusInternalServerError)
		return
	}

	aiContent := strings.TrimSpace(oc.Message.Content)
	aiContent = strings.TrimPrefix(aiContent, "```json")
	aiContent = strings.TrimPrefix(aiContent, "```")
	aiContent = strings.TrimSuffix(aiContent, "```")
	aiContent = strings.TrimSpace(aiContent)

	var gameContext GameContextRequest
	if err := json.Unmarshal([]byte(aiContent), &gameContext); err != nil {
		http.Error(w, fmt.Sprintf("Failed to parse AI response as JSON: %v\nCleaned Content:\n%s", err, aiContent), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(gameContext)
}

// ---------------- Helpers (file readers) ----------------

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

	// Parse PDF from memory
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
			// best effort: skip page on error
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
