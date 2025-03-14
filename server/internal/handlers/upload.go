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

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	_ "github.com/lib/pq"
)

const uploadDir = "uploads/" // ✅ Directory where files will be stored

func UploadVideoHandler(w http.ResponseWriter, r *http.Request, queries *db.Queries) {
	// ✅ Ensure it's a POST request
	if r.Method != http.MethodPost {
		http.Error(w, "Invalid request method", http.StatusMethodNotAllowed)
		return
	}

	// ✅ Parse the form data (50MB limit)
	err := r.ParseMultipartForm(50 << 20) // 50MB limit
	if err != nil {
		http.Error(w, "Failed to parse form data", http.StatusBadRequest)
		return
	}

	// ✅ Get user ID
	userID := r.FormValue("user_id")
	if userID == "" {
		http.Error(w, "User ID is required", http.StatusBadRequest)
		return
	}

	// ✅ Get platform (TikTok, Instagram, Facebook, etc.)
	platform := r.FormValue("platform")
	if platform == "" {
		http.Error(w, "Platform is required", http.StatusBadRequest)
		return
	}

	// ✅ Get the uploaded file
	file, handler, err := r.FormFile("file") // 🔹 Ensure field name is "file"
	if err != nil {
		http.Error(w, "File is required", http.StatusBadRequest)
		return
	}
	defer file.Close()

	// ✅ Create uploads directory if it doesn't exist
	uploadDir := "uploads/"
	if _, err := os.Stat(uploadDir); os.IsNotExist(err) {
		os.MkdirAll(uploadDir, os.ModePerm)
	}

	// ✅ Save the uploaded file locally
	filePath := filepath.Join(uploadDir, handler.Filename)
	dst, err := os.Create(filePath)
	if err != nil {
		http.Error(w, "Failed to save file", http.StatusInternalServerError)
		return
	}
	defer dst.Close()

	// ✅ Copy the file to the new location
	_, err = io.Copy(dst, file)
	if err != nil {
		http.Error(w, "Failed to copy file", http.StatusInternalServerError)
		return
	}

	// ✅ Convert user ID to int32
	userIDInt, err := strconv.Atoi(userID)
	if err != nil {
		http.Error(w, "Invalid user_id format", http.StatusBadRequest)
		return
	}

	// ✅ Save file info in the database (Include Platform!)
	jobID := fmt.Sprintf("%s-%d", userID, os.Getpid()) // Unique Job ID
	err = saveJobToDB(queries, int32(userIDInt), jobID, platform, filePath, "", "local")
	if err != nil {
		http.Error(w, "Failed to save job to database", http.StatusInternalServerError)
		return
	}

	// ✅ Respond with success message
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]string{
		"message":   "File uploaded successfully",
		"file_path": filePath,
		"job_id":    jobID,
		"platform":  platform,
	})
}



func saveJobToDB(queries *db.Queries, userID int32, jobID, platform, videoPath, fileURL, storageType string) error {
	_, err := queries.CreateUploadJob(context.TODO(), db.CreateUploadJobParams{
		ID:          jobID,
		UserID:      userID,
		VideoPath:   sql.NullString{String: videoPath, Valid: videoPath != ""}, // ✅ Store file path
		FileUrl:     sql.NullString{String: fileURL, Valid: fileURL != ""},
		StorageType: sql.NullString{String: storageType, Valid: storageType != ""},
		Status:      sql.NullString{String: "pending", Valid: true},
		Platform:    sql.NullString{String: platform, Valid: true},
	})
	return err
}