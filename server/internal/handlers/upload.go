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
	"time"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/google/uuid"
	_ "github.com/lib/pq"
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
	// groupID := r.FormValue("group_id") // 💤 not used for now

	platform := r.FormValue("platform")
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

	// Parse user ID to int
	userIDInt, err := strconv.Atoi(userID)
	if err != nil {
		http.Error(w, "Invalid user_id format", http.StatusBadRequest)
		return
	}

	// 📁 Create user upload directory (simple version, no group yet)
	uploadPath := filepath.Join(baseUploadDir, userID)
	// uploadPath := filepath.Join(baseUploadDir, userID, groupID) // 🔒 for future use

	if err := os.MkdirAll(uploadPath, os.ModePerm); err != nil {
		http.Error(w, "Failed to create upload directory", http.StatusInternalServerError)
		return
	}

	// Generate unique filename
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

	// Create job ID and save to DB
	jobID := fmt.Sprintf("%s-%s", userID, uuid.New().String())

	err = saveJobToDB(queries, int32(userIDInt), jobID, platform, fullFilePath, "", "local")
	if err != nil {
		http.Error(w, "Failed to save job to database", http.StatusInternalServerError)
		return
	}

	// Success response
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]string{
		"message":   "File uploaded successfully",
		"file_path": fullFilePath,
		"job_id":    jobID,
		"platform":  platform,
	})
}

// Save job record to DB
func saveJobToDB(queries *db.Queries, userID int32, jobID, platform, videoPath, fileURL, storageType string) error {
	_, err := queries.CreateUploadJob(context.TODO(), db.CreateUploadJobParams{
		ID:          jobID,
		UserID:      userID,
		VideoPath:   sql.NullString{String: videoPath, Valid: videoPath != ""},
		FileUrl:     sql.NullString{String: fileURL, Valid: fileURL != ""},
		StorageType: sql.NullString{String: storageType, Valid: storageType != ""},
		Status:      sql.NullString{String: "pending", Valid: true},
		Platform:    sql.NullString{String: platform, Valid: true},
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
