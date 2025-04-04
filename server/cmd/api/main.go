package main

import (
	"database/sql"
	"fmt"
	"log"
	"net/http"

	_ "github.com/lib/pq"

	"github.com/BimaPDev/ProjectMonopoly/internal/auth"
	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc" // Renamed sqlc -> db
	"github.com/BimaPDev/ProjectMonopoly/internal/handlers"
	"github.com/BimaPDev/ProjectMonopoly/internal/middleware"
)

func main() {
	// Database connection
	connStr := "user=root password=secret dbname=project_monopoly sslmode=disable"
	//connStr := "host=db user=root password=secret dbname=project_monopoly sslmode=disable"
	dbConn, err := sql.Open("postgres", connStr)
	if err != nil {
		log.Fatal(err)
	}
	defer dbConn.Close()

	// 🔹 FIX: Initialize SQLC Queries
	queries := db.New(dbConn) // ✅ This initializes SQLC-generated database queries

	// 🔹 Public Routes (No Authentication Required)
	http.HandleFunc("/trigger", handlers.TriggerPythonScript)
	http.HandleFunc("/health", handlers.HealthCheck)
	http.HandleFunc("/followers", handlers.TriggerFollowersScript)
	http.HandleFunc("/ai/deepseek", handlers.DeepSeekHandler)
	// 🔹 Authentication Routes
	http.HandleFunc("/api/register", auth.RegisterHandler(queries)) // ✅ Pass queries
	http.HandleFunc("/api/login", auth.LoginHandler(queries))       // ✅ Pass queries

	// 🔒 Protected Routes (JWT Required)
	http.HandleFunc("/api/protected/dashboard", auth.JWTMiddleware(func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("🔒 Welcome to the protected dashboard!"))
	}))

	// 🔒 POST API Request
	http.HandleFunc("/upload", func(w http.ResponseWriter, r *http.Request) {
		handlers.UploadVideoHandler(w, r, queries)
	})

	
	http.HandleFunc("/tiktok_session", func(w http.ResponseWriter, r *http.Request) {
		handlers.SaveSocialToken(w, r, queries)
	})

	http.HandleFunc("/createGroup", func(w http.ResponseWriter, r *http.Request) {
		handlers.CreateGroup(w, r, queries)
	})

	http.HandleFunc("/api/groups/", func(w http.ResponseWriter, r *http.Request) {
		handlers.CreateCompetitor(w, r, queries) // ✅ Now this refers to the package again
	})

	// Middleware (CORS)
	handlers := middleware.CORSMiddleware(http.DefaultServeMux)



	// Start the server
	port := ":8080"
	fmt.Printf("✅ API server is running on http://localhost%s\n", port)
	log.Fatal(http.ListenAndServe(port, handlers)) // Use built-in HTTP router
}
