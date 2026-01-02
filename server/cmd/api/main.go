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
		log.Fatal("DATABASE_URL environment variable is not set")
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
	// /followers: support both GET (client uses GET) and POST for flexibility
	r.GET("/followers", wrap(handlers.TriggerFollowersScript))
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

			// User - POST required as it accepts JSON body
			protected.POST("/UserID", handlers.GetUserIDHandler(queries))

			// Uploads
			protected.POST("/upload", wrap(handlers.UploadVideoHandler))
			protected.GET("/UploadItemsByGroupID", wrap(handlers.GetUploadItemsByGroupID))
			protected.DELETE("/upload/:jobID", wrap(handlers.DeleteUploadVideo))

			// Upload Scheduler (Automated Content Pipeline)
			protected.GET("/uploads/pending", wrap(handlers.ListPendingUploads))
			protected.POST("/uploads/:id/approve", wrap(handlers.ApproveUpload))
			protected.POST("/uploads/:id/cancel", wrap(handlers.CancelUpload))

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
			protected.POST("/competitors/:id/profiles", wrap(handlers.AddProfileToCompetitor))
			protected.DELETE("/competitors/:id", wrap(handlers.DeleteCompetitor))

			// Workshop
			protected.POST("/workshop/upload", wrap(handlers.WorkshopUploadHandler))
			protected.POST("/workshop/search", handlers.WorkshopSearchHandler(queries))
			protected.POST("/workshop/ask", handlers.WorkshopAskHandler(queries))

			// Games Context
			protected.POST("/games/extract", wrap(handlers.ExtractGameContext))
			protected.POST("/games/input", wrap(handlers.SaveGameContext))

			// AI Chat (Protected)
			protected.POST("/ai/chat", wrap(handlers.DeepSeekHandler))

			// Marketing AI Generation (Optimized Pipeline)
			protected.POST("/marketing/generate", handlers.GenerateMarketingStrategyHandler(queries))

			// Test LLM
			protected.POST("/test/llm", handlers.TestLLMHandler)

			// ─── Campaign Workflow ───────────────────────────────────────────
			// Wizard options (preset data)
			protected.GET("/campaigns/wizard", handlers.GetWizardOptionsHandler())

			// Campaign CRUD
			protected.POST("/campaigns", handlers.CreateCampaignHandler(queries))
			protected.GET("/campaigns", handlers.ListCampaignsHandler(queries))
			protected.GET("/campaigns/:id", handlers.GetCampaignHandler(queries))
			protected.DELETE("/campaigns/:id", handlers.DeleteCampaignHandler(queries))

			// Campaign assets
			protected.POST("/campaigns/:id/assets", handlers.AttachCampaignAssetsHandler(queries))

			// AI generation
			protected.POST("/campaigns/:id/generate", handlers.GenerateCampaignDraftsHandler(queries))

			// Drafts
			protected.GET("/campaigns/:id/drafts", handlers.ListCampaignDraftsHandler(queries))

			// Insights / feedback loop
			protected.GET("/campaigns/:id/insights", handlers.GetCampaignInsightsHandler(queries))

			// Metrics ingestion (can be called by external systems)
			protected.POST("/metrics/ingest", handlers.IngestMetricsHandler(queries))

			// Dashboard Analytics
			protected.GET("/analytics/engagement-trends", handlers.GetEngagementTrendsHandler(queries))

			// ─── Reddit Listener ────────────────────────────────────────────────
			protected.POST("/reddit/sources", handlers.CreateSourceHandler(queries))
			protected.GET("/reddit/sources", handlers.ListSourcesHandler(queries))
			protected.DELETE("/reddit/sources/:id", handlers.DeleteSourceHandler(queries))
			protected.GET("/reddit/items", handlers.ListItemsHandler(queries))
			protected.GET("/reddit/cards", handlers.ListStrategyCardsHandler(queries))
			protected.GET("/reddit/alerts", handlers.ListAlertsHandler(queries))
		}
	}

	// ─── Start Server ───────────────────────────────────────────────
	port := ":8080"
	fmt.Printf("✅ API server is running on http://localhost%s\n", port)
	if err := r.Run(port); err != nil {
		log.Fatal(err)
	}
}
