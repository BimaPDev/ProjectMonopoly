package handlers

import (
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"sync"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/BimaPDev/ProjectMonopoly/internal/utils"
	"github.com/gin-gonic/gin"
)

var (
	// Create uploads directory once
	uploadsDirOnce sync.Once
	uploadsDirErr  error
)

// DeepSeekHandler handles AI requests to DeepSeek and saves uploaded files.
func DeepSeekHandler(c *gin.Context, queries *db.Queries) {
	// CORS handled by middleware

	// Extract user_id from context (set by JWT middleware)
	// If not present, use 0 (anonymous/unauthenticated)
	var userID int32
	if uid, exists := c.Get("userID"); exists {
		if val, ok := uid.(int32); ok {
			userID = val
		}
	} else {
		// If no authentication, we'll try to proceed without game context
		fmt.Println("Warning: No user authentication found, proceeding without game context")
	}

	// Extract optional group_id from query params or form data
	var groupID *int32
	groupIDStr := c.Query("group_id")
	if groupIDStr == "" {
		groupIDStr = c.PostForm("group_id")
	}
	if groupIDStr != "" {
		if gid, err := strconv.ParseInt(groupIDStr, 10, 32); err == nil && gid > 0 {
			gidInt32 := int32(gid)
			groupID = &gidInt32
		}
	}

	// Initialize uploads directory
	uploadsDir := "./uploads"
	uploadsDirOnce.Do(func() {
		uploadsDirErr = os.MkdirAll(uploadsDir, 0755)
	})
	if uploadsDirErr != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to create uploads directory: %v", uploadsDirErr)})
		return
	}

	// Parse multipart form with limited memory usage
	// Gin does this lazily/automatically when accessing file, but we can do it explicitly or just access MultipartForm provided by Gin
	if err := c.Request.ParseMultipartForm(10 << 20); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": fmt.Sprintf("Failed to parse multipart form: %v", err)})
		return
	}

	// Extract prompt from form data
	prompt := c.PostForm("prompt")
	if prompt == "" {
		prompt = " "
	}

	// Extract conversation history if provided
	var conversationHistory []map[string]interface{}
	historyStr := c.PostForm("conversation_history")
	if historyStr != "" {
		if err := json.Unmarshal([]byte(historyStr), &conversationHistory); err != nil {
			fmt.Printf("Warning: Failed to parse conversation history: %v\n", err)
		}
	}

	// Process files and AI request concurrently
	var wg sync.WaitGroup
	var savedFiles []string
	var savedFilesMutex sync.Mutex
	var response string
	var aiErr error

	// Extract and save files in a goroutine
	wg.Add(1)
	go func() {
		defer wg.Done()
		if c.Request.MultipartForm != nil {
			for _, fileHeaders := range c.Request.MultipartForm.File {
				for _, fileHeader := range fileHeaders {
					filePath, err := saveUploadedFile(fileHeader, uploadsDir)
					if err != nil {
						// Log error but continue with other files
						fmt.Printf("Error saving file %s: %v\n", fileHeader.Filename, err)
						continue
					}

					savedFilesMutex.Lock()
					savedFiles = append(savedFiles, filePath)
					savedFilesMutex.Unlock()
				}
			}
		}
	}()

	// Get the first uploaded file for processing (if any)
	var uploadedFile *multipart.FileHeader
	if c.Request.MultipartForm != nil {
		if files := c.Request.MultipartForm.File["files"]; len(files) > 0 {
			uploadedFile = files[0]
		}
	}

	// Process AI request in a goroutine
	wg.Add(1)
	go func() {
		defer wg.Done()
		response, aiErr = utils.MainDeep(prompt, userID, groupID, uploadedFile, conversationHistory, queries)
	}()

	// Wait for both operations to complete
	wg.Wait()

	// Check for AI processing error
	if aiErr != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Error processing request: %v", aiErr)})
		return
	}

	// Return the AI-generated response along with information about saved files
	c.JSON(http.StatusOK, gin.H{
		"response":   response,
		"savedFiles": savedFiles,
	})
}

// saveUploadedFile saves a single uploaded file to the server
func saveUploadedFile(fileHeader *multipart.FileHeader, uploadsDir string) (string, error) {
	// Open the uploaded file
	uploadedFile, err := fileHeader.Open()
	if err != nil {
		return "", fmt.Errorf("failed to open uploaded file: %v", err)
	}
	defer uploadedFile.Close()

	// Create a new file on the server
	filePath := filepath.Join(uploadsDir, fileHeader.Filename)
	dst, err := os.Create(filePath)
	if err != nil {
		return "", fmt.Errorf("failed to create file on server: %v", err)
	}
	defer dst.Close()

	// Copy content from uploaded file to server file
	if _, err := io.Copy(dst, uploadedFile); err != nil {
		return "", fmt.Errorf("failed to save uploaded file: %v", err)
	}

	fmt.Printf("File saved to: %s\n", filePath)
	return filePath, nil
}
