package handlers

import (
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"

	"github.com/BimaPDev/ProjectMonopoly/internal/utils"
)

// DeepSeekHandler handles AI requests to DeepSeek and saves uploaded files.
func DeepSeekHandler(w http.ResponseWriter, r *http.Request) {
	// Set CORS headers if needed
	w.Header().Set("Access-Control-Allow-Origin", "*") // Or your specific origin
	w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

	// Handle preflight requests
	if r.Method == "OPTIONS" {
		w.WriteHeader(http.StatusOK)
		return
	}

	// Create uploads directory if it doesn't exist
	uploadsDir := "./uploads"
	if err := os.MkdirAll(uploadsDir, 0755); err != nil {
		http.Error(w, fmt.Sprintf("Failed to create uploads directory: %v", err), http.StatusInternalServerError)
		return
	}

	// Parse multipart form
	if err := r.ParseMultipartForm(32 << 20); err != nil { // 32MB max memory
		http.Error(w, fmt.Sprintf("Failed to parse multipart form: %v", err), http.StatusBadRequest)
		return
	}

	// Extract prompt from form data
	prompt := r.FormValue("prompt")
	if prompt == "" {
		prompt = " "
	}

	// Log received prompt
	fmt.Printf("Received prompt: %s\n", prompt)

	// Extract and save files
	savedFiles := []string{}
	for _, fileHeaders := range r.MultipartForm.File {
		for _, fileHeader := range fileHeaders {
			// Log file information
			fmt.Printf("Received file: %s, size: %d bytes\n",
				fileHeader.Filename, fileHeader.Size)

			// Open the uploaded file
			uploadedFile, err := fileHeader.Open()
			if err != nil {
				http.Error(w, fmt.Sprintf("Failed to open uploaded file: %v", err), http.StatusInternalServerError)
				return
			}
			defer uploadedFile.Close()

			// Create a new file on the server
			filePath := filepath.Join(uploadsDir, fileHeader.Filename)
			dst, err := os.Create(filePath)
			if err != nil {
				http.Error(w, fmt.Sprintf("Failed to create file on server: %v", err), http.StatusInternalServerError)
				return
			}
			defer dst.Close()

			// Copy content from uploaded file to server file
			if _, err := io.Copy(dst, uploadedFile); err != nil {
				http.Error(w, fmt.Sprintf("Failed to save uploaded file: %v", err), http.StatusInternalServerError)
				return
			}

			savedFiles = append(savedFiles, filePath)
			fmt.Printf("File saved to: %s\n", filePath)
		}
	}

	// Get the first uploaded file for processing (if any)
	var uploadedFile *multipart.FileHeader
	if files := r.MultipartForm.File["files"]; len(files) > 0 {
		uploadedFile = files[0]
	}

	// Call the AI processing function with the prompt and file
	response, err := utils.MainDeep(prompt, uploadedFile)
	if err != nil {
		http.Error(w, fmt.Sprintf("Error processing request: %v", err), http.StatusInternalServerError)
		return
	}

	// Return the AI-generated response along with information about saved files
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"response":   response,
		"savedFiles": savedFiles,
	})
}
