// Code generated by sqlc. DO NOT EDIT.
// versions:
//   sqlc v1.28.0
// source: account.sql

package db

import (
	"context"
	"database/sql"
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
