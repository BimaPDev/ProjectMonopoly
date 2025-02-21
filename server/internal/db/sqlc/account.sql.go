// Code generated by sqlc. DO NOT EDIT.
// versions:
//   sqlc v1.28.0
// source: account.sql

package db

import (
	"context"
	"database/sql"

	"github.com/google/uuid"
)

const checkEmailExists = `-- name: CheckEmailExists :one
SELECT COUNT(*) > 0 AS exists
FROM users
WHERE email = $1
`

// Check if only email exists (for OAuth)
func (q *Queries) CheckEmailExists(ctx context.Context, email string) (bool, error) {
	row := q.db.QueryRowContext(ctx, checkEmailExists, email)
	var exists bool
	err := row.Scan(&exists)
	return exists, err
}

const checkUsernameOrEmailExists = `-- name: CheckUsernameOrEmailExists :one
SELECT COUNT(*) > 0 AS exists
FROM users
WHERE username = $1 OR email = $2
`

type CheckUsernameOrEmailExistsParams struct {
	Username string `json:"username"`
	Email    string `json:"email"`
}

// Check if username or email exists
func (q *Queries) CheckUsernameOrEmailExists(ctx context.Context, arg CheckUsernameOrEmailExistsParams) (bool, error) {
	row := q.db.QueryRowContext(ctx, checkUsernameOrEmailExists, arg.Username, arg.Email)
	var exists bool
	err := row.Scan(&exists)
	return exists, err
}

const createOAuthUser = `-- name: CreateOAuthUser :one
INSERT INTO users (username, email, oauth_provider, oauth_id, created_at)
VALUES ($1, $2, $3, $4, NOW())
ON CONFLICT (email) DO NOTHING
RETURNING id, username, email, oauth_provider, oauth_id, created_at
`

type CreateOAuthUserParams struct {
	Username      string         `json:"username"`
	Email         string         `json:"email"`
	OauthProvider sql.NullString `json:"oauth_provider"`
	OauthID       sql.NullString `json:"oauth_id"`
}

type CreateOAuthUserRow struct {
	ID            int32          `json:"id"`
	Username      string         `json:"username"`
	Email         string         `json:"email"`
	OauthProvider sql.NullString `json:"oauth_provider"`
	OauthID       sql.NullString `json:"oauth_id"`
	CreatedAt     sql.NullTime   `json:"created_at"`
}

// Register a new OAuth user (if they don't exist)
func (q *Queries) CreateOAuthUser(ctx context.Context, arg CreateOAuthUserParams) (CreateOAuthUserRow, error) {
	row := q.db.QueryRowContext(ctx, createOAuthUser,
		arg.Username,
		arg.Email,
		arg.OauthProvider,
		arg.OauthID,
	)
	var i CreateOAuthUserRow
	err := row.Scan(
		&i.ID,
		&i.Username,
		&i.Email,
		&i.OauthProvider,
		&i.OauthID,
		&i.CreatedAt,
	)
	return i, err
}

const createSession = `-- name: CreateSession :one
INSERT INTO sessions (user_id, expires_at)
VALUES ($1, NOW() + INTERVAL '24 hours')
RETURNING id, user_id, created_at, expires_at
`

// Create a new session
func (q *Queries) CreateSession(ctx context.Context, userID sql.NullInt32) (Session, error) {
	row := q.db.QueryRowContext(ctx, createSession, userID)
	var i Session
	err := row.Scan(
		&i.ID,
		&i.UserID,
		&i.CreatedAt,
		&i.ExpiresAt,
	)
	return i, err
}

const createUploadJob = `-- name: CreateUploadJob :one
INSERT INTO upload_jobs (id, user_id, video_path, storage_type, file_url, status)
VALUES ($1, $2, $3, $4, $5, $6)  
RETURNING id, user_id, video_path, storage_type, file_url, status, created_at
`

type CreateUploadJobParams struct {
	ID          string         `json:"id"`
	UserID      int32          `json:"user_id"`
	VideoPath   sql.NullString `json:"video_path"`
	StorageType sql.NullString `json:"storage_type"`
	FileUrl     sql.NullString `json:"file_url"`
	Status      sql.NullString `json:"status"`
}

func (q *Queries) CreateUploadJob(ctx context.Context, arg CreateUploadJobParams) (UploadJob, error) {
	row := q.db.QueryRowContext(ctx, createUploadJob,
		arg.ID,
		arg.UserID,
		arg.VideoPath,
		arg.StorageType,
		arg.FileUrl,
		arg.Status,
	)
	var i UploadJob
	err := row.Scan(
		&i.ID,
		&i.UserID,
		&i.VideoPath,
		&i.StorageType,
		&i.FileUrl,
		&i.Status,
		&i.CreatedAt,
	)
	return i, err
}

const createUserWithPassword = `-- name: CreateUserWithPassword :one
INSERT INTO users (username, email, password_hash, created_at)
VALUES ($1, $2, $3, NOW())
RETURNING id, username, email, created_at
`

type CreateUserWithPasswordParams struct {
	Username     string `json:"username"`
	Email        string `json:"email"`
	PasswordHash string `json:"password_hash"`
}

type CreateUserWithPasswordRow struct {
	ID        int32        `json:"id"`
	Username  string       `json:"username"`
	Email     string       `json:"email"`
	CreatedAt sql.NullTime `json:"created_at"`
}

// Register a new user with a password
func (q *Queries) CreateUserWithPassword(ctx context.Context, arg CreateUserWithPasswordParams) (CreateUserWithPasswordRow, error) {
	row := q.db.QueryRowContext(ctx, createUserWithPassword, arg.Username, arg.Email, arg.PasswordHash)
	var i CreateUserWithPasswordRow
	err := row.Scan(
		&i.ID,
		&i.Username,
		&i.Email,
		&i.CreatedAt,
	)
	return i, err
}

const deleteSession = `-- name: DeleteSession :exec
DELETE FROM sessions WHERE id = $1
`

// Delete a session (logout)
func (q *Queries) DeleteSession(ctx context.Context, id uuid.UUID) error {
	_, err := q.db.ExecContext(ctx, deleteSession, id)
	return err
}

const deleteUser = `-- name: DeleteUser :exec
DELETE FROM users
WHERE id = $1
`

// Delete a user
func (q *Queries) DeleteUser(ctx context.Context, id int32) error {
	_, err := q.db.ExecContext(ctx, deleteUser, id)
	return err
}

const getOAuthUserByEmail = `-- name: GetOAuthUserByEmail :one
SELECT id, username, email, oauth_provider, oauth_id, created_at
FROM users
WHERE email = $1
`

type GetOAuthUserByEmailRow struct {
	ID            int32          `json:"id"`
	Username      string         `json:"username"`
	Email         string         `json:"email"`
	OauthProvider sql.NullString `json:"oauth_provider"`
	OauthID       sql.NullString `json:"oauth_id"`
	CreatedAt     sql.NullTime   `json:"created_at"`
}

// Get user by email (for OAuth login)
func (q *Queries) GetOAuthUserByEmail(ctx context.Context, email string) (GetOAuthUserByEmailRow, error) {
	row := q.db.QueryRowContext(ctx, getOAuthUserByEmail, email)
	var i GetOAuthUserByEmailRow
	err := row.Scan(
		&i.ID,
		&i.Username,
		&i.Email,
		&i.OauthProvider,
		&i.OauthID,
		&i.CreatedAt,
	)
	return i, err
}

const getSession = `-- name: GetSession :one
SELECT id, user_id, created_at, expires_at FROM sessions WHERE id = $1
`

// Get session by ID
func (q *Queries) GetSession(ctx context.Context, id uuid.UUID) (Session, error) {
	row := q.db.QueryRowContext(ctx, getSession, id)
	var i Session
	err := row.Scan(
		&i.ID,
		&i.UserID,
		&i.CreatedAt,
		&i.ExpiresAt,
	)
	return i, err
}

const getUploadJob = `-- name: GetUploadJob :one
SELECT id, user_id, video_path, storage_type, file_url, status, created_at
FROM upload_jobs
WHERE id = $1
`

func (q *Queries) GetUploadJob(ctx context.Context, id string) (UploadJob, error) {
	row := q.db.QueryRowContext(ctx, getUploadJob, id)
	var i UploadJob
	err := row.Scan(
		&i.ID,
		&i.UserID,
		&i.VideoPath,
		&i.StorageType,
		&i.FileUrl,
		&i.Status,
		&i.CreatedAt,
	)
	return i, err
}

const getUserByEmailWithPassword = `-- name: GetUserByEmailWithPassword :one
SELECT id, username, email, password_hash, created_at
FROM users
WHERE email = $1
`

type GetUserByEmailWithPasswordRow struct {
	ID           int32        `json:"id"`
	Username     string       `json:"username"`
	Email        string       `json:"email"`
	PasswordHash string       `json:"password_hash"`
	CreatedAt    sql.NullTime `json:"created_at"`
}

// Get user by email (for password login)
func (q *Queries) GetUserByEmailWithPassword(ctx context.Context, email string) (GetUserByEmailWithPasswordRow, error) {
	row := q.db.QueryRowContext(ctx, getUserByEmailWithPassword, email)
	var i GetUserByEmailWithPasswordRow
	err := row.Scan(
		&i.ID,
		&i.Username,
		&i.Email,
		&i.PasswordHash,
		&i.CreatedAt,
	)
	return i, err
}

const getUserByID = `-- name: GetUserByID :one
SELECT id, username, email, created_at
FROM users
WHERE id = $1
`

type GetUserByIDRow struct {
	ID        int32        `json:"id"`
	Username  string       `json:"username"`
	Email     string       `json:"email"`
	CreatedAt sql.NullTime `json:"created_at"`
}

// Get user by ID
func (q *Queries) GetUserByID(ctx context.Context, id int32) (GetUserByIDRow, error) {
	row := q.db.QueryRowContext(ctx, getUserByID, id)
	var i GetUserByIDRow
	err := row.Scan(
		&i.ID,
		&i.Username,
		&i.Email,
		&i.CreatedAt,
	)
	return i, err
}

const listUserUploadJobs = `-- name: ListUserUploadJobs :many
SELECT id, video_path, storage_type, file_url, status, created_at
FROM upload_jobs
WHERE user_id = $1
ORDER BY created_at DESC
`

type ListUserUploadJobsRow struct {
	ID          string         `json:"id"`
	VideoPath   sql.NullString `json:"video_path"`
	StorageType sql.NullString `json:"storage_type"`
	FileUrl     sql.NullString `json:"file_url"`
	Status      sql.NullString `json:"status"`
	CreatedAt   sql.NullTime   `json:"created_at"`
}

func (q *Queries) ListUserUploadJobs(ctx context.Context, userID int32) ([]ListUserUploadJobsRow, error) {
	rows, err := q.db.QueryContext(ctx, listUserUploadJobs, userID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []ListUserUploadJobsRow
	for rows.Next() {
		var i ListUserUploadJobsRow
		if err := rows.Scan(
			&i.ID,
			&i.VideoPath,
			&i.StorageType,
			&i.FileUrl,
			&i.Status,
			&i.CreatedAt,
		); err != nil {
			return nil, err
		}
		items = append(items, i)
	}
	if err := rows.Close(); err != nil {
		return nil, err
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return items, nil
}

const listUsers = `-- name: ListUsers :many
SELECT id, username, email, created_at
FROM users
ORDER BY created_at DESC
`

type ListUsersRow struct {
	ID        int32        `json:"id"`
	Username  string       `json:"username"`
	Email     string       `json:"email"`
	CreatedAt sql.NullTime `json:"created_at"`
}

// List all users
func (q *Queries) ListUsers(ctx context.Context) ([]ListUsersRow, error) {
	rows, err := q.db.QueryContext(ctx, listUsers)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var items []ListUsersRow
	for rows.Next() {
		var i ListUsersRow
		if err := rows.Scan(
			&i.ID,
			&i.Username,
			&i.Email,
			&i.CreatedAt,
		); err != nil {
			return nil, err
		}
		items = append(items, i)
	}
	if err := rows.Close(); err != nil {
		return nil, err
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return items, nil
}

const updateUploadJobFileURL = `-- name: UpdateUploadJobFileURL :exec
UPDATE upload_jobs
SET file_url = $2
WHERE id = $1
`

type UpdateUploadJobFileURLParams struct {
	ID      string         `json:"id"`
	FileUrl sql.NullString `json:"file_url"`
}

func (q *Queries) UpdateUploadJobFileURL(ctx context.Context, arg UpdateUploadJobFileURLParams) error {
	_, err := q.db.ExecContext(ctx, updateUploadJobFileURL, arg.ID, arg.FileUrl)
	return err
}

const updateUploadJobStatus = `-- name: UpdateUploadJobStatus :exec
UPDATE upload_jobs
SET status = $2
WHERE id = $1
`

type UpdateUploadJobStatusParams struct {
	ID     string         `json:"id"`
	Status sql.NullString `json:"status"`
}

func (q *Queries) UpdateUploadJobStatus(ctx context.Context, arg UpdateUploadJobStatusParams) error {
	_, err := q.db.ExecContext(ctx, updateUploadJobStatus, arg.ID, arg.Status)
	return err
}

const updateUser = `-- name: UpdateUser :one
UPDATE users
SET username = $2,
    email = $3
WHERE id = $1
RETURNING id, username, email, created_at
`

type UpdateUserParams struct {
	ID       int32  `json:"id"`
	Username string `json:"username"`
	Email    string `json:"email"`
}

type UpdateUserRow struct {
	ID        int32        `json:"id"`
	Username  string       `json:"username"`
	Email     string       `json:"email"`
	CreatedAt sql.NullTime `json:"created_at"`
}

// Update user details
func (q *Queries) UpdateUser(ctx context.Context, arg UpdateUserParams) (UpdateUserRow, error) {
	row := q.db.QueryRowContext(ctx, updateUser, arg.ID, arg.Username, arg.Email)
	var i UpdateUserRow
	err := row.Scan(
		&i.ID,
		&i.Username,
		&i.Email,
		&i.CreatedAt,
	)
	return i, err
}
