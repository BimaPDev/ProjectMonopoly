# Dogwood Gaming Marketing Tool (ProjectMonopoly)

An **all-in-one application** for managing social-media marketing campaigns.  
Organized as a **monorepo** with a **React/TypeScript** client and a **Go** backend, this tool enables marketing teams to:

- Upload and schedule posts across multiple platforms
- Manage competitor groups
- Track posts and engagement metrics
- Leverage AI models for content brainstorming

---

## 🚀 Features

### **Landing & Registration**
- Marketing website with hero section, features list, and CTA buttons
- Registration via **custom form** or **Google OAuth**
- Backend validation to prevent duplicate accounts

### **Authentication & Protected Routes**
- Email/password or Google OAuth login
- Token-based authentication stored in `localStorage`
- `ProtectedRoute` redirects unauthenticated users

### **Dashboard**
- Overview of followers and campaigns
- Fetched data from backend (user ID, follower counts, scheduled campaigns)
- Filterable by campaign status

### **Group Management**
- Users belong to marketing groups/projects
- **Team Switcher** for switching or creating groups
- Active group stored in React Context

### **Competitors Page**
- Track competitors across social platforms
- Add competitors via prompt
- View metrics: followers, engagement, growth rate
- Expand to see competitor posts
- **Live Feed**: card-based, real-time competitor posts

### **Upload & Scheduling**
- Multi-step form for video/image uploads
- Title & hashtag inputs
- Multi-platform selection
- Drag-and-drop, date/time picker, progress bar
- Sends `multipart/form-data` to Go backend, which stores job in DB & triggers Python publishing scripts

### **AI Studio**
- Chat interface (DeepSeek / GPT-4 / Claude)
- Timestamped messages with attachment support
- AI responses rendered via `react-markdown`

### **Settings**
- Manage social media credentials and groups
- Add/remove group items
- Extensive form & modal interactions

---

## 📂 Repository Structure

ProjectMonopoly
├── client/ # React/TypeScript front-end (Vite)
│ ├── src/
│ │ ├── app/ # Page components (react-router)
│ │ ├── components/ # Shared UI + domain components
│ │ ├── hooks/ # Custom React hooks
│ │ ├── lib/ # Utility functions
│ │ └── utils/ # API helpers
│ ├── public/ # Static assets
│ ├── Dockerfile # Builds static files, serves via Nginx
│ ├── package.json
│ ├── tailwind.config.js
│ └── vite.config.ts
└── server/ # Go backend
├── cmd/api/ # Gin router & server startup
├── internal/
│ ├── auth/ # JWT creation & middleware
│ ├── db/ # SQLC-generated code & migrations
│ ├── handlers/ # REST API handlers
│ ├── utils/ # Helper functions
│ └── function/ # Experimental features
├── python/ # Python scripts (TikTok, AI)
├── go.mod / go.sum
├── Dockerfile
├── makefile
└── sqlc.yaml


---

## 🖥 Client (React/TypeScript)

Built with **Vite**, **TailwindCSS**, **Shadcn/UI**, and **Radix UI**.  
Communicates with the backend via `VITE_API_CALL`.

### Key Pages
- **Landing Page** – Gradient background, branding, CTAs
- **Login** – Email/password or Google OAuth
- **Register** – Prevents duplicate accounts
- **Dashboard** – Followers, campaigns, tabs, graphs
- **Competitors** – List & live feed views
- **Upload** – Multi-step scheduler
- **Settings** – Manage credentials & groups
- **AI Studio** – Chat with AI models

### Notable Components
- **AppSidebar**, **NavMain**, **NavUser**
- **TeamSwitcher** (group selection & creation)
- **Dashboard component** (data visualization)
- **CompetitorsPage / LiveFeed**
- **UploadPage** (file uploads, progress tracking)
- **AIPage** (chat UI)

---

## ⚙ Server (Go Backend)

Written in **Go** using the **Gin** framework.  
Implements REST endpoints for auth, group & competitor management, uploading, and AI integration.

### Key Packages
- **internal/auth** – JWT handling, middleware
- **internal/db/sqlc** – Typed DB access
- **internal/handlers** – Core API endpoints:
  - `group.go` – Group CRUD
  - `competitor.go` – Competitor management
  - `upload.go` – File uploads
  - `ai.go` – AI model integration
  - `status.go` – Job status queries
- **internal/utils** – Password hashing, JWT parsing, Python runners
- **internal/function** – Experimental TikTok hashtag scraper

---

## 🐍 Python Integration

The backend invokes Python scripts for:
- TikTok uploads
- Follower statistics
- AI model requests

---

## 🐳 Running with Docker

**Services in `docker-compose.yml`:**
- `frontend` – React client served via Nginx
- `backend` – Go API server on port `8080`
- `db` – PostgreSQL database
- `python` – Python service for AI/automation
- `ollama` – Optional local AI model server

**Run everything:**
```bash

docker-compose up --build
Visit http://localhost for the UI.

🔧 Development Setup
Install dependencies

bash
Copy
Edit
cd client && npm install
cd ../server && go mod download
Start PostgreSQL

bash
Copy
Edit
make postgres
make createdb
make migrateup
Run the backend

bash
Copy
Edit
go run ./cmd/api
# or
make server
Run the client

bash
Copy
Edit
cd client
npm run dev
Visit http://localhost:3000 (ensure VITE_API_CALL points to backend).
