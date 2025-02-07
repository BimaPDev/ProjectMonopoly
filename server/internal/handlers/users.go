package handlers

// func CreateUserHandler(queries *db.Queries) http.HandlerFunc {
// 	return func(w http.ResponseWriter, r *http.Request) {
// 		var input service.CreateUserInput
// 		if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
// 			http.Error(w, "Invalid request body", http.StatusBadRequest)
// 			return
// 		}

// 		user, err := service.CreateUser(queries, input)
// 		if err != nil {
// 			http.Error(w, err.Error(), http.StatusInternalServerError)
// 			return
// 		}

// 		w.Header().Set("Content-Type", "application/json")
// 		json.NewEncoder(w).Encode(user)
// 	}
// }
