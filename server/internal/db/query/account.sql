-- name: CreateUsers :one
INSERT INTO users (
  username, role, created_at
) VALUES (
  $1, $2 , $3
)
RETURNING *;

-- name: GetUsers :one
SELECT * FROM users
WHERE id = $1 LIMIT 1;

-- name: ListUsers :many
SELECT * FROM users
ORDER BY id LIMIT $1 OFFSET $2;

-- name: UpdateUsers :exec
UPDATE users
set username = $2
WHERE id = $1;

-- name: DeleteUsers :exec
DELETE FROM users
WHERE id = $1;