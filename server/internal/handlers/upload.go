package handlers

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/google/uuid"
)

const baseUploadDir = "uploads" // Base upload directory

func UploadVideoHandler(w http.ResponseWriter, r *http.Request, queries *db.Queries) {
	if r.Method != http.MethodPost {
		http.Error(w, "Invalid request method", http.StatusMethodNotAllowed)
		return
	}

	err := r.ParseMultipartForm(50 << 20) // 50MB max
	if err != nil {
		http.Error(w, "Failed to parse form data", http.StatusBadRequest)
		return
	}

	// Required fields
	userID := r.FormValue("user_id")
	platform := r.FormValue("platform")

	// Optional fields
	title := r.FormValue("title")
	hashtagsRaw := r.FormValue("hashtags")

	if userID == "" || platform == "" {
		http.Error(w, "user_id and platform are required", http.StatusBadRequest)
		return
	}

	// File
	file, handler, err := r.FormFile("file")
	if err != nil {
		http.Error(w, "File is required", http.StatusBadRequest)
		return
	}
	defer file.Close()

	// Parse user ID
	userIDInt, err := strconv.Atoi(userID)
	if err != nil {
		http.Error(w, "Invalid user_id format", http.StatusBadRequest)
		return
	}

	// Create upload directory
	uploadPath := filepath.Join(baseUploadDir, userID)
	if err := os.MkdirAll(uploadPath, os.ModePerm); err != nil {
		http.Error(w, "Failed to create upload directory", http.StatusInternalServerError)
		return
	}

	// Generate safe filename
	safeFilename := generateSafeFilename(handler.Filename)
	fullFilePath := filepath.Join(uploadPath, safeFilename)

	// Save file
	dst, err := os.Create(fullFilePath)
	if err != nil {
		http.Error(w, "Failed to save file", http.StatusInternalServerError)
		return
	}
	defer dst.Close()

	if _, err = io.Copy(dst, file); err != nil {
		http.Error(w, "Failed to write file to disk", http.StatusInternalServerError)
		return
	}

	// Generate Job ID
	jobID := fmt.Sprintf("%s-%s", userID, uuid.New().String())

	// Parse hashtags from raw string to []string
	hashtags := parseHashtags(hashtagsRaw)

	// Save job to DB
	err = saveJobToDB(queries, int32(userIDInt), jobID, platform, fullFilePath, "", "local", title, hashtags)
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to save job to database: %v", err), http.StatusInternalServerError)
		fmt.Printf("❌ Upload error: %v\n", err) // Also logs to your terminal
		return
	}

	// Respond
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"message":    "File uploaded successfully",
		"file_path":  fullFilePath,
		"job_id":     jobID,
		"platform":   platform,
		"title":      title,
		"hashtags":   hashtags,
	})
}

// Save job to database
func saveJobToDB(
	queries *db.Queries,
	userID int32,
	jobID, platform, videoPath, fileURL, storageType, title string,
	hashtags []string,
) error {
	_, err := queries.CreateUploadJob(context.TODO(), db.CreateUploadJobParams{
		ID:           jobID,                                // $1
		UserID:       userID,                               // $2
		Platform:     platform,                             // $3
		VideoPath:    videoPath,                            // $4
		StorageType:  storageType,                          // $5 
		FileUrl:      sql.NullString{String: fileURL, Valid: fileURL != ""}, 
		Status:       "pending",                            
		UserTitle:    sql.NullString{String: title, Valid: title != ""},
		UserHashtags: hashtags,
	})	
	return err
}

// Generate a safe, unique filename
func generateSafeFilename(originalName string) string {
	ext := filepath.Ext(originalName)
	id := uuid.New().String()
	timestamp := time.Now().Format("20060102T150405")
	return fmt.Sprintf("%s-%s%s", id, timestamp, ext)
}

// Convert space-separated hashtags to []string
func parseHashtags(raw string) []string {
	// Split on whitespace and remove empty values
	fields := strings.Fields(raw)
	var clean []string
	for _, tag := range fields {
		trimmed := strings.TrimSpace(tag)
		if trimmed != "" {
			clean = append(clean, trimmed)
		}
	}
	return clean
}
