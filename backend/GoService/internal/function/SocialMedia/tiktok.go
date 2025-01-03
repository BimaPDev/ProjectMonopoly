package socialmedia

import "net/http"

var (
	// Replace with your real TikTok app credentials
	tiktokClientID     = "awdbdgvy7hd38f6i"
	tiktokClientSecret = "5T94zTv0cXRt7lgut9S7MnkUPto4RKBI"
	tiktokRedirectURI  = "https://yourapp.com/tiktok/callback"

	// Create an OAuth2 config specifically for TikTok’s Open Platform
	tiktokOAuthConfig = &oauth2.Config{
		ClientID:     tiktokClientID,
		ClientSecret: tiktokClientSecret,
		RedirectURL:  tiktokRedirectURI,
		Scopes:       []string{"user.info.basic", "video.upload"}, // Add scopes as needed
		Endpoint: oauth2.Endpoint{
			// Check TikTok docs for the latest AuthURL and TokenURL
			AuthURL:  "https://www.tiktok.com/auth/authorize/",
			TokenURL: "https://open-api.tiktok.com/oauth/access_token/",
		},
	}
)

func tiktokFunction() {
	http.HandleFunc("/tiktok/login", handleTikTokLogin)
	http.HandleFunc("/tiktok/callback", handleTikTokCallback)

}
