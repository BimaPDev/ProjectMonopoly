package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"

	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/BimaPDev/ProjectMonopoly/internal/service"
)

func CreateUserHandler(queries *db.Queries) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var input service.CreateUserInput
		if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
			http.Error(w, "Invalid request body", http.StatusBadRequest)
			return
		}

		user, err := service.CreateUser(queries, input)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(user)
	}
}

type getUserIDRequest struct {
	Username string `json:"username"`
	Email    string `json:"email"`
}

type getUserIDResponse struct {
	ID int32 `json:"userID"`
}

// handler
func GetUserIDHandler(q *db.Queries) http.HandlerFunc {
	fmt.Printf("userID get called")
	type req struct{ Username, Email string }
	type resp struct {
		UserID int32 `json:"userID"`
	}
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		var body req
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			http.Error(w, "invalid JSON", http.StatusBadRequest)
			return
		}
		if body.Username == "" || body.Email == "" {
			http.Error(w, "username & email required", http.StatusBadRequest)
			return
		}
		id, err := q.GetUserIDByUsernameEmail(r.Context(), db.GetUserIDByUsernameEmailParams{
			Username: body.Username, Email: body.Email,
		})
		if err != nil {
			http.Error(w, "user not found", http.StatusNotFound)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(resp{UserID: id})
	}
}
