package handlers

import (
	"encoding/json"
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
	return func(w http.ResponseWriter, r *http.Request) {
		userIDValue := r.Context().Value("userID")
		if userIDValue == nil {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}

		userID, ok := userIDValue.(int32)
		if !ok {
			http.Error(w, "invalid userID in context", http.StatusInternalServerError)
			return
		}

		resp := map[string]int32{"userID": userID}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(resp)
	}
}
