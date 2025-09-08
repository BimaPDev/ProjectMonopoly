-- name: CreateWorkshopDocument :one
INSERT INTO workshop_documents
(user_id, group_id, filename, mime, size_bytes, sha256, storage_url, status)
VALUES ($1,$2,$3,$4,$5,$6,$7,'queued')
RETURNING id;

-- name: EnqueueIngestJob :exec
INSERT INTO document_ingest_jobs(document_id) VALUES ($1);
