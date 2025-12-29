# CODEBASE_LAYOUT

- Commit: `96fbc66715468a658a0d27aa5a6147aad91a31ab5`
- Generated at: `2025-12-27T15:48:00-05:00`

## 1) Ground-truth repo tree
```text
.
+-- .idea/
|   +-- inspectionProfiles/
|   |   \-- Project_Default.xml
|   +-- .gitignore
|   +-- modules.xml
|   +-- ProjectMonopoly.iml
|   \-- vcs.xml
+-- .vscode/
|   \-- settings.json
+-- client/
|   +-- public/
|   |   \-- vite.svg
|   +-- src/
|   |   +-- app/
|   |   |   +-- Ai/
|   |   |   +-- campaigns/
|   |   |   |   +-- insights/
|   |   |   |   |   \-- page.tsx
|   |   |   |   \-- page.tsx
|   |   |   +-- competitors/
|   |   |   +-- gameContext/
|   |   |   +-- landing/
|   |   |   +-- llmTest/
|   |   |   +-- login/
|   |   |   +-- marketing/
|   |   |   +-- register/
|   |   |   +-- settings/
|   |   |   \-- upload/
|   |   +-- assets/
|   |   |   \-- react.svg
|   |   +-- components/
|   |   |   +-- ui/
|   |   |   +-- About.tsx
|   |   |   +-- Ai-page.tsx
|   |   |   +-- app-sidebar.tsx
|   |   |   +-- App.tsx
|   |   |   +-- AuthenticatedLayout.tsx
|   |   |   +-- competitorAddForm.tsx
|   |   |   +-- CompetitorEditModal.tsx
|   |   |   +-- competitors-live-feed.tsx
|   |   |   +-- competitors-page.tsx
|   |   |   +-- dashboard.tsx
|   |   |   +-- groupContext.tsx
|   |   |   +-- login-form.tsx
|   |   |   +-- nav-main.tsx
|   |   |   +-- nav-projects.tsx
|   |   |   +-- nav-user.tsx
|   |   |   +-- ProtectedRoute.tsx
|   |   |   +-- rform.tsx
|   |   |   +-- socialPlatforms.tsx
|   |   |   +-- team-switcher.tsx
|   |   |   +-- theme-provider.tsx
|   |   |   +-- upload.tsx
|   |   |   \-- uploadContext.tsx
|   |   +-- hooks/
|   |   |   +-- use-mobile.tsx
|   |   |   \-- use-toast.ts
|   |   +-- lib/
|   |   |   \-- utils.ts
|   |   +-- utils/
|   |   |   +-- api.ts
|   |   |   \-- auth.ts
|   |   +-- App.tsx
|   |   +-- index.css
|   |   +-- main.tsx
|   |   +-- typewriter-effect.d.ts
|   |   \-- vite-env.d.ts
|   +-- .env
|   +-- .gitignore
|   +-- components.json
|   +-- Dockerfile
|   +-- eslint.config.js
|   +-- index.css
|   +-- index.html
|   +-- makefile
|   +-- nginx.conf
|   +-- package-lock.json
|   +-- package.json
|   +-- postcss.config.js
|   +-- README.md
|   +-- tailwind.config.js
|   +-- tsconfig.app.json
|   +-- tsconfig.json
|   +-- tsconfig.node.json
|   \-- vite.config.ts
+-- cookies/
|   \-- instagram_cookies.pkl
+-- docs/
|   \-- CODEBASE_LAYOUT.md
+-- server/
|   +-- cmd/
|   |   +-- api/
|   |   |   +-- uploads/
|   |   |   +-- data.csv
|   |   |   +-- data.txt
|   |   |   +-- detailed_data.json
|   |   |   +-- getFollowers.py
|   |   |   \-- main.go
|   |   \-- worker/
|   |       \-- main.go
|   +-- internal/
|   |   +-- auth/
|   |   |   +-- jwt.go
|   |   |   +-- login.go
|   |   |   +-- middleware.go
|   |   |   \-- register.go
|   |   +-- db/
|   |   |   +-- migration/
|   |   |   |   +-- 000001_init_schema.down.sql
|   |   |   |   +-- 000001_init_schema.up.sql
|   |   |   |   +-- 000002_campaigns.down.sql
|   |   |   |   \-- 000002_campaigns.up.sql
|   |   |   +-- query/
|   |   |   |   +-- ListVisibleCompetitorPosts.sql
|   |   |   |   +-- account.sql
|   |   |   |   +-- analytics.sql
|   |   |   |   +-- campaigns.sql
|   |   |   |   +-- competitor_posts.sql
|   |   |   |   \-- competitor_profiles.sql
|   |   |   +-- sqlc/
|   |   |   |   +-- ListVisibleCompetitorPosts.sql.go
|   |   |   |   +-- account.sql.go
|   |   |   |   +-- analytics.sql.go
|   |   |   |   +-- campaigns.sql.go
|   |   |   |   +-- competitor_posts.sql.go
|   |   |   |   +-- competitor_profiles.sql.go
|   |   |   |   +-- db.go
|   |   |   |   +-- models.go
|   |   |   |   \-- workshop.sql.go
|   |   |   \-- PostGress.go
|   |   +-- function/
|   |   |   \-- hashtag.go
|   |   +-- handlers/
|   |   |   +-- ai.go
|   |   |   +-- ai_generator.go
|   |   |   +-- campaigns.go
|   |   |   +-- competitor.go
|   |   |   +-- competitor_list.go
|   |   |   +-- competitor_posts.go
|   |   |   +-- competitors_with_profiles.go
|   |   |   +-- game_context.go
|   |   |   +-- game_contextOLLAMA.go
|   |   |   +-- group.go
|   |   |   +-- llm_provider.go
|   |   |   +-- llm_testing.go
|   |   |   +-- marketing_prompt.go
|   |   |   +-- marketing_prompt_test.go
|   |   |   +-- status.go
|   |   |   +-- trigger.go
|   |   |   +-- upload.go
|   |   |   +-- users.go
|   |   |   +-- workshop_ask.go
|   |   |   +-- workshop_search.go
|   |   |   \-- workshop_upload.go
|   |   +-- middleware/
|   |   |   \-- corsMid.go
|   |   +-- service/
|   |   |   \-- user_service.go
|   |   \-- utils/
|   |       +-- chatGPT.go
|   |       +-- deepseek.go
|   |       +-- hash.go
|   |       +-- jwt.go
|   |       +-- model.go
|   |       +-- python.go
|   |       +-- social.go
|   |       \-- validation.go
|   +-- python/
|   |   +-- ai_web/
|   |   |   +-- output/
|   |   |   +-- AiScraper.py
|   |   |   \-- scraper.log
|   |   +-- aiModels/
|   |   |   +-- __pycache__/
|   |   |   \-- deepseek.py
|   |   +-- cookies/
|   |   |   +-- instagram_cookies.pkl
|   |   |   \-- tiktok_cookies.pkl
|   |   +-- data/
|   |   |   +-- logs/
|   |   |   \-- celerybeat-schedule.db
|   |   +-- Followers/
|   |   |   \-- getFollowers.py
|   |   +-- socialmedia/
|   |   |   +-- __pycache__/
|   |   |   +-- cookies/
|   |   |   +-- scrape_result/
|   |   |   +-- socialmedia/
|   |   |   +-- utils/
|   |   |   +-- __init__.py
|   |   |   +-- analytics.py
|   |   |   +-- analytics2.py
|   |   |   +-- analytics3.py
|   |   |   +-- auth.json
|   |   |   +-- base.py
|   |   |   +-- cookies.json
|   |   |   +-- instagram_post.py
|   |   |   +-- instagram_testing.py
|   |   |   +-- instaPage.py
|   |   |   +-- rag_ingest.py
|   |   |   +-- test.py
|   |   |   +-- tiktok.py
|   |   |   +-- tiktok_scraper.py
|   |   |   +-- upload_to_db.py
|   |   |   \-- weekly_scraper.py
|   |   +-- trends/
|   |   |   \-- hastag.py
|   |   +-- uploads/
|   |   |   \-- docs/
|   |   +-- worker/
|   |   |   +-- __pycache__/
|   |   |   +-- __init__.py
|   |   |   +-- auto_dispatch.py
|   |   |   +-- celery_app.py
|   |   |   +-- config.py
|   |   |   +-- db.py
|   |   |   +-- tasks.py
|   |   |   \-- weekly_scheduler.py
|   |   +-- workshop/
|   |   |   \-- pdf_reader.py
|   |   +-- analytics_log.txt
|   |   +-- celerybeat-schedule.db
|   |   +-- Dockerfile
|   |   +-- fix_orphan_groups.py
|   |   +-- manual_login.py
|   |   +-- README_WEEKLY_SCRAPER.md
|   |   +-- requirements.in
|   |   +-- requirements.txt
|   |   +-- run_all.py
|   |   +-- test_weekly_scraper.py
|   |   +-- upload_debug.txt
|   |   +-- upload_debug_2.txt
|   |   +-- upload_log.txt
|   |   \-- upload_log_3.txt
|   +-- uploads/
|   |   \-- 1/
|   |       +-- 17d5ad78-75ce-4bb9-86ef-487a66754310-20250909T114528.mp4
|   |       +-- 250207-lebron-james-mn-0815-1a91c8.jpg
|   |       +-- download.jpeg
|   |       +-- IMG_7010.PNG
|   |       \-- IMG_F6A880FCEF11-1.jpeg
|   +-- .env
|   +-- .gitignore
|   +-- api
|   +-- debug_competitors.go
|   +-- detailed_data.json
|   +-- Dockerfile
|   +-- err.log
|   +-- go.mod
|   +-- go.sum
|   +-- makefile
|   +-- package-lock.json
|   +-- package.json
|   \-- sqlc.yaml
+-- .gitignore
+-- docker-compose-prod.yml
+-- docker-compose.yml
+-- makefile
\-- README.md
```

## 2) Go backend: TRUE route inventory (complete)
- Normalized server path: collapse repeated slashes and normalize :<name> -> :param for comparison.

### 2.1 Routes (normalized)
| METHOD | PATH (normalized) | Handler | file:line | Middleware stack (best-effort) |
|---|---|---|---|---|
| POST | `/ai/deepseek` | `wrap(handlers.DeepSeekHandler)` | `server/cmd/api/main.go:59` | cors.New(config) |
| POST | `/api/AddGroupItem` | `wrap(handlers.AddOrUpdateGroupItem)` | `server/cmd/api/main.go:83` | cors.New(config); auth.AuthMiddleware() |
| GET | `/api/GroupItem` | `wrap(handlers.GetGroupItems)` | `server/cmd/api/main.go:84` | cors.New(config); auth.AuthMiddleware() |
| GET | `/api/UploadItemsByGroupID` | `wrap(handlers.GetUploadItemsByGroupID)` | `server/cmd/api/main.go:80` | cors.New(config); auth.AuthMiddleware() |
| POST | `/api/UserID` | `handlers.GetUserIDHandler(queries)` | `server/cmd/api/main.go:76` | cors.New(config); auth.AuthMiddleware() |
| POST | `/api/ai/chat` | `wrap(handlers.DeepSeekHandler)` | `server/cmd/api/main.go:109` | cors.New(config); auth.AuthMiddleware() |
| GET | `/api/campaigns` | `handlers.ListCampaignsHandler(queries)` | `server/cmd/api/main.go:121` | cors.New(config); auth.AuthMiddleware() |
| POST | `/api/campaigns` | `handlers.CreateCampaignHandler(queries)` | `server/cmd/api/main.go:120` | cors.New(config); auth.AuthMiddleware() |
| GET | `/api/campaigns/:param` | `handlers.GetCampaignHandler(queries)` | `server/cmd/api/main.go:122` | cors.New(config); auth.AuthMiddleware() |
| POST | `/api/campaigns/:param/assets` | `handlers.AttachCampaignAssetsHandler(queries)` | `server/cmd/api/main.go:125` | cors.New(config); auth.AuthMiddleware() |
| GET | `/api/campaigns/:param/drafts` | `handlers.ListCampaignDraftsHandler(queries)` | `server/cmd/api/main.go:131` | cors.New(config); auth.AuthMiddleware() |
| POST | `/api/campaigns/:param/generate` | `handlers.GenerateCampaignDraftsHandler(queries)` | `server/cmd/api/main.go:128` | cors.New(config); auth.AuthMiddleware() |
| GET | `/api/campaigns/:param/insights` | `handlers.GetCampaignInsightsHandler(queries)` | `server/cmd/api/main.go:134` | cors.New(config); auth.AuthMiddleware() |
| GET | `/api/campaigns/wizard` | `handlers.GetWizardOptionsHandler()` | `server/cmd/api/main.go:118` | cors.New(config); auth.AuthMiddleware() |
| GET | `/api/competitors/posts` | `wrap(handlers.ListVisibleCompetitorPosts)` | `server/cmd/api/main.go:96` | cors.New(config); auth.AuthMiddleware() |
| GET | `/api/competitors/with-profiles` | `wrap(handlers.ListCompetitorsWithProfiles)` | `server/cmd/api/main.go:97` | cors.New(config); auth.AuthMiddleware() |
| POST | `/api/games/extract` | `wrap(handlers.ExtractGameContext)` | `server/cmd/api/main.go:105` | cors.New(config); auth.AuthMiddleware() |
| POST | `/api/games/input` | `wrap(handlers.SaveGameContext)` | `server/cmd/api/main.go:106` | cors.New(config); auth.AuthMiddleware() |
| GET | `/api/groups` | `wrap(handlers.GetGroups)` | `server/cmd/api/main.go:88` | cors.New(config); auth.AuthMiddleware() |
| POST | `/api/groups` | `wrap(handlers.CreateGroup)` | `server/cmd/api/main.go:87` | cors.New(config); auth.AuthMiddleware() |
| GET | `/api/groups/:param/competitors` | `wrap(handlers.ListUserCompetitors)` | `server/cmd/api/main.go:93` | cors.New(config); auth.AuthMiddleware() |
| POST | `/api/groups/:param/competitors` | `wrap(handlers.CreateCompetitor)` | `server/cmd/api/main.go:92` | cors.New(config); auth.AuthMiddleware() |
| GET | `/api/groups/competitors` | `wrap(handlers.ListUserCompetitors)` | `server/cmd/api/main.go:95` | cors.New(config); auth.AuthMiddleware() |
| POST | `/api/groups/competitors` | `wrap(handlers.CreateCompetitor)` | `server/cmd/api/main.go:94` | cors.New(config); auth.AuthMiddleware() |
| POST | `/api/login` | `auth.LoginHandler(queries)` | `server/cmd/api/main.go:65` | cors.New(config) |
| POST | `/api/marketing/generate` | `handlers.GenerateMarketingStrategyHandler(queries)` | `server/cmd/api/main.go:112` | cors.New(config); auth.AuthMiddleware() |
| POST | `/api/metrics/ingest` | `handlers.IngestMetricsHandler(queries)` | `server/cmd/api/main.go:137` | cors.New(config); auth.AuthMiddleware() |
| GET | `/api/protected/dashboard` | `func(c *gin.Context) {...}` | `server/cmd/api/main.go:71` | cors.New(config); auth.AuthMiddleware() |
| POST | `/api/register` | `auth.RegisterHandler(queries)` | `server/cmd/api/main.go:64` | cors.New(config) |
| POST | `/api/test/llm` | `handlers.TestLLMHandler` | `server/cmd/api/main.go:115` | cors.New(config); auth.AuthMiddleware() |
| POST | `/api/upload` | `wrap(handlers.UploadVideoHandler)` | `server/cmd/api/main.go:79` | cors.New(config); auth.AuthMiddleware() |
| POST | `/api/workshop/ask` | `handlers.WorkshopAskHandler(queries)` | `server/cmd/api/main.go:102` | cors.New(config); auth.AuthMiddleware() |
| POST | `/api/workshop/search` | `handlers.WorkshopSearchHandler(queries)` | `server/cmd/api/main.go:101` | cors.New(config); auth.AuthMiddleware() |
| POST | `/api/workshop/upload` | `wrap(handlers.WorkshopUploadHandler)` | `server/cmd/api/main.go:100` | cors.New(config); auth.AuthMiddleware() |
| GET | `/followers` | `wrap(handlers.TriggerFollowersScript)` | `server/cmd/api/main.go:57` | cors.New(config) |
| POST | `/followers` | `wrap(handlers.TriggerFollowersScript)` | `server/cmd/api/main.go:58` | cors.New(config) |
| GET | `/health` | `handlers.HealthCheck` | `server/cmd/api/main.go:56` | cors.New(config) |
| POST | `/trigger` | `handlers.TriggerPythonScript` | `server/cmd/api/main.go:55` | cors.New(config) |

### 2.2 /api/protected/dashboard reconciliation
- Proven: `server/cmd/api/main.go:71` registers `GET /api/protected/dashboard`.

## 3) Client: endpoint extraction
- Normalized client path: collapse repeated slashes, replace ${...} with :param, then normalize params to :param (for contract drift).

### `/api/AddGroupItem`
- Methods used by client: **POST**
- Examples (raw URL strings):
  - `/api/AddGroupItem`
- References:
  - `client/src/app/settings/socialMedia/page.tsx:202`
  - `client/src/app/settings/socialMedia/page.tsx:295`

### `/api/GroupItem`
- Methods used by client: **GET**
- Examples (raw URL strings):
  - `/api/GroupItem?groupID=${selectedGroup.ID}`
- References:
  - `client/src/app/settings/socialMedia/page.tsx:164`

### `/api/UploadItemsByGroupID`
- Methods used by client: **GET**
- Examples (raw URL strings):
  - `/api/UploadItemsByGroupID?groupID=${activeGroup.ID}`
- References:
  - `client/src/components/dashboard.tsx:139`

### `/api/UserID`
- Methods used by client: **POST**
- Examples (raw URL strings):
  - `/api/UserID`
- References:
  - `client/src/components/dashboard.tsx:87`

### `/api/campaigns`
- Methods used by client: **GET,POST**
- Examples (raw URL strings):
  - `/api/campaigns`
- References:
  - `client/src/app/campaigns/page.tsx`

### `/api/campaigns/:param`
- Methods used by client: **GET**
- Examples (raw URL strings):
  - `/api/campaigns/${campaignId}`
- References:
  - `client/src/app/campaigns/page.tsx`

### `/api/campaigns/:param/generate`
- Methods used by client: **POST**
- Examples (raw URL strings):
  - `/api/campaigns/${campaignId}/generate`
- References:
  - `client/src/app/campaigns/page.tsx`

### `/api/campaigns/:param/insights`
- Methods used by client: **GET**
- Examples (raw URL strings):
  - `/api/campaigns/${campaignId}/insights`
- References:
  - `client/src/app/campaigns/insights/page.tsx`

### `/api/campaigns/wizard`
- Methods used by client: **GET**
- Examples (raw URL strings):
  - `/api/campaigns/wizard`
- References:
  - `client/src/app/campaigns/page.tsx`

### `/api/competitors/:param/profiles`
- Methods used by client: **POST**
- Examples (raw URL strings):
  - `/api/competitors/${competitorId}/profiles`
- References:
  - `client/src/components/CompetitorEditModal.tsx:51`

### `/api/competitors/posts`
- Methods used by client: **GET**
- Examples (raw URL strings):
  - `/api/competitors/posts?group_id=${activeGroup?.ID}`
- References:
  - `client/src/components/competitors-page.tsx:109`

### `/api/competitors/profiles/:param`
- Methods used by client: **DELETE**
- Examples (raw URL strings):
  - `/api/competitors/profiles/${profileId}`
- References:
  - `client/src/components/CompetitorEditModal.tsx:84`

### `/api/competitors/with-profiles`
- Methods used by client: **GET**
- Examples (raw URL strings):
  - `/api/competitors/with-profiles`
- References:
  - `client/src/components/competitors-page.tsx:156`

### `/api/games/extract`
- Methods used by client: **POST**
- Examples (raw URL strings):
  - `/api/games/extract`
- References:
  - `client/src/app/gameContext/page.tsx:101`

### `/api/games/input`
- Methods used by client: **POST**
- Examples (raw URL strings):
  - `/api/games/input`
- References:
  - `client/src/app/gameContext/page.tsx:228`

### `/api/groups`
- Methods used by client: **GET,POST**
- Examples (raw URL strings):
  - `/api/groups`
  - `/api/groups?userID=${numericID}`
  - `/api/groups?userID=${userID}`
- References:
  - `client/src/app/settings/socialMedia/page.tsx:112`
  - `client/src/app/settings/socialMedia/page.tsx:237`
  - `client/src/components/team-switcher.tsx:67`
  - `client/src/components/team-switcher.tsx:119`
  - `client/src/components/upload.tsx:94`

### `/api/groups/competitors`
- Methods used by client: **GET**
- Examples (raw URL strings):
  - `/api/groups/competitors`
- References:
  - `client/src/components/competitors-page.tsx:185`

### `/api/login`
- Methods used by client: **POST**
- Examples (raw URL strings):
  - `/api/login`
  - `http://127.0.0.1:8080/api/login`
- References:
  - `client/src/components/login-form.tsx:18`
  - `client/src/components/login-form.tsx:64`
  - `client/src/components/rform.tsx:23`
  - `client/src/components/rform.tsx:56`
  - `client/src/utils/auth.ts:3`

### `/api/marketing/generate`
- Methods used by client: **POST**
- Examples (raw URL strings):
  - `${import.meta.env.VITE_BACKEND_URL || ""}/api/marketing/generate`
- References:
  - `client/src/app/marketing/page.tsx:72`

### `/api/protected/dashboard`
- Methods used by client: **GET**
- Examples (raw URL strings):
  - `/api/protected/dashboard`
- References:
  - `client/src/utils/api.ts:7`

### `/api/register`
- Methods used by client: **POST**
- Examples (raw URL strings):
  - `/api/register`
- References:
  - `client/src/app/register/page.tsx:50`
  - `client/src/app/register/page.tsx:124`
  - `client/src/components/login-form.tsx:72`

### `/api/test/llm`
- Methods used by client: **POST**
- Examples (raw URL strings):
  - `/api/test/llm`
- References:
  - `client/src/app/llmTest/page.tsx:37`

### `/api/upload`
- Methods used by client: **POST**
- Examples (raw URL strings):
  - `/api/upload`
- References:
  - `client/src/components/upload.tsx:167`

### `/api/workshop/ask`
- Methods used by client: **POST**
- Examples (raw URL strings):
  - `/api/workshop/ask`
- References:
  - `client/src/components/Ai-page.tsx:176`

### `/api/workshop/upload`
- Methods used by client: **[Unknown]**
- [Unknown] method refs:
  - `client/src/components/uploadContext.tsx:49`
- Examples (raw URL strings):
  - `/api/workshop/upload`
- References:
  - `client/src/components/uploadContext.tsx:49`

### `/followers`
- Methods used by client: **GET**
- Examples (raw URL strings):
  - `/followers`
- References:
  - `client/src/components/dashboard.tsx:114`

### `/health`
- Methods used by client: **GET**
- Examples (raw URL strings):
  - `/health`
- References:
  - `client/src/components/Ai-page.tsx:85`

### [Unparsed] client callsites
- `client/src/components/competitorAddForm.tsx:29`: `/api/groups/${activeGroup?.ID || ""}/competitors`

## 4) Contract drift
| Normalized client endpoint | Client methods | Exists in server routes? | Server route entry | Client refs (file:line) |
|---|---|---:|---|---|
| `/api/AddGroupItem` | POST | Yes | POST /api/AddGroupItem server/cmd/api/main.go:83 | `client/src/app/settings/socialMedia/page.tsx:202`, `client/src/app/settings/socialMedia/page.tsx:295` |
| `/api/GroupItem` | GET | Yes | GET /api/GroupItem server/cmd/api/main.go:84 | `client/src/app/settings/socialMedia/page.tsx:164` |
| `/api/UploadItemsByGroupID` | GET | Yes | GET /api/UploadItemsByGroupID server/cmd/api/main.go:80 | `client/src/components/dashboard.tsx:139` |
| `/api/UserID` | POST | Yes | POST /api/UserID server/cmd/api/main.go:76 | `client/src/components/dashboard.tsx:87` |
| `/api/campaigns` | GET, POST | Yes | GET /api/campaigns server/cmd/api/main.go:121<br/>POST /api/campaigns server/cmd/api/main.go:120 | `client/src/app/campaigns/page.tsx` |
| `/api/campaigns/:param` | GET | Yes | GET /api/campaigns/:id server/cmd/api/main.go:122 | `client/src/app/campaigns/page.tsx` |
| `/api/campaigns/:param/generate` | POST | Yes | POST /api/campaigns/:id/generate server/cmd/api/main.go:128 | `client/src/app/campaigns/page.tsx` |
| `/api/campaigns/:param/insights` | GET | Yes | GET /api/campaigns/:id/insights server/cmd/api/main.go:134 | `client/src/app/campaigns/insights/page.tsx` |
| `/api/campaigns/wizard` | GET | Yes | GET /api/campaigns/wizard server/cmd/api/main.go:118 | `client/src/app/campaigns/page.tsx` |
| `/api/competitors/:param/profiles` | POST | No |  | `client/src/components/CompetitorEditModal.tsx:51` |
| `/api/competitors/posts` | GET | Yes | GET /api/competitors/posts server/cmd/api/main.go:96 | `client/src/components/competitors-page.tsx:109` |
| `/api/competitors/profiles/:param` | DELETE | No |  | `client/src/components/CompetitorEditModal.tsx:84` |
| `/api/competitors/with-profiles` | GET | Yes | GET /api/competitors/with-profiles server/cmd/api/main.go:97 | `client/src/components/competitors-page.tsx:156` |
| `/api/games/extract` | POST | Yes | POST /api/games/extract server/cmd/api/main.go:105 | `client/src/app/gameContext/page.tsx:101` |
| `/api/games/input` | POST | Yes | POST /api/games/input server/cmd/api/main.go:106 | `client/src/app/gameContext/page.tsx:228` |
| `/api/groups` | GET, POST | Yes | GET /api/groups server/cmd/api/main.go:88<br/>POST /api/groups server/cmd/api/main.go:87 | `client/src/app/settings/socialMedia/page.tsx:112`, `client/src/app/settings/socialMedia/page.tsx:237`, `client/src/components/team-switcher.tsx:67`, `client/src/components/team-switcher.tsx:119`, `client/src/components/upload.tsx:94` |
| `/api/groups/competitors` | GET | Yes | GET /api/groups/competitors server/cmd/api/main.go:95 | `client/src/components/competitors-page.tsx:185` |
| `/api/login` | POST | Yes | POST /api/login server/cmd/api/main.go:65 | `client/src/components/login-form.tsx:18`, `client/src/components/login-form.tsx:64`, `client/src/components/rform.tsx:23`, `client/src/components/rform.tsx:56`, `client/src/utils/auth.ts:3` |
| `/api/marketing/generate` | POST | Yes | POST /api/marketing/generate server/cmd/api/main.go:112 | `client/src/app/marketing/page.tsx:72` |
| `/api/protected/dashboard` | GET | Yes | GET /api/protected/dashboard server/cmd/api/main.go:71 | `client/src/utils/api.ts:7` |
| `/api/register` | POST | Yes | POST /api/register server/cmd/api/main.go:64 | `client/src/app/register/page.tsx:50`, `client/src/app/register/page.tsx:124`, `client/src/components/login-form.tsx:72` |
| `/api/test/llm` | POST | Yes | POST /api/test/llm server/cmd/api/main.go:115 | `client/src/app/llmTest/page.tsx:37` |
| `/api/upload` | POST | Yes | POST /api/upload server/cmd/api/main.go:79 | `client/src/components/upload.tsx:167` |
| `/api/workshop/ask` | POST | Yes | POST /api/workshop/ask server/cmd/api/main.go:102 | `client/src/components/Ai-page.tsx:176` |
| `/api/workshop/upload` | [Unknown] | Yes | POST /api/workshop/upload server/cmd/api/main.go:100 | `client/src/components/uploadContext.tsx:49` |
| `/followers` | GET | Yes | GET /followers server/cmd/api/main.go:57 | `client/src/components/dashboard.tsx:114` |
| `/health` | GET | Yes | GET /health server/cmd/api/main.go:56 | `client/src/components/Ai-page.tsx:85` |

## 5) DB layer

### 5.1 Table -> sqlc queries (filtered to migration tables)
- **campaigns**:
  - `CreateCampaign` (server/internal/db/query/campaigns.sql:3)
  - `DeleteCampaign` (server/internal/db/query/campaigns.sql:43)
  - `GetCampaignByID` (server/internal/db/query/campaigns.sql:17)
  - `GetTopHookPatterns` (server/internal/db/query/campaigns.sql:180)
  - `ListCampaignsByGroup` (server/internal/db/query/campaigns.sql:25)
  - `ListCampaignsByUser` (server/internal/db/query/campaigns.sql:20)
  - `UpdateCampaign` (server/internal/db/query/campaigns.sql:32)
  - `UpdateCampaignStatus` (server/internal/db/query/campaigns.sql:30)
- **campaign_assets**:
  - `CreateCampaignAsset` (server/internal/db/query/campaigns.sql:47)
  - `DeleteCampaignAsset` (server/internal/db/query/campaigns.sql:64)
  - `ListCampaignAssets` (server/internal/db/query/campaigns.sql:59)
- **competitor_posts**:
  - `GetBestPostingDay` (server/internal/db/query/analytics.sql:105)
  - `GetBestPostingHour` (server/internal/db/query/analytics.sql:39)
  - `GetCompetitorPostCount14Days` (server/internal/db/query/analytics.sql:95)
  - `GetPostingFrequency28Days` (server/internal/db/query/analytics.sql:130)
  - `GetRecentCompetitorPosts` (server/internal/db/query/competitor_posts.sql:78)
  - `GetTimeBoxedCompetitorInsights` (server/internal/db/query/analytics.sql:4)
  - `GetTopCompetitorHashtags` (server/internal/db/query/analytics.sql:142)
  - `GetTopCompetitorHooks` (server/internal/db/query/analytics.sql:66)
  - `ListVisibleCompetitorPosts` (server/internal/db/query/ListVisibleCompetitorPosts.sql:1)
  - `SearchCompetitorPosts` (server/internal/db/query/competitor_posts.sql:44)
- **competitor_profiles**:
  - `CreateCompetitorProfile` (server/internal/db/query/competitor_profiles.sql:3)
  - `DeleteCompetitorProfile` (server/internal/db/query/competitor_profiles.sql:29)
  - `GetCompetitorAnalytics` (server/internal/db/query/competitor_posts.sql:98)
  - `GetCompetitorByPlatformUsername` (server/internal/db/query/account.sql:328)
  - `GetCompetitorHandles` (server/internal/db/query/analytics.sql:161)
  - `GetCompetitorProfileByID` (server/internal/db/query/competitor_profiles.sql:8)
  - `GetGroupCompetitors` (server/internal/db/query/account.sql:168)
  - `GetProfileByCompetitorAndPlatform` (server/internal/db/query/competitor_profiles.sql:33)
  - `GetProfileStats` (server/internal/db/query/competitor_profiles.sql:68)
  - `GetRecentCompetitorPosts` (server/internal/db/query/competitor_posts.sql:78)
  - `GetTimeBoxedCompetitorInsights` (server/internal/db/query/analytics.sql:4)
  - `GetTopCompetitorHooks` (server/internal/db/query/analytics.sql:66)
  - `ListGroupCompetitors` (server/internal/db/query/account.sql:298)
  - `ListProfilesByCompetitor` (server/internal/db/query/competitor_profiles.sql:12)
  - `ListUserCompetitors` (server/internal/db/query/account.sql:279)
  - `SearchCompetitorPosts` (server/internal/db/query/competitor_posts.sql:44)
  - `UpdateCompetitorProfile` (server/internal/db/query/competitor_profiles.sql:17)
- **competitors**:
  - `CreateCompetitor` (server/internal/db/query/account.sql:163)
  - `CreateCompetitorEntity` (server/internal/db/query/competitor_profiles.sql:53)
  - `DeleteCompetitor` (server/internal/db/query/competitor_profiles.sql:64)
  - `GetBestPostingDay` (server/internal/db/query/analytics.sql:105)
  - `GetBestPostingHour` (server/internal/db/query/analytics.sql:39)
  - `GetCompetitorAnalytics` (server/internal/db/query/competitor_posts.sql:98)
  - `GetCompetitorByPlatformUsername` (server/internal/db/query/account.sql:328)
  - `GetCompetitorCount` (server/internal/db/query/analytics.sql:170)
  - `GetCompetitorHandles` (server/internal/db/query/analytics.sql:161)
  - `GetCompetitorPostCount14Days` (server/internal/db/query/analytics.sql:95)
  - `GetCompetitorWithAllProfiles` (server/internal/db/query/competitor_profiles.sql:48)
  - `GetGroupCompetitors` (server/internal/db/query/account.sql:168)
  - `GetPostingFrequency28Days` (server/internal/db/query/analytics.sql:130)
  - `GetRecentCompetitorPosts` (server/internal/db/query/competitor_posts.sql:78)
  - `GetTimeBoxedCompetitorInsights` (server/internal/db/query/analytics.sql:4)
  - `GetTopCompetitorHashtags` (server/internal/db/query/analytics.sql:142)
  - `GetTopCompetitorHooks` (server/internal/db/query/analytics.sql:66)
  - `ListAvailableCompetitorsToUser` (server/internal/db/query/account.sql:317)
  - `ListCompetitorsWithProfiles` (server/internal/db/query/competitor_profiles.sql:37)
  - `ListGroupCompetitors` (server/internal/db/query/account.sql:298)
  - `ListUserCompetitors` (server/internal/db/query/account.sql:279)
  - `SearchCompetitorPosts` (server/internal/db/query/competitor_posts.sql:44)
  - `UpdateCompetitorDisplayName` (server/internal/db/query/competitor_profiles.sql:58)
- **daily_followers**:
  - `GetFollowerByDate` (server/internal/db/query/account.sql:266)
  - `InsertFollowerCount` (server/internal/db/query/account.sql:257)
- **document_ingest_jobs**:
  - `EnqueueIngestJob` (server/internal/db/query/workshop.sql:7)
- **game_contexts**:
  - `CreateGameContext` (server/internal/db/query/account.sql:338)
  - `GetGameContext` (server/internal/db/query/workshop.sql:74)
  - `GetGameContextByGroupID` (server/internal/db/query/account.sql:357)
  - `GetGameContextByUserID` (server/internal/db/query/account.sql:363)
  - `ListGameContextsByUser` (server/internal/db/query/account.sql:369)
- **group_items**:
  - `GetGroupItemByGroupID` (server/internal/db/query/account.sql:136)
  - `InsertGroupItemIfNotExists` (server/internal/db/query/account.sql:130)
  - `UpdateGroupItemData` (server/internal/db/query/account.sql:333)
- **groups**:
  - `CreateGroup` (server/internal/db/query/account.sql:146)
  - `GetGroupByID` (server/internal/db/query/account.sql:141)
  - `ListGroupsByUser` (server/internal/db/query/account.sql:151)
- **post_drafts**:
  - `BulkCreateDraft` (server/internal/db/query/campaigns.sql:105)
  - `CreatePostDraft` (server/internal/db/query/campaigns.sql:69)
  - `GetPostDraftByID` (server/internal/db/query/campaigns.sql:85)
  - `GetTopHookPatterns` (server/internal/db/query/campaigns.sql:180)
  - `ListDraftsByCampaign` (server/internal/db/query/campaigns.sql:88)
  - `ListDraftsByStatus` (server/internal/db/query/campaigns.sql:93)
  - `UpdateDraftSchedule` (server/internal/db/query/campaigns.sql:101)
  - `UpdateDraftStatus` (server/internal/db/query/campaigns.sql:98)
- **post_metrics**:
  - `GetBestPostingWindows` (server/internal/db/query/campaigns.sql:165)
  - `GetMetricsSummary` (server/internal/db/query/campaigns.sql:150)
  - `GetTopHookPatterns` (server/internal/db/query/campaigns.sql:180)
  - `InsertPostMetrics` (server/internal/db/query/campaigns.sql:129)
  - `ListMetricsByDraft` (server/internal/db/query/campaigns.sql:144)
  - `ListMetricsByGroup` (server/internal/db/query/campaigns.sql:139)
- **sessions**:
  - `CreateSession` (server/internal/db/query/account.sql:66)
  - `DeleteSession` (server/internal/db/query/account.sql:78)
  - `GetSession` (server/internal/db/query/account.sql:72)
- **socialmedia_data**:
  - `CreateSocialMediaData` (server/internal/db/query/account.sql:206)
  - `DeleteSocialMediaData` (server/internal/db/query/account.sql:246)
  - `ListSocialMediaDataByGroup` (server/internal/db/query/account.sql:225)
  - `UpdateSocialMediaData` (server/internal/db/query/account.sql:238)
- **upload_jobs**:
  - `CreateUploadJob` (server/internal/db/query/account.sql:81)
  - `FetchNextPendingJob` (server/internal/db/query/account.sql:187)
  - `GetUploadJob` (server/internal/db/query/account.sql:104)
  - `GetUploadJobByGID` (server/internal/db/query/account.sql:199)
  - `ListUserUploadJobs` (server/internal/db/query/account.sql:124)
  - `UpdateUploadJobFileURL` (server/internal/db/query/account.sql:117)
  - `UpdateUploadJobStatus` (server/internal/db/query/account.sql:110)
- **user_competitors**:
  - `GetBestPostingDay` (server/internal/db/query/analytics.sql:105)
  - `GetBestPostingHour` (server/internal/db/query/analytics.sql:39)
  - `GetCompetitorAnalytics` (server/internal/db/query/competitor_posts.sql:98)
  - `GetCompetitorCount` (server/internal/db/query/analytics.sql:170)
  - `GetCompetitorHandles` (server/internal/db/query/analytics.sql:161)
  - `GetCompetitorPostCount14Days` (server/internal/db/query/analytics.sql:95)
  - `GetGroupCompetitors` (server/internal/db/query/account.sql:168)
  - `GetPostingFrequency28Days` (server/internal/db/query/analytics.sql:130)
  - `GetRecentCompetitorPosts` (server/internal/db/query/competitor_posts.sql:78)
  - `GetTimeBoxedCompetitorInsights` (server/internal/db/query/analytics.sql:4)
  - `GetTopCompetitorHashtags` (server/internal/db/query/analytics.sql:142)
  - `GetTopCompetitorHooks` (server/internal/db/query/analytics.sql:66)
  - `LinkUserToCompetitor` (server/internal/db/query/account.sql:274)
  - `ListAvailableCompetitorsToUser` (server/internal/db/query/account.sql:317)
  - `ListCompetitorsWithProfiles` (server/internal/db/query/competitor_profiles.sql:37)
  - `ListGroupCompetitors` (server/internal/db/query/account.sql:298)
  - `ListUserCompetitors` (server/internal/db/query/account.sql:279)
  - `ListVisibleCompetitorPosts` (server/internal/db/query/ListVisibleCompetitorPosts.sql:1)
  - `SearchCompetitorPosts` (server/internal/db/query/competitor_posts.sql:44)
- **users**:
  - `CheckEmailExists` (server/internal/db/query/account.sql:60)
  - `CheckUsernameOrEmailExists` (server/internal/db/query/account.sql:54)
  - `CreateOAuthUser` (server/internal/db/query/account.sql:8)
  - `CreateUserWithPassword` (server/internal/db/query/account.sql:2)
  - `DeleteUser` (server/internal/db/query/account.sql:49)
  - `GetOAuthUserByEmail` (server/internal/db/query/account.sql:28)
  - `GetUserByEmailWithPassword` (server/internal/db/query/account.sql:22)
  - `GetUserByID` (server/internal/db/query/account.sql:16)
  - `GetUserIDByUsernameEmail` (server/internal/db/query/account.sql:251)
  - `ListUsers` (server/internal/db/query/account.sql:34)
  - `UpdateUser` (server/internal/db/query/account.sql:40)
- **workshop_chunks**:
  - `FuzzyChunks` (server/internal/db/query/workshop.sql:11)
  - `GetDefaultChunks` (server/internal/db/query/workshop.sql:59)
  - `SearchChunks` (server/internal/db/query/workshop.sql:32)
- **workshop_documents**:
  - `CreateWorkshopDocument` (server/internal/db/query/workshop.sql:1)
  - `FuzzyChunks` (server/internal/db/query/workshop.sql:11)
  - `GetDefaultChunks` (server/internal/db/query/workshop.sql:59)
  - `SearchChunks` (server/internal/db/query/workshop.sql:32)

### 5.2 Go sqlc calls in handlers (file:line)

#### `server/internal/handlers/ai_generator.go`
- `q.GetGameContext(...)` at `server/internal/handlers/ai_generator.go:92`
- `q.GetPostingFrequency28Days(...)` at `server/internal/handlers/ai_generator.go:386`
- `q.GetBestPostingDay(...)` at `server/internal/handlers/ai_generator.go:410`
- `q.GetTopCompetitorHooks(...)` at `server/internal/handlers/ai_generator.go:423`
- `q.GetTopCompetitorHooks(...)` at `server/internal/handlers/ai_generator.go:441`
- `q.GetTopCompetitorHashtags(...)` at `server/internal/handlers/ai_generator.go:462`
- `q.SearchChunks(...)` at `server/internal/handlers/ai_generator.go:781`

#### `server/internal/handlers/campaigns.go`
- `q.CreateCampaign(...)` at `server/internal/handlers/campaigns.go`
- `q.GetCampaignByID(...)` at `server/internal/handlers/campaigns.go`
- `q.ListCampaignsByUser(...)` at `server/internal/handlers/campaigns.go`
- `q.ListCampaignsByGroup(...)` at `server/internal/handlers/campaigns.go`
- `q.CreateCampaignAsset(...)` at `server/internal/handlers/campaigns.go`
- `q.ListCampaignAssets(...)` at `server/internal/handlers/campaigns.go`
- `q.CreatePostDraft(...)` at `server/internal/handlers/campaigns.go`
- `q.ListDraftsByCampaign(...)` at `server/internal/handlers/campaigns.go`
- `q.InsertPostMetrics(...)` at `server/internal/handlers/campaigns.go`
- `q.GetMetricsSummary(...)` at `server/internal/handlers/campaigns.go`
- `q.GetBestPostingWindows(...)` at `server/internal/handlers/campaigns.go`
- `q.GetTopHookPatterns(...)` at `server/internal/handlers/campaigns.go`

#### `server/internal/handlers/competitor.go`
- `queries.GetCompetitorByPlatformUsername(...)` at `server/internal/handlers/competitor.go:53`
- `queries.GetProfileByCompetitorAndPlatform(...)` at `server/internal/handlers/competitor.go:60`
- `queries.CreateCompetitor(...)` at `server/internal/handlers/competitor.go:69`
- `queries.CreateCompetitorProfile(...)` at `server/internal/handlers/competitor.go:78`
- `queries.LinkUserToCompetitor(...)` at `server/internal/handlers/competitor.go:107`

#### `server/internal/handlers/competitor_list.go`
- `queries.ListUserCompetitors(...)` at `server/internal/handlers/competitor_list.go:21`

#### `server/internal/handlers/competitor_posts.go`
- `queries.ListVisibleCompetitorPosts(...)` at `server/internal/handlers/competitor_posts.go:37`

#### `server/internal/handlers/competitors_with_profiles.go`
- `queries.ListCompetitorsWithProfiles(...)` at `server/internal/handlers/competitors_with_profiles.go:47`
- `queries.GetProfileStats(...)` at `server/internal/handlers/competitors_with_profiles.go:57`

#### `server/internal/handlers/game_context.go`
- `queries.CreateGameContext(...)` at `server/internal/handlers/game_context.go:155`

#### `server/internal/handlers/game_contextOLLAMA.go`
- `queries.CreateGameContext(...)` at `server/internal/handlers/game_contextOLLAMA.go:132`

#### `server/internal/handlers/group.go`
- `queries.CreateGroup(...)` at `server/internal/handlers/group.go:38`
- `q.ListGroupsByUser(...)` at `server/internal/handlers/group.go:74`
- `q.InsertGroupItemIfNotExists(...)` at `server/internal/handlers/group.go:123`
- `q.UpdateGroupItemData(...)` at `server/internal/handlers/group.go:137`
- `q.GetGroupItemByGroupID(...)` at `server/internal/handlers/group.go:159`

#### `server/internal/handlers/upload.go`
- `queries.CreateUploadJob(...)` at `server/internal/handlers/upload.go:113`
- `q.GetUploadJobByGID(...)` at `server/internal/handlers/upload.go:170`

#### `server/internal/handlers/users.go`
- `q.GetUserIDByUsernameEmail(...)` at `server/internal/handlers/users.go:54`

#### `server/internal/handlers/workshop_ask.go`
- `q.SearchChunks(...)` at `server/internal/handlers/workshop_ask.go:136`
- `q.SearchChunks(...)` at `server/internal/handlers/workshop_ask.go:152`
- `q.FuzzyChunks(...)` at `server/internal/handlers/workshop_ask.go:166`
- `q.GetDefaultChunks(...)` at `server/internal/handlers/workshop_ask.go:187`
- `q.SearchCompetitorPosts(...)` at `server/internal/handlers/workshop_ask.go:218`
- `q.ListUserCompetitors(...)` at `server/internal/handlers/workshop_ask.go:240`
- `q.ListVisibleCompetitorPosts(...)` at `server/internal/handlers/workshop_ask.go:256`
- `q.GetRecentCompetitorPosts(...)` at `server/internal/handlers/workshop_ask.go:294`
- `q.GetGameContext(...)` at `server/internal/handlers/workshop_ask.go:329`
- `q.GetCompetitorAnalytics(...)` at `server/internal/handlers/workshop_ask.go:487`
- `q.GetRecentCompetitorPosts(...)` at `server/internal/handlers/workshop_ask.go:516`

#### `server/internal/handlers/workshop_search.go`
- `q.SearchChunks(...)` at `server/internal/handlers/workshop_search.go:60`
- `q.FuzzyChunks(...)` at `server/internal/handlers/workshop_search.go:93`

#### `server/internal/handlers/workshop_upload.go`
- `q.CreateWorkshopDocument(...)` at `server/internal/handlers/workshop_upload.go:107`
- `q.EnqueueIngestJob(...)` at `server/internal/handlers/workshop_upload.go:124`

## 6) Campaign Workflow Feature (NEW)

### 6.1 Overview
The campaigns feature provides structured marketing automation with:
- Wizard-based campaign creation with preset audience archetypes
- AI-generated post drafts with structured JSON output
- Asset management for campaign media
- Performance metrics tracking with feedback loop
- Insights generation for optimization

### 6.2 Database Tables (Migration 000002)
| Table | Purpose |
|---|---|
| `campaigns` | Stores wizard-created campaign configurations (goal, audience, pillars, cadence) |
| `campaign_assets` | Uploaded media files with tags |
| `post_drafts` | AI-generated structured content (hook, caption, hashtags, CTA, time_window) |
| `post_metrics` | Performance snapshots for feedback loop |

### 6.3 API Endpoints
| METHOD | PATH | Handler | Purpose |
|---|---|---|---|
| GET | `/api/campaigns/wizard` | `GetWizardOptionsHandler` | Fetch preset wizard options (archetypes, goals, pillars) |
| POST | `/api/campaigns` | `CreateCampaignHandler` | Create new campaign from wizard |
| GET | `/api/campaigns` | `ListCampaignsHandler` | List user's campaigns |
| GET | `/api/campaigns/:id` | `GetCampaignHandler` | Get single campaign details |
| POST | `/api/campaigns/:id/assets` | `AttachCampaignAssetsHandler` | Upload campaign media assets |
| POST | `/api/campaigns/:id/generate` | `GenerateCampaignDraftsHandler` | Trigger AI draft generation |
| GET | `/api/campaigns/:id/drafts` | `ListCampaignDraftsHandler` | List generated drafts |
| GET | `/api/campaigns/:id/insights` | `GetCampaignInsightsHandler` | Get performance insights |
| POST | `/api/metrics/ingest` | `IngestMetricsHandler` | Store performance snapshots |

### 6.4 Frontend Pages
- `client/src/app/campaigns/page.tsx` - Main campaign management page
- `client/src/app/campaigns/insights/page.tsx` - Campaign insights/analytics page