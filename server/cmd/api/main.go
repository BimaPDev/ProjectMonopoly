// cmd/api/main.go
package main

import (
	"database/sql"
	"fmt"
	"log"
	"net/http"

	_ "github.com/lib/pq"

	"github.com/BimaPDev/ProjectMonopoly/internal/auth"
	db "github.com/BimaPDev/ProjectMonopoly/internal/db/sqlc"
	"github.com/BimaPDev/ProjectMonopoly/internal/handlers"
	"github.com/BimaPDev/ProjectMonopoly/internal/middleware"
)

func main() {
	// 1) Connect to Postgres
	connStr := "user=root password=secret dbname=project_monopoly sslmode=disable"
	dbConn, err := sql.Open("postgres", connStr)
	if err != nil {
		log.Fatal(err)
	}
	defer dbConn.Close()

	// 2) Initialize SQLC queries
	queries := db.New(dbConn)

	// ─── Build a fresh mux ────────────────────────────────────────────────────────
	mux := http.NewServeMux()

	// ─── Public Routes ────────────────────────────────────────────────────────────
	mux.HandleFunc("/trigger", handlers.TriggerPythonScript)
	mux.HandleFunc("/health", handlers.HealthCheck)
	mux.HandleFunc("/followers", func(w http.ResponseWriter, r *http.Request) {
		handlers.TriggerFollowersScript(w, r, queries)
	})
	mux.HandleFunc("/ai/deepseek", handlers.DeepSeekHandler)

	// ─── Authentication ───────────────────────────────────────────────────────────
	mux.HandleFunc("/api/register", auth.RegisterHandler(queries))
	mux.HandleFunc("/api/login", auth.LoginHandler(queries))

	// ─── Protected Dashboard ────────────────────────────────────────────────────
	mux.HandleFunc("/api/protected/dashboard",
		auth.JWTMiddleware(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("🔒 Welcome to the protected dashboard!"))
		}),
	)

	// ─── getuserID ─────────────────────────────────────────────
	mux.HandleFunc("/api/getUserID", auth.JWTMiddleware(handlers.GetUserIDHandler(queries)))

	// ─── Upload Endpoint (Protected) ─────────────────────────────────────────────
	mux.HandleFunc("/api/upload", func(w http.ResponseWriter, r *http.Request) {
		handlers.UploadVideoHandler(w, r, queries)
	})

	mux.HandleFunc("/api/GetUploadItemsByGroupID",func(w http.ResponseWriter, r *http.Request){
	    handlers.GetUploadItemsByGroupID(w,r,queries)
	})

	// ─── Groups API: both "/api/groups" and "/api/groups/" ───────────────────────
	//    so that requests with or without trailing slash work.
	groupsHandler := func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			handlers.GetGroups(w, r, queries)
		case http.MethodPost:
			handlers.CreateGroup(w, r, queries)
		default:
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		}
	}

	// ─── addGroupItem ─────────────────────────────────────────────
	mux.HandleFunc("/api/AddGroupItem", func(w http.ResponseWriter, r *http.Request) {
		handlers.AddGroupItem(w, r, queries)
	})
	mux.HandleFunc("/api/GetGroupItem", func(w http.ResponseWriter, r *http.Request) {
		handlers.GetGroupItems(w,r,queries)
	})

	mux.HandleFunc("/api/groups", groupsHandler)
	mux.HandleFunc("/api/groups/", groupsHandler)

	// ─── Competitors API: both "/api/groups" and "/api/groups/" ───────────────────────
	//    so that requests with or without trailing slash work.

	// ─── Apply CORS & Start Server ───────────────────────────────────────────────
	handlerWithCORS := middleware.CORSMiddleware(mux)
	port := ":8080"
	fmt.Printf("✅ API server is running on http://localhost%s\n", port)
	log.Fatal(http.ListenAndServe(port, handlerWithCORS))
}
