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

type Uploader struct {
	Q *db.Queries
}

const maxUpload = 100 << 20 // 100 MB

func (h *Uploader) UploadPDF(w http.ResponseWriter, r *http.Request) {
	// TODO: replace with real auth. For now default to user 1 if header missing.
	userID := userIDFromHeader(r.Header.Get("X-User-ID"))
	groupID := parseInt64(r.FormValue("group_id"))
	baseDir := getenv("DOCS_DIR", "./data/docs")

	r.Body = http.MaxBytesReader(w, r.Body, maxUpload)
	if err := r.ParseMultipartForm(maxUpload); err != nil {
		http.Error(w, "invalid form or file too large", http.StatusBadRequest)
		return
	}
	f, hdr, err := r.FormFile("file")
	if err != nil {
		http.Error(w, "missing file", http.StatusBadRequest)
		return
	}
	defer f.Close()
	if !strings.HasSuffix(strings.ToLower(hdr.Filename), ".pdf") {
		http.Error(w, "only .pdf accepted", http.StatusBadRequest)
		return
	}

	// write to tmp while hashing
	tmpDir := filepath.Join(baseDir, "tmp")
	_ = os.MkdirAll(tmpDir, 0o755)
	tmpPath := filepath.Join(tmpDir, fmt.Sprintf("%d_%d_%s", userID, time.Now().UnixNano(), sanitize(hdr.Filename)))
	out, err := os.Create(tmpPath)
	if err != nil {
		http.Error(w, "tmp create failed", http.StatusInternalServerError)
		return
	}
	hasher := sha256.New()
	size, err := io.Copy(io.MultiWriter(out, hasher), f)
	_ = out.Close()
	if err != nil {
		_ = os.Remove(tmpPath)
		http.Error(w, "write failed", http.StatusInternalServerError)
		return
	}
	sha := hex.EncodeToString(hasher.Sum(nil))

	// move to final
	userDir := filepath.Join(baseDir, fmt.Sprint(userID))
	_ = os.MkdirAll(userDir, 0o755)
	finalName := fmt.Sprintf("%d_%s", time.Now().Unix(), sanitize(hdr.Filename))
	finalPath := filepath.Join(userDir, finalName)
	if err := os.Rename(tmpPath, finalPath); err != nil {
		_ = os.Remove(tmpPath)
		http.Error(w, "finalize failed", http.StatusInternalServerError)
		return
	}

	// insert + enqueue
	docID, err := h.Q.CreateWorkshopDocument(r.Context(), db.CreateWorkshopDocumentParams{
		UserID:    int32(userID),
		GroupID:   int32(groupID),
		Filename:  hdr.Filename,
		Mime:      "application/pdf",
		SizeBytes: size,
		Sha256:    sha,
		StorageUrl: sql.NullString{String: finalPath, Valid: true},
	})
	if err != nil {
		// unique(user_id, sha256) -> conflict means duplicate upload
		if strings.Contains(strings.ToLower(err.Error()), "workshop_doc_user_sha_uniq") {
			http.Error(w, "duplicate file", http.StatusConflict)
			return
		}
		http.Error(w, "db insert failed", http.StatusInternalServerError)
		return
	}
	if err := h.Q.EnqueueIngestJob(r.Context(), docID); err != nil {
		http.Error(w, "enqueue failed", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	_, _ = w.Write([]byte(fmt.Sprintf(`{"document_id":"%v","status":"queued"}`, docID)))
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

func getenv(k, d string) string { if v := os.Getenv(k); v != "" { return v }; return d }

func parseInt64(s string) int64 { var x int64; fmt.Sscanf(s, "%d", &x); return x }

func userIDFromHeader(h string) int64 {
	if h == "" { return 1 } // dev default
	var x int64
	fmt.Sscanf(h, "%d", &x)
	if x <= 0 { return 1 }
	return x
}
