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
)

const maxUpload = 100 << 20 // 100 MB

// WorkshopUploadHandler handles POST /api/workshop/upload (multipart/form-data: file, group_id)
func WorkshopUploadHandler(w http.ResponseWriter, r *http.Request, q *db.Queries) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	userID := ctxUserID(r)

	// hardcode a project-relative uploads root and make it ABSOLUTE
	absRoot := mustAbs(filepath.Join(".", "uploads", "docs"))
	if err := os.MkdirAll(absRoot, 0o755); err != nil {
		http.Error(w, "storage init failed", http.StatusInternalServerError)
		return
	}

	// limit and parse form
	r.Body = http.MaxBytesReader(w, r.Body, maxUpload)
	if err := r.ParseMultipartForm(maxUpload); err != nil {
		http.Error(w, "invalid form or file too large", http.StatusBadRequest)
		return
	}

	groupID := parseInt64(r.FormValue("group_id"))

	file, hdr, err := r.FormFile("file")
	if err != nil {
		http.Error(w, "missing file", http.StatusBadRequest)
		return
	}
	defer file.Close()

	if !strings.HasSuffix(strings.ToLower(hdr.Filename), ".pdf") {
		http.Error(w, "only .pdf accepted", http.StatusBadRequest)
		return
	}

	// write to tmp while hashing
	tmpDir := filepath.Join(absRoot, "tmp")
	if err := os.MkdirAll(tmpDir, 0o755); err != nil {
		http.Error(w, "storage init failed", http.StatusInternalServerError)
		return
	}
	tmpPath := filepath.Join(tmpDir, fmt.Sprintf("%d_%d_%s", userID, time.Now().UnixNano(), sanitize(hdr.Filename)))

	out, err := os.Create(tmpPath)
	if err != nil {
		http.Error(w, "tmp create failed", http.StatusInternalServerError)
		return
	}
	hasher := sha256.New()
	size, err := io.Copy(io.MultiWriter(out, hasher), file)
	_ = out.Close()
	if err != nil {
		_ = os.Remove(tmpPath)
		http.Error(w, "write failed", http.StatusInternalServerError)
		return
	}
	sha := hex.EncodeToString(hasher.Sum(nil))

	// move to final absolute path
	userDir := filepath.Join(absRoot, fmt.Sprint(userID))
	if err := os.MkdirAll(userDir, 0o755); err != nil {
		_ = os.Remove(tmpPath)
		http.Error(w, "storage init failed", http.StatusInternalServerError)
		return
	}
	finalName := fmt.Sprintf("%d_%s", time.Now().Unix(), sanitize(hdr.Filename))
	finalPath := filepath.Join(userDir, finalName) // absolute on disk
	if !filepath.IsAbs(finalPath) {
		finalPath = mustAbs(finalPath)
	}
	if err := os.Rename(tmpPath, finalPath); err != nil {
		_ = os.Remove(tmpPath)
		http.Error(w, "finalize failed", http.StatusInternalServerError)
		return
	}

	// insert document and enqueue job
	docID, err := q.CreateWorkshopDocument(r.Context(), db.CreateWorkshopDocumentParams{
		UserID:     int32(userID),
		GroupID:    int32(groupID),
		Filename:   hdr.Filename,
		Mime:       "application/pdf",
		SizeBytes:  size,
		Sha256:     sha,
		StorageUrl: sql.NullString{String: finalPath, Valid: true}, // absolute path, no env
	})
	if err != nil {
		if strings.Contains(strings.ToLower(err.Error()), "workshop_doc_user_group_sha_uniq") {
			http.Error(w, "duplicate file in this group", http.StatusConflict)
			return
		}
		http.Error(w, "db insert failed", http.StatusInternalServerError)
		return
	}
	if err := q.EnqueueIngestJob(r.Context(), docID); err != nil {
		http.Error(w, "enqueue failed", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	_, _ = w.Write([]byte(fmt.Sprintf(`{"document_id":"%s","status":"queued"}`, docID.String())))
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

// ctxUserID tries common keys set by middleware; default 1 for dev.
func ctxUserID(r *http.Request) int64 {
	for _, k := range []any{"user_id", "userID", "uid"} {
		if v := r.Context().Value(k); v != nil {
			switch t := v.(type) {
			case int64:
				return t
			case int:
				return int64(t)
			case float64:
				return int64(t)
			}
		}
	}
	if h := r.Header.Get("X-User-ID"); h != "" {
		var x int64
		fmt.Sscanf(h, "%d", &x)
		if x > 0 {
			return x
		}
	}
	return 1
}
