// internal/handlers/campaigns.go
package handlers

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"time"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

// ==================== Request/Response Structs ====================

// AudienceArchetype defines preset audience profiles
type AudienceArchetype struct {
	ID           string                 `json:"id"`
	Name         string                 `json:"name"`
	Description  string                 `json:"description"`
	Demographics map[string]interface{} `json:"demographics"`
}

// CadenceConfig holds platform and timing settings
type CadenceConfig struct {
	Platforms     []string `json:"platforms"`
	PostsPerWeek  int      `json:"posts_per_week"`
	PreferredDays []string `json:"preferred_days"`
	TimeWindows   []string `json:"time_windows"`
}

// CreateCampaignRequest is the wizard submission payload
type CreateCampaignRequest struct {
	Name     string          `json:"name" binding:"required"`
	GroupID  int32           `json:"group_id"`
	Goal     string          `json:"goal" binding:"required,oneof=wishlist discord demo trailer awareness launch"`
	Audience json.RawMessage `json:"audience" binding:"required"`
	Pillars  []string        `json:"pillars" binding:"required,min=1,max=5"`
	Cadence  CadenceConfig   `json:"cadence" binding:"required"`
}

// CreateCampaignResponse is returned after campaign creation
type CreateCampaignResponse struct {
	Campaign   db.Campaign   `json:"campaign"`
	WeeklyPlan []DraftOutput `json:"weekly_plan"`
	Message    string        `json:"message"`
}

// AttachAssetsRequest for uploading campaign assets
type AttachAssetsRequest struct {
	Tags []string `json:"tags"`
}

// GenerateDraftsRequest triggers AI generation
type GenerateDraftsRequest struct {
	ForceRegenerate bool   `json:"force_regenerate"`
	Platform        string `json:"platform"` // optional: filter to specific platform
}

// DraftOutput is the strict JSON schema for AI-generated drafts
type DraftOutput struct {
	Platform              string     `json:"platform"`
	PostType              string     `json:"post_type"`
	Hook                  string     `json:"hook"`
	Caption               string     `json:"caption"`
	Hashtags              []string   `json:"hashtags"`
	CTA                   string     `json:"cta"`
	RecommendedTimeWindow TimeWindow `json:"recommended_time_window"`
	ReasonCodes           []string   `json:"reason_codes"`
	Confidence            float64    `json:"confidence"`
}

// TimeWindow defines when to post
type TimeWindow struct {
	DayOfWeek string `json:"day_of_week"`
	StartHour int    `json:"start_hour"`
	EndHour   int    `json:"end_hour"`
	Timezone  string `json:"timezone"`
}

// IngestMetricsRequest for storing performance snapshots
type IngestMetricsRequest struct {
	GroupID    int32           `json:"group_id" binding:"required"`
	Platform   string          `json:"platform" binding:"required"`
	PostID     string          `json:"post_id" binding:"required"`
	DraftID    *string         `json:"draft_id"`
	Metrics    json.RawMessage `json:"metrics" binding:"required"`
	CapturedAt *time.Time      `json:"captured_at"`
}

// InsightsResponse for the feedback loop endpoint
type InsightsResponse struct {
	Summary            MetricsSummary  `json:"summary"`
	BestPostingWindows []PostingWindow `json:"best_posting_windows"`
	TopHookPatterns    []HookPattern   `json:"top_hook_patterns"`
	Recommendations    []string        `json:"recommendations"`
	DataWindowDays     int             `json:"data_window_days"`
}

type MetricsSummary struct {
	TotalPosts     int64   `json:"total_posts"`
	AvgImpressions float64 `json:"avg_impressions"`
	AvgEngagement  float64 `json:"avg_engagement"`
	AvgLikes       float64 `json:"avg_likes"`
	AvgComments    float64 `json:"avg_comments"`
	AvgShares      float64 `json:"avg_shares"`
}

type PostingWindow struct {
	DayOfWeek     int     `json:"day_of_week"`
	HourOfDay     int     `json:"hour_of_day"`
	AvgEngagement float64 `json:"avg_engagement"`
	SampleSize    int64   `json:"sample_size"`
}

type HookPattern struct {
	Hook          string  `json:"hook"`
	AvgEngagement float64 `json:"avg_engagement"`
	UsageCount    int64   `json:"usage_count"`
}

// DraftResponse is a frontend-friendly version of PostDraft
// Converts sql.NullString fields to plain strings
type DraftResponse struct {
	ID         string   `json:"id"`
	CampaignID string   `json:"campaign_id"`
	Platform   string   `json:"platform"`
	PostType   string   `json:"post_type"`
	Hook       string   `json:"hook"`
	Caption    string   `json:"caption"`
	Hashtags   []string `json:"hashtags"`
	CTA        string   `json:"cta"`
	Confidence float64  `json:"confidence"`
	Status     string   `json:"status"`
}

// ==================== Preset Data ====================

// GetAudienceArchetypes returns preset audience profiles for the wizard
var AudienceArchetypes = []AudienceArchetype{
	{
		ID:          "core_gamer",
		Name:        "Core Gamer",
		Description: "Dedicated players who seek depth and challenge",
		Demographics: map[string]interface{}{
			"age_range": "18-34",
			"platforms": []string{"PC", "Console"},
			"interests": []string{"competitive gaming", "esports", "game reviews"},
		},
	},
	{
		ID:          "casual_player",
		Name:        "Casual Player",
		Description: "Plays for relaxation and social connection",
		Demographics: map[string]interface{}{
			"age_range": "25-45",
			"platforms": []string{"Mobile", "Switch"},
			"interests": []string{"cozy games", "puzzle games", "social gaming"},
		},
	},
	{
		ID:          "content_creator",
		Name:        "Content Creator",
		Description: "Streamers and YouTubers looking for engaging content",
		Demographics: map[string]interface{}{
			"age_range": "18-30",
			"platforms": []string{"PC"},
			"interests": []string{"streaming", "YouTube", "community building"},
		},
	},
	{
		ID:          "indie_enthusiast",
		Name:        "Indie Enthusiast",
		Description: "Appreciates unique art and innovative gameplay",
		Demographics: map[string]interface{}{
			"age_range": "22-40",
			"platforms": []string{"PC", "Switch"},
			"interests": []string{"art games", "narrative", "indie developers"},
		},
	},
	{
		ID:          "nostalgia_gamer",
		Name:        "Nostalgia Gamer",
		Description: "Values retro aesthetics and classic gameplay",
		Demographics: map[string]interface{}{
			"age_range": "28-45",
			"platforms": []string{"PC", "Console", "Retro"},
			"interests": []string{"pixel art", "retro games", "remakes"},
		},
	},
}

// ContentPillars are preset content themes
var ContentPillars = []string{
	"Behind the Scenes",
	"Gameplay Highlights",
	"Developer Diaries",
	"Community Spotlight",
	"Tips & Tutorials",
	"Lore & Worldbuilding",
	"Announcements & Updates",
	"Memes & Humor",
	"Fan Art & UGC",
	"Milestones & Celebrations",
}

// ==================== Handlers ====================

// CreateCampaignHandler creates a new campaign from wizard submission
func CreateCampaignHandler(queries *db.Queries) gin.HandlerFunc {
	return func(c *gin.Context) {
		userID, exists := c.Get("userID")
		if !exists {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "User not authenticated"})
			return
		}
		userIDInt, ok := userID.(int32)
		if !ok {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid user ID type"})
			return
		}

		var req CreateCampaignRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		// Validate pillars count
		if len(req.Pillars) < 1 || len(req.Pillars) > 5 {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Must select 1-5 content pillars"})
			return
		}

		// Marshal pillars and cadence to JSON
		pillarsJSON, _ := json.Marshal(req.Pillars)
		cadenceJSON, _ := json.Marshal(req.Cadence)

		// Create campaign in DB
		campaign, err := queries.CreateCampaign(context.Background(), db.CreateCampaignParams{
			UserID:   userIDInt,
			GroupID:  sql.NullInt32{Int32: req.GroupID, Valid: req.GroupID > 0},
			Name:     req.Name,
			Goal:     req.Goal,
			Audience: req.Audience,
			Pillars:  pillarsJSON,
			Cadence:  cadenceJSON,
			Status:   "draft",
		})
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to create campaign: %v", err)})
			return
		}

		c.JSON(http.StatusCreated, CreateCampaignResponse{
			Campaign:   campaign,
			WeeklyPlan: []DraftOutput{}, // Empty until generate is called
			Message:    "Campaign created successfully. Call /generate to create drafts.",
		})
	}
}

// ListCampaignsHandler returns all campaigns for the authenticated user
func ListCampaignsHandler(queries *db.Queries) gin.HandlerFunc {
	return func(c *gin.Context) {
		userID, exists := c.Get("userID")
		if !exists {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "User not authenticated"})
			return
		}
		userIDInt := userID.(int32)

		campaigns, err := queries.ListCampaignsByUser(context.Background(), userIDInt)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to list campaigns: %v", err)})
			return
		}

		c.JSON(http.StatusOK, gin.H{"campaigns": campaigns})
	}
}

// GetCampaignHandler returns a single campaign by ID
func GetCampaignHandler(queries *db.Queries) gin.HandlerFunc {
	return func(c *gin.Context) {
		campaignID, err := uuid.Parse(c.Param("id"))
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid campaign ID"})
			return
		}

		campaign, err := queries.GetCampaignByID(context.Background(), campaignID)
		if err != nil {
			if err == sql.ErrNoRows {
				c.JSON(http.StatusNotFound, gin.H{"error": "Campaign not found"})
				return
			}
			c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to get campaign: %v", err)})
			return
		}

		c.JSON(http.StatusOK, campaign)
	}
}

// AttachCampaignAssetsHandler uploads assets to a campaign
func AttachCampaignAssetsHandler(queries *db.Queries) gin.HandlerFunc {
	return func(c *gin.Context) {
		campaignID, err := uuid.Parse(c.Param("id"))
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid campaign ID"})
			return
		}

		// Verify campaign exists
		_, err = queries.GetCampaignByID(context.Background(), campaignID)
		if err != nil {
			c.JSON(http.StatusNotFound, gin.H{"error": "Campaign not found"})
			return
		}

		// Get file
		file, err := c.FormFile("file")
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "File is required"})
			return
		}

		// Get tags
		tagsRaw := c.PostForm("tags")
		var tags []string
		if tagsRaw != "" {
			json.Unmarshal([]byte(tagsRaw), &tags)
		}

		// Create upload directory
		uploadPath := filepath.Join("uploads", "campaigns", campaignID.String())
		if err := os.MkdirAll(uploadPath, os.ModePerm); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create upload directory"})
			return
		}

		// Save file
		filename := fmt.Sprintf("%s_%s", uuid.New().String()[:8], file.Filename)
		fullPath := filepath.Join(uploadPath, filename)
		if err := c.SaveUploadedFile(file, fullPath); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to save file"})
			return
		}

		// Store in DB
		tagsJSON, _ := json.Marshal(tags)
		asset, err := queries.CreateCampaignAsset(context.Background(), db.CreateCampaignAssetParams{
			CampaignID: campaignID,
			StorageUrl: fullPath,
			Filename:   file.Filename,
			MimeType:   sql.NullString{String: file.Header.Get("Content-Type"), Valid: true},
			SizeBytes:  sql.NullInt64{Int64: file.Size, Valid: true},
			Tags:       tagsJSON,
		})
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to save asset: %v", err)})
			return
		}

		c.JSON(http.StatusCreated, asset)
	}
}

// GenerateCampaignDraftsHandler triggers AI generation of structured drafts
func GenerateCampaignDraftsHandler(queries *db.Queries) gin.HandlerFunc {
	return func(c *gin.Context) {
		campaignID, err := uuid.Parse(c.Param("id"))
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid campaign ID"})
			return
		}

		var req GenerateDraftsRequest
		c.ShouldBindJSON(&req) // Optional body

		// Get campaign
		campaign, err := queries.GetCampaignByID(context.Background(), campaignID)
		if err != nil {
			c.JSON(http.StatusNotFound, gin.H{"error": "Campaign not found"})
			return
		}

		// Parse campaign config
		var pillars []string
		json.Unmarshal(campaign.Pillars, &pillars)

		var cadence CadenceConfig
		json.Unmarshal(campaign.Cadence, &cadence)

		// Generate drafts using AI (simplified for now - would call LLM)
		drafts := generateStructuredDrafts(campaign, pillars, cadence, req.Platform)

		// Validate and store drafts
		var storedDrafts []db.PostDraft
		for _, draft := range drafts {
			// Validate draft structure
			if err := validateDraftOutput(draft); err != nil {
				continue // Skip invalid drafts
			}

			timeWindowJSON, _ := json.Marshal(draft.RecommendedTimeWindow)

			stored, err := queries.CreatePostDraft(context.Background(), db.CreatePostDraftParams{
				CampaignID:  campaignID,
				Platform:    draft.Platform,
				PostType:    draft.PostType,
				Hook:        sql.NullString{String: draft.Hook, Valid: draft.Hook != ""},
				Caption:     sql.NullString{String: draft.Caption, Valid: draft.Caption != ""},
				Hashtags:    draft.Hashtags,
				Cta:         sql.NullString{String: draft.CTA, Valid: draft.CTA != ""},
				TimeWindow:  timeWindowJSON,
				ReasonCodes: draft.ReasonCodes,
				Confidence:  sql.NullString{String: fmt.Sprintf("%.2f", draft.Confidence), Valid: true},
				Status:      "draft",
			})
			if err == nil {
				storedDrafts = append(storedDrafts, stored)
			}
		}

		// Update campaign status
		queries.UpdateCampaignStatus(context.Background(), db.UpdateCampaignStatusParams{
			ID:     campaignID,
			Status: "active",
		})

		c.JSON(http.StatusOK, gin.H{
			"drafts":       storedDrafts,
			"drafts_count": len(storedDrafts),
			"message":      "Drafts generated successfully",
		})
	}
}

// ListCampaignDraftsHandler returns all drafts for a campaign
func ListCampaignDraftsHandler(queries *db.Queries) gin.HandlerFunc {
	return func(c *gin.Context) {
		campaignID, err := uuid.Parse(c.Param("id"))
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid campaign ID"})
			return
		}

		status := c.Query("status")
		var drafts []db.PostDraft

		if status != "" {
			drafts, err = queries.ListDraftsByStatus(context.Background(), db.ListDraftsByStatusParams{
				CampaignID: campaignID,
				Status:     status,
			})
		} else {
			drafts, err = queries.ListDraftsByCampaign(context.Background(), campaignID)
		}

		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to list drafts: %v", err)})
			return
		}

		// Convert to frontend-friendly response
		response := make([]DraftResponse, len(drafts))
		for i, d := range drafts {
			confidence := 0.0
			if d.Confidence.Valid {
				fmt.Sscanf(d.Confidence.String, "%f", &confidence)
			}
			response[i] = DraftResponse{
				ID:         d.ID.String(),
				CampaignID: d.CampaignID.String(),
				Platform:   d.Platform,
				PostType:   d.PostType,
				Hook:       d.Hook.String,
				Caption:    d.Caption.String,
				Hashtags:   d.Hashtags,
				CTA:        d.Cta.String,
				Confidence: confidence,
				Status:     d.Status,
			}
		}

		c.JSON(http.StatusOK, gin.H{"drafts": response})
	}
}

// IngestMetricsHandler stores performance snapshots
func IngestMetricsHandler(queries *db.Queries) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req IngestMetricsRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		var draftID uuid.NullUUID
		if req.DraftID != nil {
			parsed, err := uuid.Parse(*req.DraftID)
			if err == nil {
				draftID = uuid.NullUUID{UUID: parsed, Valid: true}
			}
		}

		var capturedAt sql.NullTime
		if req.CapturedAt != nil {
			capturedAt = sql.NullTime{Time: *req.CapturedAt, Valid: true}
		}

		metric, err := queries.InsertPostMetrics(context.Background(), db.InsertPostMetricsParams{
			GroupID:    req.GroupID,
			Platform:   req.Platform,
			PostID:     req.PostID,
			DraftID:    draftID,
			Metrics:    req.Metrics,
			CapturedAt: capturedAt,
		})
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to store metrics: %v", err)})
			return
		}

		c.JSON(http.StatusCreated, metric)
	}
}

// GetCampaignInsightsHandler returns KPI summary and recommendations
func GetCampaignInsightsHandler(queries *db.Queries) gin.HandlerFunc {
	return func(c *gin.Context) {
		campaignID, err := uuid.Parse(c.Param("id"))
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid campaign ID"})
			return
		}

		// Get campaign to find group_id
		campaign, err := queries.GetCampaignByID(context.Background(), campaignID)
		if err != nil {
			c.JSON(http.StatusNotFound, gin.H{"error": "Campaign not found"})
			return
		}

		if !campaign.GroupID.Valid {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Campaign has no associated group"})
			return
		}

		groupID := campaign.GroupID.Int32
		windowStart := time.Now().AddDate(0, 0, -28)

		// Get metrics summary
		summary, err := queries.GetMetricsSummary(context.Background(), db.GetMetricsSummaryParams{
			GroupID:    groupID,
			CapturedAt: windowStart,
		})
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get metrics summary"})
			return
		}

		// Get best posting windows
		windows, _ := queries.GetBestPostingWindows(context.Background(), groupID)

		// Get top hook patterns
		hooks, _ := queries.GetTopHookPatterns(context.Background(), groupID)

		// Generate recommendations
		recommendations := generateRecommendations(summary, windows, hooks)

		response := InsightsResponse{
			Summary: MetricsSummary{
				TotalPosts:     summary.TotalPosts,
				AvgImpressions: summary.AvgImpressions,
				AvgEngagement:  summary.AvgEngagement,
				AvgLikes:       summary.AvgLikes,
				AvgComments:    summary.AvgComments,
				AvgShares:      summary.AvgShares,
			},
			BestPostingWindows: convertPostingWindows(windows),
			TopHookPatterns:    convertHookPatterns(hooks),
			Recommendations:    recommendations,
			DataWindowDays:     28,
		}

		c.JSON(http.StatusOK, response)
	}
}

// GetWizardOptionsHandler returns preset data for the campaign wizard
func GetWizardOptionsHandler() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"goals":     []string{"wishlist", "discord", "demo", "trailer", "awareness", "launch"},
			"audiences": AudienceArchetypes,
			"pillars":   ContentPillars,
			"platforms": []string{"instagram", "tiktok", "twitter", "youtube", "discord"},
		})
	}
}

// ==================== Helper Functions ====================

func validateDraftOutput(draft DraftOutput) error {
	if draft.Platform == "" {
		return fmt.Errorf("platform is required")
	}
	if draft.Caption == "" && draft.Hook == "" {
		return fmt.Errorf("either caption or hook is required")
	}
	if draft.Confidence < 0 || draft.Confidence > 1 {
		return fmt.Errorf("confidence must be between 0 and 1")
	}
	return nil
}

func generateStructuredDrafts(campaign db.Campaign, pillars []string, cadence CadenceConfig, filterPlatform string) []DraftOutput {
	var drafts []DraftOutput

	platforms := cadence.Platforms
	if filterPlatform != "" {
		platforms = []string{filterPlatform}
	}

	// Generate drafts based on posts per week and pillars
	postsPerWeek := cadence.PostsPerWeek
	if postsPerWeek <= 0 {
		postsPerWeek = 3
	}

	pillarIndex := 0
	for i := 0; i < postsPerWeek; i++ {
		for _, platform := range platforms {
			pillar := pillars[pillarIndex%len(pillars)]
			pillarIndex++

			draft := DraftOutput{
				Platform: platform,
				PostType: getPostTypeForPlatform(platform),
				Hook:     generateHookForPillar(pillar, campaign.Goal),
				Caption:  generateCaptionForPillar(pillar, campaign.Goal),
				Hashtags: generateHashtagsForPillar(pillar),
				CTA:      getCTAForGoal(campaign.Goal),
				RecommendedTimeWindow: TimeWindow{
					DayOfWeek: getDayForIndex(i),
					StartHour: 18,
					EndHour:   21,
					Timezone:  "UTC",
				},
				ReasonCodes: []string{
					fmt.Sprintf("pillar:%s", pillar),
					fmt.Sprintf("goal:%s", campaign.Goal),
				},
				Confidence: 0.75,
			}
			drafts = append(drafts, draft)
		}
	}

	return drafts
}

func getPostTypeForPlatform(platform string) string {
	switch platform {
	case "instagram":
		return "reel"
	case "tiktok":
		return "video"
	case "twitter":
		return "thread"
	case "youtube":
		return "short"
	default:
		return "standard"
	}
}

func generateHookForPillar(pillar, goal string) string {
	hooks := map[string]string{
		"Behind the Scenes":         "Ever wondered what goes into making a game?",
		"Gameplay Highlights":       "You won't believe this happened...",
		"Developer Diaries":         "From the desk of the dev team...",
		"Community Spotlight":       "Our amazing community strikes again!",
		"Tips & Tutorials":          "Here's a trick most players miss...",
		"Lore & Worldbuilding":      "The story behind the story...",
		"Announcements & Updates":   "Big news incoming...",
		"Memes & Humor":             "When you finally beat that boss...",
		"Fan Art & UGC":             "Look what our community created!",
		"Milestones & Celebrations": "We hit a major milestone!",
	}
	if hook, ok := hooks[pillar]; ok {
		return hook
	}
	return "Check this out..."
}

func generateCaptionForPillar(pillar, goal string) string {
	return fmt.Sprintf("Exploring %s - stay tuned for more updates! #gamedev #indiedev", pillar)
}

func generateHashtagsForPillar(pillar string) []string {
	base := []string{"gamedev", "indiedev", "gaming"}
	pillarTags := map[string][]string{
		"Behind the Scenes":   {"behindthescenes", "devlog", "gamedevlife"},
		"Gameplay Highlights": {"gameplay", "gamingclips", "epicmoments"},
		"Developer Diaries":   {"devlog", "indiegame", "gamedevelopment"},
		"Community Spotlight": {"community", "gamingcommunity", "thanksfollowing"},
		"Tips & Tutorials":    {"gamingtips", "tutorial", "howto"},
	}
	if tags, ok := pillarTags[pillar]; ok {
		return append(base, tags...)
	}
	return base
}

func getCTAForGoal(goal string) string {
	ctas := map[string]string{
		"wishlist":  "Add to your wishlist now!",
		"discord":   "Join our Discord community!",
		"demo":      "Play the free demo today!",
		"trailer":   "Watch the full trailer!",
		"awareness": "Follow for more updates!",
		"launch":    "Available now - get your copy!",
	}
	if cta, ok := ctas[goal]; ok {
		return cta
	}
	return "Learn more!"
}

func getDayForIndex(i int) string {
	days := []string{"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
	return days[i%len(days)]
}

func generateRecommendations(summary db.GetMetricsSummaryRow, windows []db.GetBestPostingWindowsRow, hooks []db.GetTopHookPatternsRow) []string {
	var recs []string

	if summary.TotalPosts < 10 {
		recs = append(recs, "Post more consistently to gather meaningful engagement data")
	}

	if len(windows) > 0 {
		recs = append(recs, fmt.Sprintf("Best posting time: Day %d at %d:00",
			windows[0].DayOfWeek, windows[0].HourOfDay))
	}

	if len(hooks) > 0 {
		recs = append(recs, fmt.Sprintf("Top performing hook style: \"%s\"", hooks[0].Hook.String))
	}

	if len(recs) == 0 {
		recs = append(recs, "Keep posting and check back for insights once you have more data")
	}

	return recs
}

func nullFloat64ToFloat(v interface{}) float64 {
	if v == nil {
		return 0
	}
	if f, ok := v.(float64); ok {
		return f
	}
	if s, ok := v.(string); ok {
		f, _ := strconv.ParseFloat(s, 64)
		return f
	}
	return 0
}

func convertPostingWindows(rows []db.GetBestPostingWindowsRow) []PostingWindow {
	var windows []PostingWindow
	for _, row := range rows {
		windows = append(windows, PostingWindow{
			DayOfWeek:     int(row.DayOfWeek),
			HourOfDay:     int(row.HourOfDay),
			AvgEngagement: row.AvgEngagement,
			SampleSize:    row.SampleSize,
		})
	}
	return windows
}

func convertHookPatterns(rows []db.GetTopHookPatternsRow) []HookPattern {
	var patterns []HookPattern
	for _, row := range rows {
		patterns = append(patterns, HookPattern{
			Hook:          row.Hook.String,
			AvgEngagement: row.AvgEngagement,
			UsageCount:    row.UsageCount,
		})
	}
	return patterns
}
