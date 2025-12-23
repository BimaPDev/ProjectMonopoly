// internal/handlers/marketing_prompt.go
package handlers

import (
	"bytes"
	"fmt"
	"strings"
	"text/template"
)

// MarketingPromptData holds all data for the marketing prompt template
type MarketingPromptData struct {
	GameName             string
	GameSummary          string
	BestDay              string  // Day name (e.g., "Wednesday")
	PostsPerWeek         float64 // Competitor cadence
	TimeHeuristic        string  // Platform-specific time advice
	TopCompetitorCaption string
	CampaignType         string
	Tone                 string
	Platform             string
	HasCompetitorData    bool
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
HARD DATA (Last 28 Days):
- Peak Engagement Day: {{.BestDay}}
- Competitor Cadence: {{printf "%.1f" .PostsPerWeek}} posts/week
{{if .TopCompetitorCaption}}- Top Performing Hook: "{{.TopCompetitorCaption}}"{{end}}
{{else -}}
HARD DATA: No competitor data available for the past 28 days.
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
3. **Call-to-Action** (if appropriate for campaign type)
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
		}
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

// BuildStrategySystemPrompt creates a concise system prompt for high-level strategy tasks
func BuildStrategySystemPrompt(gameName, gameSummary string) string {
	var b strings.Builder
	b.WriteString("You are a senior social media strategist for indie games.\n")
	b.WriteString("You're working on: " + gameName + "\n")
	b.WriteString("Game Overview: " + gameSummary + "\n\n")
	b.WriteString("RULES:\n")
	b.WriteString("- Keep recommendations actionable and specific.\n")
	b.WriteString("- Reference competitor data when provided.\n")
	b.WriteString("- Structure output with clear headers.\n")
	return b.String()
}

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

// TruncateHook safely truncates a hook to a maximum length
func TruncateHook(hook string, maxLen int) string {
	if len(hook) <= maxLen {
		return hook
	}
	// Find last space before maxLen to avoid cutting words
	truncated := hook[:maxLen]
	lastSpace := strings.LastIndex(truncated, " ")
	if lastSpace > maxLen-50 { // Don't go back too far
		truncated = truncated[:lastSpace]
	}
	return truncated + "..."
}
