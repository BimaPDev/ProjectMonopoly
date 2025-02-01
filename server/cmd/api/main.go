package main

import (
	"fmt"
	"log"
	"net/http"

	"github.com/BimaPDev/ProjectMonopoly/internal/handlers"
	"github.com/BimaPDev/ProjectMonopoly/internal/middleware" // Import middleware package
)

func main() {
	// Define routes
	http.HandleFunc("/trigger", handlers.TriggerPythonScript)
	http.HandleFunc("/health", handlers.HealthCheck)
	http.HandleFunc("/followers", handlers.TriggerFollowersScript)
	http.Handle("/Ai", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, `{"message": "AI response"}`)
	}))
	http.Handle("/ai/deepseek", middleware.CORS(http.HandlerFunc(handlers.DeepSeekHandler)))

	

	// Start the server
	port := ":8080"
	fmt.Printf("✅ API server is running on http://localhost%s\n", port)
	log.Fatal(http.ListenAndServe(port, nil))
}
