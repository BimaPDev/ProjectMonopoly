package handlers

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

const baseUploadDir = "uploads" // Base upload directory

func DeleteUploadVideo(c *gin.Context, queries *db.Queries){
	// get job id from the url
	jidStr := c.Param("jobID");
	if jidStr == "" {
		c.JSON(http.StatusNotFound, gin.H{"error": "job_id is required"});
		return
	}
	// delete the job using the job id string
	err := queries.DeleteUploadJob(c, jidStr);

	// if there was an error deleting the job
	if(err != nil){
		c.JSON(http.StatusInternalServerError, gin.H{"error": err})
		return;
	}
	
	// double check if the job is actually deleted
	_, err = queries.GetUploadJob(c, jidStr )
	if(err != nil ){
		// if it's a no row error then it was deleted 
		if errors.Is(err, sql.ErrNoRows){
			c.JSON(http.StatusOK, gin.H{"message": "Job was deleted successfully"});
			return;
		}else{
			// if we do get a result then the job is still there
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Job was not deleted"});
			return;
		}
	}
	// any other error that could pop up
	c.JSON(http.StatusInternalServerError, gin.H{"error": err});
	return;
}

func UploadVideoHandler(c *gin.Context, queries *db.Queries) {

	// Gin handles form parsing automatically with maxMemory, or we can explicit parse
	// c.Request.ParseMultipartForm(50 << 20) is done by c.FormFile internally usually or explicit call
	// For large files, explicit parse is fine or just relying on c.FormFile

	// Required fields
	userID := c.PostForm("user_id")
	platform := c.PostForm("platform")

	// Optional fields
	title := c.PostForm("title")
	hashtagsRaw := c.PostForm("hashtags")

	if userID == "" || platform == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "user_id and platform are required"})
		return
	}

	// File
	file, err := c.FormFile("file")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "File is required"})
		return
	}

	// Parse user ID
	userIDInt, err := strconv.Atoi(userID)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid user_id format"})
		return
	}

	// Create upload directory
	uploadPath := filepath.Join(baseUploadDir, userID)
	if err := os.MkdirAll(uploadPath, os.ModePerm); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create upload directory"})
		return
	}

	// Generate safe filename
	safeFilename := generateSafeFilename(file.Filename)
	fullFilePath := filepath.Join(uploadPath, safeFilename)

	// Save file
	if err := c.SaveUploadedFile(file, fullFilePath); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to save file"})
		return
	}

	// Generate Job ID
	jobID := fmt.Sprintf("%s-%s", userID, uuid.New().String())
	groupID := c.PostForm("group_id") // returns a string, like "1"
	groupIDInt, err := strconv.Atoi(groupID)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid group_id format"})
		return
	}
	// Parse hashtags from raw string to []string
	hashtags := parseHashtags(hashtagsRaw)
	layout := "02/01/2006 3.04.05 PM"
	date, _ := time.Parse(layout, c.PostForm("schedule_date"))
	// Save job to DB
	err = saveJobToDB(queries, int32(userIDInt), jobID, int32(groupIDInt), date, platform, fullFilePath, "", "local", title, hashtags)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to save job to database: %v", err)})
		fmt.Printf("❌ Upload error: %v\n", err) // Also logs to your terminal
		return
	}

	// Respond
	c.JSON(http.StatusCreated, gin.H{
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
		ID:            jobID,       // $1
		UserID:        userID,      // $2
		Platform:      platform,    // $3
		VideoPath:     videoPath,   // $4
		StorageType:   storageType, // $5
		FileUrl:       sql.NullString{String: fileURL, Valid: fileURL != ""},
		ScheduledDate: sql.NullTime{Time: scheduleDate, Valid: !scheduleDate.IsZero()}, // $6
		Status:        "pending",
		UserTitle:     sql.NullString{String: title, Valid: title != ""},
		UserHashtags:  hashtags,
		GroupID:       sql.NullInt32{Int32: groupID, Valid: true},
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
	ID       int32     `json:"ID"`
	platform string    `json:"platform"`
	status   string    `json:"status"`
	updated  time.Time `json:"updated"`
}

func GetUploadItemsByGroupID(c *gin.Context, q *db.Queries) {
	// Method check handled by Gin

	groupIDstr := c.Query("groupID")
	groupIDInt, err := strconv.Atoi(groupIDstr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid group id"})
		return
	}

	groupID := sql.NullInt32{Int32: int32(groupIDInt), Valid: true}

	uploads, err := q.GetUploadJobByGID(c.Request.Context(), groupID)

	if err != nil {
		log.Printf("Error getting uploads: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error getting uploads"})
		return
	}

	c.JSON(http.StatusOK, uploads)
}
