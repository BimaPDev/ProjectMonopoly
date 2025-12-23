// internal/handlers/ai_generator.go
package handlers

import (
	"context"
	"database/sql"
	"fmt"
	"net/http"
	"strings"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/BimaPDev/ProjectMonopoly/internal/utils"
	"github.com/gin-gonic/gin"
)

// MarketingStrategyRequest defines the input for marketing generation
type MarketingStrategyRequest struct {
	GroupID      int32  `json:"group_id" binding:"required"`
	TaskType     string `json:"task_type" binding:"required"` // "Strategy" or "Script Writing"
	CampaignType string `json:"campaign_type"`                // "Teaser", "Launch", "Update", "Community"
	Platform     string `json:"platform"`                     // "Instagram", "TikTok", "Twitter"
	CustomPrompt string `json:"custom_prompt"`                // Optional additional instructions
}

// MarketingStrategyResponse is the API response
type MarketingStrategyResponse struct {
	Content        string   `json:"content"`
	BestPostingDay string   `json:"best_posting_day"` // Day name (e.g., "Wednesday")
	PostsPerWeek   float64  `json:"posts_per_week"`   // Competitor cadence
	TopHook        string   `json:"top_hook,omitempty"`
	TopHashtags    []string `json:"top_hashtags,omitempty"` // New field
	TokensUsed     int      `json:"tokens_used_estimate"`
	DataSource     string   `json:"data_source"` // "28_day_window" or "fallback"
}

// CompetitorInsights holds the processed analytics data
type CompetitorInsights struct {
	BestDay       int     // 1=Monday, 7=Sunday (ISO day of week)
	BestDayName   string  // "Monday", "Tuesday", etc.
	PostsPerWeek  float64 // Competitor posting cadence
	TopHook       string
	TopHashtags   []string // New field
	AvgLikes      float64
	SampleSize    int64
	HasData       bool
	TimeHeuristic string // Platform-specific time advice
}

// GenerateMarketingStrategyHandler creates the Gin handler for marketing generation
func GenerateMarketingStrategyHandler(q *db.Queries) gin.HandlerFunc {
	return func(c *gin.Context) {
		userID, err := utils.GetUserID(c)
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
			return
		}

		var req MarketingStrategyRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": fmt.Sprintf("invalid request: %v", err)})
			return
		}

		// Validate task type
		taskType := strings.ToLower(strings.TrimSpace(req.TaskType))
		if taskType != "strategy" && taskType != "script writing" {
			c.JSON(http.StatusBadRequest, gin.H{
				"error": "task_type must be 'Strategy' or 'Script Writing'",
			})
			return
		}

		// Default values
		if req.CampaignType == "" {
			req.CampaignType = "Teaser"
		}
		if req.Platform == "" {
			req.Platform = "Instagram"
		}

		ctx := c.Request.Context()

		// Fetch game context (required for all task types)
		gameCtx, err := q.GetGameContext(ctx, db.GetGameContextParams{
			UserID:  int32(userID),
			GroupID: sql.NullInt32{Int32: req.GroupID, Valid: true},
		})
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{
				"error": "No game context found. Please set up your game information first.",
			})
			return
		}

		// Fetch time-boxed competitor insights with platform for time heuristic
		insights := fetchCompetitorInsights(ctx, q, int32(userID), req.GroupID, req.Platform)

		// Build context based on task type (SMART CONTEXT DE-DUPLICATION)
		var systemPrompt, userPrompt string
		var tokenEstimate int

		switch taskType {
		case "strategy":
			// HIGH-LEVEL: Only inject GameSummary (~200 tokens)
			systemPrompt, userPrompt, tokenEstimate = buildStrategyContext(gameCtx, insights, req)
		case "script writing":
			// LOW-LEVEL: Inject specific document chunks + full game context
			systemPrompt, userPrompt, tokenEstimate = buildScriptWritingContext(ctx, q, int32(userID), gameCtx, insights, req)
		}

		fmt.Printf("=== MARKETING GENERATOR ===\n")
		fmt.Printf("Task Type: %s\n", taskType)
		fmt.Printf("Token Estimate: %d\n", tokenEstimate)
		fmt.Printf("Has 28-day Data: %v\n", insights.HasData)
		if insights.HasData {
			fmt.Printf("Best Day: %s (avg likes: %.2f)\n", insights.BestDayName, insights.AvgLikes)
		}

		// Call LLM
		provider := GetLLMProvider()
		result, err := provider.Call(ctx, systemPrompt, userPrompt, map[string]any{
			"temperature": 0.7,
			"max_tokens":  1024,
			"top_p":       0.9,
		}, nil)

		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{
				"error": fmt.Sprintf("LLM generation failed: %v", err),
			})
			return
		}

		dataSource := "28_day_window"
		if !insights.HasData {
			dataSource = "fallback"
		}

		c.JSON(http.StatusOK, MarketingStrategyResponse{
			Content:        strings.TrimSpace(result),
			BestPostingDay: insights.BestDayName,
			PostsPerWeek:   insights.PostsPerWeek,
			TopHook:        insights.TopHook,
			TopHashtags:    insights.TopHashtags,
			TokensUsed:     tokenEstimate,
			DataSource:     dataSource,
		})
	}
}

// fetchCompetitorInsights fetches time-boxed analytics with fallback
// Uses 28-day window for day-of-week patterns (we only have DATE, not TIME from scraper)
func fetchCompetitorInsights(ctx context.Context, q *db.Queries, userID, groupID int32, platform string) CompetitorInsights {
	insights := CompetitorInsights{
		BestDay:       3,                                  // Default: Wednesday
		BestDayName:   "Wednesday",                        // Default day name
		TimeHeuristic: getPlatformTimeHeuristic(platform), // Platform-specific advice
		HasData:       false,
		TopHashtags:   []string{}, // Initialize empty
	}

	// Get posting frequency (28-day window)
	freqData, err := q.GetPostingFrequency28Days(ctx, db.GetPostingFrequency28DaysParams{
		UserID:  userID,
		GroupID: sql.NullInt32{Int32: groupID, Valid: true},
	})
	if err != nil || freqData.TotalPosts == 0 {
		fmt.Printf("No competitor data in 28-day window (err: %v)\n", err)
		return insights
	}

	insights.HasData = true
	insights.SampleSize = freqData.TotalPosts
	insights.PostsPerWeek = freqData.PostsPerWeek

	// Get best posting day (1=Monday, 7=Sunday)
	bestDay, err := q.GetBestPostingDay(ctx, db.GetBestPostingDayParams{
		UserID:  userID,
		GroupID: sql.NullInt32{Int32: groupID, Valid: true},
	})
	if err == nil {
		insights.BestDay = int(bestDay.BestDay)
		insights.BestDayName = dayNumberToName(int(bestDay.BestDay))
		insights.AvgLikes = bestDay.AvgLikes
		fmt.Printf("Best posting day: %s (avg likes: %.2f, sample: %d)\n",
			insights.BestDayName, insights.AvgLikes, bestDay.SampleSize)
	}

	// Get top competitor hook (still uses 14-day window from original query)
	topHooks, err := q.GetTopCompetitorHooks(ctx, db.GetTopCompetitorHooksParams{
		UserID:  userID,
		GroupID: sql.NullInt32{Int32: groupID, Valid: true},
		Limit:   1,
	})
	if err == nil && len(topHooks) > 0 {
		hook := topHooks[0].Hook
		if hook != "" {
			insights.TopHook = TruncateHook(hook, 200)
			fmt.Printf("Top hook from @%s: %s\n", topHooks[0].CompetitorHandle, insights.TopHook)
		}
	}

	// Get top hashtags (28-day window)
	tags, err := q.GetTopCompetitorHashtags(ctx, db.GetTopCompetitorHashtagsParams{
		UserID:  userID,
		GroupID: sql.NullInt32{Int32: groupID, Valid: true},
	})
	if err == nil && len(tags) > 0 {
		for _, t := range tags {
			insights.TopHashtags = append(insights.TopHashtags, t.Hashtag)
		}
		fmt.Printf("Top hashtags: %v\n", insights.TopHashtags)
	}

	return insights
}

// getPlatformTimeHeuristic returns platform-specific time recommendations
// Since we don't have actual competitor posting times, we use industry best practices
func getPlatformTimeHeuristic(platform string) string {
	switch strings.ToLower(platform) {
	case "instagram":
		return "Morning (9:00 AM) or Evening (7:00 PM)"
	case "tiktok":
		return "Late Afternoon (3:00 PM - 5:00 PM)"
	case "twitter", "x":
		return "Lunchtime (12:00 PM - 1:00 PM) or Evening (8:00 PM)"
	case "youtube":
		return "Early Afternoon (2:00 PM - 4:00 PM)"
	default:
		return "Peak hours (6:00 PM - 9:00 PM)"
	}
}

// dayNumberToName converts ISO day of week (1-7) to name
func dayNumberToName(day int) string {
	days := []string{"", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
	if day >= 1 && day <= 7 {
		return days[day]
	}
	return "Wednesday" // Safe default
}

// buildStrategyContext creates a minimal context for high-level strategy tasks
// This is optimized for token efficiency - only includes GameSummary
func buildStrategyContext(gameCtx db.GameContext, insights CompetitorInsights, req MarketingStrategyRequest) (string, string, int) {
	gameName := gameCtx.GameTitle
	gameSummary := ""
	if gameCtx.GameSummary.Valid {
		gameSummary = gameCtx.GameSummary.String
	}

	// Build system prompt
	systemPrompt := BuildStrategySystemPrompt(gameName, gameSummary)

	// Build user prompt with analytics data
	var b strings.Builder
	b.WriteString("Create a high-level marketing strategy for the following campaign:\n\n")
	b.WriteString(fmt.Sprintf("Campaign Type: %s\n", req.CampaignType))
	b.WriteString(fmt.Sprintf("Platform: %s\n\n", req.Platform))

	if insights.HasData {
		b.WriteString("HARD DATA (Last 28 Days):\n")
		b.WriteString(fmt.Sprintf("- Peak Engagement Day: %s\n", insights.BestDayName))
		b.WriteString(fmt.Sprintf("- Competitor Cadence: %.1f posts/week\n", insights.PostsPerWeek))
		if insights.TopHook != "" {
			b.WriteString(fmt.Sprintf("- Top Performing Hook: \"%s\"\n", insights.TopHook))
		}
		if len(insights.TopHashtags) > 0 {
			b.WriteString("- Top Hashtags: ")
			for _, tag := range insights.TopHashtags {
				b.WriteString(fmt.Sprintf("#%s ", tag))
			}
			b.WriteString("\n")
		}
		b.WriteString(fmt.Sprintf("- Data Sample Size: %d posts analyzed\n\n", insights.SampleSize))

		b.WriteString("STRATEGIC ADVICE:\n")
		b.WriteString(fmt.Sprintf("- Schedule posts for %s.\n", insights.BestDayName))
		b.WriteString(fmt.Sprintf("- Time Recommendation: %s (industry best practice for %s).\n\n", insights.TimeHeuristic, req.Platform))
	} else {
		b.WriteString("HARD DATA: No competitor data available for the last 28 days.\n\n")
		b.WriteString("STRATEGIC ADVICE (General Best Practices):\n")
		b.WriteString("- Schedule posts for Tuesday or Wednesday.\n")
		b.WriteString(fmt.Sprintf("- Time Recommendation: %s (industry best practice for %s).\n\n", insights.TimeHeuristic, req.Platform))
	}

	if req.CustomPrompt != "" {
		b.WriteString("Additional Instructions: " + req.CustomPrompt + "\n\n")
	}

	b.WriteString("Provide a structured strategy with:\n")
	b.WriteString("1. Content Pillars (3 key themes)\n")
	b.WriteString("2. Posting Schedule Recommendation\n")
	b.WriteString("3. Engagement Tactics\n")
	b.WriteString("4. First Week Action Items\n")

	userPrompt := b.String()

	// Estimate tokens (rough: ~4 chars per token)
	tokenEstimate := (len(systemPrompt) + len(userPrompt)) / 4

	return systemPrompt, userPrompt, tokenEstimate
}

// buildScriptWritingContext creates a detailed context for content creation
// This includes relevant document chunks for accuracy
func buildScriptWritingContext(ctx context.Context, q *db.Queries, userID int32, gameCtx db.GameContext, insights CompetitorInsights, req MarketingStrategyRequest) (string, string, int) {
	gameName := gameCtx.GameTitle

	// Build system prompt
	systemPrompt := BuildScriptWritingSystemPrompt(gameName)

	// Build prompt data for template
	promptData := MarketingPromptData{
		GameName:             gameName,
		GameSummary:          "",
		BestDay:              insights.BestDayName,
		PostsPerWeek:         insights.PostsPerWeek,
		TimeHeuristic:        insights.TimeHeuristic,
		TopCompetitorCaption: insights.TopHook,
		CampaignType:         req.CampaignType,
		Platform:             req.Platform,
		HasCompetitorData:    insights.HasData,
	}

	if gameCtx.GameSummary.Valid {
		promptData.GameSummary = gameCtx.GameSummary.String
	}

	// Build the modular prompt from template
	userPrompt, err := BuildMarketingPrompt(promptData)
	if err != nil {
		fmt.Printf("Template error: %v, falling back to basic prompt\n", err)
		userPrompt = fmt.Sprintf("Write a %s post for %s about %s", req.CampaignType, req.Platform, gameName)
	}

	// Add relevant document chunks for script writing
	var chunkContext strings.Builder

	// Fetch relevant game document chunks
	chunks, err := q.SearchChunks(ctx, db.SearchChunksParams{
		Q:       req.CampaignType + " " + gameName,
		UserID:  userID,
		GroupID: req.GroupID,
		N:       3, // Limit to 3 most relevant chunks
	})
	if err == nil && len(chunks) > 0 {
		chunkContext.WriteString("\n\nRELEVANT GAME DETAILS:\n")
		for i, chunk := range chunks {
			content := chunk.Content
			if len(content) > 400 {
				content = content[:400] + "..."
			}
			chunkContext.WriteString(fmt.Sprintf("[%d] %s\n", i+1, content))
		}
	}

	// Add game context details for script writing
	var gameDetails strings.Builder
	gameDetails.WriteString("\n\nGAME CONTEXT:\n")
	if gameCtx.PrimaryGenre.Valid {
		gameDetails.WriteString(fmt.Sprintf("- Genre: %s", gameCtx.PrimaryGenre.String))
		if gameCtx.Subgenre.Valid {
			gameDetails.WriteString(fmt.Sprintf(" / %s", gameCtx.Subgenre.String))
		}
		gameDetails.WriteString("\n")
	}
	if gameCtx.Tone.Valid {
		gameDetails.WriteString(fmt.Sprintf("- Tone: %s\n", gameCtx.Tone.String))
	}
	if gameCtx.ArtStyle.Valid {
		gameDetails.WriteString(fmt.Sprintf("- Art Style: %s\n", gameCtx.ArtStyle.String))
	}
	if gameCtx.IntendedAudience.Valid {
		gameDetails.WriteString(fmt.Sprintf("- Target Audience: %s\n", gameCtx.IntendedAudience.String))
	}
	if gameCtx.CallToAction.Valid {
		gameDetails.WriteString(fmt.Sprintf("- Preferred CTA: %s\n", gameCtx.CallToAction.String))
	}

	fullUserPrompt := userPrompt + chunkContext.String() + gameDetails.String()

	if req.CustomPrompt != "" {
		fullUserPrompt += "\n\nADDITIONAL INSTRUCTIONS: " + req.CustomPrompt
	}

	// Estimate tokens
	tokenEstimate := (len(systemPrompt) + len(fullUserPrompt)) / 4

	return systemPrompt, fullUserPrompt, tokenEstimate
}
