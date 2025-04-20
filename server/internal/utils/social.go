package utils

import (
	"fmt"
	"net/url"
	"strings"
)

type ParsedSocial struct {
	Platform   string
	Username   string
	ProfileURL string
}

// Normalize input and return clean platform, username, and profile URL
func ParseSocialInput(input string, platform string) (*ParsedSocial, error) {
	input = strings.TrimSpace(input)
	var username string

	// Handle @username
	if strings.HasPrefix(input, "@") {
		username = strings.TrimPrefix(input, "@")
	} else if u, err := url.Parse(input); err == nil && u.Host != "" {
		path := strings.Trim(u.Path, "/")
		username = strings.Split(path, "/")[0]
		if strings.Contains(u.Host, "tiktok") && strings.HasPrefix(username, "@") {
			username = strings.TrimPrefix(username, "@")
		}
	} else {
		// fallback if just the raw username
		username = input
	}

	var profileURL string
	switch platform {
	case "instagram":
		profileURL = fmt.Sprintf("https://www.instagram.com/%s", username)
	case "tiktok":
		profileURL = fmt.Sprintf("https://www.tiktok.com/@%s", username)
	case "twitter":
		profileURL = fmt.Sprintf("https://twitter.com/%s", username)
	default:
		return nil, fmt.Errorf("unsupported platform")
	}

	return &ParsedSocial{
		Platform:   platform,
		Username:   username,
		ProfileURL: profileURL,
	}, nil
}