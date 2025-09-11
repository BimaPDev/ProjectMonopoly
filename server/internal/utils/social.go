package utils

import (
	"encoding/json"
	"fmt"
	"net/url"
	"regexp"
	"strings"
)

// SocialRequest represents the incoming JSON request
type SocialRequest struct {
	Platform string `json:"platform"`
	Username string `json:"username"`
}

type ParsedSocial struct {
	Platform   string `json:"platform"`
	Username   string `json:"username"`
	ProfileURL string `json:"profile_url"`
}

// Platform configuration
type platformConfig struct {
	urlTemplate string
	domains     []string
	validator   *regexp.Regexp
}

var platforms = map[string]platformConfig{
	"instagram": {
		urlTemplate: "https://www.instagram.com/%s",
		domains:     []string{"instagram.com", "www.instagram.com"},
		validator:   regexp.MustCompile(`^[a-zA-Z0-9._]{1,30}$`),
	},
	"tiktok": {
		urlTemplate: "https://www.tiktok.com/@%s",
		domains:     []string{"tiktok.com", "www.tiktok.com"},
		validator:   regexp.MustCompile(`^[a-zA-Z0-9._]{1,24}$`),
	},
	"twitter": {
		urlTemplate: "https://twitter.com/%s",
		domains:     []string{"twitter.com", "www.twitter.com", "x.com", "www.x.com"},
		validator:   regexp.MustCompile(`^[a-zA-Z0-9_]{1,15}$`),
	},
}

// ParseSocialInput normalizes input and returns clean platform, username, and profile URL
func ParseSocialInput(input string, platform string) (*ParsedSocial, error) {
	input = strings.TrimSpace(input)

	if input == "" {
		return nil, fmt.Errorf("input cannot be empty")
	}

	// Check if platform is supported
	config, exists := platforms[strings.ToLower(platform)]
	if !exists {
		return nil, fmt.Errorf("unsupported platform: %s", platform)
	}

	username, err := extractUsername(input, platform, config)
	if err != nil {
		return nil, err
	}

	// Validate username
	if !config.validator.MatchString(username) {
		return nil, fmt.Errorf("invalid username format for %s: %s", platform, username)
	}

	profileURL := fmt.Sprintf(config.urlTemplate, username)

	return &ParsedSocial{
		Platform:   platform,
		Username:   username,
		ProfileURL: profileURL,
	}, nil
}

// ParseSocialJSON handles JSON input from frontend
func ParseSocialJSON(jsonInput string) (*ParsedSocial, error) {
	var req SocialRequest
	if err := json.Unmarshal([]byte(jsonInput), &req); err != nil {
		return nil, fmt.Errorf("failed to parse JSON: %v", err)
	}

	return ParseSocialInput(req.Username, req.Platform)
}

// extractUsername handles different input formats and extracts the username
func extractUsername(input, platform string, config platformConfig) (string, error) {
	// Handle @username format
	if strings.HasPrefix(input, "@") {
		username := strings.TrimPrefix(input, "@")
		if username == "" {
			return "", fmt.Errorf("username cannot be empty after @")
		}
		return username, nil
	}

	// Handle URL format
	if parsedURL, err := url.Parse(input); err == nil && parsedURL.Host != "" {
		return extractUsernameFromURL(parsedURL, platform, config)
	}

	// Handle raw username (fallback)
	if input == "" {
		return "", fmt.Errorf("username cannot be empty")
	}

	return input, nil
}

// extractUsernameFromURL extracts username from a social media URL
func extractUsernameFromURL(parsedURL *url.URL, platform string, config platformConfig) (string, error) {
	// Check if the URL belongs to the correct platform
	if !isDomainMatch(parsedURL.Host, config.domains) {
		return "", fmt.Errorf("URL domain does not match platform %s", platform)
	}

	path := strings.Trim(parsedURL.Path, "/")
	if path == "" {
		return "", fmt.Errorf("no username found in URL path")
	}

	// Split path and get the first segment (username)
	pathSegments := strings.Split(path, "/")
	username := pathSegments[0]

	// Handle TikTok's @username format in URLs
	if platform == "tiktok" && strings.HasPrefix(username, "@") {
		username = strings.TrimPrefix(username, "@")
	}

	if username == "" {
		return "", fmt.Errorf("username cannot be empty")
	}

	return username, nil
}

// isDomainMatch checks if the host matches any of the allowed domains
func isDomainMatch(host string, domains []string) bool {
	host = strings.ToLower(host)
	for _, domain := range domains {
		if host == domain {
			return true
		}
	}
	return false
}

// GetSupportedPlatforms returns a list of supported platforms
func GetSupportedPlatforms() []string {
	supportedPlatforms := make([]string, 0, len(platforms))
	for platform := range platforms {
		supportedPlatforms = append(supportedPlatforms, platform)
	}
	return supportedPlatforms
}

// IsValidPlatform checks if a platform is supported
func IsValidPlatform(platform string) bool {
	_, exists := platforms[platform]
	return exists
}
