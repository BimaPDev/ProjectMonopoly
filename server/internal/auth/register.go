package auth

import (
	"context"
	"encoding/json"
	"log"
	"net/http"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"golang.org/x/crypto/bcrypt"
)

func RegisterHandler(queries *db.Queries) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")

		var creds struct {
			Username string `json:"username"`
			Email    string `json:"email"`
			Password string `json:"password"`
		}

		err := json.NewDecoder(r.Body).Decode(&creds)
		if err != nil {
			w.WriteHeader(http.StatusBadRequest)
			json.NewEncoder(w).Encode(map[string]string{"error": "Invalid request format"})
			return
		}

		hashedPassword, err := bcrypt.GenerateFromPassword([]byte(creds.Password), bcrypt.DefaultCost)
		if err != nil {
			log.Printf("❌ Password hash error: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			json.NewEncoder(w).Encode(map[string]string{"error": "Failed to hash password"})
			return
		}

		_, err = queries.CreateUserWithPassword(context.Background(), db.CreateUserWithPasswordParams{
			Username:     creds.Username,
			Email:        creds.Email,
			PasswordHash: string(hashedPassword),
		})
		if err != nil {
			log.Printf("❌ Register error: %v", err)
			w.WriteHeader(http.StatusInternalServerError)
			json.NewEncoder(w).Encode(map[string]string{"error": "Failed to create user"})
			return
		}

		json.NewEncoder(w).Encode(map[string]string{"message": "User registered successfully"})
	}
}
