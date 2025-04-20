package utils

// PythonRequest represents the payload for interacting with the Python script.
type PythonRequest struct {
	SessionID string `json:"session_id"`
	VideoPath string `json:"video_path"`
	Caption   string `json:"caption"`
	Headless  bool   `json:"headless"`
}
