package main

import (
	"fmt"
	"log"
	"os"
	"path/filepath"

	"github.com/BimaPDev/GoService/internal/analytics"
	"github.com/gofiber/fiber/v2"
	"github.com/joho/godotenv"
)

func main() {
	// Explicitly define the path to the .env file
	envPath := filepath.Join(".", ".env")
	if err := godotenv.Load(envPath); err != nil {
		log.Fatalf("Error loading .env file from %s: %v", envPath, err)
	}

	// Print environment variables for verification
	fmt.Println("PORT:", os.Getenv("PORT"))
	fmt.Println("NODE_SERVICE_URL:", os.Getenv("NODE_SERVICE_URL"))

	// Initialize Fiber app
	app := fiber.New()

	// Health check route
	app.Get("/api/health", func(c *fiber.Ctx) error {
		return c.JSON(fiber.Map{
			"message": "Service is up and running",
		})
	})

	// Best time route
	app.Get("/api/best-time", analytics.GetBestTimeHandler)

	// Start the server
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	fmt.Printf("Go service running on port %s\n", port)
	log.Fatal(app.Listen(":" + port))
}
