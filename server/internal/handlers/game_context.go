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
	"strconv"
	"strings"
	"time"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/BimaPDev/ProjectMonopoly/internal/utils"
	"github.com/gin-gonic/gin"
	"github.com/ledongthuc/pdf"
)

// ---------------- Models ----------------

type GameContextRequest struct {
	GroupID             *int32   `json:"group_id,omitempty"`
	GameTitle           string   `json:"game_title"`
	StudioName          string   `json:"studio_name"`
	GameSummary         string   `json:"game_summary"`
	Platforms           []string `json:"platforms"`
	EngineTech          string   `json:"engine_tech"`
	PrimaryGenre        string   `json:"primary_genre"`
	Subgenre            string   `json:"subgenre"`
	KeyMechanics        string   `json:"key_mechanics"`
	PlaytimeLength      string   `json:"playtime_length"`
	ArtStyle            string   `json:"art_style"`
	Tone                string   `json:"tone"`
	IntendedAudience    string   `json:"intended_audience"`
	AgeRange            string   `json:"age_range"`
	PlayerMotivation    string   `json:"player_motivation"`
	ComparableGames     string   `json:"comparable_games"`
	MarketingObjective  string   `json:"marketing_objective"`
	KeyEventsDates      string   `json:"key_events_dates"`
	CallToAction        string   `json:"call_to_action"`
	ContentRestrictions string   `json:"content_restrictions"`
	CompetitorsToAvoid  string   `json:"competitors_to_avoid"`
	AdditionalInfo      string   `json:"additional_info"`
}

func toNullString(s string) sql.NullString {
	if strings.TrimSpace(s) == "" {
		return sql.NullString{Valid: false}
	}
	return sql.NullString{String: s, Valid: true}
}

// truncateString truncates a string to maxLen characters to prevent VARCHAR overflow
func truncateString(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen]
}

// toNullStringTruncated converts string to NullString with truncation to prevent VARCHAR overflow
func toNullStringTruncated(s string, maxLen int) sql.NullString {
	if strings.TrimSpace(s) == "" {
		return sql.NullString{Valid: false}
	}
	return sql.NullString{String: truncateString(s, maxLen), Valid: true}
}

// ---------------- DeepSeek API types ----------------

type deepseekChatRequest struct {
	Model       string              `json:"model"`
	Messages    []map[string]string `json:"messages"`
	Stream      bool                `json:"stream"`
	Temperature float64             `json:"temperature,omitempty"`
	MaxTokens   int                 `json:"max_tokens,omitempty"`
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

func SaveGameContext(c *gin.Context, queries *db.Queries) {
	// Method check handled by Gin router

	userID, err := utils.GetUserID(c)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "User ID not found in context"})
		return
	}
	var req GameContextRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	var groupID sql.NullInt32
	if req.GroupID != nil && *req.GroupID > 0 {
		groupID = sql.NullInt32{Int32: *req.GroupID, Valid: true}
	}

	response, err := queries.CreateGameContext(c.Request.Context(), db.CreateGameContextParams{
		UserID:              int32(userID),
		GroupID:             groupID,
		GameTitle:           truncateString(req.GameTitle, 255),                 // VARCHAR(255)
		StudioName:          toNullStringTruncated(req.StudioName, 255),         // VARCHAR(255)
		GameSummary:         toNullString(req.GameSummary),                      // TEXT - no limit
		Platforms:           req.Platforms,                                      // TEXT[]
		EngineTech:          toNullStringTruncated(req.EngineTech, 255),         // VARCHAR(255)
		PrimaryGenre:        toNullStringTruncated(req.PrimaryGenre, 100),       // VARCHAR(100)
		Subgenre:            toNullStringTruncated(req.Subgenre, 100),           // VARCHAR(100)
		KeyMechanics:        toNullString(req.KeyMechanics),                     // TEXT
		PlaytimeLength:      toNullStringTruncated(req.PlaytimeLength, 100),     // VARCHAR(100)
		ArtStyle:            toNullStringTruncated(req.ArtStyle, 100),           // VARCHAR(100)
		Tone:                toNullStringTruncated(req.Tone, 100),               // VARCHAR(100)
		IntendedAudience:    toNullString(req.IntendedAudience),                 // TEXT
		AgeRange:            toNullStringTruncated(req.AgeRange, 100),           // VARCHAR(100)
		PlayerMotivation:    toNullString(req.PlayerMotivation),                 // TEXT
		ComparableGames:     toNullString(req.ComparableGames),                  // TEXT
		MarketingObjective:  toNullStringTruncated(req.MarketingObjective, 255), // VARCHAR(255)
		KeyEventsDates:      toNullString(req.KeyEventsDates),                   // TEXT
		CallToAction:        toNullStringTruncated(req.CallToAction, 255),       // VARCHAR(255)
		ContentRestrictions: toNullString(req.ContentRestrictions),              // TEXT
		CompetitorsToAvoid:  toNullString(req.CompetitorsToAvoid),               // TEXT
		AdditionalInfo:      toNullString(req.AdditionalInfo),                   // TEXT
	})
	if err != nil {
		fmt.Printf("CreateGameContext ERROR: %v\n", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Could not save to database: %v", err)})
		return
	}

	c.JSON(http.StatusCreated, response)
}

func ExtractGameContext(c *gin.Context, queries *db.Queries) {
	// Method check handled by Gin
	// setCORSHeaders removed (handled by middleware)

	apiKey := os.Getenv("DEEPSEEK_API_KEY")
	if apiKey == "" {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "DEEPSEEK_API_KEY not configured"})
		return
	}

	model := strings.TrimSpace(os.Getenv("DEEPSEEK_MODEL"))
	if model == "" {
		model = "deepseek-chat"
	}

	// Use c.FormFile which handles multipart parsing
	file, err := c.FormFile("file")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Failed to get file"})
		return
	}

	ext := strings.ToLower(filepath.Ext(file.Filename))
	if ext != ".txt" && ext != ".pdf" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Only .txt and .pdf files are supported"})
		return
	}

	var fc string
	if ext == ".pdf" {
		fc, err = readPDFContent(file)
	} else {
		fc, err = readFileContent(file)
	}
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Error reading file: %v", err)})
		return
	}
	gameContext, err := extractInChunks(fc, apiKey, model)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to extract game context: %v", err)})
		return
	}

	c.JSON(http.StatusOK, gameContext)
}
func NewNullInt32(value int32) sql.NullInt32 {
    return sql.NullInt32{Int32: value, Valid: true}
}

// checks to make sure the group that is passed in is owned by the userID in the token
func CheckGroupOwnership(c *gin.Context, queries *db.Queries, groupID any) bool{
	if(groupID == ""){
		c.JSON(http.StatusNotFound, gin.H{"error": "Group id is required"});
		return false;
	}
	var gid int;
	switch id := groupID.(type) {
	case int:
		gid = id
	case int32:
		gid = int(id)
	case int64:
		gid = int(id)
	case float64:
		gid = int(id)
	case string:
		uid, err := strconv.Atoi(id)
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid groupID"})
			return false;
		}
		gid = uid
	default:
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid groupID type"})
		return false;
	}


	v, exists := c.Get("userID");
	if(!exists){
			c.JSON(http.StatusUnauthorized, gin.H{"error": "groupID missing"})
			return false;
		}
	// need to get the type for userID since it is initlally any
	var userID int
	switch id := v.(type) {
	case int:
		userID = id
	case int32:
		userID = int(id)
	case int64:
		userID = int(id)
	case float64:
		userID = int(id)
	case string:
		uid, err := strconv.Atoi(id)
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid userID"})
			return false;
		}
		userID = uid
	default:
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid userID type"})
		return false;
	}
	
	// check ownership of the group
	
	group,err := queries.GetGroupByID(c, int32(gid));
	if(err != nil){
		c.JSON(http.StatusNotFound, gin.H{"error": "Group not found"})
		return false;
	}
	if(group.UserID != int32(userID)){
		c.JSON(http.StatusForbidden, gin.H{"error": "Access denied"})
		return false;
	}
	return true;
		
}
type UpdateGameContextRequest struct {
	GroupID             *int32   `json:"group_id,omitempty"`
	GameTitle           string   `json:"game_title"`
	StudioName          string   `json:"studio_name"`
	GameSummary         string   `json:"game_summary"`
	Platforms           []string `json:"platforms"`
	EngineTech          string   `json:"engine_tech"`
	PrimaryGenre        string   `json:"primary_genre"`
	Subgenre            string   `json:"subgenre"`
	KeyMechanics        string   `json:"key_mechanics"`
	PlaytimeLength      string   `json:"playtime_length"`
	ArtStyle            string   `json:"art_style"`
	Tone                string   `json:"tone"`
	IntendedAudience    string   `json:"intended_audience"`
	AgeRange            string   `json:"age_range"`
	PlayerMotivation    string   `json:"player_motivation"`
	ComparableGames     string   `json:"comparable_games"`
	MarketingObjective  string   `json:"marketing_objective"`
	KeyEventsDates      string   `json:"key_events_dates"`
	CallToAction        string   `json:"call_to_action"`
	ContentRestrictions string   `json:"content_restrictions"`
	CompetitorsToAvoid  string   `json:"competitors_to_avoid"`
	AdditionalInfo      string   `json:"additional_info"`
}
func UpdateGameContext(c *gin.Context, queries *db.Queries){
	gcID := c.Param("gameContextID")
	if(gcID == ""){
		c.JSON(http.StatusBadRequest, gin.H{"error": "Game Context ID missing"});
		return;
	}
	gcInt, err :=strconv.Atoi(gcID);
	if(err != nil){
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Invalid game context id"})
		return;
	}
	gc, err := queries.GetGameContextByID(c,int32(gcInt));
	if(err != nil){
		c.JSON(http.StatusNotFound, gin.H{"error": "Game Context not found for given ID"});
		return;
	}
	var req UpdateGameContextRequest
	err = c.ShouldBindJSON(&req);
	if (err != nil){
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()});
		return
	}
	if(CheckGroupOwnership(c, queries, gc.GroupID.Int32)){
		err = queries.UpdateGameContextByID(c, db.UpdateGameContextByIDParams{
			ID: int32(gcInt),
			GameTitle:           truncateString(req.GameTitle, 255),                 // VARCHAR(255)
			StudioName:          toNullStringTruncated(req.StudioName, 255),         // VARCHAR(255)
			GameSummary:         toNullString(req.GameSummary),                      // TEXT - no limit
			Platforms:           req.Platforms,                                      // TEXT[]
			EngineTech:          toNullStringTruncated(req.EngineTech, 255),         // VARCHAR(255)
			PrimaryGenre:        toNullStringTruncated(req.PrimaryGenre, 100),       // VARCHAR(100)
			Subgenre:            toNullStringTruncated(req.Subgenre, 100),           // VARCHAR(100)
			KeyMechanics:        toNullString(req.KeyMechanics),                     // TEXT
			PlaytimeLength:      toNullStringTruncated(req.PlaytimeLength, 100),     // VARCHAR(100)
			ArtStyle:            toNullStringTruncated(req.ArtStyle, 100),           // VARCHAR(100)
			Tone:                toNullStringTruncated(req.Tone, 100),               // VARCHAR(100)
			IntendedAudience:    toNullString(req.IntendedAudience),                 // TEXT
			AgeRange:            toNullStringTruncated(req.AgeRange, 100),           // VARCHAR(100)
			PlayerMotivation:    toNullString(req.PlayerMotivation),                 // TEXT
			ComparableGames:     toNullString(req.ComparableGames),                  // TEXT
			MarketingObjective:  toNullStringTruncated(req.MarketingObjective, 255), // VARCHAR(255)
			KeyEventsDates:      toNullString(req.KeyEventsDates),                   // TEXT
			CallToAction:        toNullStringTruncated(req.CallToAction, 255),       // VARCHAR(255)
			ContentRestrictions: toNullString(req.ContentRestrictions),              // TEXT
			CompetitorsToAvoid:  toNullString(req.CompetitorsToAvoid),               // TEXT
			AdditionalInfo:      toNullString(req.AdditionalInfo),                   // TEXT

		})
		
		if(err != nil){
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()});
			return;
		}

		c.JSON(http.StatusOK, gin.H{"success": "Deleted successfully"});
		return;
	}else{
		return;
	}
}
func DeleteGameContext(c *gin.Context, queries *db.Queries){
	gcID := c.Param("gameContextID");
	if(gcID == ""){
		c.JSON(http.StatusBadRequest, gin.H{"error": "Game Context ID missing"});
		return;
	}
	gcInt, err :=strconv.Atoi(gcID);
	if(err != nil){
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Invalid game context id"})
		return;
	}
	gc, err := queries.GetGameContextByID(c,int32(gcInt));
	if(err != nil){
		c.JSON(http.StatusNotFound, gin.H{"error": "Game Context not found for given ID"});
		return;
	}
	if(CheckGroupOwnership(c, queries, gc.GroupID.Int32)){
		err = queries.DeleteGameContextByID(c, int32(gcInt));
		if(err != nil){
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()});
			return;
		}

		c.JSON(http.StatusOK, gin.H{"success": "Deleted successfully"});
		return;
	}else{
		return;
	}
	
	
}
func GetGameContext(c *gin.Context, queries *db.Queries){
	gidStr := c.Param("groupID");
	if(gidStr == ""){
		c.JSON(http.StatusNotFound, gin.H{"error": "Group id is required"});
		return;
	}
	if(CheckGroupOwnership(c, queries, gidStr)){
		gidInt, err :=strconv.Atoi(gidStr);
		var dbContexts []db.GameContext;
		dbContexts, err = queries.GetAllGameContextByGroupID(c, NewNullInt32(int32(gidInt)))
		if(err != nil){
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusOK, dbContexts)
	}else{
		return;
	}
	
	
}
type ChunkResult struct {
	Section string
	Data    map[string]interface{}
	Error   error
}

type chunkConfig struct {
	fields  []string
	prompt  string
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
			fields:  []string{"game_title", "studio_name", "game_summary", "platforms", "engine_tech"},
			prompt:  `Extract basic game info as JSON (use "" if missing): {"game_title":"","studio_name":"","game_summary":"","platforms":[],"engine_tech":""}`,
			context: format,
		},
		"identity": {
			fields:  []string{"primary_genre", "subgenre", "key_mechanics", "playtime_length", "art_style", "tone"},
			prompt:  `Extract game identity as JSON (use "" if missing): {"primary_genre":"","subgenre":"","key_mechanics":"","playtime_length":"","art_style":"","tone":""}`,
			context: format,
		},
		"audience": {
			fields:  []string{"intended_audience", "age_range", "player_motivation", "comparable_games"},
			prompt:  `Extract target audience as JSON (use "" if missing): {"intended_audience":"","age_range":"","player_motivation":"","comparable_games":""}`,
			context: format,
		},
		"marketing": {
			fields:  []string{"marketing_objective", "key_events_dates", "call_to_action", "content_restrictions", "competitors_to_avoid"},
			prompt:  `Extract marketing info as JSON (use "" if missing): {"marketing_objective":"","key_events_dates":"","call_to_action":"","content_restrictions":"","competitors_to_avoid":""}`,
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
