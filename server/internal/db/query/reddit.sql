-- name: CreateRedditSource :one
INSERT INTO reddit_sources (
  user_id, group_id, type, value, subreddit
) VALUES (
  $1, $2, $3, $4, $5
)
RETURNING *;

-- name: ListRedditSources :many
SELECT * FROM reddit_sources
WHERE user_id = $1
  AND (sqlc.narg('group_id')::int IS NULL OR group_id = sqlc.narg('group_id')::int)
ORDER BY created_at DESC;

-- name: DeleteRedditSource :exec
DELETE FROM reddit_sources
WHERE id = $1 AND user_id = $2;

-- name: GetRedditSource :one
SELECT * FROM reddit_sources
WHERE id = $1 AND user_id = $2;

-- name: ListRedditItems :many
SELECT ri.* 
FROM reddit_items ri
JOIN reddit_sources rs ON ri.source_id = rs.id
WHERE rs.user_id = $1
  AND (sqlc.narg('group_id')::int IS NULL OR rs.group_id = sqlc.narg('group_id')::int)
ORDER BY ri.created_utc DESC
LIMIT $2 OFFSET $3;

-- name: GetRedditItem :one
SELECT ri.* 
FROM reddit_items ri
JOIN reddit_sources rs ON ri.source_id = rs.id
WHERE ri.id = $1 AND rs.user_id = $2;

-- name: ListStrategyCards :many
SELECT sc.* 
FROM strategy_cards sc
JOIN reddit_items ri ON sc.item_id = ri.id
JOIN reddit_sources rs ON ri.source_id = rs.id
WHERE rs.user_id = $1
  AND (sqlc.narg('group_id')::int IS NULL OR rs.group_id = sqlc.narg('group_id')::int)
ORDER BY sc.created_at DESC
LIMIT $2 OFFSET $3;

-- name: GetTopConfidentStrategyCards :many
SELECT sc.* 
FROM strategy_cards sc
JOIN reddit_items ri ON sc.item_id = ri.id
JOIN reddit_sources rs ON ri.source_id = rs.id
WHERE rs.user_id = $1
  AND (sqlc.narg('group_id')::int IS NULL OR rs.group_id = sqlc.narg('group_id')::int)
  AND sc.confidence >= $2
ORDER BY sc.confidence DESC, sc.created_at DESC
LIMIT $3;

-- name: ListRedditAlerts :many
SELECT ra.* 
FROM reddit_alerts ra
JOIN reddit_sources rs ON ra.source_id = rs.id
WHERE rs.user_id = $1
  AND (sqlc.narg('group_id')::int IS NULL OR rs.group_id = sqlc.narg('group_id')::int)
ORDER BY ra.created_at DESC
LIMIT $2 OFFSET $3;
