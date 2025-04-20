package utils

import (
	"errors"
	"os"
)

// ValidateRequest validates API request parameters
func ValidateRequest(sessionID, videoPath, caption string) error {
	if sessionID == "" {
		return errors.New("session_id is required")
	}
	if videoPath == "" {
		return errors.New("video_path is required")
	}
	if caption == "" {
		return errors.New("caption is required")
	}
	if _, err := os.Stat(videoPath); os.IsNotExist(err) {
		return errors.New("video file does not exist at the given path")
	}
	return nil
}
