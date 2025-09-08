-- name: CreateWorkshopDocument :one
INSERT INTO workshop_documents
(user_id, group_id, filename, mime, size_bytes, sha256, storage_url, status)
VALUES ($1,$2,$3,$4,$5,$6,$7,'queued')
RETURNING id;

-- name: EnqueueIngestJob :exec
INSERT INTO document_ingest_jobs(document_id) VALUES ($1);

-- name: SearchChunks :many
WITH p AS (
  SELECT
    sqlc.arg(q)::text       AS q,
    sqlc.arg(user_id)::int  AS user_id,
    sqlc.arg(group_id)::int AS group_id,
    sqlc.arg(n)::int        AS n
)
SELECT
  c.document_id,
  c.page,
  c.chunk_index,
  c.content,
  ts_rank_cd(c.tsv, plainto_tsquery(p.q)) AS rank
FROM workshop_chunks c
JOIN workshop_documents d ON d.id = c.document_id, p
WHERE d.user_id = p.user_id
  AND d.group_id = p.group_id
  AND c.tsv @@ plainto_tsquery(p.q)
ORDER BY rank DESC
LIMIT (SELECT n FROM p);

-- name: FuzzyChunks :many
WITH p AS (
  SELECT
    sqlc.arg(q)::text       AS q,
    sqlc.arg(user_id)::int  AS user_id,
    sqlc.arg(group_id)::int AS group_id,
    sqlc.arg(n)::int        AS n
)
SELECT
  c.document_id,
  c.page,
  c.chunk_index,
  c.content,
  similarity(c.content, p.q) AS sim
FROM workshop_chunks c
JOIN workshop_documents d ON d.id = c.document_id, p
WHERE d.user_id = p.user_id
  AND d.group_id = p.group_id
ORDER BY c.content <-> p.q
LIMIT (SELECT n FROM p);