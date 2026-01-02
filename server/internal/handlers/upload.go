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

func DeleteUploadVideo(c *gin.Context, queries *db.Queries) {
	// get job id from the url
	jidStr := c.Param("jobID")
	if jidStr == "" {
		c.JSON(http.StatusNotFound, gin.H{"error": "job_id is required"})
		return
	}
	// delete the job using the job id string
	err := queries.DeleteUploadJob(c, jidStr)

	// if there was an error deleting the job
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err})
		return
	}

	// double check if the job is actually deleted
	_, err = queries.GetUploadJob(c, jidStr)
	if err != nil {
		// if it's a no row error then it was deleted
		if errors.Is(err, sql.ErrNoRows) {
			c.JSON(http.StatusOK, gin.H{"message": "Job was deleted successfully"})
			return
		} else {
			// if we do get a result then the job is still there
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Job was not deleted"})
			return
		}
	}
	// any other error that could pop up
	c.JSON(http.StatusInternalServerError, gin.H{"error": err})
	return
}

func UploadVideoHandler(c *gin.Context, queries *db.Queries) {
	// Get authenticated user ID from JWT context (set by AuthMiddleware)
	userIDVal, exists := c.Get("userID")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}
	userID, ok := userIDVal.(int32)
	if !ok {
		// Try float64 (common from JWT claims)
		if f, ok := userIDVal.(float64); ok {
			userID = int32(f)
		} else {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid user context"})
			return
		}
	}

	// Required fields
	platform := c.PostForm("platform")
	groupIDStr := c.PostForm("group_id")

	if platform == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "platform is required"})
		return
	}

	// Parse group_id
	groupIDInt, err := strconv.Atoi(groupIDStr)
	if err != nil || groupIDStr == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "valid group_id is required"})
		return
	}

	// Verify group belongs to this user
	groups, err := queries.ListGroupsByUser(c.Request.Context(), userID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to verify group ownership"})
		return
	}
	groupOwned := false
	for _, g := range groups {
		if g.ID == int32(groupIDInt) {
			groupOwned = true
			break
		}
	}
	if !groupOwned {
		c.JSON(http.StatusForbidden, gin.H{"error": "Group does not belong to user"})
		return
	}

	// Optional fields
	title := c.PostForm("title")
	hashtagsRaw := c.PostForm("hashtags")

	// File
	file, err := c.FormFile("file")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "File is required"})
		return
	}

	// Create upload directory under uploads/<userID>/
	uploadPath := filepath.Join(baseUploadDir, strconv.Itoa(int(userID)))
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
	jobID := fmt.Sprintf("%d-%s", userID, uuid.New().String())

	// Parse hashtags from raw string to []string
	hashtags := parseHashtags(hashtagsRaw)

	// Parse schedule_date if provided (RFC3339 format)
	var scheduleDate time.Time
	scheduleDateStr := c.PostForm("schedule_date")
	if scheduleDateStr != "" {
		scheduleDate, err = time.Parse(time.RFC3339, scheduleDateStr)
		if err != nil {
			// Try alternate format
			scheduleDate, _ = time.Parse("2006-01-02T15:04:05Z", scheduleDateStr)
		}
	}

	// Save job to DB with status='queued'
	err = saveJobToDB(queries, userID, jobID, int32(groupIDInt), scheduleDate, platform, fullFilePath, "", "local", title, hashtags)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to save job to database: %v", err)})
		fmt.Printf("❌ Upload error: %v\n", err)
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
		Status:        "queued",                                                        // Start in queued state for AI content generation
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
	Platform string    `json:"platform"`
	Status   string    `json:"status"`
	Updated  time.Time `json:"updated"`
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
