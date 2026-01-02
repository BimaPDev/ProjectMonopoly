package handlers

import (
	"database/sql"
	"net/http"
	"strconv"
	"time"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/gin-gonic/gin"
)

// PendingJobsResponse represents the response for pending jobs
type PendingJobsResponse struct {
	Jobs []PendingJob `json:"jobs"`
}

// PendingJob represents a single pending upload job
type PendingJob struct {
	ID            string    `json:"id"`
	Platform      string    `json:"platform"`
	Status        string    `json:"status"`
	AITitle       *string   `json:"ai_title"`
	AIHook        *string   `json:"ai_hook"`
	AIHashtags    []string  `json:"ai_hashtags"`
	ScheduledDate *string   `json:"scheduled_date"`
	ErrorMessage  *string   `json:"error_message"`
	CreatedAt     time.Time `json:"created_at"`
	UpdatedAt     time.Time `json:"updated_at"`
}

// getUserIDFromContext extracts and validates user ID from JWT context
func getUserIDFromContext(c *gin.Context) (int32, bool) {
	userIDVal, exists := c.Get("userID")
	if !exists {
		return 0, false
	}
	if userID, ok := userIDVal.(int32); ok {
		return userID, true
	}
	if f, ok := userIDVal.(float64); ok {
		return int32(f), true
	}
	return 0, false
}

// verifyGroupOwnership checks if the group belongs to the user
func verifyGroupOwnership(c *gin.Context, q *db.Queries, userID int32, groupID int32) bool {
	groups, err := q.ListGroupsByUser(c.Request.Context(), userID)
	if err != nil {
		return false
	}
	for _, g := range groups {
		if g.ID == groupID {
			return true
		}
	}
	return false
}

// ListPendingUploads returns all pending upload jobs for a group (tenant-safe)
func ListPendingUploads(c *gin.Context, q *db.Queries) {
	// Get authenticated user ID from context
	userID, ok := getUserIDFromContext(c)
	if !ok {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}

	groupIDStr := c.Query("group_id")
	if groupIDStr == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "group_id is required"})
		return
	}

	groupID, err := strconv.Atoi(groupIDStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid group_id"})
		return
	}

	// Verify group belongs to user
	if !verifyGroupOwnership(c, q, userID, int32(groupID)) {
		c.JSON(http.StatusForbidden, gin.H{"error": "Group does not belong to user"})
		return
	}

	// Call tenant-safe query with both group_id and user_id
	jobs, err := q.ListGroupPendingJobs(c.Request.Context(), db.ListGroupPendingJobsParams{
		GroupID: sql.NullInt32{Int32: int32(groupID), Valid: true},
		UserID:  userID,
	})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to fetch jobs"})
		return
	}

	response := PendingJobsResponse{Jobs: make([]PendingJob, 0, len(jobs))}
	for _, job := range jobs {
		pj := PendingJob{
			ID:         job.ID,
			Platform:   job.Platform,
			Status:     job.Status,
			AIHashtags: job.AiHashtags,
			CreatedAt:  job.CreatedAt.Time,
			UpdatedAt:  job.UpdatedAt.Time,
		}

		if job.AiTitle.Valid {
			pj.AITitle = &job.AiTitle.String
		}
		if job.AiHook.Valid {
			pj.AIHook = &job.AiHook.String
		}
		if job.ScheduledDate.Valid {
			formatted := job.ScheduledDate.Time.Format(time.RFC3339)
			pj.ScheduledDate = &formatted
		}
		if job.ErrorMessage.Valid {
			pj.ErrorMessage = &job.ErrorMessage.String
		}

		response.Jobs = append(response.Jobs, pj)
	}

	c.JSON(http.StatusOK, response)
}

// ApproveUploadRequest represents the request body for approving an upload
type ApproveUploadRequest struct {
	Caption  string   `json:"caption"`
	Hashtags []string `json:"hashtags"`
}

// ApproveUpload approves a job for scheduling (enforces ownership)
func ApproveUpload(c *gin.Context, q *db.Queries) {
	// Get authenticated user ID from context
	userID, ok := getUserIDFromContext(c)
	if !ok {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}

	jobID := c.Param("id")
	if jobID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Job ID is required"})
		return
	}

	var req ApproveUploadRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		// Allow empty body - use existing AI content
	}

	// Get the full job to check status and ownership
	job, err := q.GetUploadJobFull(c.Request.Context(), jobID)
	if err != nil {
		if err == sql.ErrNoRows {
			c.JSON(http.StatusNotFound, gin.H{"error": "Job not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get job"})
		return
	}

	// Enforce ownership: job.user_id must match authenticated user
	if job.UserID != userID {
		c.JSON(http.StatusForbidden, gin.H{"error": "You do not own this job"})
		return
	}

	if job.Status != "needs_review" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Job is not in needs_review status"})
		return
	}

	// Update caption if provided
	if req.Caption != "" {
		err = q.UpdateJobAIContent(c.Request.Context(), db.UpdateJobAIContentParams{
			ID:         jobID,
			AiTitle:    sql.NullString{String: req.Caption, Valid: true},
			AiHook:     job.AiHook,
			AiHashtags: req.Hashtags,
			AiPostTime: job.AiPostTime,
		})
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to update content"})
			return
		}
	}

	// Schedule the job using AI-suggested time or default to 24h from now
	scheduledDate := job.AiPostTime.Time
	if !job.AiPostTime.Valid {
		scheduledDate = time.Now().Add(24 * time.Hour)
	}

	err = q.ScheduleJob(c.Request.Context(), db.ScheduleJobParams{
		ID:            jobID,
		ScheduledDate: sql.NullTime{Time: scheduledDate, Valid: true},
	})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to schedule job"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message":        "Job scheduled successfully",
		"job_id":         jobID,
		"scheduled_date": scheduledDate.Format(time.RFC3339),
	})
}

// CancelUpload cancels a pending upload job (enforces ownership)
func CancelUpload(c *gin.Context, q *db.Queries) {
	// Get authenticated user ID from context
	userID, ok := getUserIDFromContext(c)
	if !ok {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
		return
	}

	jobID := c.Param("id")
	if jobID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Job ID is required"})
		return
	}

	// Get job to verify ownership
	job, err := q.GetUploadJobFull(c.Request.Context(), jobID)
	if err != nil {
		if err == sql.ErrNoRows {
			c.JSON(http.StatusNotFound, gin.H{"error": "Job not found"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get job"})
		return
	}

	// Enforce ownership
	if job.UserID != userID {
		c.JSON(http.StatusForbidden, gin.H{"error": "You do not own this job"})
		return
	}

	// Only allow canceling jobs in certain states
	if job.Status != "queued" && job.Status != "scheduled" && job.Status != "needs_review" && job.Status != "generating" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Job cannot be canceled in current status"})
		return
	}

	err = q.CancelJob(c.Request.Context(), jobID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to cancel job"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Job canceled successfully",
		"job_id":  jobID,
	})
}
