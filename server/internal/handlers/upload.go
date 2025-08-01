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
    "log"
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
	groupID := r.FormValue("group_id") // returns a string, like "1"
    groupIDInt, err := strconv.Atoi(groupID)
    if err != nil {
    	http.Error(w, "Invalid group_id format", http.StatusBadRequest)
    	return
    }
	// Parse hashtags from raw string to []string
	hashtags := parseHashtags(hashtagsRaw)
	layout:= "02/01/2006 3.04.05 PM"
	date, _ := time.Parse(layout, r.FormValue("schedule_date"))
	// Save job to DB
	err = saveJobToDB(queries, int32(userIDInt), jobID, int32(groupIDInt),date, platform, fullFilePath,"", "local", title, hashtags)
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to save job to database: %v", err), http.StatusInternalServerError)
		fmt.Printf("❌ Upload error: %v\n", err) // Also logs to your terminal
		return
	}

	// Respond
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"message":   "File uploaded successfully",
		"file_path": fullFilePath,
		"job_id":    jobID,
		"platform":  platform,
		"title":     title,
		"hashtags":  hashtags,
	})
}

// Save job to database
func saveJobToDB(
	queries *db.Queries,
	userID int32,
	jobID string,
	groupID int32,
	scheduleDate time.Time,
	platform, videoPath, fileURL, storageType, title string,
	hashtags []string,
) error {
	_, err := queries.CreateUploadJob(context.TODO(), db.CreateUploadJobParams{
		ID:           jobID,       // $1
		UserID:       userID,      // $2
		Platform:     platform,    // $3
		VideoPath:    videoPath,   // $4
		StorageType:  storageType, // $5
		FileUrl:      sql.NullString{String: fileURL, Valid: fileURL != ""},
		ScheduledDate: sql.NullTime{Time: scheduleDate, Valid: !scheduleDate.IsZero()}, // $6
		Status:       "pending",
		UserTitle:    sql.NullString{String: title, Valid: title != ""},
		UserHashtags: hashtags,
		GroupID: sql.NullInt32{Int32: groupID, Valid: true},

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


type uploadResponse struct {
	ID int32 `json:"ID"`
	platform string `json:"platform"`
	status string `json:"status"`
	updated time.Time `json:"updated"`
}

func GetUploadItemsByGroupID(w http.ResponseWriter, r *http.Request, q *db.Queries){
	if r.Method != http.MethodGet{
		http.Error(w, "Invalid request method", http.StatusMethodNotAllowed);
		return

	}

	groupIDstr := r.URL.Query().Get("groupID");
	groupIDInt, err := strconv.Atoi(groupIDstr);
	if err != nil {

		http.Error(w, "Invalid group id", http.StatusBadRequest);
	}

	groupID := sql.NullInt32{Int32: int32(groupIDInt), Valid: true};

	uploads, err := q.GetUploadJobByGID(r.Context(), groupID)

	if err != nil {
	    log.Printf("Error getting uploads: %v", err)
        http.Error(w, "Error getting uploads, UG190", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(uploads); err != nil {
		http.Error(w, "Error encoding response", http.StatusInternalServerError)
		return
	}
}