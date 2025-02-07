package auth

import (
	"context"
	"encoding/json"
	"net/http"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc" // Your SQLC-generated package
	"golang.org/x/crypto/bcrypt"
)

// Register a new user
func RegisterHandler(queries *db.Queries) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var creds struct {
			Username string `json:"username"`
			Email    string `json:"email"`
			Password string `json:"password"`
		}

		err := json.NewDecoder(r.Body).Decode(&creds)
		if err != nil {
			http.Error(w, "Invalid request format", http.StatusBadRequest)
			return
		}

		// Hash the password before storing
		hashedPassword, err := bcrypt.GenerateFromPassword([]byte(creds.Password), bcrypt.DefaultCost)
		if err != nil {
			http.Error(w, "Failed to hash password", http.StatusInternalServerError)
			return
		}

		// Store user in DB using SQLC
		_, err = queries.CreateUserWithPassword(context.Background(), db.CreateUserWithPasswordParams{
			Username:    creds.Username,
			Email:       creds.Email,
			PasswordHash: string(hashedPassword),
		})
		if err != nil {
			http.Error(w, "Failed to create user", http.StatusInternalServerError)
			return
		}

		json.NewEncoder(w).Encode(map[string]string{"message": "User registered successfully"})
	}
}
