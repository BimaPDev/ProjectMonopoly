package main

import (
	// "database/sql"
	"fmt"
	"log"
	"net/http"

	"github.com/BimaPDev/ProjectMonopoly/internal/handlers"
	// db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	// "github.com/BimaPDev/ProjectMonopoly/internal/handlers"
	// _ "github.com/lib/pq" // PostgreSQL driver
)

func main() {

	// // Initialize the database connection
	// conn, err := sql.Open("postgres", "postgresql://root:secret@localhost:5432/project_monopoly?sslmode=disable")
	// if err != nil {
	// 	log.Fatal("❌ Failed to connect to the database:", err)
	// }

	// if err := conn.Ping(); err != nil {
	// 	log.Fatal("❌ Failed to ping the database:", err)
	// }

	// queries := db.New(conn)
	// Set up HTTP routesa
	http.HandleFunc("/trigger", handlers.TriggerPythonScript)      // Trigger Python script
	http.HandleFunc("/health", handlers.HealthCheck)               // Health check
	http.HandleFunc("/followers", handlers.TriggerFollowersScript) // Default route
	http.HandleFunc("/Ai", handlers.TriggerAiScript)
	//http.HandleFunc("/api/users", handlers.CreateUserHandler(queries))
	http.HandleFunc("/ai/deepseek", handlers.DeepSeekHandler)
	print("MAIN CALLED\n")

	// Start the server
	port := ":8080"
	fmt.Printf("✅ API server is running on http://localhost%s\n", port)
	log.Fatal(http.ListenAndServe(port, nil))
}
