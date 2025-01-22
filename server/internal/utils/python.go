package utils

import (
	"bytes"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

// RunPythonScript executes the Python script with the provided arguments
func TikTokUpload(sessionID, videoPath, caption string, headless bool) (string, error) {
	// Get absolute video path
	absVideoPath, err := filepath.Abs(videoPath)
	if err != nil {
		return "", fmt.Errorf("failed to resolve video path: %v", err)
	}

	// Check if video file exists
	if _, err := os.Stat(absVideoPath); os.IsNotExist(err) {
		return "", fmt.Errorf("video file does not exist at path: %s", absVideoPath)
	}

	// Path to the Python script
	scriptPath := filepath.Join("python", "socialmedia", "tiktok.py")
	if _, err := os.Stat(scriptPath); os.IsNotExist(err) {
		return "", fmt.Errorf("Python script does not exist at path: %s", scriptPath)
	}

	// Detect Python command
	pythonCmd := DetectPythonCommand()

	// Build arguments
	args := []string{
		scriptPath,
		"--sessionid", sessionID,
		"--video", absVideoPath,
		"--caption", caption,
	}
	if headless {
		args = append(args, "--headless")
	}

	// Execute Python script
	var out bytes.Buffer
	var stderr bytes.Buffer
	cmd := exec.Command(pythonCmd, args...)
	cmd.Stdout = &out
	cmd.Stderr = &stderr

	err = cmd.Run()
	if err != nil {
		return "", fmt.Errorf("error executing Python script: %v\nStderr: %s", err, stderr.String())
	}

	return out.String(), nil
}

func GetFollowers(headless bool) (string, error) {
	// Path to the Python script
	scriptPath := filepath.Join("python", "followers", "getFollowers.py")
	if _, err := os.Stat(scriptPath); os.IsNotExist(err) {
		return "", fmt.Errorf("Python script does not exist at path: %s", scriptPath)
	}

	// Detect Python command
	pythonCmd := DetectPythonCommand()
	if pythonCmd == "" {
		return "", fmt.Errorf("could not detect Python command")
	}

	// Construct arguments
	args := []string{scriptPath}
	if headless {
		args = append(args, "--headless")
	}

	// Execute Python script
	var out bytes.Buffer
	var stderr bytes.Buffer
	cmd := exec.Command(pythonCmd, args...)
	cmd.Stdout = &out
	cmd.Stderr = &stderr
	err := cmd.Run()
	if err != nil {
		return "", fmt.Errorf("error executing Python script: %v\nStderr: %s", err, stderr.String())
	}
	return out.String(), nil
}

// DetectPythonCommand determines whether to use 'python' or 'python3'
func DetectPythonCommand() string {
	pythonCmd := "python"
	if _, err := exec.LookPath(pythonCmd); err != nil {
		pythonCmd = "python3"
		if _, err := exec.LookPath(pythonCmd); err != nil {
			panic("Neither 'python' nor 'python3' found in PATH")
		}
	}
	return pythonCmd
}

/*
USAGE:
{
    "model": "deepseek",
    "input": "What are the details in the CSV?"
}

this is what is supposed to be on the post request
*/

// TriggerModel executes a model based on the selected type (Python script or Go function).
func TriggerModel(model, input string) (string, error) {
	switch model {
	case "chatgpt":
		// Define the Python script path for ChatGPT
		scriptPath := filepath.Join("python", "models", "chatgpt.py")

		// Check if the Python script exists
		if _, err := os.Stat(scriptPath); os.IsNotExist(err) {
			return "", fmt.Errorf("Python script does not exist at path: %s", scriptPath)
		}

		// Detect Python command
		pythonCmd := DetectPythonCommand()

		// Build arguments
		args := []string{scriptPath, "--input", input}

		// Execute Python script
		var out bytes.Buffer
		var stderr bytes.Buffer
		cmd := exec.Command(pythonCmd, args...)
		cmd.Stdout = &out
		cmd.Stderr = &stderr

		err := cmd.Run()
		if err != nil {
			return "", fmt.Errorf("error executing chatgpt script: %v\nStderr: %s", err, stderr.String())
		}

		return out.String(), nil

	case "deepseek":
		// Call the Go function directly for DeepSeek
		return mainDeep(input)

	default:
		return "", fmt.Errorf("invalid model: %s", model)
	}
}