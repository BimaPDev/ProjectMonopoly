# 🎯 Dogwood Gaming Marketing Tool (ProjectMonopoly)

---

## ✨ What Makes This Special

Transform your marketing workflow with a comprehensive platform that combines **intelligent automation**, **real-time analytics**, and **AI-powered insights** in one seamless experience.

### 🌟 Core Capabilities

| Feature | Description | Benefits |
|---------|-------------|----------|
| **📅 Smart Scheduling** | Upload and schedule posts across multiple platforms | Save hours of manual posting |
| **🎯 Competitor Intelligence** | Track rivals' strategies and performance metrics | Stay ahead of the competition |
| **📊 Analytics Dashboard** | Real-time engagement tracking and campaign insights | Make data-driven decisions |
| **🤖 AI Content Studio** | Leverage GPT-4, Claude, and DeepSeek for brainstorming | Never run out of creative ideas |

---

## 🚀 Feature Highlights

### 🏠 **Landing & Onboarding**
- **Stunning marketing website** with gradient hero sections and compelling CTAs
- **Dual authentication**: Custom forms + Google OAuth integration
- **Smart validation** prevents duplicate accounts and ensures data integrity

### 🔐 **Security & Access Control**
- **JWT-based authentication** with secure token storage
- **Protected routes** with automatic redirects for unauthorized access
- **Multi-platform credential management** with encrypted storage

### 📈 **Intelligent Dashboard**
- **Real-time follower tracking** across all connected platforms
- **Campaign performance overview** with filtering and status updates
- **Visual analytics** with interactive charts and growth metrics

### 👥 **Team Collaboration**
- **Group-based organization** for marketing teams and projects
- **Dynamic team switching** with context preservation
- **Role-based permissions** for different team members

### 🕵️ **Competitor Monitoring**
- **Multi-platform competitor tracking** (Instagram, TikTok, Twitter, YouTube)
- **Live feed dashboard** with real-time competitor post updates
- **Performance metrics**: followers, engagement rates, growth analysis
- **Expandable post details** with full content preview

### 📤 **Advanced Upload System**
- **Multi-step wizard** with intuitive drag-and-drop interface
- **Bulk scheduling** across multiple platforms simultaneously
- **Smart hashtag suggestions** and title optimization
- **Real-time progress tracking** with detailed status updates

### 🧠 **AI-Powered Studio**
- **Multi-model support**: GPT-4, Claude, DeepSeek integration
- **Rich chat interface** with markdown rendering and attachments
- **Conversation history** with timestamps and context preservation
- **Content brainstorming** and strategy recommendations

### ⚙️ **Comprehensive Settings**
- **Social media credential management** with secure encryption
- **Team and group administration** with granular controls
- **Extensive customization options** for workflows and preferences

---

## 🏗️ Architecture Overview
<img src="https://i.imgur.com/ODGDssP.png" alt="Dogwood Gaming Marketing Tool Dashboard" width="800"/>
---

## 💻 Frontend Technologies

### 🛠️ **Tech Stack**
- **⚡ Vite** - Lightning-fast build tool and dev server
- **🎨 TailwindCSS** - Utility-first CSS framework
- **🎭 Shadcn/UI** - Beautiful, accessible component library
- **🔧 Radix UI** - Low-level UI primitives
- **🌐 React Router** - Client-side routing solution

### 🎯 **Key Pages & Components**

#### **Core Pages**
| Page | Purpose | Key Features |
|------|---------|-------------|
| 🏠 **Landing** | Marketing website | Gradient backgrounds, animations, CTAs |
| 🔑 **Authentication** | Login/Register | OAuth integration, validation |
| 📊 **Dashboard** | Analytics overview | Real-time data, interactive charts |
| 🎯 **Competitors** | Rival tracking | Live feeds, performance metrics |
| 📤 **Upload** | Content scheduling | Multi-platform, progress tracking |
| 🤖 **AI Studio** | Content creation | Multi-model chat interface |
| ⚙️ **Settings** | Configuration | Credentials, team management |

#### **Notable Components**
- **🧭 AppSidebar** - Responsive navigation with collapsible sections
- **👤 NavUser** - User profile and account management
- **🔄 TeamSwitcher** - Dynamic group selection and creation
- **📈 Dashboard** - Data visualization with interactive elements
- **🎯 CompetitorsPage** - Comprehensive competitor analysis
- **📺 LiveFeed** - Real-time social media monitoring
- **📤 UploadPage** - Advanced file handling with progress tracking
- **🤖 AIPage** - Conversational AI interface with rich formatting

---

## ⚙️ Backend Architecture

### 🛠️ **Technology Stack**
- **🚀 Go (Gin Framework)** - High-performance HTTP router
- **🗃️ PostgreSQL** - Robust relational database
- **🔒 JWT Authentication** - Secure token-based auth
- **📝 SQLC** - Type-safe SQL code generation

### 🎯 **API Endpoints**

<details>
<summary><strong>📋 Complete API Reference</strong></summary>

#### **Authentication**
- `POST /auth/login` - User authentication
- `POST /auth/register` - Account creation
- `POST /auth/oauth/google` - Google OAuth flow

#### **Group Management**
- `GET /groups` - List user groups
- `POST /groups` - Create new group
- `PUT /groups/:id` - Update group details
- `DELETE /groups/:id` - Remove group

#### **Competitor Tracking**
- `GET /competitors` - List tracked competitors
- `POST /competitors` - Add new competitor
- `GET /competitors/:id/posts` - Fetch competitor posts
- `DELETE /competitors/:id` - Remove competitor

#### **Content Management**
- `POST /upload` - Upload and schedule content
- `GET /campaigns` - List scheduled campaigns
- `GET /status/:jobId` - Check upload progress

#### **AI Integration**
- `POST /ai/chat` - Send message to AI models
- `GET /ai/models` - List available AI models

</details>

### 🔧 **Core Packages**

| Package | Responsibility | Key Features |
|---------|----------------|-------------|
| **🔐 internal/auth** | Security layer | JWT generation, middleware, validation |
| **💾 internal/db/sqlc** | Database access | Type-safe queries, migrations |
| **🎯 internal/handlers** | API logic | REST endpoints, request handling |
| **🛠️ internal/utils** | Utilities | Password hashing, Python integration |
| **⚡ internal/function** | Experimental | TikTok scraper, advanced features |

---

## 🐍 Python Integration Layer

Our Go backend seamlessly integrates with Python scripts for specialized tasks:

- **📱 TikTok Automation** - Automated posting and engagement
- **📊 Analytics Processing** - Follower statistics and growth analysis  
- **🤖 AI Model Communication** - Interface with various AI providers
- **🔍 Data Scraping** - Competitor content and hashtag analysis

---

## 🐳 Docker Deployment

### **🏗️ Service Architecture**

```yaml
services:
  frontend:    # 🎨 React client via Nginx
  backend:     # 🔧 Go API server (port 8080)  
  db:          # 💾 PostgreSQL database
  python:      # 🐍 AI & automation service
  ollama:      # 🤖 Local AI model server (optional)
```

### **🚀 Quick Start**

```bash
# Launch entire stack
docker-compose up --build

# Access application
open http://localhost
```

---

## 🛠️ Development Setup

### **📋 Prerequisites**
- **Node.js** 18+ and npm
- **Go** 1.21+ 
- **PostgreSQL** 14+
- **Docker** (optional but recommended)

### **⚡ Quick Setup**

#### **1️⃣ Install Dependencies**
```bash
# Frontend dependencies
cd client && npm install

# Backend dependencies  
cd ../server && go mod download
```

#### **2️⃣ Database Setup**
```bash
# Start PostgreSQL
make postgres

# Create database
make createdb

# Run migrations
make migrateup
```

#### **3️⃣ Start Development Servers**

**Backend (Terminal 1):**
```bash
# Start Go API server
go run ./cmd/api

# Or use makefile
make server
```

**Frontend (Terminal 2):**
```bash
cd client
npm run dev
```

**🌐 Access Points:**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8080
- **Database**: localhost:5432

---

## 🎯 Getting Started

1. **🔧 Clone & Setup**
   ```bash
   git clone <repository-url>
   cd ProjectMonopoly
   ```

2. **🐳 Docker Quick Start**
   ```bash
   docker-compose up --build
   ```

3. **🌐 Access Application**
   - Open http://localhost
   - Register your account
   - Connect social media platforms
   - Start scheduling content!

4. **📚 Explore Features**
   - Add competitors to track
   - Schedule your first post
   - Chat with AI for content ideas
   - Analyze your performance metrics

---

## 🎯 Campaign Workflow (NEW)

The Campaign Workflow feature makes marketing "usable by non-marketers" through a guided wizard, structured AI outputs, and a feedback loop.

### 📋 How It Works

1. **Campaign Wizard** (5 Steps)
   - **Step 1: Goal** - Choose your objective (wishlist, discord, demo, trailer, awareness, launch)
   - **Step 2: Audience** - Select from preset audience archetypes (Core Gamer, Casual Player, Content Creator, etc.)
   - **Step 3: Content Pillars** - Pick 1-5 content themes (Behind the Scenes, Gameplay Highlights, etc.)
   - **Step 4: Assets** - Upload media files with tags (optional)
   - **Step 5: Cadence** - Select platforms and posting frequency

2. **AI Generation**
   - Campaign creation triggers automatic generation of structured post drafts
   - Each draft includes: platform, post type, hook, caption, hashtags, CTA, recommended time window, confidence score
   - Strict JSON schema ensures consistent, actionable output

3. **Feedback Loop**
   - Ingest post metrics via `/api/metrics/ingest`
   - View insights at `/dashboard/campaigns/:id/insights`
   - AI analyzes last 28 days of data to recommend:
     - Best posting windows (day + hour)
     - Top-performing hook patterns
     - Actionable improvement suggestions

### 🚀 Running Locally with Docker Compose

```bash
# 1. Set required environment variables
export JWT_SECRET="your-secure-secret-here"

# 2. Start all services
docker-compose up --build

# 3. Run database migrations
docker-compose exec backend go run ./cmd/migrate up

# 4. Access the app
open http://localhost

# 5. Navigate to Campaigns
# Go to Dashboard -> Campaigns -> New Campaign
```

### 📡 Campaign API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/campaigns/wizard` | Get wizard preset options |
| POST | `/api/campaigns` | Create campaign from wizard |
| GET | `/api/campaigns` | List user's campaigns |
| GET | `/api/campaigns/:id` | Get campaign details |
| POST | `/api/campaigns/:id/assets` | Upload campaign assets |
| POST | `/api/campaigns/:id/generate` | Generate AI drafts |
| GET | `/api/campaigns/:id/drafts` | List campaign drafts |
| GET | `/api/campaigns/:id/insights` | Get KPI summary + recommendations |
| POST | `/api/metrics/ingest` | Store post performance metrics |

### 🔧 Environment Variables

```bash
# Required in production
JWT_SECRET=your-secure-jwt-secret

# Database (defaults work for docker-compose)
DATABASE_URL=postgresql://root:secret@db:5432/project_monopoly?sslmode=disable

# Python Worker (auto-configured for docker-compose)
DB_HOST=db
CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
```

---

*Transforming social media marketing, one post at a time*

</div>
