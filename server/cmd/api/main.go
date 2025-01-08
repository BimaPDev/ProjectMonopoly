package main

import (
	"fmt"
	"log"
	"net/http"

	"github.com/BimaPDev/ProjectMonopoly/internal/handlers"
)

func main() {
	// Set up HTTP routes
	http.HandleFunc("/trigger", handlers.TriggerPythonScript) // Trigger Python script
	http.HandleFunc("/health", handlers.HealthCheck)          // Health check

	// Start the server
	port := ":8080"
	fmt.Printf("✅ API server is running on http://localhost%s\n", port)
	log.Fatal(http.ListenAndServe(port, nil))
}
