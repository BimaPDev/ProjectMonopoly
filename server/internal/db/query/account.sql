-- Register a new user with a password
-- name: CreateUserWithPassword :one
INSERT INTO users (username, email, password_hash, created_at, updated_at)
VALUES ($1, $2, $3, NOW(), NOW())
RETURNING id, username, email, created_at, updated_at;

-- Register a new OAuth user (if they don't exist, update username if needed)
-- name: CreateOAuthUser :one
INSERT INTO users (username, email, oauth_provider, oauth_id, created_at, updated_at)
VALUES ($1, $2, $3, $4, NOW(), NOW())
ON CONFLICT (email) 
DO UPDATE SET username = EXCLUDED.username, updated_at = NOW()
RETURNING id, username, email, oauth_provider, oauth_id, created_at, updated_at;

-- Get user by ID
-- name: GetUserByID :one
SELECT id, username, email, created_at, updated_at
FROM users
WHERE id = $1;

-- Get user by email (for password login)
-- name: GetUserByEmailWithPassword :one
SELECT id, username, email, password_hash, created_at, updated_at
FROM users
WHERE email = $1;

-- Get user by email (for OAuth login)
-- name: GetOAuthUserByEmail :one
SELECT id, username, email, oauth_provider, oauth_id, created_at, updated_at
FROM users
WHERE email = $1;

-- List all users
-- name: ListUsers :many
SELECT id, username, email, created_at, updated_at
FROM users
ORDER BY created_at DESC;

-- Update user details
-- name: UpdateUser :one
UPDATE users
SET username = $2,
    email = $3,
    updated_at = NOW()
WHERE id = $1
RETURNING id, username, email, created_at, updated_at;

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

-- Create a new session with configurable expiration
-- name: CreateSession :one
INSERT INTO sessions (user_id, expires_at)
VALUES ($1, NOW() + INTERVAL '24 hours')
RETURNING id, user_id, created_at, expires_at;

-- Get session by ID
-- name: GetSession :one
SELECT id, user_id, created_at, expires_at 
FROM sessions 
WHERE id = $1;

-- Delete a session (logout)
-- name: DeleteSession :exec
DELETE FROM sessions WHERE id = $1;

-- Create a new upload job with platform support
-- name: CreateUploadJob :one
INSERT INTO upload_jobs (id, user_id, platform, video_path, storage_type, file_url, status, created_at, updated_at)
VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())  
RETURNING id, user_id, platform, video_path, storage_type, file_url, status, created_at, updated_at;

-- Get upload job by ID
-- name: GetUploadJob :one
SELECT id, user_id, platform, video_path, storage_type, file_url, status, created_at, updated_at
FROM upload_jobs
WHERE id = $1;

-- Update upload job status
-- name: UpdateUploadJobStatus :exec
UPDATE upload_jobs
SET status = $2,
    updated_at = NOW()
WHERE id = $1;

-- Update upload job file URL
-- name: UpdateUploadJobFileURL :exec
UPDATE upload_jobs
SET file_url = $2,
    updated_at = NOW()
WHERE id = $1;

-- List all upload jobs for a user
-- name: ListUserUploadJobs :many
SELECT id, platform, video_path, platform ,storage_type, file_url, status, created_at, updated_at
FROM upload_jobs
WHERE user_id = $1
ORDER BY created_at DESC;
