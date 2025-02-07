package service

import (
	"errors"
	"time"
)

type CreateUserInput struct {
	Username string `json:"username"`
	Email    string `json:"email"`
	Password string `json:"password"`
}

var ErrUserAlreadyExists = errors.New("username or email already exists")

// func CreateUser(queries *db.Queries, input CreateUserInput) (*UserResponse, error) {
// 	// Check if username or email already exists
// 	exists, err := queries.CheckUsernameOrEmailExists(context.TODO(), db.CheckUsernameOrEmailExistsParams{
// 		Username: input.Username,
// 		Email:    input.Email,
// 	})
// 	if err != nil {
// 		return nil, err
// 	}
// 	if exists {
// 		return nil, ErrUserAlreadyExists
// 	}

// 	// Hash the password
// 	hashedPassword, err := utils.HashPassword(input.Password)
// 	if err != nil {
// 		return nil, err
// 	}

// 	// Create the user
// 	userRow, err := queries.CreateUser(context.TODO(), db.CreateUserParams{
// 		Username:     input.Username,
// 		Email:        input.Email,
// 		PasswordHash: hashedPassword,
// 	})
// 	if err != nil {
// 		return nil, err
// 	}

// 	// Map to UserResponse
// 	response := &UserResponse{
// 		ID:        int64(userRow.ID),
// 		Username:  userRow.Username,
// 		Email:     userRow.Email,
// 		CreatedAt: userRow.CreatedAt.Time, // Extract the time value
// 	}

// 	return response, nil
// }

type UserResponse struct {
	ID        int64     `json:"id"`
	Username  string    `json:"username"`
	Email     string    `json:"email"`
	CreatedAt time.Time `json:"created_at"`
}
