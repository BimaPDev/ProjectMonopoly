package service

import (
	"context"
	"errors"
	"time"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/BimaPDev/ProjectMonopoly/internal/utils"
)

type CreateUserInput struct {
	Username string `json:"username"`
	Email    string `json:"email"`
	Password string `json:"password"`
}

var ErrUserAlreadyExists = errors.New("username or email already exists")

func CreateUser(queries *db.Queries, input CreateUserInput) (*UserResponse, error) {
	// Check if username or email already exists
	exists, err := queries.CheckUsernameOrEmailExists(context.TODO(), db.CheckUsernameOrEmailExistsParams{
		Username: input.Username,
		Email:    input.Email,
	})
	if err != nil {
		return nil, err
	}
	if exists {
		return nil, ErrUserAlreadyExists
	}

	// Hash the password
	hashedPassword, err := utils.HashPassword(input.Password)
	if err != nil {
		return nil, err
	}

	// 🔹 FIX: Change from `CreateUser` to `CreateUserWithPassword`
	userRow, err := queries.CreateUserWithPassword(context.TODO(), db.CreateUserWithPasswordParams{
		Username:     input.Username,
		Email:        input.Email,
		PasswordHash: hashedPassword,
	})
	if err != nil {
		return nil, err
	}

	// Map to UserResponse
	response := &UserResponse{
		ID:        int64(userRow.ID),
		Username:  userRow.Username,
		Email:     userRow.Email,
		CreatedAt: userRow.CreatedAt.Time, // Extract the time value
	}

	return response, nil
}

type UserResponse struct {
	ID        int64     `json:"id"`
	Username  string    `json:"username"`
	Email     string    `json:"email"`
	CreatedAt time.Time `json:"created_at"`
}
