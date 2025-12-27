package handlers

import (
	"strings"
	"testing"
)

func TestValidateMarketingValidators(t *testing.T) {
	tests := []struct {
		name    string
		isPost  bool // true = ValidatePostOutput, false = ValidateStrategyOutput
		output  string
		policy  CTAPolicy
		wantOk  bool
		wantErr string // substring match
	}{
		// --- POST VALIDATOR TESTS ---
		{
			name:   "Post Valid Teaser",
			isPost: true,
			output: "Hook: ...\n\nBody: ...\n\nEngagement Question: What do you think?\n\nHashtags: #game #indie",
			policy: CTAPolicyNone,
			wantOk: true,
		},
		{
			name:    "Post Teaser with Wishlist",
			isPost:  true,
			output:  "Hook: ...\nBody: ...\nWishlist now on Steam!",
			policy:  CTAPolicyNone,
			wantOk:  false,
			wantErr: "banned sales term 'wishlist'",
		},
		{
			name:    "Post Teaser Missing Question",
			isPost:  true,
			output:  "Hook: ...\nBody: ...\nNo question here.\n#tag1 #tag2",
			policy:  CTAPolicyNone,
			wantOk:  false,
			wantErr: "MISSING_ENGAGEMENT_QUESTION",
		},
		{
			name:    "Post Unstructured",
			isPost:  true,
			output:  "Just random text",
			policy:  CTAPolicyHard,
			wantOk:  false,
			wantErr: "STRUCTURE_ERROR",
		},

		// --- STRATEGY VALIDATOR TESTS ---
		{
			name:   "Strategy Valid (No Q/Hashtags needed)",
			isPost: false,
			output: "Strategy: Focus on mystery.\nTimeline: Week 1...",
			policy: CTAPolicyNone,
			wantOk: true,
		},
		{
			name:   "Strategy with Launch Campaign (Allowed)",
			isPost: false,
			output: "Plan: We will have a launch campaign in Q4.",
			policy: CTAPolicyNone,
			wantOk: true,
		},
		{
			name:    "Strategy with Wishlist (Banned)",
			isPost:  false,
			output:  "Goal: Drive wishlist conversions on Steam.",
			policy:  CTAPolicyNone,
			wantOk:  false,
			wantErr: "banned conversion term 'wishlist'",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var gotOk bool
			var issues []string

			if tt.isPost {
				gotOk, issues = ValidatePostOutput(tt.output, tt.policy)
			} else {
				gotOk, issues = ValidateStrategyOutput(tt.output, tt.policy)
			}

			if gotOk != tt.wantOk {
				t.Errorf("Validation ok = %v, want %v. Issues: %v", gotOk, tt.wantOk, issues)
			}
			if !tt.wantOk && tt.wantErr != "" {
				found := false
				for _, issue := range issues {
					if strings.Contains(issue, tt.wantErr) {
						found = true
						break
					}
				}
				if !found {
					t.Errorf("Validation missing expected error '%s'. Got: %v", tt.wantErr, issues)
				}
			}
		})
	}
}

func TestValidateStrategyOutputWithConfig(t *testing.T) {
	tests := []struct {
		name    string
		output  string
		config  StrategyValidationConfig
		wantOk  bool
		wantErr string
	}{
		// URL validation tests
		{
			name:   "Strategy with http URL",
			output: "Check out our game at http://example.com",
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyHard,
				RecommendedPostsPerWeek: 3,
			},
			wantOk:  false,
			wantErr: "URL_VIOLATION",
		},
		{
			name:   "Strategy with https URL",
			output: "Visit https://store.steampowered.com for wishlist",
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyHard,
				RecommendedPostsPerWeek: 3,
			},
			wantOk:  false,
			wantErr: "URL_VIOLATION",
		},
		{
			name:   "Strategy with www URL",
			output: "Go to www.ourgame.com",
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyHard,
				RecommendedPostsPerWeek: 3,
			},
			wantOk:  false,
			wantErr: "URL_VIOLATION",
		},

		// Image markdown validation tests
		{
			name:   "Strategy with image markdown",
			output: "Here's our logo: ![logo](image.png)",
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyHard,
				RecommendedPostsPerWeek: 3,
			},
			wantOk:  false,
			wantErr: "IMAGE_MARKDOWN_VIOLATION",
		},

		// Cadence validation tests
		{
			name:   "Strategy with valid cadence",
			output: "## Posting Cadence\nPostsPerWeek: 2\nPrimary Day: Thursday",
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyHard,
				RecommendedPostsPerWeek: 3,
			},
			wantOk: true,
		},
		{
			name:   "Strategy exceeding max cadence",
			output: "## Posting Cadence\nPostsPerWeek: 7\nPost daily for maximum reach!",
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyHard,
				RecommendedPostsPerWeek: 2,
			},
			wantOk:  false,
			wantErr: "CADENCE_VIOLATION",
		},
		{
			name:   "Strategy with daily posting suggestion",
			output: "We recommend a daily post schedule for engagement",
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyHard,
				RecommendedPostsPerWeek: 2,
			},
			wantOk:  false,
			wantErr: "CADENCE_VIOLATION",
		},

		// Competitor hashtag validation tests
		{
			name:   "Strategy with competitor hashtag",
			output: "Use hashtags: #indiegame #gaming #stickaroundgame",
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyHard,
				RecommendedPostsPerWeek: 3,
				CompetitorHandles:       []string{"stickaround", "othercompetitor"},
			},
			wantOk:  false,
			wantErr: "COMPETITOR_HANDLE_VIOLATION", // Updated to new unified error type
		},
		{
			name: "Strategy without competitor hashtags",
			output: `## Content Pillars
- Gaming strategy

## Hashtag Pack
#indiegame #gaming #boardgame`,
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyHard,
				RecommendedPostsPerWeek: 3,
				CompetitorHandles:       []string{"stickaround", "othercompetitor"},
			},
			wantOk: true,
		},

		// Teaser language validation tests
		{
			name:   "Teaser with launch now",
			output: "Call to action: Launch now and get it!",
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyNone,
				RecommendedPostsPerWeek: 2,
				CampaignType:            "Teaser",
			},
			wantOk:  false,
			wantErr: "TEASER_LANGUAGE_VIOLATION",
		},
		{
			name:   "Teaser with launching on",
			output: "We are launching on December 25th!",
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyNone,
				RecommendedPostsPerWeek: 2,
				CampaignType:            "Teaser",
			},
			wantOk:  false,
			wantErr: "TEASER_LANGUAGE_VIOLATION",
		},
		{
			name:   "Teaser with correct language",
			output: "Kick off the teaser series with mystery posts. Start the journey this week.",
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyNone,
				RecommendedPostsPerWeek: 2,
				CampaignType:            "Teaser",
			},
			wantOk: true,
		},

		// Low confidence validation tests
		{
			name:   "Low confidence without confidence statement",
			output: "## Strategy\nPost on Thursday for best results.",
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyHard,
				RecommendedPostsPerWeek: 2,
				IsLowConfidence:         true,
			},
			wantOk:  false,
			wantErr: "LOW_CONFIDENCE_VIOLATION",
		},
		{
			name:   "Low confidence without A/B test",
			output: "Confidence: low. Post on Thursday.",
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyHard,
				RecommendedPostsPerWeek: 2,
				IsLowConfidence:         true,
			},
			wantOk:  false,
			wantErr: "LOW_CONFIDENCE_VIOLATION",
		},
		{
			name:   "Low confidence with proper structure",
			output: "Confidence: low (sample size: 5 posts)\n\n## A/B Test Plan\nTest Variable: Posting day",
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyHard,
				RecommendedPostsPerWeek: 2,
				IsLowConfidence:         true,
			},
			wantOk: true,
		},

		// Combined valid strategy
		{
			name: "Complete valid strategy",
			output: `## Content Pillars
- Gameplay mystery
- Character reveals
- Community engagement

## Posting Cadence
PostsPerWeek: 2
Primary Day: Thursday
Confidence: low (sample size: 6 posts)

## A/B Test Plan
Test Variable: Posting day (Thursday vs Tuesday)

## Hook Ideas
1. What's hiding in the shadows?
2. They're watching...

## Hashtag Pack
#indiegame #gaming #mysterygame`,
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyNone,
				RecommendedPostsPerWeek: 2,
				IsLowConfidence:         true,
				CampaignType:            "Teaser",
				CompetitorHandles:       []string{"competitor1"},
			},
			wantOk: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			gotOk, issues := ValidateStrategyOutputWithConfig(tt.output, tt.config)

			if gotOk != tt.wantOk {
				t.Errorf("ValidateStrategyOutputWithConfig() ok = %v, want %v. Issues: %v", gotOk, tt.wantOk, issues)
			}
			if !tt.wantOk && tt.wantErr != "" {
				found := false
				for _, issue := range issues {
					if strings.Contains(issue, tt.wantErr) {
						found = true
						break
					}
				}
				if !found {
					t.Errorf("ValidateStrategyOutputWithConfig() missing expected error '%s'. Got: %v", tt.wantErr, issues)
				}
			}
		})
	}
}

func TestSanitizeHashtags(t *testing.T) {
	tests := []struct {
		name              string
		tags              []string
		competitorHandles []string
		want              []string
	}{
		{
			name:              "Basic sanitization",
			tags:              []string{"#GameDev", "#IndieGame", "#gaming"},
			competitorHandles: []string{},
			want:              []string{"gamedev", "indiegame", "gaming"},
		},
		{
			name:              "Remove competitor hashtags",
			tags:              []string{"#gamedev", "#stickaroundgame", "#indiegame"},
			competitorHandles: []string{"stickaround"},
			want:              []string{"gamedev", "indiegame"},
		},
		{
			name:              "Remove stoplist hashtags",
			tags:              []string{"#gamedev", "#fyp", "#cat", "#indiegame", "#viral"},
			competitorHandles: []string{},
			want:              []string{"gamedev", "indiegame"},
		},
		{
			name:              "Deduplicate hashtags",
			tags:              []string{"#GameDev", "#gamedev", "#GAMEDEV", "#indiegame"},
			competitorHandles: []string{},
			want:              []string{"gamedev", "indiegame"},
		},
		{
			name:              "Cap at 5 hashtags",
			tags:              []string{"#tag1", "#tag2", "#tag3", "#tag4", "#tag5", "#tag6", "#tag7"},
			competitorHandles: []string{},
			want:              []string{"tag1", "tag2", "tag3", "tag4", "tag5"},
		},
		{
			name:              "Strip # prefix",
			tags:              []string{"gamedev", "#indiegame", "##gaming"},
			competitorHandles: []string{},
			want:              []string{"gamedev", "indiegame", "gaming"},
		},
		{
			name:              "Remove competitor variations",
			tags:              []string{"#gamedev", "#competitorgame", "#competitorofficial", "#indiegame"},
			competitorHandles: []string{"competitor"},
			want:              []string{"gamedev", "indiegame"},
		},
		{
			name:              "Complex filtering",
			tags:              []string{"#FYP", "#StickaroundGame", "#indiegame", "#CAT", "#gaming", "#stickaround", "#boardgame"},
			competitorHandles: []string{"stickaround"},
			want:              []string{"indiegame", "gaming", "boardgame"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := SanitizeHashtags(tt.tags, tt.competitorHandles)

			if len(got) != len(tt.want) {
				t.Errorf("SanitizeHashtags() returned %d tags, want %d. Got: %v, Want: %v", len(got), len(tt.want), got, tt.want)
				return
			}

			for i, tag := range got {
				if tag != tt.want[i] {
					t.Errorf("SanitizeHashtags()[%d] = %s, want %s", i, tag, tt.want[i])
				}
			}
		})
	}
}

func TestComputeRecommendedPostsPerWeek(t *testing.T) {
	tests := []struct {
		name                   string
		competitorPostsPerWeek float64
		want                   int
	}{
		{"Zero cadence defaults to 2", 0, DefaultPostsPerWeek},
		{"Negative cadence defaults to 2", -1, DefaultPostsPerWeek},
		{"Low cadence rounds up to 1", 0.5, 1},
		{"Cadence 1.5 rounds up to 2", 1.5, 2},
		{"Cadence 2.1 rounds up to 3", 2.1, 3},
		{"High cadence capped at 3", 5.0, MaxRecommendedPostsPerWeek},
		{"Very high cadence capped at 3", 10.0, MaxRecommendedPostsPerWeek},
		{"Exact 1", 1.0, 1},
		{"Exact 2", 2.0, 2},
		{"Exact 3", 3.0, 3},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := ComputeRecommendedPostsPerWeek(tt.competitorPostsPerWeek)
			if got != tt.want {
				t.Errorf("ComputeRecommendedPostsPerWeek(%v) = %d, want %d", tt.competitorPostsPerWeek, got, tt.want)
			}
		})
	}
}

func TestDetermineConfidence(t *testing.T) {
	tests := []struct {
		name          string
		postsAnalyzed int
		want          string
	}{
		{"Zero posts is low", 0, "low"},
		{"5 posts is low", 5, "low"},
		{"9 posts is low", 9, "low"},
		{"10 posts is medium", 10, "medium"},
		{"15 posts is medium", 15, "medium"},
		{"19 posts is medium", 19, "medium"},
		{"20 posts is high", 20, "high"},
		{"100 posts is high", 100, "high"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := DetermineConfidence(tt.postsAnalyzed)
			if got != tt.want {
				t.Errorf("DetermineConfidence(%d) = %s, want %s", tt.postsAnalyzed, got, tt.want)
			}
		})
	}
}

func TestValidateCadence(t *testing.T) {
	tests := []struct {
		name            string
		output          string
		maxPostsPerWeek int
		wantOk          bool
		wantErr         string
	}{
		{
			name:            "Valid explicit cadence",
			output:          "PostsPerWeek: 2\nPrimary Day: Thursday",
			maxPostsPerWeek: 3,
			wantOk:          true,
		},
		{
			name:            "Exceeds explicit cadence",
			output:          "PostsPerWeek: 5\nFor maximum visibility",
			maxPostsPerWeek: 2,
			wantOk:          false,
			wantErr:         "CADENCE_VIOLATION",
		},
		{
			name:            "Daily posting pattern",
			output:          "Post daily to maintain engagement",
			maxPostsPerWeek: 2,
			wantOk:          false,
			wantErr:         "CADENCE_VIOLATION",
		},
		{
			name:            "Every day pattern",
			output:          "We should post every day for best results",
			maxPostsPerWeek: 3,
			wantOk:          false,
			wantErr:         "CADENCE_VIOLATION",
		},
		{
			name:            "No explicit cadence, acceptable schedule",
			output:          "Post on Thursday and Sunday for good coverage",
			maxPostsPerWeek: 3,
			wantOk:          true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			gotOk, gotErr := validateCadence(tt.output, tt.maxPostsPerWeek)
			if gotOk != tt.wantOk {
				t.Errorf("validateCadence() ok = %v, want %v. Error: %s", gotOk, tt.wantOk, gotErr)
			}
			if !tt.wantOk && tt.wantErr != "" && !strings.Contains(gotErr, tt.wantErr) {
				t.Errorf("validateCadence() error = %s, want to contain %s", gotErr, tt.wantErr)
			}
		})
	}
}

// =============================================================================
// NEW TESTS: Output Hygiene (REPAIR: leakage blocked/stripped)
// =============================================================================

func TestStripInternalMeta(t *testing.T) {
	tests := []struct {
		name   string
		input  string
		expect string
	}{
		{
			name:   "No meta markers - unchanged",
			input:  "## Content Pillars\n- Gaming\n- Community",
			expect: "## Content Pillars\n- Gaming\n- Community",
		},
		{
			name:   "REPAIR marker stripped",
			input:  "## Content Pillars\n- Gaming\n\nREPAIR:\nRegenerated from scratch...",
			expect: "## Content Pillars\n- Gaming",
		},
		{
			name:   "DEBUG marker stripped",
			input:  "## Strategy\nPost on Thursday\n\nDEBUG:\nValidation passed",
			expect: "## Strategy\nPost on Thursday",
		},
		{
			name:   "Multiple markers - first one truncates",
			input:  "Content here\n\nREPAIR:\nFix this\n\nDEBUG:\nMore debug",
			expect: "Content here",
		},
		{
			name:   "VALIDATION marker stripped",
			input:  "## Schedule\nWeek 1\n\nVALIDATION\nPassed all checks",
			expect: "## Schedule\nWeek 1",
		},
		{
			name:   "PREVIOUS OUTPUT marker stripped",
			input:  "New content\n\nPREVIOUS OUTPUT\nOld content here",
			expect: "New content",
		},
		// NEW: Additional markers to strip
		{
			name:   "OFFENDING LINES stripped",
			input:  "Good content\n\nOFFENDING LINES:\nL5: bad line",
			expect: "Good content",
		},
		{
			name:   "REGENERATION REQUIRED stripped",
			input:  "Strategy here\n\nREGENERATION REQUIRED\nPlease fix",
			expect: "Strategy here",
		},
		{
			name:   "Removed: stripped",
			input:  "Content\n\nRemoved: competitor tag\nMore content",
			expect: "Content",
		},
		{
			name:   "ERRORS: stripped",
			input:  "Valid strategy\n\nERRORS:\n- Issue 1\n- Issue 2",
			expect: "Valid strategy",
		},
		{
			name:   "Note: stripped",
			input:  "Good strategy\n\nNote: This was regenerated",
			expect: "Good strategy",
		},
		{
			name:   "Case insensitive stripping",
			input:  "Content\n\noffending lines:\nBad stuff",
			expect: "Content",
		},
		// NEW: Additional repair prompt leakage markers
		{
			name:   "PROBLEMS: stripped (repair prompt leakage)",
			input:  "Good content\n\nPROBLEMS:\n- Issue 1",
			expect: "Good content",
		},
		{
			name:   "RULES: stripped (repair prompt leakage)",
			input:  "Content here\n\nRULES:\n1. No URLs",
			expect: "Content here",
		},
		{
			name:   "RETRY stripped (repair prompt leakage)",
			input:  "Strategy output\n\nRETRY - generate clean version",
			expect: "Strategy output",
		},
		{
			name:   "NOTE: uppercase stripped",
			input:  "Valid output\n\nNOTE: Model generated this",
			expect: "Valid output",
		},
		{
			name:   "PROBLEM LINES stripped",
			input:  "Good strategy\n\nPROBLEM LINES:\n- Line 5: bad",
			expect: "Good strategy",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := StripInternalMeta(tt.input)
			if got != tt.expect {
				t.Errorf("StripInternalMeta() = %q, want %q", got, tt.expect)
			}
		})
	}
}

func TestContainsInternalMeta(t *testing.T) {
	tests := []struct {
		name   string
		input  string
		expect bool
	}{
		{"No meta", "Normal content here", false},
		{"Contains REPAIR:", "Some text REPAIR: fix this", true},
		{"Contains DEBUG:", "Output DEBUG: test", true},
		{"Contains VALIDATION", "Check VALIDATION status", true},
		{"Contains INVALID OUTPUT", "INVALID OUTPUT detected", true},
		{"Case insensitive repair", "repair: something", true},
		{"Case insensitive debug", "debug: info", true},
		{"Partial match - repair without colon", "This needs repair soon", false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := ContainsInternalMeta(tt.input)
			if got != tt.expect {
				t.Errorf("ContainsInternalMeta(%q) = %v, want %v", tt.input, got, tt.expect)
			}
		})
	}
}

func TestCheckInternalMetaViolation(t *testing.T) {
	tests := []struct {
		name    string
		input   string
		wantOk  bool
		wantErr string
	}{
		{"Clean output", "## Content\n- Item 1\n- Item 2", true, ""},
		{"REPAIR marker", "Content\nREPAIR: Regenerated", false, "INTERNAL_META_VIOLATION"},
		{"DEBUG marker", "Content\nDEBUG: Testing", false, "INTERNAL_META_VIOLATION"},
		{"VALIDATION marker", "Output\nVALIDATION passed", false, "INTERNAL_META_VIOLATION"},
		{"INVALID OUTPUT", "INVALID OUTPUT: try again", false, "INTERNAL_META_VIOLATION"},
		// NEW: Additional meta markers to block
		{"OFFENDING LINES marker", "Content\nOFFENDING LINES:\n- Line 5", false, "INTERNAL_META_VIOLATION"},
		{"OFFENDING SNIPPETS marker", "Content\nOFFENDING SNIPPETS here", false, "INTERNAL_META_VIOLATION"},
		{"Removed marker", "Content\nRemoved: competitor hashtag", false, "INTERNAL_META_VIOLATION"},
		{"REGENERATION REQUIRED", "REGENERATION REQUIRED\nContent here", false, "INTERNAL_META_VIOLATION"},
		{"VIOLATIONS FOUND", "VIOLATIONS FOUND:\n- Issue 1", false, "INTERNAL_META_VIOLATION"},
		{"ERRORS marker", "ERRORS:\n- Something wrong", false, "INTERNAL_META_VIOLATION"},
		{"ISSUES FOUND", "ISSUES FOUND in output", false, "INTERNAL_META_VIOLATION"},
		{"BANNED TOKENS", "BANNED TOKENS: #competitor", false, "INTERNAL_META_VIOLATION"},
		{"[REMOVED] marker", "Content [REMOVED] more content", false, "INTERNAL_META_VIOLATION"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ok, issue := CheckInternalMetaViolation(tt.input)
			if ok != tt.wantOk {
				t.Errorf("CheckInternalMetaViolation() ok = %v, want %v", ok, tt.wantOk)
			}
			if !tt.wantOk && !strings.Contains(issue, tt.wantErr) {
				t.Errorf("CheckInternalMetaViolation() issue = %q, want to contain %q", issue, tt.wantErr)
			}
		})
	}
}

// =============================================================================
// NEW TESTS: Hashtags in Schedule Detection
// =============================================================================

func TestCheckHashtagsInSchedule(t *testing.T) {
	tests := []struct {
		name    string
		output  string
		wantOk  bool
		wantErr string
	}{
		{
			name: "Clean schedule - no hashtags",
			output: `## 2-Week Schedule
Week 1:
- Thursday: Behind-the-scenes content
- Sunday: Character reveal
Week 2:
- Thursday: Gameplay teaser
- Sunday: Community poll

## Hashtag Pack
#indiegame #gaming`,
			wantOk: true,
		},
		{
			name: "Hashtag in schedule line",
			output: `## 2-Week Schedule
Week 1:
- Thursday: Behind-the-scenes #bts content
- Sunday: Character reveal

## Hashtag Pack
#indiegame`,
			wantOk:  false,
			wantErr: "HASHTAGS_IN_SCHEDULE_VIOLATION",
		},
		{
			name: "Hashtag at end of schedule line",
			output: `## 2-Week Schedule
Week 1:
- Thursday: Teaser post #teaser
Week 2:
- Thursday: More content

## Hook Ideas`,
			wantOk:  false,
			wantErr: "HASHTAGS_IN_SCHEDULE_VIOLATION",
		},
		{
			name: "Multiple hashtags in schedule",
			output: `## Schedule
Week 1:
- Monday: Post with #gaming #indie
- Wednesday: Another #post

## Hashtag Pack`,
			wantOk:  false,
			wantErr: "HASHTAGS_IN_SCHEDULE_VIOLATION",
		},
		{
			name: "Hashtags only in Hashtag Pack section - valid",
			output: `## Content Pillars
- Mystery

## 2-Week Schedule
Week 1:
- Thursday: Mystery reveal

## Hashtag Pack
#indiegame #mysterygame #gaming #boardgame #tabletop`,
			wantOk: true,
		},
		{
			name: "Markdown heading in schedule - not a violation",
			output: `## 2-Week Schedule
## Week 1
- Thursday: Content type

## Hook Ideas`,
			wantOk: true,
		},
		// NEW: Numbering like #2 should NOT trigger (false positive fix)
		{
			name: "Schedule with numbering #2 - NOT a violation",
			output: `## 2-Week Schedule
Week 1:
- Monday: Teaser Drop #2 - Second reveal
- Thursday: Character Spotlight #3
Week 2:
- Monday: Behind-the-scenes #1

## Hook Ideas`,
			wantOk: true,
		},
		{
			name: "Schedule with Part numbering - valid",
			output: `## 2-Week Schedule
Week 1:
- Monday: Teaser Part 2
- Thursday: Reveal (3)

## Hook Ideas`,
			wantOk: true,
		},
		// Real hashtag in schedule SHOULD trigger
		{
			name: "Schedule with real hashtag #gamedev - SHOULD fail",
			output: `## 2-Week Schedule
Week 1:
- Monday: Teaser Drop #gamedev content
- Thursday: More content

## Hook Ideas`,
			wantOk:  false,
			wantErr: "HASHTAGS_IN_SCHEDULE_VIOLATION",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ok, issue := CheckHashtagsInSchedule(tt.output)
			if ok != tt.wantOk {
				t.Errorf("CheckHashtagsInSchedule() ok = %v, want %v. Issue: %s", ok, tt.wantOk, issue)
			}
			if !tt.wantOk && !strings.Contains(issue, tt.wantErr) {
				t.Errorf("CheckHashtagsInSchedule() issue = %q, want to contain %q", issue, tt.wantErr)
			}
		})
	}
}

// =============================================================================
// NEW TESTS: Hashtags Outside Pack Detection (Hook Ideas, Pillars, etc.)
// =============================================================================

func TestCheckHashtagsOutsidePack(t *testing.T) {
	tests := []struct {
		name    string
		output  string
		wantOk  bool
		wantErr string
	}{
		{
			name: "Clean output - hashtags only in pack",
			output: `## Content Pillars
- Mystery themes
- Character reveals

## Hook Ideas
1. What lurks beneath the surface?
2. They're always watching...

## Hashtag Pack
#indiegame #gaming #mysterygame`,
			wantOk: true,
		},
		{
			name: "Hashtag in Hook Ideas - SHOULD fail",
			output: `## Hook Ideas
1. What's hiding? #mystery
2. They're watching...

## Hashtag Pack
#indiegame`,
			wantOk:  false,
			wantErr: "HASHTAGS_OUTSIDE_PACK_VIOLATION",
		},
		{
			name: "Multiple hashtags in Hook Ideas - SHOULD fail",
			output: `## Hook Ideas
1. Check this out #gamedev #indiegame
2. More hooks here

## Hashtag Pack
#gaming`,
			wantOk:  false,
			wantErr: "HASHTAGS_OUTSIDE_PACK_VIOLATION",
		},
		{
			name: "Hashtag in Content Pillars - SHOULD fail",
			output: `## Content Pillars
- Mystery #horror
- Action gameplay

## Hashtag Pack
#indiegame`,
			wantOk:  false,
			wantErr: "HASHTAGS_OUTSIDE_PACK_VIOLATION",
		},
		{
			name: "Numbering in Hook Ideas - should NOT fail",
			output: `## Hook Ideas
1. Teaser #2 is here!
2. Part #3 coming soon

## Hashtag Pack
#indiegame`,
			wantOk: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ok, issue := CheckHashtagsOutsidePack(tt.output)
			if ok != tt.wantOk {
				t.Errorf("CheckHashtagsOutsidePack() ok = %v, want %v. Issue: %s", ok, tt.wantOk, issue)
			}
			if !tt.wantOk && !strings.Contains(issue, tt.wantErr) {
				t.Errorf("CheckHashtagsOutsidePack() issue = %q, want to contain %q", issue, tt.wantErr)
			}
		})
	}
}

// =============================================================================
// NEW TESTS: Competitor Handle Detection (@handle and plain handle)
// =============================================================================

func TestCheckCompetitorHandleViolations(t *testing.T) {
	tests := []struct {
		name              string
		output            string
		competitorHandles []string
		wantIssues        int
		wantContains      string
	}{
		{
			name:              "No competitor handles - clean",
			output:            "Great strategy for #indiegame #gaming",
			competitorHandles: []string{"stickaround", "competitor"},
			wantIssues:        0,
		},
		{
			name:              "Hashtag form #competitor",
			output:            "Use hashtags like #stickaround for reach",
			competitorHandles: []string{"stickaround"},
			wantIssues:        1,
			wantContains:      "COMPETITOR_HANDLE_VIOLATION",
		},
		{
			name:              "Mention form @competitor",
			output:            "Check out @stickaround for inspiration",
			competitorHandles: []string{"stickaround"},
			wantIssues:        1,
			wantContains:      "COMPETITOR_HANDLE_VIOLATION",
		},
		{
			name:              "Plain word form competitor",
			output:            "We should study stickaround and their approach",
			competitorHandles: []string{"stickaround"},
			wantIssues:        1,
			wantContains:      "COMPETITOR_HANDLE_VIOLATION",
		},
		{
			name:              "All three forms",
			output:            "Look at #stickaround and @stickaround - stickaround is great",
			competitorHandles: []string{"stickaround"},
			wantIssues:        3,
		},
		{
			name:              "Competitor variant #competitorgame",
			output:            "Use #stickaroundgame as a reference",
			competitorHandles: []string{"stickaround"},
			wantIssues:        2, // Catches both #stickaround (substring) and #stickaroundgame (variant)
			wantContains:      "COMPETITOR_HANDLE_VIOLATION",
		},
		{
			name:              "Competitor variant @competitorofficial",
			output:            "Follow @stickaroundofficial",
			competitorHandles: []string{"stickaround"},
			wantIssues:        2, // Catches both @stickaround (substring) and @stickaroundofficial (variant)
			wantContains:      "COMPETITOR_HANDLE_VIOLATION",
		},
		{
			name:              "Case insensitive detection",
			output:            "Check #STICKAROUND and @StickarOund",
			competitorHandles: []string{"stickaround"},
			wantIssues:        2,
		},
		{
			name:              "Mixed case #StickAroundGame - SHOULD fail",
			output:            "Use #StickAroundGame for inspiration",
			competitorHandles: []string{"stickaround"},
			wantIssues:        2, // Catches both base and game variant
			wantContains:      "COMPETITOR_HANDLE_VIOLATION",
		},
		{
			name:              "Mixed case @StickAroundGame - SHOULD fail",
			output:            "Follow @StickAroundGame on social",
			competitorHandles: []string{"stickaround"},
			wantIssues:        2,
			wantContains:      "COMPETITOR_HANDLE_VIOLATION",
		},
		{
			name:              "Multiple competitors",
			output:            "Analyze #competitor1 and @competitor2",
			competitorHandles: []string{"competitor1", "competitor2"},
			wantIssues:        2,
		},
		{
			name:              "Partial match should NOT trigger (in middle of word)",
			output:            "The unsticking mechanism is interesting",
			competitorHandles: []string{"stick"},
			wantIssues:        0,
		},
		{
			name:              "Short handle (< 3 chars) ignored",
			output:            "Check out #ab and @ab",
			competitorHandles: []string{"ab"},
			wantIssues:        0,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			issues := CheckCompetitorHandleViolations(tt.output, tt.competitorHandles)
			if len(issues) != tt.wantIssues {
				t.Errorf("CheckCompetitorHandleViolations() got %d issues, want %d. Issues: %v", len(issues), tt.wantIssues, issues)
			}
			if tt.wantContains != "" && len(issues) > 0 {
				found := false
				for _, issue := range issues {
					if strings.Contains(issue, tt.wantContains) {
						found = true
						break
					}
				}
				if !found {
					t.Errorf("Issues should contain %q, got: %v", tt.wantContains, issues)
				}
			}
		})
	}
}

// =============================================================================
// NEW TESTS: Minimal Snippet Regen Builder
// =============================================================================

func TestExtractViolatingSnippets(t *testing.T) {
	tests := []struct {
		name              string
		output            string
		issues            []string
		competitorHandles []string
		maxSnippets       int
		wantMinSnippets   int
		wantMaxSnippets   int
	}{
		{
			name:            "URL violation extraction",
			output:          "Line 1\nCheck http://example.com\nLine 3",
			issues:          []string{"URL_VIOLATION"},
			maxSnippets:     5,
			wantMinSnippets: 1,
			wantMaxSnippets: 1,
		},
		{
			name:            "Multiple violations",
			output:          "Line 1\nhttp://test.com\nLine 3\nhttps://other.com\nLine 5",
			issues:          []string{"URL_VIOLATION"},
			maxSnippets:     5,
			wantMinSnippets: 2,
			wantMaxSnippets: 2,
		},
		{
			name:              "Competitor handle violation",
			output:            "Line 1\nUse #stickaround\nLine 3",
			issues:            []string{"COMPETITOR_HANDLE_VIOLATION"},
			competitorHandles: []string{"stickaround"},
			maxSnippets:       5,
			wantMinSnippets:   1,
			wantMaxSnippets:   1,
		},
		{
			name:            "REPAIR marker extraction",
			output:          "Content\nREPAIR: regenerated\nMore",
			issues:          []string{"INTERNAL_META_VIOLATION"},
			maxSnippets:     5,
			wantMinSnippets: 1,
			wantMaxSnippets: 1,
		},
		{
			name:            "Max snippets limit",
			output:          "http://1.com\nhttp://2.com\nhttp://3.com\nhttp://4.com\nhttp://5.com\nhttp://6.com",
			issues:          []string{"URL_VIOLATION"},
			maxSnippets:     3,
			wantMinSnippets: 3,
			wantMaxSnippets: 3,
		},
		{
			name:            "No violations - empty result",
			output:          "Clean content\nNo issues here\nAll good",
			issues:          []string{},
			maxSnippets:     5,
			wantMinSnippets: 0,
			wantMaxSnippets: 0,
		},
		{
			name: "Hashtag in schedule violation",
			output: `## 2-Week Schedule
Week 1:
- Thursday: Post with #hashtag
## Hook Ideas`,
			issues:          []string{"HASHTAGS_IN_SCHEDULE_VIOLATION"},
			maxSnippets:     5,
			wantMinSnippets: 1,
			wantMaxSnippets: 1,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			snippets := ExtractViolatingSnippets(tt.output, tt.issues, tt.competitorHandles, tt.maxSnippets, 800)
			if len(snippets) < tt.wantMinSnippets || len(snippets) > tt.wantMaxSnippets {
				t.Errorf("ExtractViolatingSnippets() got %d snippets, want between %d and %d. Snippets: %+v",
					len(snippets), tt.wantMinSnippets, tt.wantMaxSnippets, snippets)
			}
		})
	}
}

func TestBuildMinimalRepairPrompt(t *testing.T) {
	issues := []string{"URL_VIOLATION", "COMPETITOR_HANDLE_VIOLATION"}
	snippets := []ViolationSnippet{
		{LineNum: 5, Content: "Check http://example.com", Issue: "URL_VIOLATION"},
		{LineNum: 10, Content: "Use #competitor tag", Issue: "COMPETITOR_HANDLE_VIOLATION"},
	}
	bannedTokens := []string{"#stickaround", "@stickaround", "stickaround"}

	prompt := BuildMinimalRepairPrompt("Original prompt", issues, snippets, bannedTokens)

	// Check required elements - using NEW format that doesn't echo problematic words
	if !strings.Contains(prompt, "RETRY") {
		t.Error("Prompt should contain RETRY header")
	}
	if !strings.Contains(prompt, "PROBLEMS:") {
		t.Error("Prompt should list PROBLEMS")
	}
	if !strings.Contains(prompt, "Line 5:") {
		t.Error("Prompt should include line number 5")
	}
	if !strings.Contains(prompt, "Line 10:") {
		t.Error("Prompt should include line number 10")
	}
	if !strings.Contains(prompt, "RULES:") {
		t.Error("Prompt should contain RULES section")
	}
	if !strings.Contains(prompt, "FORBIDDEN WORDS/TAGS") {
		t.Error("Prompt should include banned tokens section")
	}
	if !strings.Contains(prompt, "#stickaround") {
		t.Error("Prompt should include banned token #stickaround")
	}

	// CRITICAL: Prompt should NOT contain words that model might echo
	if strings.Contains(prompt, "OFFENDING") {
		t.Error("Prompt should NOT contain 'OFFENDING' - model will echo it")
	}
	if strings.Contains(prompt, "VIOLATIONS FOUND") {
		t.Error("Prompt should NOT contain 'VIOLATIONS FOUND' - model will echo it")
	}
	if strings.Contains(prompt, "REGENERATION REQUIRED") {
		t.Error("Prompt should NOT contain 'REGENERATION REQUIRED' - model will echo it")
	}

	// Check it's reasonably sized (not bloated)
	if len(prompt) > 2000 {
		t.Errorf("Prompt seems too long (%d chars), should be minimal", len(prompt))
	}
}

func TestBuildBannedTokensList(t *testing.T) {
	handles := []string{"SticKAround", "Competitor"}
	tokens := BuildBannedTokensList(handles)

	// Should contain lowercase versions
	expectedTokens := []string{
		"stickaround", "#stickaround", "@stickaround",
		"stickaroundgame", "#stickaroundgame", "@stickaroundgame",
		"competitor", "#competitor", "@competitor",
	}

	for _, expected := range expectedTokens {
		found := false
		for _, token := range tokens {
			if token == expected {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("BuildBannedTokensList() missing expected token %q, got: %v", expected, tokens)
		}
	}
}

// =============================================================================
// NEW TESTS: Hashtag Normalization
// =============================================================================

func TestNormalizeStrategyHashtags(t *testing.T) {
	tests := []struct {
		name              string
		input             string
		allowedHashtags   []string
		competitorHandles []string
		wantContains      []string
		wantNotContains   []string
	}{
		{
			name: "Removes hashtags from schedule and rebuilds Hashtag Pack",
			input: `## 2-Week Schedule
Week 1:
- Monday: Teaser Drop #gamedev content
- Thursday: Behind-the-scenes #indiegame

## Hook Ideas
1. What lurks beneath?

## Hashtag Pack
#indiegame #gaming #mysterygame`,
			allowedHashtags:   []string{"indiegame", "gaming", "gamedev"},
			competitorHandles: []string{}, // No competitors
			// Now rebuilds pack deterministically from allowed hashtags, not preserving original pack content
			wantContains:    []string{"## Hashtag Pack", "#indiegame", "#gaming", "#gamedev", "Teaser Drop", "Behind-the-scenes"},
			wantNotContains: []string{"#gamedev content", "#indiegame\n\n## Hook"}, // Hashtags removed from schedule
		},
		{
			name: "Adds Hashtag Pack if missing",
			input: `## 2-Week Schedule
Week 1:
- Monday: Teaser content

## Hook Ideas
1. Mystery awaits`,
			allowedHashtags:   []string{"indiegame", "gaming", "boardgame"},
			competitorHandles: []string{},
			wantContains:      []string{"## Hashtag Pack", "#indiegame", "#gaming", "#boardgame"},
		},
		{
			name: "Does not remove numbering like #2",
			input: `## 2-Week Schedule
Week 1:
- Monday: Teaser Drop #2
- Thursday: Reveal #3

## Hashtag Pack
#indiegame`,
			allowedHashtags:   []string{"indiegame"},
			competitorHandles: []string{},
			wantContains:      []string{"Teaser Drop #2", "Reveal #3", "#indiegame"},
		},
		{
			name: "Removes hashtags from Hook Ideas",
			input: `## Hook Ideas
1. Mystery awaits #mystery
2. They're watching #suspense

## Hashtag Pack
#indiegame #gaming`,
			allowedHashtags:   []string{"indiegame", "gaming"},
			competitorHandles: []string{},
			wantContains:      []string{"Mystery awaits", "They're watching", "#indiegame", "#gaming"},
			wantNotContains:   []string{"#mystery", "#suspense"},
		},
		{
			name: "Populates empty Hashtag Pack",
			input: `## Content Pillars
- Mystery

## Hashtag Pack

## Notes`,
			allowedHashtags:   []string{"gamedev", "indiegame", "gaming"},
			competitorHandles: []string{},
			wantContains:      []string{"## Hashtag Pack", "#gamedev", "#indiegame", "#gaming"},
		},
		{
			name: "Handles multiple hashtags on same line",
			input: `## 2-Week Schedule
Week 1:
- Monday: Content #tag1 and #tag2 together

## Hashtag Pack
#existing`,
			allowedHashtags:   []string{"existing"},
			competitorHandles: []string{},
			wantContains:      []string{"Content", "together", "#existing"},
			wantNotContains:   []string{"#tag1", "#tag2"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := NormalizeStrategyHashtags(tt.input, tt.allowedHashtags, tt.competitorHandles)

			for _, want := range tt.wantContains {
				if !strings.Contains(result, want) {
					t.Errorf("NormalizeStrategyHashtags() result should contain %q\nGot:\n%s", want, result)
				}
			}

			for _, notWant := range tt.wantNotContains {
				if strings.Contains(result, notWant) {
					t.Errorf("NormalizeStrategyHashtags() result should NOT contain %q\nGot:\n%s", notWant, result)
				}
			}
		})
	}
}

func TestNormalizeStrategyHashtags_PreservesCompetitorHandles(t *testing.T) {
	// CRITICAL: Normalization must NEVER remove competitor handles
	// They must be PRESERVED so validation catches them and triggers regen/422

	tests := []struct {
		name              string
		input             string
		allowedHashtags   []string
		competitorHandles []string
		wantContains      []string // Competitor handles MUST remain
		wantNotContains   []string // Non-competitor hashtags should be removed
	}{
		{
			name: "Competitor hashtag in schedule is PRESERVED",
			input: `## 2-Week Schedule
Week 1:
- Monday: Check #stickaroundgame content

## Hashtag Pack
#indiegame`,
			allowedHashtags:   []string{"indiegame"},
			competitorHandles: []string{"stickaround"},
			wantContains:      []string{"#stickaroundgame", "#indiegame"}, // MUST keep competitor
		},
		{
			name: "Competitor hashtag in Hook Ideas is PRESERVED",
			input: `## Hook Ideas
1. Check out #stickaroundgame for ideas

## Hashtag Pack
#indiegame`,
			allowedHashtags:   []string{"indiegame"},
			competitorHandles: []string{"stickaround"},
			wantContains:      []string{"#stickaroundgame", "#indiegame"},
		},
		{
			name: "Competitor @mention is PRESERVED",
			input: `## Hook Ideas
1. Follow @stickaround for tips

## Hashtag Pack
#indiegame`,
			allowedHashtags:   []string{"indiegame"},
			competitorHandles: []string{"stickaround"},
			wantContains:      []string{"@stickaround", "#indiegame"},
		},
		{
			name: "Mixed: removes benign hashtag but preserves competitor",
			input: `## 2-Week Schedule
Week 1:
- Monday: Check #gamedev and #stickaroundgame content

## Hashtag Pack
#indiegame`,
			allowedHashtags:   []string{"indiegame"},
			competitorHandles: []string{"stickaround"},
			wantContains:      []string{"#stickaroundgame"}, // Competitor preserved
			// Note: #gamedev might also be preserved since line contains competitor
		},
		{
			name: "Benign hashtag removed from schedule, competitor line preserved",
			input: `## 2-Week Schedule
Week 1:
- Monday: Teaser #gamedev content
- Tuesday: Check #stickaroundgame stuff

## Hashtag Pack
#indiegame`,
			allowedHashtags:   []string{"indiegame"},
			competitorHandles: []string{"stickaround"},
			wantContains:      []string{"#stickaroundgame", "Teaser content"}, // Competitor line preserved, schedule cleaned
			wantNotContains:   []string{"#gamedev content"},                   // Benign hashtag removed from schedule line
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := NormalizeStrategyHashtags(tt.input, tt.allowedHashtags, tt.competitorHandles)

			for _, want := range tt.wantContains {
				if !strings.Contains(result, want) {
					t.Errorf("NormalizeStrategyHashtags() MUST contain %q (security: competitor must not be removed)\nGot:\n%s", want, result)
				}
			}

			for _, notWant := range tt.wantNotContains {
				if strings.Contains(result, notWant) {
					t.Errorf("NormalizeStrategyHashtags() should NOT contain %q\nGot:\n%s", notWant, result)
				}
			}
		})
	}
}

func TestIsOnlyHashtagPlacementViolation(t *testing.T) {
	tests := []struct {
		name   string
		issues []string
		want   bool
	}{
		{
			name:   "Empty issues - false",
			issues: []string{},
			want:   false,
		},
		{
			name:   "Only HASHTAGS_IN_SCHEDULE - true",
			issues: []string{"HASHTAGS_IN_SCHEDULE_VIOLATION: Found #gamedev in schedule"},
			want:   true,
		},
		{
			name:   "Only HASHTAGS_OUTSIDE_PACK - true",
			issues: []string{"HASHTAGS_OUTSIDE_PACK_VIOLATION: Found #tag in Hook Ideas"},
			want:   true,
		},
		{
			name: "Multiple hashtag violations - true",
			issues: []string{
				"HASHTAGS_IN_SCHEDULE_VIOLATION: Found #gamedev",
				"HASHTAGS_OUTSIDE_PACK_VIOLATION: Found #indie",
			},
			want: true,
		},
		{
			name: "Mixed with COMPETITOR_HANDLE_VIOLATION - false",
			issues: []string{
				"HASHTAGS_IN_SCHEDULE_VIOLATION: Found #gamedev",
				"COMPETITOR_HANDLE_VIOLATION: Found #stickaround",
			},
			want: false,
		},
		{
			name:   "Only COMPETITOR_HANDLE_VIOLATION - false",
			issues: []string{"COMPETITOR_HANDLE_VIOLATION: Found #stickaround"},
			want:   false,
		},
		{
			name:   "Only COMPETITOR_HASHTAG_VIOLATION - false",
			issues: []string{"COMPETITOR_HASHTAG_VIOLATION: Found #stickaroundgame"},
			want:   false,
		},
		{
			name:   "Only COMPETITOR_MENTION_VIOLATION - false",
			issues: []string{"COMPETITOR_MENTION_VIOLATION: Found @stickaround"},
			want:   false,
		},
		{
			name: "Hashtag placement + COMPETITOR_HASHTAG - false",
			issues: []string{
				"HASHTAGS_OUTSIDE_PACK_VIOLATION: Found #indie",
				"COMPETITOR_HASHTAG_VIOLATION: Found #stickaroundgame in Hook Ideas",
			},
			want: false,
		},
		{
			name:   "Only URL violation - false",
			issues: []string{"URL_VIOLATION: Found http://example.com"},
			want:   false,
		},
		{
			name:   "Only meta violation - false",
			issues: []string{"INTERNAL_META_VIOLATION: Found REPAIR:"},
			want:   false,
		},
		{
			name: "Hashtag + URL - false",
			issues: []string{
				"HASHTAGS_IN_SCHEDULE_VIOLATION: Found #tag",
				"URL_VIOLATION: Found URL",
			},
			want: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := IsOnlyHashtagPlacementViolation(tt.issues)
			if got != tt.want {
				t.Errorf("IsOnlyHashtagPlacementViolation() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestRemoveRealHashtags(t *testing.T) {
	tests := []struct {
		name  string
		input string
		want  string
	}{
		{
			name:  "Removes single hashtag",
			input: "Content #gamedev here",
			want:  "Content here",
		},
		{
			name:  "Removes multiple hashtags",
			input: "Check #tag1 and #tag2 together",
			want:  "Check and together",
		},
		{
			name:  "Preserves #2 numbering",
			input: "Teaser Drop #2 content",
			want:  "Teaser Drop #2 content",
		},
		{
			name:  "Preserves #3 numbering",
			input: "Part #3 reveal",
			want:  "Part #3 reveal",
		},
		{
			name:  "Mixed hashtag and numbering",
			input: "Teaser #2 with #gamedev tag",
			want:  "Teaser #2 with tag",
		},
		{
			name:  "Hashtag at end of line",
			input: "Content here #gamedev",
			want:  "Content here",
		},
		{
			name:  "Hashtag at start of line",
			input: "#gamedev content here",
			want:  "content here",
		},
		{
			name:  "No hashtags",
			input: "Plain content here",
			want:  "Plain content here",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := removeRealHashtags(tt.input)
			// Normalize spaces for comparison
			got = strings.TrimSpace(got)
			want := strings.TrimSpace(tt.want)
			if got != want {
				t.Errorf("removeRealHashtags() = %q, want %q", got, want)
			}
		})
	}
}

// =============================================================================
// INTEGRATION TEST: Full validation with all new rules
// =============================================================================

func TestValidateStrategyOutputWithConfig_AllNewRules(t *testing.T) {
	tests := []struct {
		name    string
		output  string
		config  StrategyValidationConfig
		wantOk  bool
		wantErr string
	}{
		{
			name: "REPAIR leakage should fail",
			output: `## Content Pillars
- Gaming
REPAIR: Regenerated due to previous issues`,
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyHard,
				RecommendedPostsPerWeek: 3,
			},
			wantOk:  false,
			wantErr: "INTERNAL_META_VIOLATION",
		},
		{
			name: "DEBUG leakage should fail",
			output: `## Strategy
Post on Thursday
DEBUG: Validation passed`,
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyHard,
				RecommendedPostsPerWeek: 3,
			},
			wantOk:  false,
			wantErr: "INTERNAL_META_VIOLATION",
		},
		{
			name: "Hashtag in schedule should fail",
			output: `## 2-Week Schedule
Week 1:
- Thursday: Mystery reveal #teaser
## Hashtag Pack
#indiegame`,
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyHard,
				RecommendedPostsPerWeek: 2,
			},
			wantOk:  false,
			wantErr: "HASHTAGS_IN_SCHEDULE_VIOLATION",
		},
		{
			name: "@competitor mention should fail",
			output: `## Strategy
Check @stickaround for inspiration`,
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyHard,
				RecommendedPostsPerWeek: 2,
				CompetitorHandles:       []string{"stickaround"},
			},
			wantOk:  false,
			wantErr: "COMPETITOR_HANDLE_VIOLATION",
		},
		{
			name: "Plain competitor name should fail",
			output: `## Strategy
Study how stickaround approaches their audience`,
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyHard,
				RecommendedPostsPerWeek: 2,
				CompetitorHandles:       []string{"stickaround"},
			},
			wantOk:  false,
			wantErr: "COMPETITOR_HANDLE_VIOLATION",
		},
		{
			name: "Clean output passes all checks",
			output: `## Content Pillars
- Gameplay mystery
- Character reveals

## Posting Cadence
PostsPerWeek: 2
Primary Day: Thursday

## 2-Week Schedule
Week 1:
- Thursday: Behind-the-scenes
- Sunday: Character tease
Week 2:
- Thursday: Gameplay snippet
- Sunday: Community prompt (question or poll)

## Hook Ideas
1. What lurks beneath?
2. They're watching...

## Hashtag Pack
#indiegame #mysterygame #gaming`,
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyHard,
				RecommendedPostsPerWeek: 2,
				CompetitorHandles:       []string{"stickaround", "competitor"},
			},
			wantOk: true,
		},
		// NEW: Additional integration tests
		{
			name: "OFFENDING LINES leakage should fail",
			output: `## Strategy
Content here
OFFENDING LINES:
L5: bad content`,
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyHard,
				RecommendedPostsPerWeek: 3,
			},
			wantOk:  false,
			wantErr: "INTERNAL_META_VIOLATION",
		},
		{
			name: "Removed: leakage should fail",
			output: `## Strategy
Content
Removed: competitor hashtag #stickaround`,
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyHard,
				RecommendedPostsPerWeek: 3,
			},
			wantOk:  false,
			wantErr: "INTERNAL_META_VIOLATION",
		},
		{
			name: "Mixed case #StickAroundGame should fail",
			output: `## Hook Ideas
1. Check out #StickAroundGame

## Hashtag Pack
#indiegame`,
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyHard,
				RecommendedPostsPerWeek: 2,
				CompetitorHandles:       []string{"stickaround"},
			},
			wantOk:  false,
			wantErr: "COMPETITOR_HANDLE_VIOLATION",
		},
		{
			name: "Hashtag in Hook Ideas should fail",
			output: `## Hook Ideas
1. Mystery awaits #gamedev
2. They're watching

## Hashtag Pack
#indiegame`,
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyHard,
				RecommendedPostsPerWeek: 2,
			},
			wantOk:  false,
			wantErr: "HASHTAGS_OUTSIDE_PACK_VIOLATION",
		},
		{
			name: "Schedule with numbering #2 should pass",
			output: `## 2-Week Schedule
Week 1:
- Monday: Mechanic tease #2
- Thursday: Feature reveal #3
Week 2:
- Monday: Behind-the-scenes dev snippet

## Hook Ideas
1. What lurks beneath?

## Hashtag Pack
#indiegame #gaming`,
			config: StrategyValidationConfig{
				Policy:                  CTAPolicyHard,
				RecommendedPostsPerWeek: 2,
			},
			wantOk: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ok, issues := ValidateStrategyOutputWithConfig(tt.output, tt.config)
			if ok != tt.wantOk {
				t.Errorf("ValidateStrategyOutputWithConfig() ok = %v, want %v. Issues: %v", ok, tt.wantOk, issues)
			}
			if !tt.wantOk && tt.wantErr != "" {
				found := false
				for _, issue := range issues {
					if strings.Contains(issue, tt.wantErr) {
						found = true
						break
					}
				}
				if !found {
					t.Errorf("Expected issue containing %q, got: %v", tt.wantErr, issues)
				}
			}
		})
	}
}

// =============================================================================
// NEW TESTS: Teaser Availability Language
// =============================================================================

func TestCheckTeaserAvailabilityLanguage(t *testing.T) {
	tests := []struct {
		name    string
		output  string
		wantOk  bool
		wantErr string
	}{
		{
			name:    "Clean teaser output - passes",
			output:  "Get ready for the first look at our mystery game. Something lurks beneath.",
			wantOk:  true,
			wantErr: "",
		},
		{
			name:    "Contains 'about to open its doors' - fails",
			output:  "The casino is about to open its doors to new players!",
			wantOk:  false,
			wantErr: "open its doors", // Matches first in the banned phrases list
		},
		{
			name:    "Contains 'opens its doors' - fails",
			output:  "Our game opens its doors next week.",
			wantOk:  false,
			wantErr: "opens its doors",
		},
		{
			name:    "Contains 'coming soon' - fails",
			output:  "The new update is coming soon to a store near you!",
			wantOk:  false,
			wantErr: "coming soon",
		},
		{
			name:    "Contains 'wishlist' - fails",
			output:  "Wishlist now on Steam!",
			wantOk:  false,
			wantErr: "wishlist",
		},
		{
			name:    "Contains 'link in bio' - fails",
			output:  "Check out the link in bio for more info.",
			wantOk:  false,
			wantErr: "link in bio",
		},
		{
			name:    "Contains 'out now' - fails",
			output:  "The game is out now on all platforms!",
			wantOk:  false,
			wantErr: "out now",
		},
		{
			name:    "Contains 'early access' - fails",
			output:  "Join our early access program today!",
			wantOk:  false,
			wantErr: "early access",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ok, issue := CheckTeaserAvailabilityLanguage(tt.output)
			if ok != tt.wantOk {
				t.Errorf("CheckTeaserAvailabilityLanguage() ok = %v, want %v", ok, tt.wantOk)
			}
			if !tt.wantOk && !strings.Contains(issue, tt.wantErr) {
				t.Errorf("Expected issue to contain %q, got: %s", tt.wantErr, issue)
			}
		})
	}
}

// =============================================================================
// NEW TESTS: Deterministic Hashtag Pack
// =============================================================================

func TestBuildFinalHashtagPack(t *testing.T) {
	tests := []struct {
		name            string
		observed        []string
		selfBrand       []string
		enableSelfBrand bool
		contextTags     []string
		enableContext   bool
		competitors     []string
		wantContains    []string
		wantNotContain  []string
		wantExactLen    int // Use -1 to skip exact length check
		wantMaxLen      int
	}{
		{
			name:          "Uses observed hashtags",
			observed:      []string{"gamedev", "indiegame", "gaming", "boardgame", "tabletop"},
			selfBrand:     nil,
			contextTags:   nil,
			enableContext: false,
			competitors:   nil,
			wantContains:  []string{"gamedev", "indiegame", "gaming"},
			wantExactLen:  5, // All 5 observed tags
			wantMaxLen:    5,
		},
		{
			name:            "Adds self-brand when enabled",
			observed:        []string{"gamedev", "indiegame"},
			selfBrand:       []string{"MyAwesomeGame"},
			enableSelfBrand: true,
			contextTags:     nil,
			enableContext:   false,
			competitors:     nil,
			wantContains:    []string{"gamedev", "indiegame", "myawesomegame"},
			wantExactLen:    3, // 2 observed + 1 self-brand
			wantMaxLen:      5,
		},
		{
			name:            "Ignores self-brand when disabled - returns exactly 2",
			observed:        []string{"gamedev", "indiegame"},
			selfBrand:       []string{"MyAwesomeGame"},
			enableSelfBrand: false,
			contextTags:     nil,
			enableContext:   false,
			competitors:     nil,
			wantContains:    []string{"gamedev", "indiegame"},
			wantNotContain:  []string{"myawesomegame", "gaming", "indie"}, // NO fallbacks
			wantExactLen:    2,                                            // Only 2 observed, no fallbacks added
			wantMaxLen:      5,
		},
		{
			name:           "Single observed tag returns exactly one - NO fallbacks",
			observed:       []string{"customtag"},
			selfBrand:      nil,
			contextTags:    nil,
			enableContext:  false,
			competitors:    nil,
			wantContains:   []string{"customtag"},
			wantNotContain: []string{"gamedev", "indiegame", "gaming", "indie", "games"}, // NO fallbacks
			wantExactLen:   1,                                                            // Only 1 tag, no fallbacks added
			wantMaxLen:     5,
		},
		{
			name:           "Empty observed returns empty - NO fallbacks",
			observed:       nil,
			selfBrand:      nil,
			contextTags:    nil,
			enableContext:  false,
			competitors:    nil,
			wantNotContain: []string{"gamedev", "indiegame", "gaming"}, // NO fallbacks
			wantExactLen:   0,                                          // Empty, no fallbacks added
			wantMaxLen:     5,
		},
		{
			name:          "Normalizes and dedupes",
			observed:      []string{"GameDev", "#indiegame", "  GAMING  ", "gamedev"},
			selfBrand:     nil,
			contextTags:   nil,
			enableContext: false,
			competitors:   nil,
			wantContains:  []string{"gamedev", "indiegame", "gaming"},
			wantExactLen:  3, // 3 unique after dedup
			wantMaxLen:    5,
		},
		{
			name:            "Two observed tags returns exactly two - critical test",
			observed:        []string{"gamedev", "indiegame"},
			selfBrand:       nil,
			enableSelfBrand: false,
			contextTags:     nil,
			enableContext:   false,
			competitors:     nil,
			wantContains:    []string{"gamedev", "indiegame"},
			wantNotContain:  []string{"gaming", "indie", "games"}, // NO fallbacks like #gaming
			wantExactLen:    2,                                    // EXACTLY 2, not 3 with fallback
			wantMaxLen:      5,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := BuildFinalHashtagPack(tt.observed, tt.selfBrand, tt.enableSelfBrand, tt.contextTags, tt.enableContext, tt.competitors)

			// Check exact length if specified
			if tt.wantExactLen >= 0 && len(result) != tt.wantExactLen {
				t.Errorf("BuildFinalHashtagPack() returned %d tags, want exactly %d. Got: %v", len(result), tt.wantExactLen, result)
			}
			if len(result) > tt.wantMaxLen {
				t.Errorf("BuildFinalHashtagPack() returned %d tags, want at most %d", len(result), tt.wantMaxLen)
			}

			// Check required tags are present
			for _, want := range tt.wantContains {
				found := false
				for _, tag := range result {
					if tag == want {
						found = true
						break
					}
				}
				if !found {
					t.Errorf("BuildFinalHashtagPack() should contain %q, got: %v", want, result)
				}
			}

			// Check forbidden tags are NOT present (no fallbacks)
			for _, notWant := range tt.wantNotContain {
				for _, tag := range result {
					if tag == notWant {
						t.Errorf("BuildFinalHashtagPack() should NOT contain fallback %q, got: %v", notWant, result)
					}
				}
			}

			// Verify no # prefix
			for _, tag := range result {
				if strings.HasPrefix(tag, "#") {
					t.Errorf("BuildFinalHashtagPack() should return plain tokens, got: %s", tag)
				}
			}
		})
	}
}

func TestReplaceOrAppendHashtagPack(t *testing.T) {
	tests := []struct {
		name       string
		input      string
		finalTags  []string
		wantResult string
	}{
		{
			name: "Replaces existing pack",
			input: `## Content Pillars
- Mystery
- Suspense

## Hashtag Pack
#oldtag1 #oldtag2 #duckculture`,
			finalTags:  []string{"gamedev", "indiegame"},
			wantResult: "#gamedev #indiegame",
		},
		{
			name: "Appends pack when missing",
			input: `## Content Pillars
- Mystery
- Suspense

## Hook Ideas
1. What lurks beneath?`,
			finalTags:  []string{"gamedev", "indiegame", "gaming"},
			wantResult: "## Hashtag Pack\n#gamedev #indiegame #gaming",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := ReplaceOrAppendHashtagPack(tt.input, tt.finalTags)

			if !strings.Contains(result, tt.wantResult) {
				t.Errorf("ReplaceOrAppendHashtagPack() should contain %q\nGot:\n%s", tt.wantResult, result)
			}
		})
	}
}

func TestCheckHashtagPackMembership(t *testing.T) {
	tests := []struct {
		name              string
		output            string
		allowed           map[string]struct{}
		competitorHandles []string
		wantOk            bool
		wantErr           string
	}{
		{
			name: "All tags in allowed set - passes",
			output: `## Hashtag Pack
#gamedev #indiegame #gaming`,
			allowed:           map[string]struct{}{"gamedev": {}, "indiegame": {}, "gaming": {}},
			competitorHandles: nil,
			wantOk:            true,
		},
		{
			name: "Invented tag 'duckculture' not in allowed - fails",
			output: `## Hashtag Pack
#gamedev #indiegame #duckculture`,
			allowed:           map[string]struct{}{"gamedev": {}, "indiegame": {}},
			competitorHandles: nil,
			wantOk:            false,
			wantErr:           "duckculture",
		},
		{
			name: "Competitor handle in pack - fails",
			output: `## Hashtag Pack
#gamedev #stickaroundgame`,
			allowed:           map[string]struct{}{"gamedev": {}, "stickaroundgame": {}},
			competitorHandles: []string{"stickaround"},
			wantOk:            false,
			wantErr:           "COMPETITOR",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ok, issue := CheckHashtagPackMembership(tt.output, tt.allowed, tt.competitorHandles)
			if ok != tt.wantOk {
				t.Errorf("CheckHashtagPackMembership() ok = %v, want %v. Issue: %s", ok, tt.wantOk, issue)
			}
			if !tt.wantOk && !strings.Contains(issue, tt.wantErr) {
				t.Errorf("Expected issue to contain %q, got: %s", tt.wantErr, issue)
			}
		})
	}
}

// =============================================================================
// NEW TESTS: Grounding / Anti-Hallucination
// =============================================================================

func TestCheckUngroundedFeatureClaims(t *testing.T) {
	tests := []struct {
		name            string
		output          string
		allowedKeywords map[string]struct{}
		wantOk          bool
		wantErr         string
	}{
		{
			name:            "Clean output without factual claims - passes",
			output:          "Experience the thrill of our mystery game. Something lurks beneath the surface.",
			allowedKeywords: map[string]struct{}{"mystery": {}, "game": {}, "thrill": {}},
			wantOk:          true,
		},
		{
			name:            "Hard claim 'rigged in favor' - fails",
			output:          "Our slot machines are rigged in favor of players!",
			allowedKeywords: map[string]struct{}{"game": {}, "casino": {}},
			wantOk:          false,
			wantErr:         "UNGROUNDED_CLAIM",
		},
		{
			name:            "Hard claim 'always win' - fails",
			output:          "Players always win at our casino tables.",
			allowedKeywords: map[string]struct{}{"game": {}, "fun": {}},
			wantOk:          false,
			wantErr:         "always win",
		},
		{
			name:            "Hard claim 'guaranteed win' - fails",
			output:          "Our roulette table offers guaranteed win on every spin.",
			allowedKeywords: map[string]struct{}{"game": {}},
			wantOk:          false,
			wantErr:         "guaranteed win",
		},
		{
			name:            "Hard claim 'can't lose' - fails",
			output:          "You can't lose at Monte Quacko!",
			allowedKeywords: map[string]struct{}{"game": {}},
			wantOk:          false,
			wantErr:         "can't lose",
		},
		{
			name:            "Legitimate use of game terms without claims - passes",
			output:          "Try our slot machine mini-game for a chance to win virtual rewards.",
			allowedKeywords: map[string]struct{}{"slot": {}, "game": {}, "rewards": {}},
			wantOk:          true,
		},
		// FALSE POSITIVE REGRESSION TESTS
		{
			name:            "REGRESSION: 'like never before' marketing phrase - passes",
			output:          "Get ready to bet, spin, and play like never before at Monte Quacko.",
			allowedKeywords: map[string]struct{}{"game": {}, "casino": {}},
			wantOk:          true,
		},
		{
			name:            "REGRESSION: 'never before seen' - passes",
			output:          "Experience never before seen gameplay mechanics.",
			allowedKeywords: map[string]struct{}{"game": {}},
			wantOk:          true,
		},
		{
			name:            "REGRESSION: 'ultimate' and 'biggest' intensifiers - passes",
			output:          "The ultimate casino experience with the biggest jackpots.",
			allowedKeywords: map[string]struct{}{"casino": {}, "jackpot": {}},
			wantOk:          true,
		},
		{
			name:            "REGRESSION: 'high-stakes' - passes",
			output:          "High-stakes action awaits you at every table.",
			allowedKeywords: map[string]struct{}{"game": {}},
			wantOk:          true,
		},
		{
			name:            "Hypothetical framing with 'imagine' - passes",
			output:          "Imagine winning big at every turn.",
			allowedKeywords: map[string]struct{}{"game": {}},
			wantOk:          true,
		},
		{
			name:            "Hypothetical framing with 'what if' - passes",
			output:          "What if you could always win? That's the dream.",
			allowedKeywords: map[string]struct{}{"game": {}},
			wantOk:          true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ok, issue := CheckUngroundedFeatureClaims(tt.output, tt.allowedKeywords)
			if ok != tt.wantOk {
				t.Errorf("CheckUngroundedFeatureClaims() ok = %v, want %v. Issue: %s", ok, tt.wantOk, issue)
			}
			if !tt.wantOk && !strings.Contains(issue, tt.wantErr) {
				t.Errorf("Expected issue to contain %q, got: %s", tt.wantErr, issue)
			}
		})
	}
}

func TestBuildContextKeywordSet(t *testing.T) {
	keywords := BuildContextKeywordSet("casino/gambling", "slots, poker, blackjack", "fun and exciting", "casual mobile", "card games for all ages")

	expectedKeywords := []string{"casino", "gambling", "slots", "poker", "blackjack", "fun", "exciting", "casual", "mobile", "card", "games", "ages"}

	for _, expected := range expectedKeywords {
		if _, ok := keywords[expected]; !ok {
			t.Errorf("BuildContextKeywordSet() should contain %q", expected)
		}
	}
}

// =============================================================================
// NEW TESTS: Hook Sanitization
// =============================================================================

func TestSanitizeCompetitorHook(t *testing.T) {
	tests := []struct {
		name              string
		hook              string
		competitorHandles []string
		wantNotContain    []string
	}{
		{
			name:              "Removes hashtags from hook",
			hook:              "Check out this amazing #gamedev tip! #indiegame",
			competitorHandles: nil,
			wantNotContain:    []string{"#gamedev", "#indiegame"},
		},
		{
			name:              "Removes @mentions from hook",
			hook:              "Follow @stickaround for more tips!",
			competitorHandles: []string{"stickaround"},
			wantNotContain:    []string{"@stickaround"},
		},
		{
			name:              "Removes competitor handles",
			hook:              "Better than stickaround's approach to game marketing.",
			competitorHandles: []string{"stickaround"},
			wantNotContain:    []string{"stickaround"},
		},
		{
			name:              "Removes competitor hashtags",
			hook:              "Unlike #stickaroundgame, our game is...",
			competitorHandles: []string{"stickaround"},
			wantNotContain:    []string{"#stickaroundgame"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := SanitizeCompetitorHook(tt.hook, tt.competitorHandles)

			for _, notWant := range tt.wantNotContain {
				if strings.Contains(strings.ToLower(result), strings.ToLower(notWant)) {
					t.Errorf("SanitizeCompetitorHook() should NOT contain %q, got: %s", notWant, result)
				}
			}
		})
	}
}

func TestDescribeHookStyle(t *testing.T) {
	tests := []struct {
		name        string
		hook        string
		wantContain string
	}{
		{
			name:        "Question hook",
			hook:        "Why do players keep coming back?",
			wantContain: "question",
		},
		{
			name:        "Short hook",
			hook:        "Game on!",
			wantContain: "short",
		},
		{
			name:        "Hook with line breaks",
			hook:        "First line\nSecond line\nThird line",
			wantContain: "line breaks",
		},
		{
			name:        "Empty hook",
			hook:        "",
			wantContain: "unknown",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := DescribeHookStyle(tt.hook)

			if !strings.Contains(strings.ToLower(result), strings.ToLower(tt.wantContain)) {
				t.Errorf("DescribeHookStyle() should contain %q, got: %s", tt.wantContain, result)
			}
		})
	}
}

// =============================================================================
// NEW TESTS: Hashtag Candidates Parsing and Filtering
// =============================================================================

func TestParseHashtagCandidates(t *testing.T) {
	input := `## Content Pillars
- Mystery

## Hashtag Candidates (no #)
gamedev
indiegame
mysterygame
boardgame
tabletop

## Hook Ideas
1. What lurks beneath?`

	candidates := ParseHashtagCandidates(input)

	expectedCandidates := []string{"gamedev", "indiegame", "mysterygame", "boardgame", "tabletop"}
	for _, expected := range expectedCandidates {
		found := false
		for _, c := range candidates {
			if c == expected {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("ParseHashtagCandidates() should contain %q, got: %v", expected, candidates)
		}
	}
}

func TestFilterCandidates(t *testing.T) {
	tests := []struct {
		name              string
		candidates        []string
		contextKeywords   map[string]struct{}
		competitorHandles []string
		stoplist          map[string]bool
		wantContains      []string
		wantNotContains   []string
	}{
		{
			name:            "Filters to relevant keywords",
			candidates:      []string{"gamedev", "cooking", "mysterygame", "fashion"},
			contextKeywords: map[string]struct{}{"game": {}, "mystery": {}, "dev": {}},
			wantContains:    []string{"gamedev", "mysterygame"},
			wantNotContains: []string{"cooking", "fashion"},
		},
		{
			name:              "Removes competitor handles",
			candidates:        []string{"gamedev", "stickaroundgame", "indiegame"},
			contextKeywords:   map[string]struct{}{"game": {}, "indie": {}},
			competitorHandles: []string{"stickaround"},
			wantContains:      []string{"gamedev", "indiegame"},
			wantNotContains:   []string{"stickaroundgame"},
		},
		{
			name:            "Removes stoplist items",
			candidates:      []string{"gamedev", "fyp", "viral", "indiegame"},
			contextKeywords: map[string]struct{}{"game": {}, "indie": {}},
			stoplist:        HashtagStoplist,
			wantContains:    []string{"gamedev", "indiegame"},
			wantNotContains: []string{"fyp", "viral"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := FilterCandidates(tt.candidates, tt.contextKeywords, tt.competitorHandles, tt.stoplist)

			for _, want := range tt.wantContains {
				found := false
				for _, c := range result {
					if c == want {
						found = true
						break
					}
				}
				if !found {
					t.Errorf("FilterCandidates() should contain %q, got: %v", want, result)
				}
			}

			for _, notWant := range tt.wantNotContains {
				for _, c := range result {
					if c == notWant {
						t.Errorf("FilterCandidates() should NOT contain %q, got: %v", notWant, result)
					}
				}
			}
		})
	}
}

// =============================================================================
// NEW TESTS: Normalization with Deterministic Pack
// =============================================================================

func TestNormalizeStrategyHashtagsExtended(t *testing.T) {
	tests := []struct {
		name              string
		input             string
		observedHashtags  []string
		selfBrandHashtags []string
		enableSelfBrand   bool
		competitorHandles []string
		wantContains      []string
		wantNotContains   []string
	}{
		{
			name: "Replaces invented tags with deterministic pack",
			input: `## Content Pillars
- Mystery

## Hashtag Pack
#gamedev #indiegame #duckculture`,
			observedHashtags: []string{"gamedev", "indiegame", "boardgame"},
			wantContains:     []string{"#gamedev", "#indiegame", "#boardgame"},
			wantNotContains:  []string{"#duckculture"},
		},
		{
			name: "Preserves competitor handles for validation",
			input: `## Hook Ideas
1. Check out #stickaroundgame

## Hashtag Pack
#gamedev`,
			observedHashtags:  []string{"gamedev", "indiegame"},
			competitorHandles: []string{"stickaround"},
			wantContains:      []string{"#stickaroundgame"}, // Must be preserved
		},
		{
			name: "Removes hashtags outside pack",
			input: `## 2-Week Schedule
- Monday: Teaser #gamedev content

## Hashtag Pack
#indiegame`,
			observedHashtags: []string{"indiegame", "gamedev", "gaming"},
			wantNotContains:  []string{"#gamedev content"}, // Removed from schedule
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := NormalizeStrategyHashtagsExtended(
				tt.input,
				tt.observedHashtags,
				tt.selfBrandHashtags,
				tt.enableSelfBrand,
				nil,
				false,
				tt.competitorHandles,
			)

			for _, want := range tt.wantContains {
				if !strings.Contains(result, want) {
					t.Errorf("NormalizeStrategyHashtagsExtended() should contain %q\nGot:\n%s", want, result)
				}
			}

			for _, notWant := range tt.wantNotContains {
				if strings.Contains(result, notWant) {
					t.Errorf("NormalizeStrategyHashtagsExtended() should NOT contain %q\nGot:\n%s", notWant, result)
				}
			}
		})
	}
}

// =============================================================================
// NEW TESTS: IsOnlyHashtagPlacementViolation extended
// =============================================================================

func TestIsOnlyHashtagPlacementViolation_Extended(t *testing.T) {
	tests := []struct {
		name   string
		issues []string
		want   bool
	}{
		{
			name:   "Only HASHTAG_PACK_MEMBERSHIP - true",
			issues: []string{"HASHTAG_PACK_MEMBERSHIP_VIOLATION: Invalid hashtag #duckculture"},
			want:   true,
		},
		{
			name:   "Only INVALID_HASHTAG - true",
			issues: []string{"INVALID_HASHTAG_VIOLATION: Found invented tag"},
			want:   true,
		},
		{
			name: "Mixed hashtag membership + placement - true",
			issues: []string{
				"HASHTAGS_OUTSIDE_PACK_VIOLATION: Found #tag",
				"HASHTAG_PACK_MEMBERSHIP_VIOLATION: Invalid hashtag",
			},
			want: true,
		},
		{
			name: "Hashtag + competitor violation - false",
			issues: []string{
				"HASHTAG_PACK_MEMBERSHIP_VIOLATION: Invalid hashtag",
				"COMPETITOR_HANDLE_VIOLATION: Found #stickaround",
			},
			want: false,
		},
		{
			name:   "Teaser language violation - false",
			issues: []string{"TEASER_LANGUAGE_VIOLATION: Found banned phrase"},
			want:   false,
		},
		{
			name:   "Ungrounded claim violation - false",
			issues: []string{"UNGROUNDED_CLAIM_VIOLATION: Unverifiable claim"},
			want:   false,
		},
		{
			name:   "Placeholder violation blocks fast-path",
			issues: []string{"PLACEHOLDER_VIOLATION: Output contains placeholders"},
			want:   false,
		},
		{
			name:   "Schedule incomplete violation blocks fast-path",
			issues: []string{"SCHEDULE_INCOMPLETE_VIOLATION: Line 12 schedule entry is too short"},
			want:   false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := IsOnlyHashtagPlacementViolation(tt.issues)
			if got != tt.want {
				t.Errorf("IsOnlyHashtagPlacementViolation() = %v, want %v", got, tt.want)
			}
		})
	}
}

// =============================================================================
// NEW TESTS: Truncation After Hashtag Pack
// =============================================================================

func TestTruncateAfterHashtagPack(t *testing.T) {
	tests := []struct {
		name           string
		input          string
		wantContains   []string
		wantNotContain []string
	}{
		{
			name: "Removes trailing paragraph after Hashtag Pack",
			input: `## Content Pillars
- Mystery
- Suspense

## Hashtag Pack
#gamedev #indiegame

This is extra narrative that should be removed.
Another trailing paragraph here.`,
			wantContains:   []string{"## Hashtag Pack", "#gamedev #indiegame", "## Content Pillars"},
			wantNotContain: []string{"extra narrative", "trailing paragraph"},
		},
		{
			name: "Keeps content before Hashtag Pack intact",
			input: `## Content Pillars
- Mystery
- Suspense

## Hook Ideas
1. What lurks beneath?
2. They're watching.

## Hashtag Pack
#indiegame #gaming

Note: this should be removed`,
			wantContains:   []string{"## Content Pillars", "## Hook Ideas", "What lurks beneath", "#indiegame #gaming"},
			wantNotContain: []string{"Note: this should be removed"},
		},
		{
			name: "Handles output with no trailing content",
			input: `## Content Pillars
- Gaming

## Hashtag Pack
#gamedev`,
			wantContains:   []string{"## Content Pillars", "## Hashtag Pack", "#gamedev"},
			wantNotContain: []string{},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := TruncateAfterHashtagPack(tt.input)

			for _, want := range tt.wantContains {
				if !strings.Contains(result, want) {
					t.Errorf("TruncateAfterHashtagPack() should contain %q\nGot:\n%s", want, result)
				}
			}

			for _, notWant := range tt.wantNotContain {
				if strings.Contains(result, notWant) {
					t.Errorf("TruncateAfterHashtagPack() should NOT contain %q\nGot:\n%s", notWant, result)
				}
			}
		})
	}
}

func TestCheckContentAfterHashtagPack(t *testing.T) {
	tests := []struct {
		name    string
		output  string
		wantOk  bool
		wantErr string
	}{
		{
			name: "No content after pack - passes",
			output: `## Content Pillars
- Gaming

## Hashtag Pack
#gamedev #indiegame`,
			wantOk: true,
		},
		{
			name: "Trailing paragraph after pack - fails",
			output: `## Content Pillars
- Gaming

## Hashtag Pack
#gamedev #indiegame

This is extra content that shouldn't be here.`,
			wantOk:  false,
			wantErr: "CONTENT_AFTER_HASHTAG_PACK",
		},
		{
			name: "Empty lines after pack - passes",
			output: `## Hashtag Pack
#gamedev

`,
			wantOk: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ok, issue := CheckContentAfterHashtagPack(tt.output)
			if ok != tt.wantOk {
				t.Errorf("CheckContentAfterHashtagPack() ok = %v, want %v. Issue: %s", ok, tt.wantOk, issue)
			}
			if !tt.wantOk && !strings.Contains(issue, tt.wantErr) {
				t.Errorf("Expected issue containing %q, got: %s", tt.wantErr, issue)
			}
		})
	}
}

func TestExtractHashtagPackLine(t *testing.T) {
	tests := []struct {
		name   string
		output string
		want   string
	}{
		{
			name: "Extracts hashtag line",
			output: `## Hashtag Pack
#gamedev #indiegame #gaming`,
			want: "#gamedev #indiegame #gaming",
		},
		{
			name: "No hashtag pack - returns none found",
			output: `## Content Pillars
- Gaming`,
			want: "(none found)",
		},
		{
			name: "Empty hashtag pack - returns none found",
			output: `## Hashtag Pack

## Notes`,
			want: "(none found)",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := extractHashtagPackLine(tt.output)
			if got != tt.want {
				t.Errorf("extractHashtagPackLine() = %q, want %q", got, tt.want)
			}
		})
	}
}

// =============================================================================
// NEW TESTS: Final Assertions
// =============================================================================

func TestRunFinalAssertions(t *testing.T) {
	tests := []struct {
		name              string
		output            string
		allowedHashtags   map[string]struct{}
		competitorHandles []string
		wantIssueCount    int
		wantContains      string
	}{
		{
			name: "Clean output - no issues",
			output: `## Content Pillars
- Gaming

## Hashtag Pack
#gamedev #indiegame`,
			allowedHashtags:   map[string]struct{}{"gamedev": {}, "indiegame": {}},
			competitorHandles: []string{},
			wantIssueCount:    0,
		},
		{
			name: "Contains URL - assertion fails",
			output: `## Content
Check https://example.com

## Hashtag Pack
#gamedev`,
			allowedHashtags:   map[string]struct{}{"gamedev": {}},
			competitorHandles: []string{},
			wantIssueCount:    1,
			wantContains:      "URL",
		},
		{
			name: "Invalid hashtag in pack - assertion fails",
			output: `## Hashtag Pack
#gamedev #duckculture`,
			allowedHashtags:   map[string]struct{}{"gamedev": {}},
			competitorHandles: []string{},
			wantIssueCount:    1,
			wantContains:      "MEMBERSHIP",
		},
		{
			name: "Competitor handle - assertion fails",
			output: `## Content
Check out stickaround for tips

## Hashtag Pack
#gamedev`,
			allowedHashtags:   map[string]struct{}{"gamedev": {}},
			competitorHandles: []string{"stickaround"},
			wantIssueCount:    1,
			wantContains:      "competitor",
		},
		{
			name: "Hashtag outside pack - assertion fails",
			output: `## Content
Check out #gamedev tips

## Hashtag Pack
#indiegame`,
			allowedHashtags:   map[string]struct{}{"gamedev": {}, "indiegame": {}},
			competitorHandles: []string{},
			wantIssueCount:    1,
			wantContains:      "OUTSIDE_PACK",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			issues := runFinalAssertions(tt.output, tt.allowedHashtags, tt.competitorHandles, nil)

			if len(issues) != tt.wantIssueCount {
				t.Errorf("runFinalAssertions() returned %d issues, want %d. Issues: %v",
					len(issues), tt.wantIssueCount, issues)
			}

			if tt.wantContains != "" && len(issues) > 0 {
				found := false
				for _, issue := range issues {
					if strings.Contains(strings.ToUpper(issue), strings.ToUpper(tt.wantContains)) {
						found = true
						break
					}
				}
				if !found {
					t.Errorf("Expected issues to contain %q, got: %v", tt.wantContains, issues)
				}
			}
		})
	}
}

// =============================================================================
// NEW TESTS: Normalization Return Correctness
// =============================================================================

func TestNormalizationReturnsOnlyAllowedHashtags(t *testing.T) {
	// Simulate output with invented hashtags
	input := `## Content Pillars
- Gaming

## 2-Week Schedule
Week 1:
- Monday: Teaser content

## Hook Ideas
1. Mystery awaits

## Hashtag Pack
#gamedev #duckculture #montequacko #indiegame`

	allowedHashtags := []string{"gamedev", "indiegame", "gaming"}
	competitorHandles := []string{}

	// Run normalization
	result := NormalizeStrategyHashtagsExtended(input, allowedHashtags, nil, false, nil, false, competitorHandles)
	result = TruncateAfterHashtagPack(result)

	// Extract final hashtags
	packLine := extractHashtagPackLine(result)

	// Verify no invented hashtags remain
	if strings.Contains(packLine, "duckculture") {
		t.Errorf("Normalization failed: #duckculture still present in pack: %s", packLine)
	}
	if strings.Contains(packLine, "montequacko") {
		t.Errorf("Normalization failed: #montequacko still present in pack: %s", packLine)
	}

	// Verify allowed hashtags are present
	if !strings.Contains(packLine, "gamedev") {
		t.Errorf("Normalization failed: #gamedev should be present in pack: %s", packLine)
	}
	if !strings.Contains(packLine, "indiegame") {
		t.Errorf("Normalization failed: #indiegame should be present in pack: %s", packLine)
	}

	// Run final assertions to ensure it passes
	allowedSet := BuildAllowedHashtagSet(allowedHashtags, nil, false, nil, false, nil)
	issues := runFinalAssertions(result, allowedSet, competitorHandles, nil)
	if len(issues) > 0 {
		t.Errorf("Normalized output failed final assertions: %v", issues)
	}
}

func TestNormalizationMembershipEnforcement(t *testing.T) {
	// Only gamedev and indiegame are allowed
	allowedHashtags := []string{"gamedev", "indiegame"}

	input := `## Hashtag Pack
#gamedev #casino #montechuckto #duckgames`

	result := NormalizeStrategyHashtagsExtended(input, allowedHashtags, nil, false, nil, false, nil)
	result = TruncateAfterHashtagPack(result)

	packLine := extractHashtagPackLine(result)

	// Verify ONLY allowed hashtags are present
	if strings.Contains(packLine, "casino") {
		t.Errorf("Invented tag #casino still present: %s", packLine)
	}
	if strings.Contains(packLine, "montechuckto") {
		t.Errorf("Invented tag #montechuckto still present: %s", packLine)
	}
	if strings.Contains(packLine, "duckgames") {
		t.Errorf("Invented tag #duckgames still present: %s", packLine)
	}

	// Verify allowed tags are present
	if !strings.Contains(packLine, "gamedev") {
		t.Errorf("Allowed tag #gamedev missing: %s", packLine)
	}
	if !strings.Contains(packLine, "indiegame") {
		t.Errorf("Allowed tag #indiegame missing: %s", packLine)
	}

	// Verify membership validation passes
	allowedSet := BuildAllowedHashtagSet(allowedHashtags, nil, false, nil, false, nil)
	ok, issue := CheckHashtagPackMembership(result, allowedSet, nil)
	if !ok {
		t.Errorf("Membership check failed after normalization: %s", issue)
	}
}

// =============================================================================
// CRITICAL TEST: No Fallback/Generic Tags Added
// =============================================================================

func TestNoFallbackTagsAddedWhenNotInAllowed(t *testing.T) {
	// CRITICAL: This test ensures #gaming is NEVER added when not in allowed set
	// This was the bug: allowed = {gamedev, indiegame}, but output included #gaming

	allowedHashtags := []string{"gamedev", "indiegame"}

	// Build final pack - should be EXACTLY these 2 tags
	pack := BuildFinalHashtagPack(allowedHashtags, nil, false, nil, false, nil)

	// Verify exactly 2 tags returned
	if len(pack) != 2 {
		t.Errorf("Expected exactly 2 tags, got %d: %v", len(pack), pack)
	}

	// Verify #gaming is NOT present (it was being added as fallback)
	for _, tag := range pack {
		if tag == "gaming" {
			t.Errorf("CRITICAL: #gaming was added as fallback but is NOT in allowed set: %v", pack)
		}
		if tag == "indie" {
			t.Errorf("CRITICAL: #indie was added as fallback but is NOT in allowed set: %v", pack)
		}
		if tag == "games" {
			t.Errorf("CRITICAL: #games was added as fallback but is NOT in allowed set: %v", pack)
		}
	}

	// Verify only allowed tags are present
	for _, tag := range pack {
		if tag != "gamedev" && tag != "indiegame" {
			t.Errorf("Unexpected tag %q in pack - only gamedev and indiegame allowed: %v", tag, pack)
		}
	}
}

func TestMembershipRejectsGamingWhenNotAllowed(t *testing.T) {
	// Allowed set is ONLY {gamedev, indiegame}
	allowedSet := BuildAllowedHashtagSet([]string{"gamedev", "indiegame"}, nil, false, nil, false, nil)

	// Verify #gaming is NOT in allowed set
	if _, ok := allowedSet["gaming"]; ok {
		t.Errorf("CRITICAL: BuildAllowedHashtagSet is adding #gaming to allowed set when it shouldn't")
	}

	// Output with #gaming should FAIL membership
	outputWithGaming := `## Hashtag Pack
#gamedev #indiegame #gaming`

	ok, issue := CheckHashtagPackMembership(outputWithGaming, allowedSet, nil)
	if ok {
		t.Errorf("CRITICAL: Membership check passed but #gaming is not in allowed set")
	}
	if !strings.Contains(issue, "gaming") {
		t.Errorf("Expected issue to mention 'gaming', got: %s", issue)
	}
}

func TestBuildAllowedHashtagSetIsStrict(t *testing.T) {
	// Test that allowed set contains ONLY observed + selfBrand
	observed := []string{"gamedev", "indiegame"}
	allowedSet := BuildAllowedHashtagSet(observed, nil, false, nil, false, nil)

	// Should contain exactly these 2
	if len(allowedSet) != 2 {
		t.Errorf("Expected exactly 2 tags in allowed set, got %d: %v", len(allowedSet), allowedSet)
	}

	// Should contain the observed tags
	if _, ok := allowedSet["gamedev"]; !ok {
		t.Errorf("Missing 'gamedev' from allowed set")
	}
	if _, ok := allowedSet["indiegame"]; !ok {
		t.Errorf("Missing 'indiegame' from allowed set")
	}

	// Should NOT contain fallbacks
	for _, fallback := range []string{"gaming", "indie", "games"} {
		if _, ok := allowedSet[fallback]; ok {
			t.Errorf("CRITICAL: Allowed set contains fallback '%s' but it wasn't in observed list", fallback)
		}
	}
}

func TestEndToEndNormalizationNoFallbacks(t *testing.T) {
	// Simulates exact scenario from logs:
	// Observed: [gamedev, indiegame]
	// LLM outputs: #gamedev #indiegame #montequcko #duckcasino
	// After normalization: should be EXACTLY #gamedev #indiegame
	// NOT #gamedev #indiegame #gaming

	input := `## Content Pillars
- Gaming themes

## Hashtag Pack
#gamedev #indiegame #montequcko #duckcasino #customducks`

	allowedHashtags := []string{"gamedev", "indiegame"} // ONLY these two allowed

	result := NormalizeStrategyHashtagsExtended(input, allowedHashtags, nil, false, nil, false, nil)
	result = TruncateAfterHashtagPack(result)

	packLine := extractHashtagPackLine(result)

	// CRITICAL: #gaming should NOT appear
	if strings.Contains(strings.ToLower(packLine), "gaming") {
		t.Errorf("CRITICAL: #gaming appeared in pack but is NOT in allowed set. Pack: %s", packLine)
	}

	// Invented tags should be gone
	if strings.Contains(packLine, "montequcko") {
		t.Errorf("Invented tag #montequcko still present: %s", packLine)
	}
	if strings.Contains(packLine, "duckcasino") {
		t.Errorf("Invented tag #duckcasino still present: %s", packLine)
	}
	if strings.Contains(packLine, "customducks") {
		t.Errorf("Invented tag #customducks still present: %s", packLine)
	}

	// Only allowed tags should be present
	if !strings.Contains(packLine, "gamedev") {
		t.Errorf("Allowed tag #gamedev missing: %s", packLine)
	}
	if !strings.Contains(packLine, "indiegame") {
		t.Errorf("Allowed tag #indiegame missing: %s", packLine)
	}

	// Membership should pass
	allowedSet := BuildAllowedHashtagSet(allowedHashtags, nil, false, nil, false, nil)
	ok, issue := CheckHashtagPackMembership(result, allowedSet, nil)
	if !ok {
		t.Errorf("Membership check failed: %s", issue)
	}
}

// =============================================================================
// NEW TESTS: Self-brand + Context-derived Hashtags
// =============================================================================

func TestBuildSelfBrandHashtags(t *testing.T) {
	tags := BuildSelfBrandHashtags("Monte Quacko!", "", "Always Bet On Quack Studio")
	if len(tags) == 0 {
		t.Fatalf("Expected some self-brand tags, got none")
	}
	// Deterministic order: game name first
	if tags[0] != "montequacko" {
		t.Fatalf("Expected first tag to be 'montequacko', got %q (all: %v)", tags[0], tags)
	}
	for _, tag := range tags {
		if strings.Contains(tag, " ") || strings.Contains(tag, "-") {
			t.Fatalf("Self-brand tag should be slugified to a single token, got %q", tag)
		}
		if len(tag) < 4 {
			t.Fatalf("Self-brand tag too short: %q", tag)
		}
	}
}

func TestBuildContextDerivedHashtags_FilteringAndCap(t *testing.T) {
	// Includes some unsafe/stoplist-ish tokens and some safe ones
	context := map[string]struct{}{
		"multiplayer": {},
		"casino":      {},
		"game":        {}, // often generic/stoplist
		"thisiswaytoolongkeywordthatexceeds20chars": {},
	}
	competitors := []string{"stickaround"}
	got := BuildContextDerivedHashtags(context, competitors)
	if len(got) > 2 {
		t.Fatalf("Expected hard cap of 2 context-derived tags, got %d: %v", len(got), got)
	}
	for _, tag := range got {
		if len(tag) > 20 {
			t.Fatalf("Context-derived tag exceeds 20 chars: %q", tag)
		}
		if HashtagStoplist[tag] {
			t.Fatalf("Context-derived tag should not include stoplisted token: %q", tag)
		}
	}
}

func TestDeterministicPackIncludesSelfBrandWhenObservedSparse(t *testing.T) {
	observed := []string{"gamedev", "indiegame"}
	selfBrand := []string{"montequacko", "alwaysbetonquack"}
	contextTags := []string{"multiplayer"}

	pack := BuildFinalHashtagPack(observed, selfBrand, true, contextTags, true, nil)
	if len(pack) < 3 || len(pack) > 5 {
		t.Fatalf("Expected 3-5 tags when possible, got %d: %v", len(pack), pack)
	}
	// Must include observed first in stable order
	if pack[0] != "gamedev" || pack[1] != "indiegame" {
		t.Fatalf("Expected observed tags to be first, got: %v", pack)
	}
	// Must include at least one self-brand tag to reach 3
	foundSelf := false
	for _, t := range pack {
		if t == "montequacko" || t == "alwaysbetonquack" {
			foundSelf = true
			break
		}
	}
	if !foundSelf {
		t.Fatalf("Expected pack to include self-brand tags, got: %v", pack)
	}
}

func TestCompetitorSubstringIsRejectedFromAllowedAndPack(t *testing.T) {
	// Competitor handle "quacko" should block "montequacko" (contains competitor substring)
	competitors := []string{"quacko"}
	observed := []string{"gamedev", "indiegame"}
	selfBrand := []string{"montequacko", "alwaysbetonquack"}

	allowed := BuildAllowedHashtagSet(observed, selfBrand, true, nil, false, competitors)
	if _, ok := allowed["montequacko"]; ok {
		t.Fatalf("Expected montequacko to be excluded from allowed set due to competitor substring")
	}

	pack := BuildFinalHashtagPack(observed, selfBrand, true, nil, false, competitors)
	for _, tag := range pack {
		if strings.Contains(tag, "quacko") {
			t.Fatalf("Expected competitor substring to be rejected from pack, got: %v", pack)
		}
	}
}

func TestMembershipAcceptsSelfBrandAndContextWhenAllowed(t *testing.T) {
	observed := []string{"gamedev", "indiegame"}
	selfBrand := []string{"montequacko"}
	contextTags := []string{"multiplayer"}
	competitors := []string{}

	allowed := BuildAllowedHashtagSet(observed, selfBrand, true, contextTags, true, competitors)
	out := `## Hashtag Pack
#gamedev #indiegame #montequacko #multiplayer`
	ok, issue := CheckHashtagPackMembership(out, allowed, competitors)
	if !ok {
		t.Fatalf("Expected membership to pass for allowed self-brand/context tags, got: %s", issue)
	}
}

func TestDeterministicOrderingStable(t *testing.T) {
	observed := []string{"gamedev", "indiegame"}
	selfBrand := []string{"montequacko", "alwaysbetonquack"}
	contextTags := []string{"multiplayer", "casual"}
	competitors := []string{}

	a := BuildFinalHashtagPack(observed, selfBrand, true, contextTags, true, competitors)
	b := BuildFinalHashtagPack(observed, selfBrand, true, contextTags, true, competitors)
	if strings.Join(a, ",") != strings.Join(b, ",") {
		t.Fatalf("Expected deterministic ordering to be stable. A=%v B=%v", a, b)
	}
}

// =============================================================================
// NEW TESTS: Placeholder / Incompleteness
// =============================================================================

func TestCheckPlaceholderViolations(t *testing.T) {
	tests := []struct {
		name    string
		output  string
		wantOk  bool
		wantErr string
	}{
		{
			name: "Schedule contains [content type] placeholder - fails",
			output: `## 2-Week Schedule
Week 1:
- Monday: [content type]

## Hashtag Pack
#gamedev #indiegame`,
			wantOk:  false,
			wantErr: "PLACEHOLDER_VIOLATION",
		},
		{
			name: "Pillars contain [Pillar 1] placeholder - fails",
			output: `## Content Pillars
- [Pillar 1: theme/topic]

## Hashtag Pack
#gamedev #indiegame`,
			wantOk:  false,
			wantErr: "PLACEHOLDER_VIOLATION",
		},
		{
			name: "No placeholders - passes",
			output: `## Content Pillars
- Character customization spotlight
- Mini-game reveal
- Behind-the-scenes dev snippets

## 2-Week Schedule
Week 1:
- Monday: Character customization spotlight (feature + question)

## Hashtag Pack
#gamedev #indiegame`,
			wantOk: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ok, issue := CheckPlaceholderViolations(tt.output)
			if ok != tt.wantOk {
				t.Errorf("CheckPlaceholderViolations() ok = %v, want %v. Issue: %s", ok, tt.wantOk, issue)
			}
			if !tt.wantOk && !strings.Contains(issue, tt.wantErr) {
				t.Errorf("Expected issue to contain %q, got: %s", tt.wantErr, issue)
			}
		})
	}
}

func TestCheckScheduleLineQuality(t *testing.T) {
	tests := []struct {
		name    string
		output  string
		wantOk  bool
		wantErr string
	}{
		{
			name: "Too short after day - fails",
			output: `## 2-Week Schedule
Week 1:
- Thursday: teaser

## Hashtag Pack
#gamedev #indiegame`,
			wantOk:  false,
			wantErr: "SCHEDULE_INCOMPLETE_VIOLATION",
		},
		{
			name: "Bracket token in schedule - fails",
			output: `## 2-Week Schedule
Week 1:
- Monday: [content type]

## Hashtag Pack
#gamedev #indiegame`,
			wantOk:  false,
			wantErr: "SCHEDULE_INCOMPLETE_VIOLATION",
		},
		{
			name: "No content-type anchor - fails",
			output: `## 2-Week Schedule
Week 1:
- Monday: a post about the game world (no label)

## Hashtag Pack
#gamedev #indiegame`,
			wantOk:  false,
			wantErr: "SCHEDULE_INCOMPLETE_VIOLATION",
		},
		{
			name: "Valid schedule line with anchor - passes",
			output: `## 2-Week Schedule
Week 1:
- Monday: Mechanic tease (1 mechanic + 1 question)

## Hashtag Pack
#gamedev #indiegame`,
			wantOk: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ok, issue := CheckScheduleLineQuality(tt.output)
			if ok != tt.wantOk {
				t.Errorf("CheckScheduleLineQuality() ok = %v, want %v. Issue: %s", ok, tt.wantOk, issue)
			}
			if !tt.wantOk && !strings.Contains(issue, tt.wantErr) {
				t.Errorf("Expected issue to contain %q, got: %s", tt.wantErr, issue)
			}
		})
	}
}

// =============================================================================
// NEW TESTS: Generic Output / Context Keyword Hits
// =============================================================================

func TestCheckGenericOutput(t *testing.T) {
	context := map[string]struct{}{
		"duck":     {},
		"casino":   {},
		"minigame": {},
	}

	t.Run("Fails when <3 keyword hits outside Hashtag Pack", func(t *testing.T) {
		output := `## Content Pillars
- Behind-the-scenes
- Community prompts
- Gameplay clips

## 2-Week Schedule
Week 1:
- Monday: Behind-the-scenes dev snippet (clip concept)

## Hashtag Pack
#gamedev #indiegame #duck #casino #minigame`

		ok, issue := CheckGenericOutput(output, context, 3)
		if ok {
			t.Fatalf("Expected generic output to fail, but it passed")
		}
		if !strings.Contains(issue, "GENERIC_OUTPUT_VIOLATION") {
			t.Fatalf("Expected GENERIC_OUTPUT_VIOLATION, got: %s", issue)
		}
	})

	t.Run("Passes when >=3 keyword hits outside Hashtag Pack", func(t *testing.T) {
		output := `## Content Pillars
- Duck casino chaos
- Minigame reveals
- Behind-the-scenes dev snippets

## 2-Week Schedule
Week 1:
- Monday: Mini-game reveal (duck-themed mechanic tease)
- Wednesday: Behind-the-scenes dev snippet (casino UI iteration)

## Hashtag Pack
#gamedev #indiegame`

		ok, issue := CheckGenericOutput(output, context, 3)
		if !ok {
			t.Fatalf("Expected generic output to pass, but it failed: %s", issue)
		}
	})
}
