package handlers

import (
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/BimaPDev/ProjectMonopoly/internal/utils"
	"github.com/gin-gonic/gin"
)

const maxUpload = 100 << 20 // 100 MB

// WorkshopUploadHandler handles POST /api/workshop/upload (multipart/form-data: file, group_id)
func WorkshopUploadHandler(c *gin.Context, q *db.Queries) {
	// Gin handles method checking via routing

	userID, err := utils.GetUserID(c)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
		return
	}

	// hardcode a project-relative uploads root and make it ABSOLUTE
	absRoot := mustAbs(filepath.Join(".", "uploads", "docs"))
	if err := os.MkdirAll(absRoot, 0o755); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "storage init failed"})
		return
	}

	// limit and parse form (Gin does this with MaxMultipartMemory but we can also limit request body?)
	// defaults to 32MB. 100MB required.
	// c.Request.Body = http.MaxBytesReader(c.Writer, c.Request.Body, maxUpload)
	// if err := c.Request.ParseMultipartForm(maxUpload); err != nil { ... }
	// Better: just use c.FormFile which parses internally

	groupID := parseInt64(c.PostForm("group_id"))

	fileHeader, err := c.FormFile("file")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "missing file"})
		return
	}

	file, err := fileHeader.Open()
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "failed to open file"})
		return
	}
	defer file.Close()

	if !strings.HasSuffix(strings.ToLower(fileHeader.Filename), ".pdf") {
		c.JSON(http.StatusBadRequest, gin.H{"error": "only .pdf accepted"})
		return
	}

	// write to tmp while hashing
	tmpDir := filepath.Join(absRoot, "tmp")
	if err := os.MkdirAll(tmpDir, 0o755); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "storage init failed"})
		return
	}
	tmpPath := filepath.Join(tmpDir, fmt.Sprintf("%d_%d_%s", userID, time.Now().UnixNano(), sanitize(fileHeader.Filename)))

	out, err := os.Create(tmpPath)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "tmp create failed"})
		return
	}
	hasher := sha256.New()
	size, err := io.Copy(io.MultiWriter(out, hasher), file)
	_ = out.Close()
	if err != nil {
		_ = os.Remove(tmpPath)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "write failed"})
		return
	}
	sha := hex.EncodeToString(hasher.Sum(nil))

	// move to final absolute path
	userDir := filepath.Join(absRoot, fmt.Sprint(userID))
	if err := os.MkdirAll(userDir, 0o755); err != nil {
		_ = os.Remove(tmpPath)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "storage init failed"})
		return
	}
	finalName := fmt.Sprintf("%d_%s", time.Now().Unix(), sanitize(fileHeader.Filename))
	finalPath := filepath.Join(userDir, finalName) // absolute on disk
	if !filepath.IsAbs(finalPath) {
		finalPath = mustAbs(finalPath)
	}
	if err := os.Rename(tmpPath, finalPath); err != nil {
		_ = os.Remove(tmpPath)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "finalize failed"})
		return
	}

	// insert document and enqueue job
	docID, err := q.CreateWorkshopDocument(c.Request.Context(), db.CreateWorkshopDocumentParams{
		UserID:     int32(userID),
		GroupID:    int32(groupID),
		Filename:   fileHeader.Filename,
		Mime:       "application/pdf",
		SizeBytes:  size,
		Sha256:     sha,
		StorageUrl: sql.NullString{String: finalPath, Valid: true}, // absolute path, no env
	})
	if err != nil {
		if strings.Contains(strings.ToLower(err.Error()), "workshop_doc_user_group_sha_uniq") {
			c.JSON(http.StatusConflict, gin.H{"error": "duplicate file in this group"})
			return
		}
		c.JSON(http.StatusInternalServerError, gin.H{"error": "db insert failed"})
		return
	}
	if err := q.EnqueueIngestJob(c.Request.Context(), docID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "enqueue failed"})
		return
	}

	c.JSON(http.StatusCreated, gin.H{"document_id": docID, "status": "queued"})
}

func sanitize(name string) string {
	name = strings.ReplaceAll(name, " ", "_")
	return strings.Map(func(r rune) rune {
		switch {
		case r >= 'a' && r <= 'z', r >= 'A' && r <= 'Z', r >= '0' && r <= '9', r == '.', r == '_', r == '-':
			return r
		default:
			return '_'
		}
	}, name)
}

func mustAbs(p string) string {
	abs, err := filepath.Abs(p)
	if err != nil {
		return p
	}
	return abs
}

func parseInt64(s string) int64 { var x int64; fmt.Sscanf(s, "%d", &x); return x }
