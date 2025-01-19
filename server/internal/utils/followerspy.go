package utils

import (
	"bytes"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

// RunPythonScript executes the Python script with the provided arguments
func RunPythonScriptFollow(headless bool) (string, error) {
	fmt.Println("Running followerspy.go: RunPythonScript called") // Debugging message

	// Path to the Python script
	scriptPath := filepath.Join("python", "Followers", "getFollowers.py")
	if _, err := os.Stat(scriptPath); os.IsNotExist(err) {
		return "", fmt.Errorf("Python script does not exist at path: %s", scriptPath)
	}

	// Detect Python command
	pythonCmd := DetectPythonCommand()

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
func DetectPythonCommandFollow() string {
	fmt.Println("Running DetectPythonCommand") // Debugging message
	pythonCmd := "python"
	if _, err := exec.LookPath(pythonCmd); err != nil {
		pythonCmd = "python3"
		if _, err := exec.LookPath(pythonCmd); err != nil {
			panic("Neither 'python' nor 'python3' found in PATH")
		}
	}
	return pythonCmd
}
