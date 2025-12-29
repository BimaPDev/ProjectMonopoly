// internal/handlers/marketing_prompt.go
package handlers

import (
	"bytes"
	"fmt"
	"math"
	"regexp"
	"sort"
	"strings"
	"text/template"
)

// DefaultDataWindowDays is the analytics window used consistently across UI/logs/prompt
const DefaultDataWindowDays = 14

// InternalMetaMarkers are strings that must never appear in user-facing output
// Case-insensitive matching is used during validation
var InternalMetaMarkers = []string{
	"REPAIR:",
	"VALIDATION",
	"INVALID OUTPUT",
	"DEBUG:",
	"PREVIOUS OUTPUT (INVALID)",
	"VIOLATIONS FOUND",
	"OFFENDING SNIPPETS",
	"OFFENDING LINES",
	"OFFENDING",
	"REGENERATION REQUIRED",
	"Removed:",
	"ERRORS:",
	"ISSUES FOUND",
	"BANNED TOKENS",
	"[REMOVED]",
	"Note:",
	"NOTE:",
	"PROBLEM LINES",
	"PROBLEMS:",
	"RULES:",
	"RETRY",
}

// RealHashtagRegex matches actual hashtags (starts with letter), not numbering like #2
// Format: #[a-z][a-z0-9_]* (case-insensitive)
var RealHashtagRegex = regexp.MustCompile(`(?i)#[a-z][a-z0-9_]*`)

// CTAPolicy defines how Call-to-Actions should be handled
type CTAPolicy string

const (
	CTAPolicyNone CTAPolicy = "none" // Strictly no CTAs
	CTAPolicySoft CTAPolicy = "soft" // Engagement-only (vote, comment, share)
	CTAPolicyHard CTAPolicy = "hard" // Sales/conversion allowed
)

// HashtagStoplist contains generic/noise hashtags that should be filtered out
var HashtagStoplist = map[string]bool{
	"fyp":             true,
	"foryou":          true,
	"foryoupage":      true,
	"viral":           true,
	"trending":        true,
	"explore":         true,
	"explorepage":     true,
	"cat":             true,
	"cats":            true,
	"dog":             true,
	"dogs":            true,
	"campfood":        true,
	"food":            true,
	"love":            true,
	"instagood":       true,
	"photooftheday":   true,
	"beautiful":       true,
	"happy":           true,
	"cute":            true,
	"follow":          true,
	"followme":        true,
	"like4like":       true,
	"likeforlike":     true,
	"followforfollow": true,
	"f4f":             true,
	"l4l":             true,
	"repost":          true,
	"daily":           true,
}

// LowConfidenceThreshold is the minimum posts needed for high-confidence recommendations
const LowConfidenceThreshold = 10

// MaxRecommendedPostsPerWeek caps posting frequency recommendations
const MaxRecommendedPostsPerWeek = 3

// MinRecommendedPostsPerWeek is the minimum posting frequency
const MinRecommendedPostsPerWeek = 1

// DefaultPostsPerWeek is used when no competitor data is available
const DefaultPostsPerWeek = 2

// MarketingPromptData holds all data for the marketing prompt template
type MarketingPromptData struct {
	GameName             string
	GameSummary          string
	BestDay              string  // Day name (e.g., "Wednesday")
	PostsPerWeek         float64 // Competitor cadence
	TimeHeuristic        string  // Platform-specific time advice
	TopCompetitorCaption string
	TopHashtags          []string // Pre-sanitized hashtags
	CampaignType         string
	Tone                 string
	Platform             string
	HasCompetitorData    bool

	// Fields for policy and audit
	CTAPolicy           CTAPolicy
	DataWindowDays      int
	CompetitorsAnalyzed int
	PostsAnalyzed       int
	MetricName          string // e.g. "Avg Likes"
	Confidence          string // "low" | "medium" | "high"

	// New fields for cadence guardrails and low-confidence handling
	RecommendedPostsPerWeek int  // Computed guardrail for strategy
	IsLowConfidence         bool // True if PostsAnalyzed < 10 or Confidence == "low"
}

// SanitizeHashtags preprocesses hashtags before including in prompts
// Steps: strip #, lowercase, dedupe, remove competitor handles, remove stoplist, cap to 5
func SanitizeHashtags(tags []string, competitorHandles []string) []string {
	seen := make(map[string]bool)
	competitorSet := make(map[string]bool)

	// Build competitor handle set (lowercase, without special chars)
	for _, handle := range competitorHandles {
		normalized := normalizeHashtag(handle)
		if normalized != "" {
			competitorSet[normalized] = true
			// Also add variants: e.g., "stickaround" -> "stickaroundgame"
			competitorSet[normalized+"game"] = true
			competitorSet[normalized+"official"] = true
		}
	}

	var result []string
	for _, tag := range tags {
		normalized := normalizeHashtag(tag)
		if normalized == "" {
			continue
		}

		// Skip if already seen
		if seen[normalized] {
			continue
		}
		seen[normalized] = true

		// Skip competitor-branded hashtags
		if isCompetitorBranded(normalized, competitorSet) {
			continue
		}

		// Skip stoplist hashtags
		if HashtagStoplist[normalized] {
			continue
		}

		result = append(result, normalized)

		// Cap to 5 hashtags
		if len(result) >= 5 {
			break
		}
	}

	return result
}

// normalizeHashtag strips # prefix, lowercases, and removes non-alphanumeric chars
func normalizeHashtag(tag string) string {
	tag = strings.TrimPrefix(tag, "#")
	tag = strings.ToLower(tag)
	// Remove non-alphanumeric characters except underscores
	reg := regexp.MustCompile(`[^a-z0-9_]`)
	tag = reg.ReplaceAllString(tag, "")
	return tag
}

// isCompetitorBranded checks if a hashtag is related to a competitor
func isCompetitorBranded(tag string, competitorSet map[string]bool) bool {
	// Direct match
	if competitorSet[tag] {
		return true
	}

	// Check if tag contains any competitor handle
	for handle := range competitorSet {
		if len(handle) >= 4 && strings.Contains(tag, handle) {
			return true
		}
	}

	return false
}

// ComputeRecommendedPostsPerWeek calculates the posting cadence guardrail
func ComputeRecommendedPostsPerWeek(competitorPostsPerWeek float64) int {
	if competitorPostsPerWeek <= 0 {
		return DefaultPostsPerWeek
	}

	// Ceiling of competitor cadence, clamped to [1, 3]
	recommended := int(math.Ceil(competitorPostsPerWeek))
	if recommended < MinRecommendedPostsPerWeek {
		recommended = MinRecommendedPostsPerWeek
	}
	if recommended > MaxRecommendedPostsPerWeek {
		recommended = MaxRecommendedPostsPerWeek
	}

	return recommended
}

// DetermineConfidence returns "low", "medium", or "high" based on sample size
func DetermineConfidence(postsAnalyzed int) string {
	if postsAnalyzed < LowConfidenceThreshold {
		return "low"
	}
	if postsAnalyzed < 20 {
		return "medium"
	}
	return "high"
}

// CampaignConstraints defines constraints per campaign type
var CampaignConstraints = map[string][]string{
	"Teaser": {
		"DO NOT use words like \"Download Now\", \"Launch\", \"Available Now\", or \"Buy\".",
		"Focus on mystery and intrigue - tease without revealing too much.",
		"End with a question or cliffhanger to drive engagement.",
	},
	"Launch": {
		"Include a clear call-to-action (Wishlist, Download, Buy).",
		"Highlight the key differentiator immediately.",
		"Create urgency without being pushy.",
	},
	"Update": {
		"Lead with the most exciting change.",
		"Keep technical details minimal - focus on player impact.",
		"Thank the community for feedback if applicable.",
	},
	"Community": {
		"Be conversational and authentic.",
		"Ask questions to encourage engagement.",
		"Showcase user-generated content or player stories when possible.",
	},
}

// BaseMarketingPromptTemplate is the core template structure
// Clearly separates "Hard Data" (from analytics) from "Strategic Advice" (heuristics)
const BaseMarketingPromptTemplate = `Role: Social Media Manager for {{.GameName}}
Context: {{.GameSummary}}

{{if .HasCompetitorData -}}
HARD DATA (Last {{.DataWindowDays}} Days):
- Audit: {{.CompetitorsAnalyzed}} competitors, {{.PostsAnalyzed}} posts analyzed
- Metric: {{.MetricName}} (Confidence: {{.Confidence}})
- Peak Engagement Day: {{.BestDay}}
- Competitor Cadence: {{printf "%.1f" .PostsPerWeek}} posts/week
{{if .TopCompetitorCaption}}- Top Performing Hook: "{{.TopCompetitorCaption}}"{{end}}
{{if .TopHashtags}}- Top Hashtags: {{range .TopHashtags}}#{{.}} {{end}}{{end}}
{{else -}}
HARD DATA: No competitor data available for the past {{.DataWindowDays}} days.
{{end}}

STRATEGIC ADVICE:
- Schedule this post for {{if .HasCompetitorData}}{{.BestDay}}{{else}}Tuesday or Wednesday{{end}}.
- Time Recommendation: {{.TimeHeuristic}} (industry best practice for {{.Platform}}).

TASK:
Write a {{.CampaignType}} post for {{.Platform}}.

CONSTRAINTS:
{{range $i, $constraint := .Constraints -}}
{{add $i 1}}. {{$constraint}}
{{end -}}
{{if .TopCompetitorCaption -}}
{{add (len .Constraints) 1}}. Study the competitor hook's tone and structure, then apply similar energy to OUR game's unique setting.
{{end}}

OUTPUT FORMAT:
1. **Hook** (first line - must stop the scroll)
2. **Body** (2-3 short sentences max)
{{if eq .CTAPolicy "none" -}}
3. **Engagement Question** (must end with '?')
{{else -}}
3. **Call-to-Action** ({{.CTAPolicy}} policy: {{if eq .CTAPolicy "soft"}}engagement only, no sales{{else}}sales allowed{{end}})
{{end -}}
4. **Hashtags** (3-5 relevant tags)
`

// MarketingPromptDataWithConstraints extends MarketingPromptData for template use
type MarketingPromptDataWithConstraints struct {
	MarketingPromptData
	Constraints []string
}

// BuildMarketingPrompt constructs the full system prompt for marketing generation
func BuildMarketingPrompt(data MarketingPromptData) (string, error) {
	// Get constraints for the campaign type
	constraints, ok := CampaignConstraints[data.CampaignType]
	if !ok {
		// Default constraints if campaign type not recognized
		constraints = []string{
			"Be authentic to the game's tone and style.",
			"Keep it concise and scroll-stopping.",
			"Be authentic to the game's tone and style.",
			"Keep it concise and scroll-stopping.",
		}
	}

	// Enforce strict policy constraints
	if data.CTAPolicy == CTAPolicyNone {
		constraints = append(constraints, "No CTA of any kind. No 'wishlist', 'link in bio', 'buy', etc.")
		constraints = append(constraints, "Only ask an engagement question.")
	} else if data.CTAPolicy == CTAPolicySoft {
		constraints = append(constraints, "Soft CTA only (e.g. 'follow', 'share', 'comment'). NO sales terms like 'buy' or 'wishlist'.")
	}

	// Create extended data with constraints
	extData := MarketingPromptDataWithConstraints{
		MarketingPromptData: data,
		Constraints:         constraints,
	}

	// Create template with custom functions
	funcMap := template.FuncMap{
		"add": func(a, b int) int { return a + b },
	}

	tmpl, err := template.New("marketing").Funcs(funcMap).Parse(BaseMarketingPromptTemplate)
	if err != nil {
		return "", fmt.Errorf("failed to parse template: %w", err)
	}

	var buf bytes.Buffer
	if err := tmpl.Execute(&buf, extData); err != nil {
		return "", fmt.Errorf("failed to execute template: %w", err)
	}

	return buf.String(), nil
}

// StrategyPromptConfig holds configuration for strategy prompt building
type StrategyPromptConfig struct {
	GameName                string
	GameSummary             string
	CampaignType            string
	CTAPolicy               CTAPolicy
	RecommendedPostsPerWeek int
	IsLowConfidence         bool
	PostsAnalyzed           int
	BestDay                 string
}

// BuildStrategySystemPrompt creates a concise system prompt for high-level strategy tasks
func BuildStrategySystemPrompt(config StrategyPromptConfig) string {
	var b strings.Builder
	b.WriteString("You are a senior social media strategist for indie games.\n\n")

	b.WriteString("PROJECT:\n")
	b.WriteString("Game: " + config.GameName + "\n")
	b.WriteString("Overview: " + config.GameSummary + "\n\n")

	b.WriteString("ABSOLUTE RULES (VIOLATIONS WILL CAUSE REJECTION):\n")
	b.WriteString("1) NEVER include URLs (http://, https://, www.) in your output.\n")
	b.WriteString("2) NEVER include image markdown syntax (![...] or ![](...)).\n")
	b.WriteString("3) NEVER recommend more than " + fmt.Sprintf("%d", config.RecommendedPostsPerWeek) + " posts per week.\n")
	b.WriteString("4) NEVER use competitor handles in any form: #competitor, @competitor, or the plain competitor name.\n")
	b.WriteString("5) NEVER include hashtags (#word) anywhere except the final 'Hashtag Pack' section.\n")
	b.WriteString("   - NO hashtags in Content Pillars\n")
	b.WriteString("   - NO hashtags in Posting Cadence\n")
	b.WriteString("   - NO hashtags in the 2-Week Schedule\n")
	b.WriteString("   - NO hashtags in Hook Ideas (hooks must be plain text)\n")
	b.WriteString("6) NEVER output meta-commentary like 'Note:', 'Removed:', 'REPAIR:', 'OFFENDING', or process descriptions.\n\n")
	b.WriteString("7) NEVER use placeholders or bracketed tokens.\n")
	b.WriteString("   - Do NOT use square brackets [] anywhere.\n")
	b.WriteString("   - Do NOT use tokens like: [content type], [Pillar 1], TBD, TODO, placeholder, fill in.\n")
	b.WriteString("   - Every schedule line must contain a real, specific content type label.\n\n")

	b.WriteString("GROUNDING RULES (QUALITY REQUIREMENTS):\n")
	b.WriteString("7) Do NOT invent game features, mechanics, characters, modes, events, rewards, contests, or \"facts\".\n")
	b.WriteString("   - If a detail is not explicitly provided in GAME CONTEXT, keep it generic or omit it.\n")
	b.WriteString("8) Do NOT make absolute gameplay claims (e.g., \"always\", \"guaranteed\", \"rigged\", \"won by players\").\n")
	b.WriteString("9) Competitor data is for strategy signals only. Do NOT copy competitor wording or distinctive phrases.\n\n")

	// Teaser-specific language rules
	if config.CampaignType == "Teaser" || config.CTAPolicy == CTAPolicyNone {
		b.WriteString("CAMPAIGN LANGUAGE:\n")
		b.WriteString("10) This is a TEASER campaign: focus on mystery/curiosity/anticipation, not sales.\n")
		b.WriteString("11) Avoid sales/availability phrasing: launch, release, out now, available, buy, wishlist, download, link in bio.\n")
		b.WriteString("    Use: kick off, start the series, teaser drop, first look.\n\n")
	}

	b.WriteString("OUTPUT REQUIREMENTS:\n")
	b.WriteString("- Structure output EXACTLY using the required format.\n")
	b.WriteString("- Include the EXACT line: PostsPerWeek: X\n")
	b.WriteString("- Schedule lines must be content types only (no quotes, no hashtags).\n")
	b.WriteString("- Hook Ideas must be plain text sentences/questions only (no hashtags).\n")
	b.WriteString("- Do NOT include square brackets [] anywhere.\n")
	b.WriteString("\nSCHEDULE LINE EXAMPLES (copy the pattern, not the wording):\n")
	b.WriteString("- Monday: Character customization spotlight (show 1 feature + ask 1 question)\n")
	b.WriteString("- Wednesday: Behind-the-scenes dev snippet (short clip concept)\n")
	b.WriteString("- Friday: Community prompt (player choice / poll / question)\n")

	// Low confidence handling
	if config.IsLowConfidence {
		b.WriteString("\nLOW CONFIDENCE MODE:\n")
		b.WriteString("- You MUST include: Confidence: low (sample size: " + fmt.Sprintf("%d", config.PostsAnalyzed) + " posts)\n")
		b.WriteString("- Present " + config.BestDay + " as an initial hypothesis, not a certainty.\n")
		b.WriteString("- You MUST include a 2-week A/B test plan with a primary metric.\n")
	}

	return b.String()
}

// StrategyOutputTemplate is the required structure for strategy outputs
const StrategyOutputTemplate = `
OUTPUT FORMAT (follow EXACTLY):

## Content Pillars
- Pillar 1: (write a real theme/topic from the GAME CONTEXT)
- Pillar 2: (write a real theme/topic from the GAME CONTEXT)
- Pillar 3: (write a real theme/topic from the GAME CONTEXT)

## Posting Cadence
PostsPerWeek: {{.RecommendedPostsPerWeek}}
Primary Day: (day name)
{{if .IsLowConfidence}}Confidence: low (sample size: {{.PostsAnalyzed}} posts){{end}}

## 2-Week Schedule
Week 1:
{{range $i, $day := .ScheduleDays}}- {{$day}}: (specific content type label, no brackets, no hashtags)
{{end}}
Week 2:
{{range $i, $day := .ScheduleDays}}- {{$day}}: (specific content type label, no brackets, no hashtags)
{{end}}
{{if .IsLowConfidence}}
## A/B Test Plan
- Test Variable: Posting day ({{.BestDay}} vs a second day)
- Duration: 2 weeks
- Primary Metric: engagement rate (choose one)
- Decision Criteria: define the winner clearly
{{end}}
## Hook Ideas (5 one-liners)
1. (hook line 1)
2. (hook line 2)
3. (hook line 3)
4. (hook line 4)
5. (hook line 5)

## Hashtag Pack (1-5 tags, NO competitor tags)
#gamedev #indiegame
`

// BuildScriptWritingSystemPrompt creates a detailed system prompt for content creation
func BuildScriptWritingSystemPrompt(gameName string) string {
	var b strings.Builder
	b.WriteString("You are a creative content writer specializing in gaming social media.\n")
	b.WriteString("You're creating content for: " + gameName + "\n\n")
	b.WriteString("RULES:\n")
	b.WriteString("- Use the provided game documents to ensure accuracy.\n")
	b.WriteString("- Match the game's established tone and terminology.\n")
	b.WriteString("- Cite specific game features when relevant.\n")
	b.WriteString("- Output should be ready-to-post with minimal editing.\n")
	return b.String()
}

// BannedConversionTerms for Strategy mode (strict conversion only)
var BannedConversionTerms = []string{
	"wishlist", "steam", "store page", "link in bio", "buy now", "purchase now", "get it now",
}

// BannedPostTerms for Post mode (broader, but "launch"/"sale" removed to reduce false positives)
var BannedPostTerms = []string{
	"wishlist", "steam", "store page", "link in bio", "buy", "purchase",
	"download", "out now", "available now", "preorder", "get it now",
}

// ================================================================================
// COMPLETENESS + GROUNDING (ANTI-PLACEHOLDER / ANTI-GENERIC) VALIDATION
// ================================================================================

// PlaceholderMarkers are patterns that must never appear in final user-visible output.
// NOTE: These are intentionally broad; the model must output real content, not templates.
var PlaceholderMarkers = []string{
	"[content type]",
	"[pillar",
	"tbd",
	"todo",
	"fill in",
	"placeholder",
	"coming soon: [",
	"[day]",
	"[n]",
}

// BracketTokenRegex matches any square-bracket token like "[something]".
var BracketTokenRegex = regexp.MustCompile(`\[[^\]\n]{1,80}\]`)

// ContentTypeAnchors are minimal "content type" signals used to ensure schedule lines are meaningful.
// These are deliberately broad (to avoid brittleness) but prevent empty/generic placeholders.
var ContentTypeAnchors = []string{
	"character customization",
	"customization spotlight",
	"character spotlight",
	"mini-game",
	"minigame",
	"behind-the-scenes",
	"behind the scenes",
	"setting tease",
	"gameplay clip",
	"clip concept",
	"community prompt",
	"dev snippet",
	"mechanic tease",
	"mechanic spotlight",
	"feature reveal",
	"reveal",
	"spotlight",
	"bts",
	"prompt",
	"snippet",
	"tease",
}

// CheckPlaceholderViolations flags template-like output, including square-bracket tokens.
// Returns PLACEHOLDER_VIOLATION with offending lines.
func CheckPlaceholderViolations(output string) (bool, string) {
	lines := strings.Split(output, "\n")
	var offenders []string

	for i, line := range lines {
		trimmed := strings.TrimSpace(line)
		if trimmed == "" {
			continue
		}
		lower := strings.ToLower(trimmed)

		// Explicit markers
		for _, marker := range PlaceholderMarkers {
			if strings.Contains(lower, marker) {
				offenders = append(offenders, fmt.Sprintf("Line %d: %s", i+1, truncateForError(trimmed, 120)))
				break
			}
		}

		// Any [token] anywhere is considered placeholder leakage
		if BracketTokenRegex.MatchString(trimmed) {
			offenders = append(offenders, fmt.Sprintf("Line %d: %s", i+1, truncateForError(trimmed, 120)))
			continue
		}
	}

	if len(offenders) > 0 {
		// Cap to reduce token bloat in repair prompt
		if len(offenders) > 5 {
			offenders = offenders[:5]
		}
		return false, "PLACEHOLDER_VIOLATION: Output contains placeholders/template tokens. " + strings.Join(offenders, " | ")
	}

	return true, ""
}

// CheckScheduleLineQuality validates schedule entries are meaningful and complete.
// Rules:
// - No square brackets on schedule lines
// - Content after "- Day:" must be >= 12 characters
// - Must include at least one content-type anchor
func CheckScheduleLineQuality(output string) (bool, string) {
	lines := strings.Split(output, "\n")
	inSchedule := false
	scheduleEndMarkers := []string{"## hook", "## hashtag", "## a/b", "## content type", "##hook", "##hashtag"}

	for i, line := range lines {
		lowerLine := strings.ToLower(strings.TrimSpace(line))
		trimmed := strings.TrimSpace(line)

		// Detect schedule section start
		if strings.Contains(lowerLine, "2-week schedule") ||
			strings.Contains(lowerLine, "## schedule") ||
			strings.HasPrefix(lowerLine, "week 1:") {
			inSchedule = true
			continue
		}

		// Detect schedule section end
		if inSchedule {
			for _, marker := range scheduleEndMarkers {
				if strings.Contains(lowerLine, marker) {
					inSchedule = false
					break
				}
			}
			if strings.HasPrefix(lowerLine, "## ") && !strings.Contains(lowerLine, "schedule") {
				inSchedule = false
			}
		}

		if !inSchedule {
			continue
		}

		// Only validate bullet schedule lines
		if !strings.HasPrefix(trimmed, "- ") || !strings.Contains(trimmed, ":") {
			continue
		}

		// No brackets on schedule lines
		if strings.Contains(trimmed, "[") || strings.Contains(trimmed, "]") || BracketTokenRegex.MatchString(trimmed) {
			return false, fmt.Sprintf("SCHEDULE_INCOMPLETE_VIOLATION: Line %d contains brackets, which are not allowed in schedule lines: '%s'",
				i+1, truncateForError(trimmed, 100))
		}

		parts := strings.SplitN(strings.TrimPrefix(trimmed, "- "), ":", 2)
		if len(parts) < 2 {
			continue
		}
		afterColon := strings.TrimSpace(parts[1])
		if len(afterColon) < 12 {
			return false, fmt.Sprintf("SCHEDULE_INCOMPLETE_VIOLATION: Line %d schedule entry is too short (need >= 12 chars after day): '%s'",
				i+1, truncateForError(trimmed, 100))
		}

		afterLower := strings.ToLower(afterColon)
		foundAnchor := false
		for _, anchor := range ContentTypeAnchors {
			if strings.Contains(afterLower, anchor) {
				foundAnchor = true
				break
			}
		}
		if !foundAnchor {
			return false, fmt.Sprintf("SCHEDULE_INCOMPLETE_VIOLATION: Line %d schedule entry lacks a specific content-type label: '%s'",
				i+1, truncateForError(trimmed, 120))
		}
	}

	return true, ""
}

// GenericKeywordStoplist removes ultra-generic tokens that would make the generic-output check meaningless.
var GenericKeywordStoplist = map[string]struct{}{
	"game":    {},
	"games":   {},
	"gaming":  {},
	"play":    {},
	"player":  {},
	"players": {},
	"fun":     {},
	"social":  {},
}

// CheckGenericOutput requires at least minHits context keyword hits across the output (excluding Hashtag Pack).
// This prevents strategies that could apply to any game.
func CheckGenericOutput(output string, contextKeywords map[string]struct{}, minHits int) (bool, string) {
	if minHits <= 0 {
		minHits = 3
	}
	if len(contextKeywords) == 0 {
		return true, ""
	}

	text := strings.ToLower(extractTextExcludingHashtagPack(output))
	if strings.TrimSpace(text) == "" {
		return false, "GENERIC_OUTPUT_VIOLATION: Output is empty or only contains Hashtag Pack"
	}

	seenHits := make(map[string]struct{})
	for kw := range contextKeywords {
		kw = strings.ToLower(strings.TrimSpace(kw))
		if len(kw) < 3 {
			continue
		}
		if _, blocked := GenericKeywordStoplist[kw]; blocked {
			continue
		}

		// Boundary-ish match to avoid substring noise (handles hyphens reasonably)
		pat := regexp.MustCompile(`(?i)(?:^|[^a-z0-9])` + regexp.QuoteMeta(kw) + `(?:$|[^a-z0-9])`)
		if pat.FindStringIndex(text) != nil {
			seenHits[kw] = struct{}{}
			if len(seenHits) >= minHits {
				return true, ""
			}
		}
	}

	return false, fmt.Sprintf("GENERIC_OUTPUT_VIOLATION: Output is too generic (requires >= %d context keyword hits outside Hashtag Pack; got %d)",
		minHits, len(seenHits))
}

// extractTextExcludingHashtagPack returns output text excluding the Hashtag Pack section.
func extractTextExcludingHashtagPack(output string) string {
	lines := strings.Split(output, "\n")
	inHashtagPack := false
	var kept []string

	for _, line := range lines {
		lowerLine := strings.ToLower(strings.TrimSpace(line))

		// Detect Hashtag Pack header
		isPackHeader := false
		for _, header := range HashtagPackHeaders {
			if strings.Contains(lowerLine, header) || strings.HasPrefix(lowerLine, header) {
				isPackHeader = true
				break
			}
		}
		if isPackHeader {
			inHashtagPack = true
			continue
		}

		// Stop skipping on next section header
		if inHashtagPack && (strings.HasPrefix(lowerLine, "## ") || strings.HasPrefix(lowerLine, "# ")) {
			inHashtagPack = false
		}

		if inHashtagPack {
			continue
		}
		kept = append(kept, line)
	}

	return strings.Join(kept, "\n")
}

// StrategyValidationConfig holds parameters for strategy validation
type StrategyValidationConfig struct {
	Policy                  CTAPolicy
	RecommendedPostsPerWeek int
	IsLowConfidence         bool
	CampaignType            string
	CompetitorHandles       []string
	// New fields for deterministic hashtag validation
	AllowedHashtags        []string // Observed + allowed hashtags (plain tokens, no #)
	SelfBrandHashtags      []string // User's own brand hashtags (optional)
	EnableSelfBrand        bool     // Whether to allow self-brand hashtags
	ContextDerivedHashtags []string // Context-derived hashtags (optional, curated)
	EnableContextHashtags  bool     // Whether to allow context-derived hashtags
	// New fields for grounding validation
	ContextKeywords map[string]struct{} // Keywords from RAG context for grounding
}

// ValidateStrategyOutput checks strategy content with comprehensive guardrails
func ValidateStrategyOutput(output string, policy CTAPolicy) (bool, []string) {
	// Use default config for backward compatibility
	return ValidateStrategyOutputWithConfig(output, StrategyValidationConfig{
		Policy:                  policy,
		RecommendedPostsPerWeek: MaxRecommendedPostsPerWeek,
		IsLowConfidence:         false,
		CampaignType:            "",
		CompetitorHandles:       nil,
	})
}

// ValidateStrategyOutputWithConfig performs comprehensive strategy validation
func ValidateStrategyOutputWithConfig(output string, config StrategyValidationConfig) (bool, []string) {
	var issues []string
	lowerOutput := strings.ToLower(output)

	// 0. Check for internal meta markers (REPAIR:, DEBUG:, etc.) - HIGHEST PRIORITY
	if metaOk, metaIssue := CheckInternalMetaViolation(output); !metaOk {
		issues = append(issues, metaIssue)
	}

	// 0.5 Completeness check: placeholders/template tokens (must run before any auto-normalization decision)
	if ok, issue := CheckPlaceholderViolations(output); !ok {
		issues = append(issues, issue)
	}

	// 0.6 Schedule quality check (must be meaningful; no brackets; no placeholders)
	if ok, issue := CheckScheduleLineQuality(output); !ok {
		issues = append(issues, issue)
	}

	// 1. Block URLs (http://, https://, www.)
	if strings.Contains(lowerOutput, "http://") ||
		strings.Contains(lowerOutput, "https://") ||
		strings.Contains(lowerOutput, "www.") {
		issues = append(issues, "URL_VIOLATION: Output contains URLs which are not allowed")
	}

	// 2. Block markdown image syntax
	if strings.Contains(output, "![") || strings.Contains(output, "](http") {
		issues = append(issues, "IMAGE_MARKDOWN_VIOLATION: Output contains image markdown syntax")
	}

	// 3. Check banned conversion terms for None/Soft policies
	if config.Policy == CTAPolicyNone || config.Policy == CTAPolicySoft {
		for _, term := range BannedConversionTerms {
			if strings.Contains(lowerOutput, term) {
				issues = append(issues, fmt.Sprintf("POLICY_VIOLATION: Found banned conversion term '%s' (policy: %s)", term, config.Policy))
			}
		}
	}

	// 4. Strict checks for None policy (CTA phrasing)
	if config.Policy == CTAPolicyNone {
		if strings.Contains(lowerOutput, "call to action") ||
			strings.Contains(lowerOutput, "link in bio") {
			issues = append(issues, "POLICY_VIOLATION: Found CTA phrasing in NO_CTA policy")
		}
	}

	// 5. Teaser language check - avoid "launch" in CTA contexts
	if config.CampaignType == "Teaser" || config.Policy == CTAPolicyNone {
		launchPatterns := []string{
			"launch now",
			"launching on",
			"launch date",
			"at launch",
			"day one",
			"release day",
		}
		for _, pattern := range launchPatterns {
			if strings.Contains(lowerOutput, pattern) {
				issues = append(issues, fmt.Sprintf("TEASER_LANGUAGE_VIOLATION: Found launch phrasing '%s' in teaser campaign", pattern))
			}
		}
	}

	// 6. Cadence compliance check
	cadenceOk, cadenceIssue := validateCadence(output, config.RecommendedPostsPerWeek)
	if !cadenceOk && cadenceIssue != "" {
		issues = append(issues, cadenceIssue)
	}

	// 7. Enhanced competitor handle blocking (#handle, @handle, plain handle)
	handleIssues := CheckCompetitorHandleViolations(output, config.CompetitorHandles)
	issues = append(issues, handleIssues...)

	// 8. Hashtag placement check - no real hashtags in schedule section
	if hashtagOk, hashtagIssue := CheckHashtagsInSchedule(output); !hashtagOk {
		issues = append(issues, hashtagIssue)
	}

	// 9. Hashtag placement check - hashtags only in Hashtag Pack (checks all sections)
	if hashtagPackOk, hashtagPackIssue := CheckHashtagsOutsidePack(output); !hashtagPackOk {
		issues = append(issues, hashtagPackIssue)
	}

	// 10. Low confidence mode check
	if config.IsLowConfidence {
		if !strings.Contains(lowerOutput, "confidence") {
			issues = append(issues, "LOW_CONFIDENCE_VIOLATION: Low-confidence output must include confidence statement")
		}
		if !strings.Contains(lowerOutput, "a/b") && !strings.Contains(lowerOutput, "test plan") && !strings.Contains(lowerOutput, "test variable") {
			issues = append(issues, "LOW_CONFIDENCE_VIOLATION: Low-confidence output must include A/B test plan")
		}
	}

	// 11. Teaser availability/CTA language check (extended)
	if config.CampaignType == "Teaser" || config.Policy == CTAPolicyNone {
		if teaserOk, teaserIssue := CheckTeaserAvailabilityLanguage(output); !teaserOk {
			issues = append(issues, teaserIssue)
		}
	}

	// 12. Hashtag Pack membership check - only allowed tags
	if len(config.AllowedHashtags) > 0 {
		allowedSet := BuildAllowedHashtagSet(
			config.AllowedHashtags,
			config.SelfBrandHashtags,
			config.EnableSelfBrand,
			config.ContextDerivedHashtags,
			config.EnableContextHashtags,
			config.CompetitorHandles,
		)
		if packOk, packIssue := CheckHashtagPackMembership(output, allowedSet, config.CompetitorHandles); !packOk {
			issues = append(issues, packIssue)
		}
	}

	// 13. Grounding check - detect unverifiable factual claims
	if len(config.ContextKeywords) > 0 {
		if groundedOk, groundedIssue := CheckUngroundedFeatureClaims(output, config.ContextKeywords); !groundedOk {
			issues = append(issues, groundedIssue)
		}
	}

	// 14. Generic output check - require context keyword hits (lightweight grounding)
	if len(config.ContextKeywords) > 0 {
		if ok, issue := CheckGenericOutput(output, config.ContextKeywords, 3); !ok {
			issues = append(issues, issue)
		}
	}

	return len(issues) == 0, issues
}

// validateCadence checks if the recommended posts per week is within bounds
func validateCadence(output string, maxPostsPerWeek int) (bool, string) {
	lowerOutput := strings.ToLower(output)

	// Look for explicit "PostsPerWeek: X" pattern
	postsPerWeekRegex := regexp.MustCompile(`postsperweek:\s*(\d+)`)
	matches := postsPerWeekRegex.FindStringSubmatch(lowerOutput)
	if len(matches) >= 2 {
		var postsPerWeek int
		fmt.Sscanf(matches[1], "%d", &postsPerWeek)
		if postsPerWeek > maxPostsPerWeek {
			return false, fmt.Sprintf("CADENCE_VIOLATION: Recommended %d posts/week exceeds maximum of %d", postsPerWeek, maxPostsPerWeek)
		}
		return true, ""
	}

	// Heuristic: count weekday mentions that look like scheduling
	weekdays := []string{"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
	scheduledDays := 0
	for _, day := range weekdays {
		// Look for patterns like "Monday: post" or "post on Monday"
		if strings.Contains(lowerOutput, day+":") || strings.Contains(lowerOutput, "on "+day) {
			scheduledDays++
		}
	}

	// If more than 7 scheduled mentions per week pattern detected
	if scheduledDays > maxPostsPerWeek*2 { // Allow some flexibility
		return false, fmt.Sprintf("CADENCE_VIOLATION: Schedule appears to exceed %d posts/week", maxPostsPerWeek)
	}

	// Also check for "daily" or "every day" patterns
	if strings.Contains(lowerOutput, "daily post") ||
		strings.Contains(lowerOutput, "post daily") ||
		strings.Contains(lowerOutput, "every day") ||
		strings.Contains(lowerOutput, "7 days a week") {
		if maxPostsPerWeek < 7 {
			return false, fmt.Sprintf("CADENCE_VIOLATION: 'Daily posting' exceeds recommended %d posts/week", maxPostsPerWeek)
		}
	}

	return true, ""
}

// ValidatePostOutput checks post content (strict structure + punctuation + terms)
func ValidatePostOutput(output string, policy CTAPolicy) (bool, []string) {
	var issues []string
	lowerOutput := strings.ToLower(output)

	// 1. Check banned terms for None/Soft policies
	if policy == CTAPolicyNone || policy == CTAPolicySoft {
		for _, term := range BannedPostTerms {
			if strings.Contains(lowerOutput, term) {
				issues = append(issues, fmt.Sprintf("POLICY_VIOLATION: Found banned sales term '%s' (policy: %s)", term, policy))
			}
		}
	}

	// 2. Strict checks for None policy
	if policy == CTAPolicyNone {
		if strings.Contains(lowerOutput, "call to action") ||
			strings.Contains(lowerOutput, "follow us") ||
			strings.Contains(lowerOutput, "follow for more") {
			issues = append(issues, "POLICY_VIOLATION: Found CTA phrasing in NO_CTA policy")
		}

		// Must have a question mark (engagement)
		if !strings.Contains(output, "?") {
			issues = append(issues, "MISSING_ENGAGEMENT_QUESTION: Output must contain a question mark to drive engagement without CTAs")
		}
	}

	// 3. Basic structure checks
	if !strings.Contains(lowerOutput, "hook") && !strings.Contains(output, "\n\n") {
		issues = append(issues, "STRUCTURE_ERROR: Output appears unstructured (missing sections)")
	}

	// 4. Hashtag check
	if strings.Count(output, "#") < 2 {
		issues = append(issues, "HASHTAG_ERROR: Too few hashtags found (min 2)")
	}

	return len(issues) == 0, issues
}

// TruncateHook safely truncates a hook to a maximum length (rune-safe)
func TruncateHook(hook string, maxLen int) string {
	runes := []rune(hook)
	if len(runes) <= maxLen {
		return hook
	}

	// Truncate to max rune length
	truncatedRunes := runes[:maxLen]

	// Find last space within the last 50 runes to avoid cutting in middle of word
	lastSpace := -1
	for i := len(truncatedRunes) - 1; i >= 0; i-- {
		if truncatedRunes[i] == ' ' {
			lastSpace = i
			break
		}
	}

	// Only cut at space if it's not too far back (e.g., within last 50 chars)
	if lastSpace != -1 && (len(truncatedRunes)-lastSpace) < 50 {
		truncatedRunes = truncatedRunes[:lastSpace]
	}

	return string(truncatedRunes) + "..."
}

// ================================================================================
// OUTPUT HYGIENE: Strip internal meta markers from output
// ================================================================================

// StripInternalMeta removes internal debugging/meta content from output
// Truncates at common internal marker prefixes like "\nREPAIR:", "\nDEBUG:", etc.
func StripInternalMeta(output string) string {
	// Markers that indicate start of meta content - truncate at first match
	markers := []string{
		"\nREPAIR:",
		"\nDEBUG:",
		"\nVALIDATION",
		"\nINVALID OUTPUT",
		"\nPREVIOUS OUTPUT",
		"\nVIOLATIONS FOUND",
		"\nOFFENDING SNIPPETS",
		"\nOFFENDING LINES",
		"\nOFFENDING",
		"\nREGENERATION REQUIRED",
		"\nRemoved:",
		"\nERRORS:",
		"\nISSUES FOUND",
		"\nBANNED TOKENS",
		"\n[REMOVED]",
		"\n---\nERRORS",   // Common separator format
		"\n---\nISSUES",   // Common separator format
		"\n\nNote:",       // AI often adds notes
		"\n*Note:",        // Markdown note format
		"\nNote:",         // Simple note
		"\nNOTE:",         // Uppercase note
		"\nPROBLEM LINES", // Repair prompt leakage
		"\nPROBLEMS:",     // Repair prompt leakage
		"\nRULES:",        // Repair prompt leakage
		"\nRETRY",         // Repair prompt leakage
	}

	result := output
	for _, marker := range markers {
		// Case-insensitive search
		lowerResult := strings.ToLower(result)
		lowerMarker := strings.ToLower(marker)
		if idx := strings.Index(lowerResult, lowerMarker); idx != -1 {
			result = result[:idx]
		}
	}

	return strings.TrimSpace(result)
}

// ContainsInternalMeta checks if output contains any internal meta markers
func ContainsInternalMeta(output string) bool {
	upperOutput := strings.ToUpper(output)
	for _, marker := range InternalMetaMarkers {
		if strings.Contains(upperOutput, strings.ToUpper(marker)) {
			return true
		}
	}
	return false
}

// ================================================================================
// MINIMAL REPAIR CONTEXT: Build compact regeneration prompts
// ================================================================================

// ViolationSnippet represents an offending line with context
type ViolationSnippet struct {
	LineNum int
	Content string
	Issue   string
}

// ExtractViolatingSnippets finds lines containing violations for minimal repair context
// Returns up to maxSnippets lines that contain violating tokens
func ExtractViolatingSnippets(output string, issues []string, competitorHandles []string, maxSnippets int, maxChars int) []ViolationSnippet {
	if maxSnippets <= 0 {
		maxSnippets = 5
	}
	if maxChars <= 0 {
		maxChars = 800
	}

	lines := strings.Split(output, "\n")
	var snippets []ViolationSnippet
	totalChars := 0

	// Build violation patterns to search for
	violationPatterns := []struct {
		pattern string
		issue   string
	}{
		{"http://", "URL_VIOLATION"},
		{"https://", "URL_VIOLATION"},
		{"www.", "URL_VIOLATION"},
		{"![", "IMAGE_MARKDOWN_VIOLATION"},
		{"repair:", "INTERNAL_META_VIOLATION"},
		{"debug:", "INTERNAL_META_VIOLATION"},
		{"validation", "INTERNAL_META_VIOLATION"},
		{"invalid output", "INTERNAL_META_VIOLATION"},
	}

	// Add competitor handles as patterns
	for _, handle := range competitorHandles {
		normalized := strings.ToLower(handle)
		if normalized != "" {
			violationPatterns = append(violationPatterns, struct {
				pattern string
				issue   string
			}{"#" + normalized, "COMPETITOR_HANDLE_VIOLATION"})
			violationPatterns = append(violationPatterns, struct {
				pattern string
				issue   string
			}{"@" + normalized, "COMPETITOR_HANDLE_VIOLATION"})
		}
	}

	for lineNum, line := range lines {
		if len(snippets) >= maxSnippets || totalChars >= maxChars {
			break
		}

		lowerLine := strings.ToLower(line)
		for _, vp := range violationPatterns {
			if strings.Contains(lowerLine, vp.pattern) {
				// Truncate long lines
				content := line
				if len(content) > 150 {
					content = content[:150] + "..."
				}
				snippets = append(snippets, ViolationSnippet{
					LineNum: lineNum + 1,
					Content: content,
					Issue:   vp.issue,
				})
				totalChars += len(content)
				break // Only add each line once
			}
		}
	}

	// Also check for hashtags in schedule section
	inSchedule := false
	for lineNum, line := range lines {
		if len(snippets) >= maxSnippets || totalChars >= maxChars {
			break
		}

		lowerLine := strings.ToLower(line)
		if strings.Contains(lowerLine, "2-week schedule") || strings.Contains(lowerLine, "## schedule") {
			inSchedule = true
			continue
		}
		if inSchedule && (strings.HasPrefix(lowerLine, "## ") || strings.HasPrefix(lowerLine, "# ")) {
			inSchedule = false
		}

		if inSchedule && strings.Contains(line, "#") && !strings.HasPrefix(strings.TrimSpace(line), "##") {
			// Check if it's not a markdown heading
			content := line
			if len(content) > 150 {
				content = content[:150] + "..."
			}
			// Avoid duplicates
			alreadyAdded := false
			for _, s := range snippets {
				if s.LineNum == lineNum+1 {
					alreadyAdded = true
					break
				}
			}
			if !alreadyAdded {
				snippets = append(snippets, ViolationSnippet{
					LineNum: lineNum + 1,
					Content: content,
					Issue:   "HASHTAGS_IN_SCHEDULE_VIOLATION",
				})
				totalChars += len(content)
			}
		}
	}

	return snippets
}

// BuildMinimalRepairPrompt constructs a compact prompt for regeneration
// Uses only violating snippets instead of the entire previous output
// IMPORTANT: Avoids using words that the model might echo (OFFENDING, REMOVED, VIOLATIONS, etc.)
func BuildMinimalRepairPrompt(originalPrompt string, issues []string, snippets []ViolationSnippet, bannedTokens []string) string {
	var b strings.Builder

	b.WriteString("RETRY - generate a clean version.\n\n")

	b.WriteString("PROBLEMS:\n")
	for _, issue := range issues {
		// Strip verbose details, keep just the violation type - but clean it up
		shortIssue := issue
		if colonIdx := strings.Index(issue, ":"); colonIdx != -1 && colonIdx < 40 {
			shortIssue = issue[:colonIdx]
		}
		// Make it more concise and neutral (no meta-teaching words)
		shortIssue = strings.ReplaceAll(shortIssue, "_VIOLATION", "")
		shortIssue = strings.ReplaceAll(shortIssue, "VIOLATION", "")
		shortIssue = strings.ReplaceAll(shortIssue, "OFFENDING", "")
		b.WriteString(fmt.Sprintf("- %s\n", shortIssue))
	}

	if len(snippets) > 0 {
		b.WriteString("\nEXAMPLES (do not copy):\n")
		for _, s := range snippets {
			b.WriteString(fmt.Sprintf("  Line %d: %s\n", s.LineNum, s.Content))
		}
	}

	if len(bannedTokens) > 0 {
		b.WriteString("\nFORBIDDEN WORDS/TAGS:\n")
		for i, token := range bannedTokens {
			if i > 0 {
				b.WriteString(", ")
			}
			b.WriteString(token)
		}
		b.WriteString("\n")
	}

	b.WriteString("\nRULES:\n")
	b.WriteString("1. Generate the strategy from scratch.\n")
	b.WriteString("2. NO hashtags except in Hashtag Pack section at the end.\n")
	b.WriteString("3. NO competitor names or handles anywhere.\n")
	b.WriteString("4. NO URLs or image markdown.\n")
	b.WriteString("5. Do NOT copy competitor wording or hooks.\n")
	b.WriteString("6. Do NOT invent features or factual claims not in the provided context.\n")
	b.WriteString("7. Output ONLY the clean strategy. Do not include any meta commentary.\n")
	b.WriteString("8. NEVER use placeholders or bracketed tokens. Do NOT use square brackets [] anywhere.\n")

	// If placeholder/schedule issues exist, provide targeted repair instructions + examples
	upperIssues := strings.ToUpper(strings.Join(issues, " | "))
	if strings.Contains(upperIssues, "PLACEHOLDER") || strings.Contains(upperIssues, "SCHEDULE_INCOMPLETE") {
		b.WriteString("\nPLACEHOLDER/SCHEDULE FIX:\n")
		b.WriteString("- Replace every placeholder with a specific, real content type.\n")
		b.WriteString("- Do NOT include square brackets [] anywhere.\n")
		b.WriteString("- Every schedule line must be a real content type label (>= 12 characters after the day).\n")
		b.WriteString("\nVALID SCHEDULE LINE EXAMPLES (do not copy competitor wording; no hashtags):\n")
		b.WriteString("- Monday: Character customization spotlight (feature + question)\n")
		b.WriteString("- Wednesday: Behind-the-scenes dev snippet (clip concept)\n")
		b.WriteString("- Friday: Mechanic tease (1 mechanic + 1 player question)\n")
	}

	return b.String()
}

// BuildBannedTokensList creates a list of banned tokens from competitor handles
func BuildBannedTokensList(competitorHandles []string) []string {
	var tokens []string
	seen := make(map[string]bool)

	for _, handle := range competitorHandles {
		normalized := strings.ToLower(strings.TrimSpace(handle))
		if normalized == "" || len(normalized) < 3 {
			continue
		}

		// Add various forms of the handle
		forms := []string{
			normalized,
			"#" + normalized,
			"@" + normalized,
			normalized + "game",
			"#" + normalized + "game",
			"@" + normalized + "game",
		}

		for _, form := range forms {
			if !seen[form] {
				tokens = append(tokens, form)
				seen[form] = true
			}
		}
	}

	return tokens
}

// ================================================================================
// COMPETITOR HANDLE BLOCKING: Enhanced validation for #, @, and plain handles
// ================================================================================

// CheckCompetitorHandleViolations checks for competitor handles in various forms
// Returns violation issues for #handle, @handle, and plain " handle " (word-boundary)
func CheckCompetitorHandleViolations(output string, competitorHandles []string) []string {
	var issues []string
	lowerOutput := strings.ToLower(output)

	for _, handle := range competitorHandles {
		normalized := normalizeHashtag(handle)
		if normalized == "" || len(normalized) < 3 {
			continue
		}

		// Check #handle
		hashtagForm := "#" + normalized
		if strings.Contains(lowerOutput, hashtagForm) {
			issues = append(issues, fmt.Sprintf("COMPETITOR_HANDLE_VIOLATION: Output contains competitor hashtag '%s'", hashtagForm))
		}

		// Check @handle
		mentionForm := "@" + normalized
		if strings.Contains(lowerOutput, mentionForm) {
			issues = append(issues, fmt.Sprintf("COMPETITOR_HANDLE_VIOLATION: Output contains competitor mention '%s'", mentionForm))
		}

		// Check plain "handle" with word boundaries (space/punctuation before/after)
		// Use regex for word boundary matching to avoid partial matches
		wordBoundaryPattern := regexp.MustCompile(`(?i)(?:^|[\s\.,!?;:'"()\[\]{}])` + regexp.QuoteMeta(normalized) + `(?:[\s\.,!?;:'"()\[\]{}]|$)`)
		if wordBoundaryPattern.MatchString(output) {
			issues = append(issues, fmt.Sprintf("COMPETITOR_HANDLE_VIOLATION: Output contains competitor name '%s' as standalone word", normalized))
		}

		// Also check common variations
		variations := []string{
			normalized + "game",
			normalized + "official",
			normalized + "hq",
		}
		for _, variant := range variations {
			if strings.Contains(lowerOutput, "#"+variant) {
				issues = append(issues, fmt.Sprintf("COMPETITOR_HANDLE_VIOLATION: Output contains competitor hashtag variant '#%s'", variant))
			}
			if strings.Contains(lowerOutput, "@"+variant) {
				issues = append(issues, fmt.Sprintf("COMPETITOR_HANDLE_VIOLATION: Output contains competitor mention variant '@%s'", variant))
			}
		}
	}

	return issues
}

// ================================================================================
// HASHTAG PLACEMENT VALIDATION: Hashtags only in Hashtag Pack section
// ================================================================================

// CheckHashtagsInSchedule validates that real hashtags only appear in the Hashtag Pack section
// Uses RealHashtagRegex to match actual hashtags (#word), not numbering (#2, #3)
// Returns a violation if any real hashtag patterns are found in the 2-Week Schedule section
func CheckHashtagsInSchedule(output string) (bool, string) {
	lines := strings.Split(output, "\n")
	inSchedule := false
	scheduleEndMarkers := []string{"## hook", "## hashtag", "## a/b", "## content type", "##hook", "##hashtag"}

	for _, line := range lines {
		lowerLine := strings.ToLower(strings.TrimSpace(line))

		// Detect schedule section start
		if strings.Contains(lowerLine, "2-week schedule") ||
			strings.Contains(lowerLine, "## schedule") ||
			strings.HasPrefix(lowerLine, "week 1:") {
			inSchedule = true
			continue
		}

		// Detect schedule section end
		if inSchedule {
			for _, marker := range scheduleEndMarkers {
				if strings.HasPrefix(lowerLine, marker) {
					inSchedule = false
					break
				}
			}
			// Also end on any new major section
			if strings.HasPrefix(lowerLine, "## ") && !strings.Contains(lowerLine, "schedule") {
				inSchedule = false
			}
		}

		// Check for real hashtags in schedule section using regex
		if inSchedule {
			// Skip markdown headings (##, ###)
			trimmed := strings.TrimSpace(line)
			if strings.HasPrefix(trimmed, "##") || strings.HasPrefix(trimmed, "# ") {
				continue
			}
			// Skip Week headers
			if strings.HasPrefix(lowerLine, "week ") {
				continue
			}
			// Use regex to find real hashtags (not #2, #3 numbering)
			if matches := RealHashtagRegex.FindAllString(line, -1); len(matches) > 0 {
				return false, fmt.Sprintf("HASHTAGS_IN_SCHEDULE_VIOLATION: Schedule line contains hashtag '%s': '%s'", matches[0], truncateForError(line, 80))
			}
		}
	}

	return true, ""
}

// CheckHashtagsOutsidePack validates that hashtags appear ONLY in the Hashtag Pack section
// Checks Schedule, Hook Ideas, Content Pillars, and other sections
// Returns a violation if real hashtags are found outside Hashtag Pack
func CheckHashtagsOutsidePack(output string) (bool, string) {
	lines := strings.Split(output, "\n")
	currentSection := ""
	inHashtagPack := false

	for _, line := range lines {
		lowerLine := strings.ToLower(strings.TrimSpace(line))
		trimmed := strings.TrimSpace(line)

		// Track current section
		if strings.HasPrefix(lowerLine, "## ") || strings.HasPrefix(lowerLine, "# ") {
			currentSection = lowerLine
			inHashtagPack = strings.Contains(lowerLine, "hashtag pack") ||
				strings.Contains(lowerLine, "hashtags") ||
				strings.Contains(lowerLine, "## hashtag")
			continue
		}

		// Skip if we're in the hashtag pack section
		if inHashtagPack {
			continue
		}

		// Skip markdown headings
		if strings.HasPrefix(trimmed, "##") || strings.HasPrefix(trimmed, "# ") {
			continue
		}

		// Check for real hashtags using regex
		if matches := RealHashtagRegex.FindAllString(line, -1); len(matches) > 0 {
			sectionName := "unknown section"
			if strings.Contains(currentSection, "hook") {
				sectionName = "Hook Ideas"
			} else if strings.Contains(currentSection, "schedule") {
				sectionName = "Schedule"
			} else if strings.Contains(currentSection, "pillar") {
				sectionName = "Content Pillars"
			} else if strings.Contains(currentSection, "cadence") {
				sectionName = "Posting Cadence"
			} else if currentSection != "" {
				sectionName = currentSection
			}
			return false, fmt.Sprintf("HASHTAGS_OUTSIDE_PACK_VIOLATION: Found '%s' in %s (hashtags only allowed in Hashtag Pack)", matches[0], sectionName)
		}
	}

	return true, ""
}

// truncateForError safely truncates a string for error messages
func truncateForError(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen] + "..."
}

// ================================================================================
// INTERNAL META VALIDATION: Check for debugging/meta leakage
// ================================================================================

// CheckInternalMetaViolation validates that no internal meta markers appear in output
func CheckInternalMetaViolation(output string) (bool, string) {
	upperOutput := strings.ToUpper(output)
	for _, marker := range InternalMetaMarkers {
		if strings.Contains(upperOutput, strings.ToUpper(marker)) {
			return false, fmt.Sprintf("INTERNAL_META_VIOLATION: Output contains internal marker '%s'", marker)
		}
	}
	return true, ""
}

// ================================================================================
// HASHTAG NORMALIZATION: Remove hashtags from non-pack sections
// ================================================================================

// HashtagPackHeaders are the headers that identify the Hashtag Pack section
var HashtagPackHeaders = []string{
	"## hashtag pack",
	"## hashtags",
	"## hashtag",
	"hashtag pack:",
	"hashtags:",
}

// NormalizeStrategyHashtags removes real hashtags from all sections except the Hashtag Pack
// and ensures the Hashtag Pack section exists with valid hashtags.
// This allows automatic correction of hashtag placement issues without regeneration.
// CRITICAL: Lines containing competitor handles are NEVER modified - they are preserved
// so that validation will catch them and trigger regen/422.
func NormalizeStrategyHashtags(output string, allowedHashtags []string, competitorHandles []string) string {
	// Use the extended version with default self-brand settings
	return NormalizeStrategyHashtagsExtended(output, allowedHashtags, nil, false, nil, false, competitorHandles)
}

// NormalizeStrategyHashtagsExtended provides full control over hashtag normalization
// including self-brand hashtags and deterministic pack rebuilding
func NormalizeStrategyHashtagsExtended(output string, observedHashtags []string, selfBrandHashtags []string, enableSelfBrand bool, contextHashtags []string, enableContextHashtags bool, competitorHandles []string) string {
	lines := strings.Split(output, "\n")
	var result []string
	inHashtagPack := false

	// Build competitor handle set for checking (lowercase)
	competitorSet := buildCompetitorSet(competitorHandles)

	// First pass: remove hashtags from non-pack sections, skip pack content entirely
	for _, line := range lines {
		lowerLine := strings.ToLower(strings.TrimSpace(line))
		trimmed := strings.TrimSpace(line)

		// Check if this is the Hashtag Pack header
		isPackHeader := false
		for _, header := range HashtagPackHeaders {
			if strings.Contains(lowerLine, header) || strings.HasPrefix(lowerLine, header) {
				isPackHeader = true
				break
			}
		}

		if isPackHeader {
			inHashtagPack = true
			// Don't add the header yet - we'll rebuild the entire pack
			continue
		}

		// Check if we're leaving the Hashtag Pack section (new major header)
		if inHashtagPack && (strings.HasPrefix(lowerLine, "## ") || strings.HasPrefix(lowerLine, "# ")) {
			inHashtagPack = false
			result = append(result, line)
			continue
		}

		if inHashtagPack {
			// Skip all existing Hashtag Pack content - we'll rebuild it
			continue
		}

		// Non-pack content processing
		// Skip markdown headers (##, ###)
		if strings.HasPrefix(trimmed, "##") || strings.HasPrefix(trimmed, "# ") {
			result = append(result, line)
			continue
		}

		// CRITICAL: If line contains a competitor handle, DO NOT modify it
		// Leave it unchanged so validation will catch it
		if lineContainsCompetitorHandle(line, competitorSet) {
			result = append(result, line)
			continue
		}

		// Remove real hashtags but keep numbering like #2, #3
		cleanedLine := removeRealHashtags(line)
		result = append(result, cleanedLine)
	}

	output = strings.Join(result, "\n")

	// Build deterministic hashtag pack
	finalTags := BuildFinalHashtagPack(observedHashtags, selfBrandHashtags, enableSelfBrand, contextHashtags, enableContextHashtags, competitorHandles)
	if len(finalTags) < 3 {
		fmt.Printf("WARN: HASHTAG_PACK_UNDERFILLED: only %d tags (observed=%d selfBrand=%d context=%d)\n",
			len(finalTags), len(observedHashtags), len(selfBrandHashtags), len(contextHashtags))
	}

	// Replace or append the Hashtag Pack with deterministic tags
	output = ReplaceOrAppendHashtagPack(output, finalTags)

	return strings.TrimSpace(output)
}

// buildCompetitorSet creates a set of competitor handle patterns to check against
func buildCompetitorSet(competitorHandles []string) map[string]bool {
	set := make(map[string]bool)
	for _, handle := range competitorHandles {
		normalized := strings.ToLower(strings.TrimSpace(handle))
		if normalized == "" || len(normalized) < 3 {
			continue
		}
		// Add base handle and common variants
		set[normalized] = true
		set[normalized+"game"] = true
		set[normalized+"official"] = true
		set[normalized+"hq"] = true
	}
	return set
}

// lineContainsCompetitorHandle checks if a line contains any competitor handle in any form
// Checks for #handle, @handle, and plain handle (word boundary)
func lineContainsCompetitorHandle(line string, competitorSet map[string]bool) bool {
	lowerLine := strings.ToLower(line)

	for handle := range competitorSet {
		// Check #handle
		if strings.Contains(lowerLine, "#"+handle) {
			return true
		}
		// Check @handle
		if strings.Contains(lowerLine, "@"+handle) {
			return true
		}
		// Check plain handle with word boundaries (space/punctuation)
		// Simple check: if handle appears after space or at start, and before space/punctuation or at end
		patterns := []string{
			" " + handle + " ",
			" " + handle + ".",
			" " + handle + ",",
			" " + handle + "!",
			" " + handle + "?",
			" " + handle + "\n",
		}
		for _, pattern := range patterns {
			if strings.Contains(lowerLine, pattern) {
				return true
			}
		}
		// Check if line starts with handle
		if strings.HasPrefix(lowerLine, handle+" ") || strings.HasPrefix(lowerLine, handle+".") {
			return true
		}
		// Check if line ends with handle
		if strings.HasSuffix(lowerLine, " "+handle) {
			return true
		}
	}

	return false
}

// removeRealHashtags removes real hashtags (#word) from a line but preserves numbering (#2, #3)
func removeRealHashtags(line string) string {
	// Find all real hashtags
	matches := RealHashtagRegex.FindAllStringIndex(line, -1)
	if len(matches) == 0 {
		return line
	}

	// Remove matches from right to left to preserve indices
	result := line
	for i := len(matches) - 1; i >= 0; i-- {
		start := matches[i][0]
		end := matches[i][1]
		// Remove the hashtag
		result = result[:start] + result[end:]
	}

	// Clean up extra spaces
	result = cleanupSpaces(result)
	return result
}

// cleanupSpaces removes double spaces and trailing/leading spaces on list items
func cleanupSpaces(s string) string {
	// Replace multiple spaces with single space
	multiSpace := regexp.MustCompile(`\s{2,}`)
	s = multiSpace.ReplaceAllString(s, " ")

	// Trim trailing spaces
	s = strings.TrimRight(s, " ")

	// Clean up patterns like "- Monday: content  " -> "- Monday: content"
	s = strings.TrimSpace(s)
	if strings.HasPrefix(s, "- ") || strings.HasPrefix(s, "* ") {
		// Keep the list marker format clean
		parts := strings.SplitN(s, " ", 2)
		if len(parts) == 2 {
			s = parts[0] + " " + strings.TrimSpace(parts[1])
		}
	}

	return s
}

// ensureHashtagPack appends a Hashtag Pack section if it doesn't exist
// CRITICAL: Does NOT add fallback/generic hashtags - uses only provided allowed tags
func ensureHashtagPack(output string, allowedHashtags []string) string {
	// If no allowed hashtags, append empty section (validation will catch this)
	if len(allowedHashtags) == 0 {
		return output + "\n\n## Hashtag Pack\n"
	}

	// Limit to 5 hashtags
	if len(allowedHashtags) > 5 {
		allowedHashtags = allowedHashtags[:5]
	}

	// Build hashtag string
	var hashtagStr strings.Builder
	for i, tag := range allowedHashtags {
		if i > 0 {
			hashtagStr.WriteString(" ")
		}
		if !strings.HasPrefix(tag, "#") {
			hashtagStr.WriteString("#")
		}
		hashtagStr.WriteString(tag)
	}

	return output + "\n\n## Hashtag Pack\n" + hashtagStr.String()
}

// ensureHashtagPackPopulated checks if the Hashtag Pack section has content and populates if empty
func ensureHashtagPackPopulated(output string, allowedHashtags []string, _ int) string {
	lines := strings.Split(output, "\n")
	inHashtagPack := false
	packHasContent := false
	packHeaderIdx := -1

	for i, line := range lines {
		lowerLine := strings.ToLower(strings.TrimSpace(line))

		// Check for Hashtag Pack header
		isPackHeader := false
		for _, header := range HashtagPackHeaders {
			if strings.Contains(lowerLine, header) {
				isPackHeader = true
				break
			}
		}

		if isPackHeader {
			inHashtagPack = true
			packHeaderIdx = i
			continue
		}

		// Check if we're leaving the section
		if inHashtagPack && (strings.HasPrefix(lowerLine, "## ") || strings.HasPrefix(lowerLine, "# ")) {
			inHashtagPack = false
		}

		if inHashtagPack {
			// Check if line has real hashtags
			if RealHashtagRegex.MatchString(line) {
				packHasContent = true
			}
		}
	}

	// If pack exists but is empty, populate it with ONLY allowed hashtags
	// CRITICAL: Does NOT add fallback/generic hashtags
	if packHeaderIdx >= 0 && !packHasContent {
		// If no allowed hashtags, leave empty (validation will catch this)
		if len(allowedHashtags) == 0 {
			return output
		}
		if len(allowedHashtags) > 5 {
			allowedHashtags = allowedHashtags[:5]
		}

		var hashtagStr strings.Builder
		for i, tag := range allowedHashtags {
			if i > 0 {
				hashtagStr.WriteString(" ")
			}
			if !strings.HasPrefix(tag, "#") {
				hashtagStr.WriteString("#")
			}
			hashtagStr.WriteString(tag)
		}

		// Insert hashtags after the header
		newLines := make([]string, 0, len(lines)+1)
		for i, line := range lines {
			newLines = append(newLines, line)
			if i == packHeaderIdx {
				newLines = append(newLines, hashtagStr.String())
			}
		}
		return strings.Join(newLines, "\n")
	}

	return output
}

// IsOnlyHashtagPlacementViolation checks if the ONLY validation issues are benign hashtag placement
// Returns true if violations can be fixed by hashtag normalization
// CRITICAL: Returns false if ANY competitor-related violation exists (those must never be auto-fixed)
func IsOnlyHashtagPlacementViolation(issues []string) bool {
	if len(issues) == 0 {
		return false
	}

	for _, issue := range issues {
		upperIssue := strings.ToUpper(issue)

		// CRITICAL: Competitor violations must NEVER be auto-fixed
		// If any competitor violation exists, we cannot use normalization fast-path
		if strings.Contains(upperIssue, "COMPETITOR_HANDLE") ||
			strings.Contains(upperIssue, "COMPETITOR_HASHTAG") ||
			strings.Contains(upperIssue, "COMPETITOR_MENTION") {
			return false
		}

		// If it's NOT a hashtag placement/membership violation, return false
		if !strings.Contains(upperIssue, "HASHTAGS_IN_SCHEDULE") &&
			!strings.Contains(upperIssue, "HASHTAGS_OUTSIDE_PACK") &&
			!strings.Contains(upperIssue, "HASHTAG_PACK_MEMBERSHIP") &&
			!strings.Contains(upperIssue, "INVALID_HASHTAG") {
			return false
		}
	}

	return true
}

// ================================================================================
// SECTION A: DETERMINISTIC HASHTAG PACK
// ================================================================================

// BuildFinalHashtagPack creates a deterministic hashtag pack from STRICTLY allowed sources only
// Priority: observed -> selfBrand (if enabled) -> context-derived (if enabled)
// Returns plain tokens (no leading #), 2-5 tags when possible (may return <3 if insufficient safe tags exist)
// CRITICAL: Filters stoplist + malformed tokens + competitor-handle substrings.
func BuildFinalHashtagPack(observed []string, selfBrand []string, enableSelfBrand bool, contextHashtags []string, enableContextHashtags bool, competitorHandles []string) []string {
	seen := make(map[string]bool)
	var result []string
	competitorSet := buildCompetitorSet(competitorHandles)

	// Add observed hashtags first (already sanitized)
	for _, tag := range observed {
		normalized := strings.ToLower(strings.TrimSpace(tag))
		normalized = strings.TrimPrefix(normalized, "#")
		if normalized == "" || len(normalized) < 2 || len(normalized) > 30 {
			continue
		}
		if HashtagStoplist[normalized] {
			continue
		}
		if isCompetitorBranded(normalized, competitorSet) {
			continue
		}
		if !HashtagTokenRegex.MatchString(normalized) {
			continue
		}
		if seen[normalized] {
			continue
		}
		seen[normalized] = true
		result = append(result, normalized)
		if len(result) >= 5 {
			break
		}
	}

	// Add self-brand hashtags if enabled and need more
	if enableSelfBrand && len(result) < 5 {
		for _, tag := range selfBrand {
			normalized := strings.ToLower(strings.TrimSpace(tag))
			normalized = strings.TrimPrefix(normalized, "#")
			if normalized == "" || seen[normalized] {
				continue
			}
			if len(normalized) < 4 || len(normalized) > 30 {
				continue
			}
			if HashtagStoplist[normalized] {
				continue
			}
			if isCompetitorBranded(normalized, competitorSet) {
				continue
			}
			if !HashtagTokenRegex.MatchString(normalized) {
				continue
			}
			seen[normalized] = true
			result = append(result, normalized)
			if len(result) >= 5 {
				break
			}
		}
	}

	// Add context-derived hashtags last (if enabled)
	if enableContextHashtags && len(result) < 5 {
		for _, tag := range contextHashtags {
			normalized := strings.ToLower(strings.TrimSpace(tag))
			normalized = strings.TrimPrefix(normalized, "#")
			if normalized == "" || seen[normalized] {
				continue
			}
			if len(normalized) < 4 || len(normalized) > 20 {
				continue
			}
			if HashtagStoplist[normalized] {
				continue
			}
			if isCompetitorBranded(normalized, competitorSet) {
				continue
			}
			if !HashtagTokenRegex.MatchString(normalized) {
				continue
			}
			seen[normalized] = true
			result = append(result, normalized)
			if len(result) >= 5 {
				break
			}
		}
	}

	return result
}

// ReplaceOrAppendHashtagPack replaces or appends the Hashtag Pack section with deterministic tags
func ReplaceOrAppendHashtagPack(output string, finalTags []string) string {
	if len(finalTags) == 0 {
		return output
	}

	// Build the hashtag line with # prefixes
	var tagLine strings.Builder
	for i, tag := range finalTags {
		if i > 0 {
			tagLine.WriteString(" ")
		}
		tagLine.WriteString("#")
		tagLine.WriteString(tag)
	}
	newPackContent := tagLine.String()

	lines := strings.Split(output, "\n")
	var result []string
	inHashtagPack := false
	packReplaced := false

	for i, line := range lines {
		lowerLine := strings.ToLower(strings.TrimSpace(line))

		// Detect Hashtag Pack header
		isPackHeader := false
		for _, header := range HashtagPackHeaders {
			if strings.Contains(lowerLine, header) || strings.HasPrefix(lowerLine, header) {
				isPackHeader = true
				break
			}
		}

		if isPackHeader {
			inHashtagPack = true
			packReplaced = true
			result = append(result, line)
			result = append(result, newPackContent)
			continue
		}

		// Check if we're leaving the Hashtag Pack (new section header)
		if inHashtagPack {
			if strings.HasPrefix(lowerLine, "## ") || strings.HasPrefix(lowerLine, "# ") {
				inHashtagPack = false
				result = append(result, line)
				continue
			}
			// Skip existing hashtag pack content lines (they're replaced)
			if strings.TrimSpace(line) != "" && !strings.HasPrefix(lowerLine, "##") {
				// Check if this line looks like hashtag content
				if RealHashtagRegex.MatchString(line) || (len(strings.TrimSpace(line)) > 0 && i > 0) {
					continue // Skip this line, we already added new content
				}
			}
			continue
		}

		result = append(result, line)
	}

	output = strings.Join(result, "\n")

	// If no pack was found, append it
	if !packReplaced {
		output = strings.TrimSpace(output) + "\n\n## Hashtag Pack\n" + newPackContent
	}

	return strings.TrimSpace(output)
}

// BuildAllowedHashtagSet creates a set of allowed hashtags for membership validation
func BuildAllowedHashtagSet(observed []string, selfBrand []string, enableSelfBrand bool, contextHashtags []string, enableContextHashtags bool, competitorHandles []string) map[string]struct{} {
	allowed := make(map[string]struct{})
	competitorSet := buildCompetitorSet(competitorHandles)

	for _, tag := range observed {
		normalized := strings.ToLower(strings.TrimPrefix(strings.TrimSpace(tag), "#"))
		if normalized != "" && !HashtagStoplist[normalized] && !isCompetitorBranded(normalized, competitorSet) && HashtagTokenRegex.MatchString(normalized) {
			allowed[normalized] = struct{}{}
		}
	}

	if enableSelfBrand {
		for _, tag := range selfBrand {
			normalized := strings.ToLower(strings.TrimPrefix(strings.TrimSpace(tag), "#"))
			if normalized != "" && !HashtagStoplist[normalized] && !isCompetitorBranded(normalized, competitorSet) && HashtagTokenRegex.MatchString(normalized) {
				allowed[normalized] = struct{}{}
			}
		}
	}

	if enableContextHashtags {
		for _, tag := range contextHashtags {
			normalized := strings.ToLower(strings.TrimPrefix(strings.TrimSpace(tag), "#"))
			if normalized != "" && !HashtagStoplist[normalized] && !isCompetitorBranded(normalized, competitorSet) && HashtagTokenRegex.MatchString(normalized) {
				allowed[normalized] = struct{}{}
			}
		}
	}

	return allowed
}

// CheckHashtagPackMembership validates that all hashtags in the pack are in the allowed set
func CheckHashtagPackMembership(output string, allowed map[string]struct{}, competitorHandles []string) (bool, string) {
	lines := strings.Split(output, "\n")
	inHashtagPack := false
	competitorSet := buildCompetitorSet(competitorHandles)

	for _, line := range lines {
		lowerLine := strings.ToLower(strings.TrimSpace(line))

		// Detect Hashtag Pack header
		isPackHeader := false
		for _, header := range HashtagPackHeaders {
			if strings.Contains(lowerLine, header) || strings.HasPrefix(lowerLine, header) {
				isPackHeader = true
				break
			}
		}

		if isPackHeader {
			inHashtagPack = true
			continue
		}

		// Check if we're leaving the pack
		if inHashtagPack && (strings.HasPrefix(lowerLine, "## ") || strings.HasPrefix(lowerLine, "# ")) {
			inHashtagPack = false
			continue
		}

		if inHashtagPack {
			// Extract hashtags from this line
			matches := RealHashtagRegex.FindAllString(line, -1)
			for _, match := range matches {
				tag := strings.ToLower(strings.TrimPrefix(match, "#"))

				// Malformed tokens are never allowed
				if !HashtagTokenRegex.MatchString(tag) {
					return false, fmt.Sprintf("HASHTAG_PACK_MALFORMED_VIOLATION: Hashtag Pack contains malformed tag '%s'", match)
				}
				// Stoplist noise is never allowed
				if HashtagStoplist[tag] {
					return false, fmt.Sprintf("HASHTAG_PACK_STOPLIST_VIOLATION: Hashtag Pack contains stoplisted tag '%s'", match)
				}

				// Check for competitor handles first (security)
				for handle := range competitorSet {
					if tag == handle || strings.Contains(tag, handle) {
						return false, fmt.Sprintf("HASHTAG_PACK_COMPETITOR_VIOLATION: Hashtag Pack contains competitor handle '%s'", match)
					}
				}

				// Check membership
				if _, ok := allowed[tag]; !ok {
					return false, fmt.Sprintf("HASHTAG_PACK_MEMBERSHIP_VIOLATION: Invalid hashtag '%s' not in allowed set", match)
				}
			}
		}
	}

	return true, ""
}

// TruncateAfterHashtagPack removes any content that appears after the Hashtag Pack section
// This ensures the output structure is exact and no extra narrative leaks through
func TruncateAfterHashtagPack(output string) string {
	lines := strings.Split(output, "\n")
	var result []string
	inHashtagPack := false
	packContentFound := false

	for _, line := range lines {
		lowerLine := strings.ToLower(strings.TrimSpace(line))

		// Detect Hashtag Pack header
		isPackHeader := false
		for _, header := range HashtagPackHeaders {
			if strings.Contains(lowerLine, header) || strings.HasPrefix(lowerLine, header) {
				isPackHeader = true
				break
			}
		}

		if isPackHeader {
			inHashtagPack = true
			result = append(result, line)
			continue
		}

		if inHashtagPack {
			// Check if this line has hashtags (the actual content line)
			if RealHashtagRegex.MatchString(line) {
				result = append(result, line)
				packContentFound = true
				// After finding the hashtag content line, stop - truncate everything after
				break
			}
			// If it's a new section header, we're done (no hashtag content found)
			if strings.HasPrefix(lowerLine, "## ") || strings.HasPrefix(lowerLine, "# ") {
				break
			}
			// Include blank lines within the section
			if strings.TrimSpace(line) == "" {
				result = append(result, line)
				continue
			}
			// Include lines that might be part of hashtag pack content
			result = append(result, line)
			if RealHashtagRegex.MatchString(line) {
				packContentFound = true
				break
			}
		} else {
			result = append(result, line)
		}
	}

	// If no pack content found but we have the header, that's fine
	_ = packContentFound

	return strings.TrimSpace(strings.Join(result, "\n"))
}

// extractHashtagPackLine extracts the hashtag content line from the Hashtag Pack section
func extractHashtagPackLine(output string) string {
	lines := strings.Split(output, "\n")
	inHashtagPack := false

	for _, line := range lines {
		lowerLine := strings.ToLower(strings.TrimSpace(line))

		// Detect Hashtag Pack header
		isPackHeader := false
		for _, header := range HashtagPackHeaders {
			if strings.Contains(lowerLine, header) || strings.HasPrefix(lowerLine, header) {
				isPackHeader = true
				break
			}
		}

		if isPackHeader {
			inHashtagPack = true
			continue
		}

		if inHashtagPack {
			// Return the first non-empty line with hashtags
			if RealHashtagRegex.MatchString(line) {
				return strings.TrimSpace(line)
			}
			// Stop if we hit another section
			if strings.HasPrefix(lowerLine, "## ") || strings.HasPrefix(lowerLine, "# ") {
				break
			}
		}
	}

	return "(none found)"
}

// CheckContentAfterHashtagPack validates that no content appears after the Hashtag Pack section
func CheckContentAfterHashtagPack(output string) (bool, string) {
	lines := strings.Split(output, "\n")
	inHashtagPack := false
	packContentLineFound := false
	afterPackContent := false

	for i, line := range lines {
		lowerLine := strings.ToLower(strings.TrimSpace(line))
		trimmed := strings.TrimSpace(line)

		// Detect Hashtag Pack header
		isPackHeader := false
		for _, header := range HashtagPackHeaders {
			if strings.Contains(lowerLine, header) || strings.HasPrefix(lowerLine, header) {
				isPackHeader = true
				break
			}
		}

		if isPackHeader {
			inHashtagPack = true
			continue
		}

		if inHashtagPack {
			if RealHashtagRegex.MatchString(line) {
				packContentLineFound = true
				afterPackContent = true
				continue
			}
			// If we found pack content and now see non-empty content, that's a violation
			if afterPackContent && trimmed != "" && !strings.HasPrefix(trimmed, "#") {
				return false, fmt.Sprintf("CONTENT_AFTER_HASHTAG_PACK_VIOLATION: Line %d has content after Hashtag Pack: '%s'",
					i+1, truncateForError(trimmed, 50))
			}
		}
	}

	// If no pack found at all, that's handled elsewhere
	_ = packContentLineFound

	return true, ""
}

// runFinalAssertions performs final validation checks before returning 200
// This is a defensive measure to ensure invalid content never reaches the client
func runFinalAssertions(output string, allowedHashtags map[string]struct{}, competitorHandles []string, contextKeywords map[string]struct{}) []string {
	var issues []string

	// 0. No placeholders/template tokens
	if ok, issue := CheckPlaceholderViolations(output); !ok {
		issues = append(issues, "ASSERTION_FAILED: "+issue)
	}

	// 0.1 Schedule completeness/quality
	if ok, issue := CheckScheduleLineQuality(output); !ok {
		issues = append(issues, "ASSERTION_FAILED: "+issue)
	}

	// 1. No URLs
	lowerOutput := strings.ToLower(output)
	if strings.Contains(lowerOutput, "http://") ||
		strings.Contains(lowerOutput, "https://") ||
		strings.Contains(lowerOutput, "www.") {
		issues = append(issues, "ASSERTION_FAILED: Output contains URLs")
	}

	// 2. No image markdown
	if strings.Contains(output, "![") || strings.Contains(output, "](http") {
		issues = append(issues, "ASSERTION_FAILED: Output contains image markdown")
	}

	// 3. No competitor handles
	competitorSet := buildCompetitorSet(competitorHandles)
	for handle := range competitorSet {
		if strings.Contains(lowerOutput, handle) {
			issues = append(issues, fmt.Sprintf("ASSERTION_FAILED: Output contains competitor handle '%s'", handle))
			break // One is enough
		}
	}

	// 4. Hashtags only in Hashtag Pack section
	if ok, issue := CheckHashtagsOutsidePack(output); !ok {
		issues = append(issues, "ASSERTION_FAILED: "+issue)
	}

	// 5. Hashtag Pack membership valid
	if ok, issue := CheckHashtagPackMembership(output, allowedHashtags, competitorHandles); !ok {
		issues = append(issues, "ASSERTION_FAILED: "+issue)
	}

	// 6. No content after Hashtag Pack
	if ok, issue := CheckContentAfterHashtagPack(output); !ok {
		issues = append(issues, "ASSERTION_FAILED: "+issue)
	}

	// 7. Not generic if context keywords are provided
	if len(contextKeywords) > 0 {
		if ok, issue := CheckGenericOutput(output, contextKeywords, 3); !ok {
			issues = append(issues, "ASSERTION_FAILED: "+issue)
		}
	}

	return issues
}

// ================================================================================
// SECTION C: TEASER AVAILABILITY/CTA LANGUAGE VALIDATION
// ================================================================================

// TeaserBannedPhrases are availability/CTA phrases banned in Teaser campaigns
var TeaserBannedPhrases = []string{
	"open its doors",
	"opens its doors",
	"opening its doors",
	"about to open",
	"coming soon",
	"out soon",
	"available soon",
	"preorder",
	"pre-order",
	"wishlist",
	"add to wishlist",
	"download now",
	"buy now",
	"purchase now",
	"link in bio",
	"play now",
	"out now",
	"available now",
	"get it now",
	"order now",
	"reserve now",
	"sign up now",
	"join now",
	"register now",
	"early access",
	"launching soon",
	"releases soon",
	"dropping soon",
}

// CheckTeaserAvailabilityLanguage validates teaser output doesn't contain availability/CTA phrases
func CheckTeaserAvailabilityLanguage(output string) (bool, string) {
	lowerOutput := strings.ToLower(output)

	for _, phrase := range TeaserBannedPhrases {
		if strings.Contains(lowerOutput, phrase) {
			return false, fmt.Sprintf("TEASER_LANGUAGE_VIOLATION: Output contains banned teaser phrase '%s'", phrase)
		}
	}

	return true, ""
}

// ================================================================================
// SECTION D: COMPETITOR HOOK SANITIZATION
// ================================================================================

// SanitizeCompetitorHook removes hashtags and handles from a competitor hook
// Returns a safe version that won't leak competitor branding into prompts
func SanitizeCompetitorHook(hook string, competitorHandles []string) string {
	if hook == "" {
		return ""
	}

	result := hook

	// Remove all real hashtags
	result = RealHashtagRegex.ReplaceAllString(result, "")

	// Remove @mentions
	atMentionRegex := regexp.MustCompile(`@[a-zA-Z][a-zA-Z0-9_]*`)
	result = atMentionRegex.ReplaceAllString(result, "")

	// Remove competitor handles (plain word)
	competitorSet := buildCompetitorSet(competitorHandles)
	for handle := range competitorSet {
		// Word boundary replacement (case insensitive)
		pattern := regexp.MustCompile(`(?i)\b` + regexp.QuoteMeta(handle) + `\b`)
		result = pattern.ReplaceAllString(result, "")
	}

	// Clean up extra spaces
	result = cleanupSpaces(result)

	return strings.TrimSpace(result)
}

// DescribeHookStyle creates a safe style description instead of passing raw hook text
func DescribeHookStyle(hook string) string {
	if hook == "" {
		return "unknown style"
	}

	var traits []string

	// Count sentences (rough)
	sentences := len(strings.Split(hook, ".")) + len(strings.Split(hook, "!")) + len(strings.Split(hook, "?")) - 2
	if sentences <= 1 {
		traits = append(traits, "single sentence")
	} else if sentences <= 3 {
		traits = append(traits, "2-3 sentences")
	} else {
		traits = append(traits, "multiple sentences")
	}

	// Check for question
	if strings.Contains(hook, "?") {
		traits = append(traits, "includes question")
	}

	// Check for line breaks
	if strings.Contains(hook, "\n") {
		traits = append(traits, "uses line breaks")
	}

	// Check length
	if len(hook) < 50 {
		traits = append(traits, "short/punchy")
	} else if len(hook) > 150 {
		traits = append(traits, "detailed/storytelling")
	}

	// Check for common patterns
	lowerHook := strings.ToLower(hook)
	if strings.Contains(lowerHook, "why") {
		traits = append(traits, "explainer/why format")
	}
	if strings.Contains(lowerHook, "secret") || strings.Contains(lowerHook, "hidden") {
		traits = append(traits, "secret reveal")
	}
	if strings.HasPrefix(strings.TrimSpace(lowerHook), "i ") || strings.HasPrefix(strings.TrimSpace(lowerHook), "we ") {
		traits = append(traits, "first-person narrative")
	}

	if len(traits) == 0 {
		return "standard engagement hook"
	}

	return strings.Join(traits, ", ")
}

// ================================================================================
// SECTION E: GROUNDING / ANTI-HALLUCINATION VALIDATION
// ================================================================================

// HardClaimPhrases are outcome/guarantee claims that MUST be blocked
// These indicate factual claims about game outcomes or mechanics
var HardClaimPhrases = []string{
	"always win",
	"never lose",
	"can't lose",
	"cannot lose",
	"guaranteed win",
	"guaranteed payout",
	"guaranteed to win",
	"rigged in favor",
	"rigged for",
	"fixed odds",
	"fixed in favor",
	"won by players",
	"lost by players",
	"ensures you win",
	"ensures you'll win",
	"programmed to pay",
	"designed to pay",
	"scientifically proven",
	"studies show",
	"research proves",
	"100% chance",
	"100% win",
	"every time you",
	"without fail",
}

// SoftMarketingPhrases are intensifiers that are ALLOWED (not false positives)
var SoftMarketingPhrases = []string{
	"like never before",
	"never before",
	"never seen",
	"never experienced",
	"best ever",
	"ultimate",
	"biggest",
	"most exciting",
	"high-stakes",
	"high stakes",
}

// BuildContextKeywordSet extracts keywords from RAG context for grounding validation
func BuildContextKeywordSet(genre, mechanics, tone, audience, additionalInfo string) map[string]struct{} {
	keywords := make(map[string]struct{})

	// Split and normalize all context fields
	allText := strings.ToLower(genre + " " + mechanics + " " + tone + " " + audience + " " + additionalInfo)

	// Split on common delimiters
	delimiters := regexp.MustCompile(`[,;/\s]+`)
	tokens := delimiters.Split(allText, -1)

	for _, token := range tokens {
		token = strings.TrimSpace(token)
		if len(token) >= 3 && len(token) <= 30 {
			keywords[token] = struct{}{}
		}
	}

	return keywords
}

// CheckUngroundedFeatureClaims detects ungrounded factual claims about mechanics/outcomes
func CheckUngroundedFeatureClaims(output string, allowedKeywords map[string]struct{}) (bool, string) {
	lowerOutput := strings.ToLower(output)
	lines := strings.Split(lowerOutput, "\n")

	for lineNum, line := range lines {
		// Skip lines with hypothetical framing - these are allowed
		if containsHypotheticalFraming(line) {
			continue
		}

		// Skip lines that contain soft marketing phrases (avoid false positives)
		if containsSoftMarketingPhrase(line) {
			continue
		}

		// Check for hard-claim phrases that indicate factual outcome claims
		for _, hardClaim := range HardClaimPhrases {
			if strings.Contains(line, hardClaim) {
				return false, fmt.Sprintf("UNGROUNDED_CLAIM_VIOLATION: Line %d contains unverifiable outcome claim '%s'",
					lineNum+1, hardClaim)
			}
		}
	}

	return true, ""
}

// containsHypotheticalFraming checks if a line uses hypothetical language
func containsHypotheticalFraming(line string) bool {
	hypotheticalMarkers := []string{
		"might", "could", "would", "may",
		"what if", "imagine", "picture this",
		"perhaps", "possibly", "potentially",
	}
	for _, marker := range hypotheticalMarkers {
		if strings.Contains(line, marker) {
			return true
		}
	}
	return false
}

// containsSoftMarketingPhrase checks if a line contains allowed marketing intensifiers
func containsSoftMarketingPhrase(line string) bool {
	for _, phrase := range SoftMarketingPhrases {
		if strings.Contains(line, phrase) {
			return true
		}
	}
	return false
}

// ================================================================================
// SECTION B: HASHTAG CANDIDATES PARSING AND FILTERING (OPTIONAL)
// ================================================================================

// HashtagCandidateRegex matches valid hashtag tokens (no leading #, lowercase, reasonable length)
var HashtagCandidateRegex = regexp.MustCompile(`^[a-z][a-z0-9_]{2,24}$`)

// HashtagTokenRegex is used for final pack membership checks (slightly wider length).
// Must be lowercase a-z start, then a-z0-9_ only.
var HashtagTokenRegex = regexp.MustCompile(`^[a-z][a-z0-9_]{2,29}$`)

// slugifyHashtagToken lowercases, removes punctuation, and collapses spaces into a single token.
// Example: "Always Bet on Quack!" -> "alwaysbetonquack"
func slugifyHashtagToken(s string) string {
	s = strings.ToLower(strings.TrimSpace(s))
	if s == "" {
		return ""
	}
	var b strings.Builder
	b.Grow(len(s))
	lastWasSpace := false

	for _, r := range s {
		if r >= 'a' && r <= 'z' {
			b.WriteRune(r)
			lastWasSpace = false
			continue
		}
		if r >= '0' && r <= '9' {
			b.WriteRune(r)
			lastWasSpace = false
			continue
		}
		// Treat underscores as allowed
		if r == '_' {
			b.WriteRune(r)
			lastWasSpace = false
			continue
		}
		// Collapse any whitespace/punctuation into nothing (single-token hashtags)
		if r == ' ' || r == '\t' || r == '\n' || r == '-' {
			// We intentionally drop separators to produce a single token.
			// Keep a flag in case you want to later switch to underscores.
			lastWasSpace = true
			_ = lastWasSpace
			continue
		}
		// Drop other punctuation/symbols
	}

	return b.String()
}

func isPurelyNumeric(s string) bool {
	if s == "" {
		return false
	}
	for _, r := range s {
		if r < '0' || r > '9' {
			return false
		}
	}
	return true
}

// BuildSelfBrandHashtags generates deterministic self-brand hashtags from game/world/studio names.
// Produces up to 3 tags total, in stable order: gameName, worldName, studioName.
// Rules:
// - slugify to a single token
// - len >= 4
// - not purely numeric
// - must match HashtagTokenRegex
func BuildSelfBrandHashtags(gameName, worldName, studioName string) []string {
	candidates := []string{gameName, worldName, studioName}
	seen := make(map[string]bool)
	var out []string

	for _, raw := range candidates {
		if raw == "" {
			continue
		}
		token := slugifyHashtagToken(raw)
		if token == "" || seen[token] {
			continue
		}
		if len(token) < 4 || isPurelyNumeric(token) {
			continue
		}
		if !HashtagTokenRegex.MatchString(token) {
			continue
		}
		seen[token] = true
		out = append(out, token)
		if len(out) >= 3 {
			break
		}
	}

	return out
}

// BuildContextDerivedHashtags selects a small, safe subset of context keywords as hashtag tokens.
// Hard cap: 0–2 tags. Must be <= 20 chars, must not be stoplisted, and must not match/contain competitor handles.
func BuildContextDerivedHashtags(contextKeywords map[string]struct{}, competitorHandles []string) []string {
	if len(contextKeywords) == 0 {
		return nil
	}
	competitorSet := buildCompetitorSet(competitorHandles)

	// Deterministic order: sort keys
	var keys []string
	for k := range contextKeywords {
		k = strings.ToLower(strings.TrimSpace(k))
		if k != "" {
			keys = append(keys, k)
		}
	}
	sort.Strings(keys)

	seen := make(map[string]bool)
	var out []string
	for _, k := range keys {
		token := slugifyHashtagToken(k)
		if token == "" || seen[token] {
			continue
		}
		// Only allow single-token-ish results
		if len(token) < 4 || len(token) > 20 {
			continue
		}
		if !HashtagCandidateRegex.MatchString(token) && !HashtagTokenRegex.MatchString(token) {
			continue
		}
		if HashtagStoplist[token] {
			continue
		}
		// Strict competitor protection: reject if equals OR contains competitor variants
		if isCompetitorBranded(token, competitorSet) {
			continue
		}
		seen[token] = true
		out = append(out, token)
		if len(out) >= 2 {
			break
		}
	}

	return out
}

// ParseHashtagCandidates extracts proposed hashtag candidates from the output
func ParseHashtagCandidates(output string) []string {
	var candidates []string
	lines := strings.Split(output, "\n")
	inCandidatesSection := false

	for _, line := range lines {
		lowerLine := strings.ToLower(strings.TrimSpace(line))

		// Look for candidates section header
		if strings.Contains(lowerLine, "hashtag candidates") {
			inCandidatesSection = true
			continue
		}

		// Exit on next section header
		if inCandidatesSection && (strings.HasPrefix(lowerLine, "## ") || strings.HasPrefix(lowerLine, "# ")) {
			break
		}

		if inCandidatesSection {
			// Extract tokens from line (split by whitespace, commas)
			tokens := regexp.MustCompile(`[,\s]+`).Split(line, -1)
			for _, token := range tokens {
				token = strings.ToLower(strings.TrimSpace(token))
				token = strings.TrimPrefix(token, "#")
				token = strings.TrimPrefix(token, "-")
				token = strings.TrimSpace(token)
				if HashtagCandidateRegex.MatchString(token) {
					candidates = append(candidates, token)
				}
			}
		}
	}

	return candidates
}

// FilterCandidates filters hashtag candidates for safety and relevance
func FilterCandidates(candidates []string, contextKeywords map[string]struct{}, competitorHandles []string, stoplist map[string]bool) []string {
	var filtered []string
	competitorSet := buildCompetitorSet(competitorHandles)
	seen := make(map[string]bool)

	for _, candidate := range candidates {
		candidate = strings.ToLower(strings.TrimSpace(candidate))

		// Basic validation
		if !HashtagCandidateRegex.MatchString(candidate) {
			continue
		}

		// Skip duplicates
		if seen[candidate] {
			continue
		}

		// Skip stoplist
		if stoplist[candidate] {
			continue
		}

		// Skip competitor handles
		isCompetitor := false
		for handle := range competitorSet {
			if candidate == handle || strings.Contains(candidate, handle) {
				isCompetitor = true
				break
			}
		}
		if isCompetitor {
			continue
		}

		// Check relevance (must match context keyword via substring)
		isRelevant := false
		for keyword := range contextKeywords {
			if strings.Contains(candidate, keyword) || strings.Contains(keyword, candidate) {
				isRelevant = true
				break
			}
		}
		if !isRelevant {
			continue
		}

		seen[candidate] = true
		filtered = append(filtered, candidate)

		// Cap at reasonable number
		if len(filtered) >= 5 {
			break
		}
	}

	return filtered
}
