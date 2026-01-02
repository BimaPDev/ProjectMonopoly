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
	CTAPolicy    string `json:"cta_policy"`                   // "none", "soft", "hard" (optional override)
}

// MarketingStrategyResponse is the API response
type MarketingStrategyResponse struct {
	Content        string   `json:"content"`
	BestPostingDay string   `json:"best_posting_day"` // Day name (e.g., "Wednesday")
	PostsPerWeek   float64  `json:"posts_per_week"`   // Competitor cadence
	TopHook        string   `json:"top_hook,omitempty"`
	TopHashtags    []string `json:"top_hashtags,omitempty"`
	TokensUsed     int      `json:"tokens_used_estimate"`
	DataSource     string   `json:"data_source"`      // "14_day_window" or "fallback"
	DataWindowDays int      `json:"data_window_days"` // Consistent window value (e.g., 14)
}

// CompetitorInsights holds the processed analytics data
type CompetitorInsights struct {
	BestDay                 int     // 1=Monday, 7=Sunday (ISO day of week)
	BestDayName             string  // "Monday", "Tuesday", etc.
	PostsPerWeek            float64 // Competitor posting cadence
	RecommendedPostsPerWeek int     // Guardrail: clamped cadence for strategy
	TopHook                 string
	TopHashtags             []string // Sanitized hashtags (no competitor/noise)
	CompetitorHandles       []string // For validation filtering
	CompetitorsAnalyzed     int
	AvgLikes                float64
	SampleSize              int64
	HasData                 bool
	TimeHeuristic           string            // Platform-specific time advice
	Confidence              string            // "low", "medium", "high"
	IsLowConfidence         bool              // Convenience flag
	DataWindowDays          int               // Analytics window (consistent with DefaultDataWindowDays)
	StrategyCards           []db.StrategyCard // Proven tactics from Reddit
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

		// Determine CTA Policy
		policy := CTAPolicyHard // Default
		if req.CampaignType == "Teaser" {
			policy = CTAPolicyNone
		} else if req.CampaignType == "Community" {
			policy = CTAPolicySoft
		}
		// Allow override
		if req.CTAPolicy != "" {
			switch strings.ToLower(req.CTAPolicy) {
			case "none":
				policy = CTAPolicyNone
			case "soft":
				policy = CTAPolicySoft
			case "hard":
				policy = CTAPolicyHard
			}
		}

		// Build context based on task type (SMART CONTEXT DE-DUPLICATION)
		var systemPrompt, userPrompt string
		var tokenEstimate int

		switch taskType {
		case "strategy":
			// HIGH-LEVEL: Only inject GameSummary (~200 tokens)
			systemPrompt, userPrompt, tokenEstimate = buildStrategyContext(gameCtx, insights, req, policy)
		case "script writing":
			// LOW-LEVEL: Inject specific document chunks + full game context
			systemPrompt, userPrompt, tokenEstimate = buildScriptWritingContext(ctx, q, int32(userID), gameCtx, insights, req, policy)
		}

		fmt.Printf("=== MARKETING GENERATOR ===\n")
		fmt.Printf("Task Type: %s\n", taskType)
		fmt.Printf("Policy: %s\n", policy)
		fmt.Printf("Token Estimate: %d\n", tokenEstimate)
		fmt.Printf("DataWindowDays: %d, HasData: %v\n", insights.DataWindowDays, insights.HasData)
		if insights.HasData {
			fmt.Printf("Best Day: %s (avg likes: %.2f)\n", insights.BestDayName, insights.AvgLikes)
		}

		// Call LLM with Regeneration Loop
		provider := GetLLMProvider()
		maxAttempts := 2
		var finalResult string
		var lastErr error
		var lastIssues []string

		// Build context keywords for grounding validation
		var contextKeywords map[string]struct{}
		if gameCtx.PrimaryGenre.Valid || gameCtx.KeyMechanics.Valid || gameCtx.Tone.Valid || gameCtx.AdditionalInfo.Valid {
			genre := ""
			mechanics := ""
			tone := ""
			additionalInfo := ""
			if gameCtx.PrimaryGenre.Valid {
				genre = gameCtx.PrimaryGenre.String
			}
			if gameCtx.KeyMechanics.Valid {
				mechanics = gameCtx.KeyMechanics.String
			}
			if gameCtx.Tone.Valid {
				tone = gameCtx.Tone.String
			}
			if gameCtx.AdditionalInfo.Valid {
				additionalInfo = gameCtx.AdditionalInfo.String
			}
			audience := ""
			if gameCtx.IntendedAudience.Valid {
				audience = gameCtx.IntendedAudience.String
			}
			contextKeywords = BuildContextKeywordSet(genre, mechanics, tone, audience, additionalInfo)
		}

		// Build validation config once
		validationConfig := StrategyValidationConfig{
			Policy:                  policy,
			RecommendedPostsPerWeek: insights.RecommendedPostsPerWeek,
			IsLowConfidence:         insights.IsLowConfidence,
			CampaignType:            req.CampaignType,
			CompetitorHandles:       insights.CompetitorHandles,
			AllowedHashtags:         insights.TopHashtags,
			// Enable self-brand hashtags by default for strategy tasks (safe + deterministic)
			SelfBrandHashtags: BuildSelfBrandHashtags(
				gameCtx.GameTitle,
				"", // worldName not currently stored; reserved for future
				func() string {
					if gameCtx.StudioName.Valid {
						return gameCtx.StudioName.String
					}
					return ""
				}(),
			),
			EnableSelfBrand: true,
			// Add a small, safe subset of context-derived hashtags (0-2)
			ContextDerivedHashtags: BuildContextDerivedHashtags(contextKeywords, insights.CompetitorHandles),
			EnableContextHashtags:  true,
			ContextKeywords:        contextKeywords,
		}

		// First attempt uses the original prompt
		currentPrompt := userPrompt
		for attempt := 1; attempt <= maxAttempts; attempt++ {
			fmt.Printf("DEBUG: Gen Attempt %d (prompt length: %d chars)\n", attempt, len(currentPrompt))
			result, err := provider.Call(ctx, systemPrompt, currentPrompt, map[string]any{
				"temperature": 0.7,
				"max_tokens":  1024,
				"top_p":       0.9,
			}, nil)

			if err != nil {
				lastErr = err
				break
			}

			// Step 1: Strip any internal meta markers that might have leaked
			cleanedResult := StripInternalMeta(result)

			// Step 2: For strategy outputs, ALWAYS rebuild hashtag pack deterministically
			// This ensures invented hashtags can never survive to final output
			var ok bool
			var issues []string
			if taskType == "strategy" {
				// First validate non-hashtag issues
				ok, issues = ValidateStrategyOutputWithConfig(cleanedResult, validationConfig)

				// If only hashtag issues OR no issues, normalize the output.
				// CRITICAL: Never auto-normalize if any non-hashtag issue exists (placeholders, schedule incompleteness, generic output, grounding, competitors, URLs, etc.)
				// Use the shared helper to prevent drift between handler logic and tests.
				if len(issues) == 0 || IsOnlyHashtagPlacementViolation(issues) {
					// Log allowed hashtag sources
					fmt.Printf("DEBUG: AllowedHashtags sources - observed: %d tags %v, selfBrand: %d tags %v (enabled=%v), context: %d tags %v (enabled=%v)\n",
						len(insights.TopHashtags), insights.TopHashtags,
						len(validationConfig.SelfBrandHashtags), validationConfig.SelfBrandHashtags, validationConfig.EnableSelfBrand,
						len(validationConfig.ContextDerivedHashtags), validationConfig.ContextDerivedHashtags, validationConfig.EnableContextHashtags)

					// Extract original hashtag pack for logging
					originalPackLine := extractHashtagPackLine(cleanedResult)
					fmt.Printf("DEBUG: Original Hashtag Pack (LLM output): %s\n", originalPackLine)

					normalizedResult := NormalizeStrategyHashtagsExtended(
						cleanedResult,
						insights.TopHashtags,
						validationConfig.SelfBrandHashtags,
						validationConfig.EnableSelfBrand,
						validationConfig.ContextDerivedHashtags,
						validationConfig.EnableContextHashtags,
						insights.CompetitorHandles,
					)

					// Truncate any content after Hashtag Pack section
					normalizedResult = TruncateAfterHashtagPack(normalizedResult)

					// Log final hashtag pack and verify membership
					finalPackLine := extractHashtagPackLine(normalizedResult)
					allowedSet := BuildAllowedHashtagSet(
						insights.TopHashtags,
						validationConfig.SelfBrandHashtags,
						validationConfig.EnableSelfBrand,
						validationConfig.ContextDerivedHashtags,
						validationConfig.EnableContextHashtags,
						insights.CompetitorHandles,
					)
					fmt.Printf("DEBUG: Final Hashtag Pack (deterministic): %s\n", finalPackLine)
					fmt.Printf("DEBUG: Allowed set size: %d tags\n", len(allowedSet))

					// Re-validate after normalization
					ok, issues = ValidateStrategyOutputWithConfig(normalizedResult, validationConfig)
					if ok {
						fmt.Printf("DEBUG: Normalization successful, output is now valid\n")
						// CRITICAL: Set finalResult to normalizedResult and break immediately
						// Do NOT allow the code below to overwrite this
						finalResult = normalizedResult
						break
					}
					// If still failing after normalization, these are other issues
					fmt.Printf("DEBUG: Post-normalization validation failed: %v\n", issues)
					cleanedResult = normalizedResult
				}
			} else {
				ok, issues = ValidatePostOutput(cleanedResult, policy)
			}

			// Only set finalResult here for non-strategy tasks or if normalization wasn't done
			if ok && finalResult == "" {
				finalResult = cleanedResult
				break
			}

			// Validation failed
			lastIssues = issues
			fmt.Printf("DEBUG: Validation failed (attempt %d): %v\n", attempt, issues)

			if attempt < maxAttempts {
				// Build MINIMAL repair prompt - extract only violating snippets
				snippets := ExtractViolatingSnippets(result, issues, insights.CompetitorHandles, 5, 800)
				bannedTokens := BuildBannedTokensList(insights.CompetitorHandles)
				repairPrompt := BuildMinimalRepairPrompt(userPrompt, issues, snippets, bannedTokens)

				// Replace the entire prompt with original + minimal repair context
				// This avoids token bloat from including the full invalid output
				currentPrompt = userPrompt + "\n\n---\n\n" + repairPrompt
			}
		}

		// Final validation failed - return 422
		if finalResult == "" && lastErr == nil {
			c.JSON(http.StatusUnprocessableEntity, gin.H{
				"error":  "generated content failed validation",
				"issues": lastIssues,
			})
			return
		}

		if lastErr != nil {
			c.JSON(http.StatusInternalServerError, gin.H{
				"error": fmt.Sprintf("LLM generation failed: %v", lastErr),
			})
			return
		}

		// DEFENSIVE ASSERTION: Final scan before returning 200
		// Ensures no invalid content can ever reach the client
		if taskType == "strategy" {
			finalResult = strings.TrimSpace(finalResult)
			allowedSet := BuildAllowedHashtagSet(
				insights.TopHashtags,
				validationConfig.SelfBrandHashtags,
				validationConfig.EnableSelfBrand,
				validationConfig.ContextDerivedHashtags,
				validationConfig.EnableContextHashtags,
				insights.CompetitorHandles,
			)

			assertionIssues := runFinalAssertions(finalResult, allowedSet, insights.CompetitorHandles, contextKeywords)
			if len(assertionIssues) > 0 {
				fmt.Printf("CRITICAL: Final assertion failed before returning 200: %v\n", assertionIssues)
				c.JSON(http.StatusUnprocessableEntity, gin.H{
					"error":  "final assertion failed - output invalid",
					"issues": assertionIssues,
				})
				return
			}
		}

		dataSource := fmt.Sprintf("%d_day_window", insights.DataWindowDays)
		if !insights.HasData {
			dataSource = "fallback"
		}

		c.JSON(http.StatusOK, MarketingStrategyResponse{
			Content:        strings.TrimSpace(finalResult),
			BestPostingDay: insights.BestDayName,
			PostsPerWeek:   insights.PostsPerWeek,
			TopHook:        insights.TopHook,
			TopHashtags:    insights.TopHashtags,
			TokensUsed:     tokenEstimate,
			DataSource:     dataSource,
			DataWindowDays: insights.DataWindowDays,
		})
	}
}

// fetchCompetitorInsights fetches time-boxed analytics with fallback
// Uses DefaultDataWindowDays (14) for consistency with UI and optimized queries
func fetchCompetitorInsights(ctx context.Context, q *db.Queries, userID, groupID int32, platform string) CompetitorInsights {
	insights := CompetitorInsights{
		BestDay:                 3,                                  // Default: Wednesday
		BestDayName:             "Wednesday",                        // Default day name
		TimeHeuristic:           getPlatformTimeHeuristic(platform), // Platform-specific advice
		HasData:                 false,
		TopHashtags:             []string{},
		CompetitorHandles:       []string{},
		RecommendedPostsPerWeek: DefaultPostsPerWeek,
		Confidence:              "low",
		IsLowConfidence:         true,
		DataWindowDays:          DefaultDataWindowDays, // Consistent window value
		StrategyCards:           []db.StrategyCard{},
	}

	// Get posting frequency (uses DefaultDataWindowDays window)
	freqData, err := q.GetPostingFrequency28Days(ctx, db.GetPostingFrequency28DaysParams{
		UserID:  userID,
		GroupID: sql.NullInt32{Int32: groupID, Valid: true},
	})
	if err != nil || freqData.TotalPosts == 0 {
		fmt.Printf("No competitor data in %d-day window (err: %v)\n", DefaultDataWindowDays, err)
		return insights
	}

	insights.HasData = true
	insights.SampleSize = freqData.TotalPosts
	insights.PostsPerWeek = freqData.PostsPerWeek

	// Compute recommended posts per week with guardrails
	insights.RecommendedPostsPerWeek = ComputeRecommendedPostsPerWeek(freqData.PostsPerWeek)

	// Determine confidence level
	insights.Confidence = DetermineConfidence(int(freqData.TotalPosts))
	insights.IsLowConfidence = insights.Confidence == "low"

	fmt.Printf("Competitor insights: %.1f posts/week, recommended: %d, confidence: %s (sample: %d)\n",
		insights.PostsPerWeek, insights.RecommendedPostsPerWeek, insights.Confidence, insights.SampleSize)

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

	// Get top competitor hook (uses 14-day window)
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
		// Collect competitor handles for hashtag filtering
		for _, h := range topHooks {
			insights.CompetitorHandles = append(insights.CompetitorHandles, h.CompetitorHandle)
		}
	}

	// Get more competitor hooks just for handles (to build complete filter list)
	moreHooks, err := q.GetTopCompetitorHooks(ctx, db.GetTopCompetitorHooksParams{
		UserID:  userID,
		GroupID: sql.NullInt32{Int32: groupID, Valid: true},
		Limit:   10,
	})
	if err == nil {
		handleSet := make(map[string]bool)
		for _, h := range insights.CompetitorHandles {
			handleSet[strings.ToLower(h)] = true
		}
		for _, h := range moreHooks {
			lower := strings.ToLower(h.CompetitorHandle)
			if !handleSet[lower] {
				insights.CompetitorHandles = append(insights.CompetitorHandles, h.CompetitorHandle)
				handleSet[lower] = true
			}
		}
	}

	// Get top hashtags (DataWindowDays window) and sanitize them
	rawTags := []string{}
	tags, err := q.GetTopCompetitorHashtags(ctx, db.GetTopCompetitorHashtagsParams{
		UserID:  userID,
		GroupID: sql.NullInt32{Int32: groupID, Valid: true},
	})
	if err == nil && len(tags) > 0 {
		for _, t := range tags {
			if tagStr, ok := t.Hashtag.(string); ok {
				rawTags = append(rawTags, tagStr)
			}
		}
	}

	// Sanitize hashtags: remove competitor-branded, stoplist, and noise
	insights.TopHashtags = SanitizeHashtags(rawTags, insights.CompetitorHandles)
	fmt.Printf("Sanitized hashtags: %v (from raw: %v, window: %d days)\n", insights.TopHashtags, rawTags, insights.DataWindowDays)

	// Fetch high-confidence strategy cards (confidence >= 0.7)
	cards, err := q.GetTopConfidentStrategyCards(ctx, db.GetTopConfidentStrategyCardsParams{
		UserID:     userID,
		GroupID:    sql.NullInt32{Int32: groupID, Valid: true},
		Confidence: sql.NullFloat64{Float64: 0.7, Valid: true},
		Limit:      3,
	})
	if err == nil && len(cards) > 0 {
		insights.StrategyCards = cards
		fmt.Printf("Fetched %d high-confidence strategy cards\n", len(cards))
	} else {
		// Fallback: get recent cards with lower threshold if none found
		cards, err = q.GetTopConfidentStrategyCards(ctx, db.GetTopConfidentStrategyCardsParams{
			UserID:     userID,
			GroupID:    sql.NullInt32{Int32: groupID, Valid: true},
			Confidence: sql.NullFloat64{Float64: 0.5, Valid: true},
			Limit:      2,
		})
		if err == nil && len(cards) > 0 {
			insights.StrategyCards = cards
			fmt.Printf("Fetched %d medium-confidence strategy cards (fallback)\n", len(cards))
		}
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
func buildStrategyContext(gameCtx db.GameContext, insights CompetitorInsights, req MarketingStrategyRequest, policy CTAPolicy) (string, string, int) {
	gameName := gameCtx.GameTitle
	gameSummary := ""
	if gameCtx.GameSummary.Valid {
		gameSummary = gameCtx.GameSummary.String
	}

	// Build system prompt with new structured config
	systemPrompt := BuildStrategySystemPrompt(StrategyPromptConfig{
		GameName:                gameName,
		GameSummary:             gameSummary,
		CampaignType:            req.CampaignType,
		CTAPolicy:               policy,
		RecommendedPostsPerWeek: insights.RecommendedPostsPerWeek,
		IsLowConfidence:         insights.IsLowConfidence,
		PostsAnalyzed:           int(insights.SampleSize),
		BestDay:                 insights.BestDayName,
		StrategyCards:           insights.StrategyCards,
	})

	// Build user prompt with analytics data and strict structure requirements
	var b strings.Builder
	b.WriteString("Create a marketing strategy for the following campaign:\n\n")
	b.WriteString(fmt.Sprintf("Campaign Type: %s\n", req.CampaignType))
	b.WriteString(fmt.Sprintf("Platform: %s\n\n", req.Platform))

	// GAME CONTEXT (source: user docs / RAG)
	b.WriteString("GAME CONTEXT (source: user docs):\n")
	if gameCtx.PrimaryGenre.Valid {
		b.WriteString(fmt.Sprintf("- Genre: %s", gameCtx.PrimaryGenre.String))
		if gameCtx.Subgenre.Valid {
			b.WriteString(fmt.Sprintf(" / %s", gameCtx.Subgenre.String))
		}
		b.WriteString("\n")
	}
	if gameCtx.KeyMechanics.Valid {
		b.WriteString(fmt.Sprintf("- Key Mechanics (ONLY use these): %s\n", gameCtx.KeyMechanics.String))
	}
	if gameCtx.Tone.Valid {
		b.WriteString(fmt.Sprintf("- Tone: %s\n", gameCtx.Tone.String))
	}
	if gameCtx.IntendedAudience.Valid {
		b.WriteString(fmt.Sprintf("- Target Audience: %s\n", gameCtx.IntendedAudience.String))
	}
	if gameCtx.AdditionalInfo.Valid {
		b.WriteString(fmt.Sprintf("- Additional Info: %s\n", gameCtx.AdditionalInfo.String))
	}
	b.WriteString("\n")

	// COMPETITOR SIGNALS (reference only; do not copy wording)
	if insights.HasData {
		b.WriteString("COMPETITOR SIGNALS (reference only; do not copy wording):\n")
		b.WriteString(fmt.Sprintf("- Data window: last %d days\n", insights.DataWindowDays))
		b.WriteString(fmt.Sprintf("- Posts analyzed: %d\n", insights.SampleSize))
		b.WriteString(fmt.Sprintf("- Confidence: %s\n", insights.Confidence))
		b.WriteString(fmt.Sprintf("- Peak engagement day (hypothesis): %s\n", insights.BestDayName))
		b.WriteString(fmt.Sprintf("- Competitor cadence: %.1f posts/week\n", insights.PostsPerWeek))

		// Convert hook to style description instead of passing verbatim (safety)
		if insights.TopHook != "" {
			// Use pattern classification for strategic insight
			hookPattern := classifyHookPattern(insights.TopHook)
			// Also get style description for additional context
			hookStyle := DescribeHookStyle(insights.TopHook)
			b.WriteString(fmt.Sprintf("- Hook pattern observed: %s (%s)\n", hookPattern, hookStyle))
		}

		// Pass hashtags as plain tokens (no #) to prevent model from echoing them in wrong places
		if len(insights.TopHashtags) > 0 {
			b.WriteString("- Allowed hashtags for final pack ONLY (plain tokens, no #): ")
			b.WriteString(strings.Join(insights.TopHashtags, " "))
			b.WriteString("\n")
		}
		b.WriteString("\n")

		// MANDATORY CONSTRAINTS
		b.WriteString("MANDATORY CONSTRAINTS:\n")
		b.WriteString(fmt.Sprintf("- PostsPerWeek MUST be exactly: %d\n", insights.RecommendedPostsPerWeek))
		b.WriteString(fmt.Sprintf("- Primary Day MUST be: %s\n", insights.BestDayName))
		b.WriteString(fmt.Sprintf("- Time Recommendation: %s\n", insights.TimeHeuristic))

		if insights.IsLowConfidence {
			b.WriteString("\nLOW CONFIDENCE NOTICE:\n")
			b.WriteString("- Treat day/time recommendations as hypotheses.\n")
			b.WriteString("- Include a 2-week A/B test plan comparing posting days.\n")
			b.WriteString("- Define a primary success metric (engagement rate, saves/impression, etc.).\n")
		}
	} else {
		b.WriteString(fmt.Sprintf("COMPETITOR SIGNALS: No competitor data available for the last %d days.\n\n", insights.DataWindowDays))
		b.WriteString("MANDATORY CONSTRAINTS:\n")
		b.WriteString(fmt.Sprintf("- PostsPerWeek MUST be exactly: %d\n", DefaultPostsPerWeek))
		b.WriteString("- Primary Day MUST be: Tuesday or Wednesday (industry default)\n")
		b.WriteString(fmt.Sprintf("- Time Recommendation: %s\n", insights.TimeHeuristic))
		b.WriteString("\nLOW CONFIDENCE NOTICE:\n")
		b.WriteString("- Treat day/time recommendations as hypotheses.\n")
		b.WriteString("- Include a 2-week A/B test plan comparing posting days.\n")
	}

	if req.CustomPrompt != "" {
		b.WriteString("\nAdditional Instructions: " + req.CustomPrompt + "\n")
	}

	// Required output structure
	b.WriteString("\n---\n")
	b.WriteString("OUTPUT STRUCTURE (follow EXACTLY):\n\n")
	b.WriteString("## Content Pillars\n")
	b.WriteString("- [Pillar 1]\n- [Pillar 2]\n- [Pillar 3]\n\n")
	b.WriteString("## Posting Cadence\n")
	b.WriteString(fmt.Sprintf("PostsPerWeek: %d\n", insights.RecommendedPostsPerWeek))
	b.WriteString(fmt.Sprintf("Primary Day: %s\n", insights.BestDayName))
	if insights.IsLowConfidence || !insights.HasData {
		b.WriteString(fmt.Sprintf("Confidence: low (sample size: %d posts)\n\n", insights.SampleSize))
	} else {
		b.WriteString("\n")
	}

	// Generate schedule days based on recommended posts per week
	scheduleDays := generateScheduleDays(insights.BestDayName, insights.RecommendedPostsPerWeek)
	b.WriteString("## 2-Week Schedule\n")
	b.WriteString("Week 1:\n")
	for _, day := range scheduleDays {
		b.WriteString(fmt.Sprintf("- %s: [content type]\n", day))
	}
	b.WriteString("Week 2:\n")
	for _, day := range scheduleDays {
		b.WriteString(fmt.Sprintf("- %s: [content type]\n", day))
	}

	if insights.IsLowConfidence || !insights.HasData {
		b.WriteString("\n## A/B Test Plan (REQUIRED)\n")
		b.WriteString("- Test Variable: [e.g., posting day]\n")
		b.WriteString("- Duration: 2 weeks\n")
		b.WriteString("- Primary Metric: [e.g., engagement rate]\n")
		b.WriteString("- Decision Criteria: [what determines winner]\n")
	}

	b.WriteString("\n## Hook Ideas (5 one-liners)\n")
	b.WriteString("1. [Hook]\n2. [Hook]\n3. [Hook]\n4. [Hook]\n5. [Hook]\n\n")

	// Hashtag Pack - only place where # appears
	b.WriteString("## Hashtag Pack (3-5 tags)\n")
	if len(insights.TopHashtags) > 0 {
		for _, tag := range insights.TopHashtags {
			b.WriteString(fmt.Sprintf("#%s ", tag))
		}
		b.WriteString("\n")
	} else {
		b.WriteString("[Generate 3-5 relevant hashtags - NO competitor brand tags]\n")
	}

	userPrompt := b.String()

	// Estimate tokens (rough: ~4 chars per token)
	tokenEstimate := (len(systemPrompt) + len(userPrompt)) / 4

	return systemPrompt, userPrompt, tokenEstimate
}

// classifyHookPattern converts a competitor hook into a pattern label
// This prevents the model from copying verbatim text while still providing strategic insight
func classifyHookPattern(hook string) string {
	lowerHook := strings.ToLower(hook)

	// Classify by common hook patterns
	switch {
	case strings.Contains(lowerHook, "why") && (strings.Contains(lowerHook, "doesn't") || strings.Contains(lowerHook, "won't") || strings.Contains(lowerHook, "can't")):
		return "Myth-busting: why X doesn't Y"
	case strings.Contains(lowerHook, "never") || strings.Contains(lowerHook, "stop"):
		return "Contrarian statement hook"
	case strings.Contains(lowerHook, "secret") || strings.Contains(lowerHook, "hidden"):
		return "Secret/hidden feature reveal"
	case strings.Contains(lowerHook, "?"):
		return "Question-based curiosity hook"
	case strings.Contains(lowerHook, "how to") || strings.Contains(lowerHook, "how i"):
		return "How-to explainer hook"
	case strings.Contains(lowerHook, "everyone") || strings.Contains(lowerHook, "nobody"):
		return "Contrarian everyone/nobody hook"
	case strings.Contains(lowerHook, "surprising") || strings.Contains(lowerHook, "unexpected"):
		return "Unexpected reveal hook"
	case strings.Contains(lowerHook, "mistake") || strings.Contains(lowerHook, "wrong"):
		return "Mistake/correction hook"
	case strings.Contains(lowerHook, "finally") || strings.Contains(lowerHook, "just"):
		return "Announcement/timing hook"
	case strings.Contains(lowerHook, "bet you") || strings.Contains(lowerHook, "did you know"):
		return "Challenge/trivia hook"
	case strings.Contains(lowerHook, "wait") || strings.Contains(lowerHook, "look"):
		return "Attention-grabbing imperative hook"
	case len(hook) < 30:
		return "Short punchy statement"
	default:
		return "Engagement-focused hook"
	}
}

// generateScheduleDays creates a list of posting days based on best day and frequency
func generateScheduleDays(bestDay string, postsPerWeek int) []string {
	if postsPerWeek <= 0 {
		postsPerWeek = 1
	}
	if postsPerWeek > 7 {
		postsPerWeek = 7
	}

	// Map day names to numbers for calculation
	dayOrder := map[string]int{
		"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
		"Friday": 4, "Saturday": 5, "Sunday": 6,
	}
	dayNames := []string{"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}

	bestDayNum, ok := dayOrder[bestDay]
	if !ok {
		bestDayNum = 3 // Default to Thursday
	}

	result := []string{bestDay}
	if postsPerWeek == 1 {
		return result
	}

	// Spread posts evenly across the week
	interval := 7 / postsPerWeek
	for i := 1; i < postsPerWeek; i++ {
		nextDayNum := (bestDayNum + (i * interval)) % 7
		result = append(result, dayNames[nextDayNum])
	}

	return result
}

// buildScriptWritingContext creates a detailed context for content creation
// This includes relevant document chunks for accuracy
func buildScriptWritingContext(ctx context.Context, q *db.Queries, userID int32, gameCtx db.GameContext, insights CompetitorInsights, req MarketingStrategyRequest, policy CTAPolicy) (string, string, int) {
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
		TopHashtags:          insights.TopHashtags,
		CampaignType:         req.CampaignType,
		Platform:             req.Platform,
		HasCompetitorData:    insights.HasData,
		CTAPolicy:            policy,
		DataWindowDays:       14,
		CompetitorsAnalyzed:  5, // Hardcoded estimate for now as SQL doesn't return it
		PostsAnalyzed:        int(insights.SampleSize),
		MetricName:           "Avg Engagement",
		Confidence:           "Medium",
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
