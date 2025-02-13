-- Register a new user with a password
-- name: CreateUserWithPassword :one
INSERT INTO users (username, email, password_hash, created_at)
VALUES ($1, $2, $3, NOW())
RETURNING id, username, email, created_at;

-- Register a new OAuth user (if they don't exist)
-- name: CreateOAuthUser :one
INSERT INTO users (username, email, oauth_provider, oauth_id, created_at)
VALUES ($1, $2, $3, $4, NOW())
ON CONFLICT (email) DO NOTHING
RETURNING id, username, email, oauth_provider, oauth_id, created_at;

-- Get user by ID
-- name: GetUserByID :one
SELECT id, username, email, created_at
FROM users
WHERE id = $1;

-- Get user by email (for password login)
-- name: GetUserByEmailWithPassword :one
SELECT id, username, email, password_hash, created_at
FROM users
WHERE email = $1;

-- Get user by email (for OAuth login)
-- name: GetOAuthUserByEmail :one
SELECT id, username, email, oauth_provider, oauth_id, created_at
FROM users
WHERE email = $1;

-- List all users
-- name: ListUsers :many
SELECT id, username, email, created_at
FROM users
ORDER BY created_at DESC;

-- Update user details
-- name: UpdateUser :one
UPDATE users
SET username = $2,
    email = $3
WHERE id = $1
RETURNING id, username, email, created_at;

-- Delete a user
-- name: DeleteUser :exec
DELETE FROM users
WHERE id = $1;

-- Check if username or email exists
-- name: CheckUsernameOrEmailExists :one
SELECT COUNT(*) > 0 AS exists
FROM users
WHERE username = $1 OR email = $2;

-- Check if only email exists (for OAuth)
-- name: CheckEmailExists :one
SELECT COUNT(*) > 0 AS exists
FROM users
WHERE email = $1;

-- Create a new session
-- name: CreateSession :one
INSERT INTO sessions (user_id, expires_at)
VALUES ($1, NOW() + INTERVAL '24 hours')
RETURNING id, user_id, created_at, expires_at;

-- Get session by ID
-- name: GetSession :one
SELECT id, user_id, created_at, expires_at FROM sessions WHERE id = $1;

-- Delete a session (logout)
-- name: DeleteSession :exec
DELETE FROM sessions WHERE id = $1;
