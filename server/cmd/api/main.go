// cmd/api/main.go
package main

import (
	"database/sql"
	"fmt"
	"log"
	"net/http"
	"os"

	_ "github.com/lib/pq"

	"github.com/BimaPDev/ProjectMonopoly/internal/auth"
	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/BimaPDev/ProjectMonopoly/internal/handlers"
	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
)

func main() {
	// 1) Connect to Postgres
	fmt.Println("Starting Server v2 (Gin)...")
	connStr := os.Getenv("DATABASE_URL")
	if connStr == "" {
		connStr = "user=root password=secret dbname=project_monopoly sslmode=disable"
	}
	dbConn, err := sql.Open("postgres", connStr)
	if err != nil {
		log.Fatal(err)
	}
	defer dbConn.Close()

	// 2) Initialize SQLC queries
	queries := db.New(dbConn)

	// 3) Initialize Gin
	// gin.SetMode(gin.ReleaseMode) // Uncomment for production
	r := gin.Default()

	// 4) CORS Configuration
	config := cors.DefaultConfig()
	config.AllowAllOrigins = true
	config.AllowMethods = []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"}
	config.AllowHeaders = []string{"Origin", "Content-Type", "Authorization", "X-User-ID"}
	r.Use(cors.New(config))

	// Helper to wrap handlers that need queries
	wrap := func(h func(*gin.Context, *db.Queries)) gin.HandlerFunc {
		return func(c *gin.Context) {
			h(c, queries)
		}
	}

	// ─── Public Routes ────────────────────────────────────────────────────────────
	r.POST("/trigger", handlers.TriggerPythonScript)
	r.GET("/health", handlers.HealthCheck)
	r.POST("/followers", wrap(handlers.TriggerFollowersScript))
	r.POST("/ai/deepseek", wrap(handlers.DeepSeekHandler))

	// ─── Authentication ───────────────────────────────────────────────────────────
	api := r.Group("/api")
	{
		api.POST("/register", auth.RegisterHandler(queries))
		api.POST("/login", auth.LoginHandler(queries))

		// ─── Protected Routes ─────────────────────────────────────────────────────
		protected := api.Group("/")
		protected.Use(auth.AuthMiddleware())
		{
			protected.GET("/protected/dashboard", func(c *gin.Context) {
				c.String(http.StatusOK, "🔒 Welcome to the protected dashboard!")
			})

			// User
			protected.GET("/UserID", handlers.GetUserIDHandler(queries))

			// Uploads
			protected.POST("/upload", wrap(handlers.UploadVideoHandler))
			protected.GET("/UploadItemsByGroupID", wrap(handlers.GetUploadItemsByGroupID))

			// Group Items
			protected.POST("/AddGroupItem", wrap(handlers.AddOrUpdateGroupItem))
			protected.GET("/GroupItem", wrap(handlers.GetGroupItems))

			// Groups
			protected.POST("/groups", wrap(handlers.CreateGroup))
			protected.GET("/groups", wrap(handlers.GetGroups))

			// Competitors
			// Note: CreateCompetitor expects :groupID param
			protected.POST("/groups/:groupID/competitors", wrap(handlers.CreateCompetitor))
			protected.GET("/groups/:groupID/competitors", wrap(handlers.ListUserCompetitors))
			protected.POST("/groups/competitors", wrap(handlers.CreateCompetitor))
			protected.GET("/groups/competitors", wrap(handlers.ListUserCompetitors))
			protected.GET("/competitors/posts", wrap(handlers.ListVisibleCompetitorPosts))
			protected.GET("/competitors/with-profiles", wrap(handlers.ListCompetitorsWithProfiles))

			// Workshop
			protected.POST("/workshop/upload", wrap(handlers.WorkshopUploadHandler))
			protected.POST("/workshop/search", handlers.WorkshopSearchHandler(queries))
			protected.POST("/workshop/ask", handlers.WorkshopAskHandler(queries))

			// Games Context
			protected.POST("/games/extract", wrap(handlers.ExtractGameContext))
			protected.POST("/games/input", wrap(handlers.SaveGameContext))

			// AI Chat (Protected)
			protected.POST("/ai/chat", wrap(handlers.DeepSeekHandler))

			// Test LLM
			protected.POST("/test/llm", handlers.TestLLMHandler)
		}
	}

	// ─── Start Server ───────────────────────────────────────────────
	port := ":8080"
	fmt.Printf("✅ API server is running on http://localhost%s\n", port)
	if err := r.Run(port); err != nil {
		log.Fatal(err)
	}
}
