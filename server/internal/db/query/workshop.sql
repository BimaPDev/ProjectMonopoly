-- name: CreateWorkshopDocument :one
INSERT INTO workshop_documents (
  group_id, user_id, filename, mime, size_bytes, sha256, status
) VALUES ($1,$2,$3,$4,$5,$6,'queued')
RETURNING *;

-- name: SetDocumentStatus :exec
UPDATE workshop_documents
SET status = $2, error = $3, updated_at = now()
WHERE id = $1;

-- name: InsertChunk :exec
INSERT INTO workshop_chunks (
  document_id, group_id, page, chunk_index, content, token_count, embedding
) VALUES ($1,$2,$3,$4,$5,$6,$7);

-- name: RetrieveChunksHybrid :many
WITH ranked AS (
  SELECT id, document_id, page, content,
         1 - (embedding <=> $3) AS vscore,
         similarity(content, $2) AS kscore
  FROM workshop_chunks
  WHERE group_id = $1
  ORDER BY (0.7*(1 - (embedding <=> $3)) + 0.3*similarity(content, $2)) DESC
  LIMIT 20
)
SELECT * FROM ranked;
