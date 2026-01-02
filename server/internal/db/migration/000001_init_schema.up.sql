CREATE EXTENSION IF NOT EXISTS pgcrypto;      -- for gen_random_uuid() and digest()
CREATE EXTENSION IF NOT EXISTS pg_trgm;       -- for gin_trgm_ops
CREATE EXTENSION IF NOT EXISTS vector;        -- for vector type
CREATE EXTENSION IF NOT EXISTS citext;

CREATE TABLE "users" (
  "id" SERIAL PRIMARY KEY,
  "username" VARCHAR(255) UNIQUE NOT NULL,
  "email" VARCHAR(255) UNIQUE NOT NULL,
  "password_hash" VARCHAR(255) NOT NULL,
  "oauth_provider" VARCHAR(50),
  "oauth_id" VARCHAR(255),
  "created_at" TIMESTAMP DEFAULT NOW(),
  "updated_at" TIMESTAMP DEFAULT NOW()
);

CREATE TABLE "groups" (
  "id" SERIAL PRIMARY KEY,
  "user_id" INT NOT NULL,
  "name" VARCHAR(255) NOT NULL,
  "description" TEXT,
  "created_at" TIMESTAMP DEFAULT NOW(),
  "updated_at" TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE CASCADE
);

CREATE TABLE "group_items" (
  "id" SERIAL PRIMARY KEY,
  "group_id" INT NOT NULL,
  "platform" VARCHAR(50) NOT NULL, 
  "data" JSONB NOT NULL DEFAULT '{}'::jsonb,
  "created_at" TIMESTAMP DEFAULT NOW(),
  "updated_at" TIMESTAMP DEFAULT NOW(),
  "cookie_created_at" TIMESTAMP,
  FOREIGN KEY ("group_id") REFERENCES "groups" ("id") ON DELETE CASCADE
);
ALTER TABLE group_items
ADD CONSTRAINT unique_group_platform UNIQUE (group_id, platform);

CREATE TABLE competitors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  platform VARCHAR(50) NOT NULL,
  username VARCHAR(100) NOT NULL,
  profile_url TEXT NOT NULL,
  last_checked TIMESTAMP DEFAULT NOW(),
  followers BIGINT DEFAULT 0,
  engagement_rate NUMERIC(4,2) DEFAULT 0.0,
  growth_rate NUMERIC(4,2) DEFAULT 0.0,
  posting_frequency NUMERIC(5,2) DEFAULT 0.0,
  total_posts BIGINT DEFAULT 0,
  UNIQUE (platform, username)
);

CREATE TABLE competitor_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  competitor_id UUID REFERENCES competitors(id) ON DELETE CASCADE,
  followers BIGINT,
  engagement_rate NUMERIC(5,2),
  snapshot_date DATE DEFAULT CURRENT_DATE,
  UNIQUE (competitor_id, snapshot_date)
);

CREATE TABLE user_competitors (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  group_id INT, -- optional
  competitor_id UUID NOT NULL REFERENCES competitors(id) ON DELETE CASCADE,
  visibility VARCHAR(10) NOT NULL DEFAULT 'group', -- 'global', 'user', or 'group'
  added_at TIMESTAMP DEFAULT NOW(),
  UNIQUE (user_id, competitor_id, group_id)
);


CREATE TABLE "posts" (
  "id" SERIAL PRIMARY KEY,
  "group_id" INT NOT NULL,
  "title" VARCHAR(255) NOT NULL,
  "social_media_link" VARCHAR(255) NOT NULL,
  "created_at" TIMESTAMP DEFAULT NOW(),
  "updated_at" TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY ("group_id") REFERENCES "groups" ("id") ON DELETE CASCADE
);

CREATE TABLE "sessions" (
  "id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  "user_id" INT NOT NULL,
  "created_at" TIMESTAMP DEFAULT NOW(),
  "expires_at" TIMESTAMP NOT NULL,
  FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE CASCADE
);

CREATE TABLE "upload_jobs" (
  "id" TEXT PRIMARY KEY,
  "user_id" INT NOT NULL,
  "group_id" INT,  -- Nullable, but can be linked to groups table
  "platform" VARCHAR(50) NOT NULL,  -- e.g., 'tiktok', 'youtube'
  "video_path" TEXT NOT NULL,
  "storage_type" VARCHAR(50) NOT NULL DEFAULT 'local',
  "file_url" TEXT DEFAULT '',
  "status" TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'uploading', 'done', 'failed')),
  "caption" TEXT DEFAULT '',
  "user_title" TEXT DEFAULT '',
  "user_hashtags" TEXT[] DEFAULT '{}',
  "ai_title" TEXT DEFAULT '',
  "ai_hashtags" TEXT[] DEFAULT '{}',
  "ai_post_time" TIMESTAMP,
  "created_at" TIMESTAMP DEFAULT NOW(),
  "updated_at" TIMESTAMP DEFAULT NOW(),
  "scheduled_date" date DEFAULT NOW(),

  FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE CASCADE,
  FOREIGN KEY ("group_id") REFERENCES "groups" ("id") ON DELETE SET NULL
);



CREATE TABLE competitor_posts (
  id SERIAL PRIMARY KEY,
  competitor_id UUID REFERENCES competitors(id) ON DELETE CASCADE,
  username TEXT,
  platform VARCHAR(50) NOT NULL,
  post_id VARCHAR(100) NOT NULL,
  content TEXT,
  media JSONB DEFAULT '{}'::jsonb,
  posted_at TIMESTAMP,
  engagement JSONB DEFAULT '{}'::jsonb,
  hashtags TEXT[] DEFAULT '{}',
  scraped_at TIMESTAMP DEFAULT NOW(),
  caption_hash TEXT,
  UNIQUE (platform, post_id)
);

CREATE TABLE hashtag_posts (
  id SERIAL PRIMARY KEY,
  hashtag TEXT NOT NULL,
  platform VARCHAR(50) NOT NULL,
  post_id VARCHAR(100) NOT NULL,
  username TEXT,
  content TEXT,
  media JSONB DEFAULT '{}'::jsonb,
  posted_at TIMESTAMP,
  likes BIGINT DEFAULT 0,
  comments_count BIGINT DEFAULT 0,
  hashtags TEXT[] DEFAULT '{}',
  scraped_at TIMESTAMP DEFAULT NOW(),
  caption_hash TEXT,
  UNIQUE (platform, post_id)
);

CREATE INDEX IF NOT EXISTS idx_hashtag_posts_hashtag ON hashtag_posts(hashtag);
CREATE INDEX IF NOT EXISTS idx_hashtag_posts_posted_at ON hashtag_posts(posted_at);
CREATE INDEX IF NOT EXISTS idx_hashtag_posts_platform ON hashtag_posts(platform);
CREATE INDEX IF NOT EXISTS idx_hashtag_posts_username ON hashtag_posts(username);


--socialmeiad data, id PK, groupsid FK, type, data, created, upadted
CREATE TABLE socialmedia_data (
  id SERIAL PRIMARY KEY,
  group_id   INT NOT NULL
    REFERENCES groups(id)
    ON DELETE CASCADE,
  platform   VARCHAR(50)   NOT NULL,    -- e.g. 'twitter', 'instagram'
  type       VARCHAR(50)   NOT NULL,    -- e.g. 'followers', 'posts', 'engagement'
  data       JSONB         NOT NULL,    -- any details you want to store
  created_at TIMESTAMP     NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP     NOT NULL DEFAULT NOW()
);


-- Daily followers table to track follower counts per day
CREATE TABLE daily_followers (
  id              SERIAL      PRIMARY KEY,
  record_date     DATE        NOT NULL DEFAULT CURRENT_DATE,
  follower_count  BIGINT      NOT NULL
);


-- ================= WORKSHOP / RAG =================
CREATE TABLE workshop_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  group_id INT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
  user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  filename TEXT NOT NULL,
  mime TEXT NOT NULL,
  size_bytes BIGINT NOT NULL,
  sha256 TEXT NOT NULL,
  version INT NOT NULL DEFAULT 1,
  pages INT,
  status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','processing','ready','error')),
  error TEXT,
  storage_url TEXT,                              -- ok to be NULL pre-upload
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now(),
  CONSTRAINT workshop_doc_user_group_sha_uniq UNIQUE (user_id, group_id, sha256),
  -- FIX: make sha length sane hex
  CONSTRAINT workshop_doc_sha256_ck CHECK (sha256 ~ '^[0-9a-f]{64}$')
);
-- Keep updated_at fresh
CREATE OR REPLACE FUNCTION touch_updated_at() RETURNS trigger AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END $$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS trg_touch_workshop_documents ON workshop_documents;
CREATE TRIGGER trg_touch_workshop_documents
BEFORE UPDATE ON workshop_documents FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

-- FIX: Either drop group_id from chunks OR enforce it matches the document.
-- Here we ENFORCE it via composite FK.
ALTER TABLE workshop_documents
  ADD CONSTRAINT workshop_documents_id_group_uniq UNIQUE (id, group_id);

CREATE TABLE workshop_chunks (
  id BIGSERIAL PRIMARY KEY,
  document_id UUID NOT NULL REFERENCES workshop_documents(id) ON DELETE CASCADE,
  group_id INT NOT NULL,
  page INT,
  chunk_index INT NOT NULL,
  content TEXT NOT NULL,
  token_count INT,
  tsv tsvector,                 -- maintained by trigger below
  content_sha TEXT
);

-- Enforce chunk group matches document group
ALTER TABLE workshop_chunks
  ADD CONSTRAINT workshop_chunks_doc_group_fk
  FOREIGN KEY (document_id, group_id)
  REFERENCES workshop_documents(id, group_id) ON DELETE CASCADE;

-- Dedupe guard
UPDATE workshop_chunks
SET content_sha = encode(digest(content, 'sha1'), 'hex')
WHERE content_sha IS NULL;
ALTER TABLE workshop_chunks
  ADD CONSTRAINT workshop_chunk_dedupe UNIQUE (document_id, chunk_index, content_sha);

-- Keep tsv up to date
CREATE OR REPLACE FUNCTION chunks_tsv_update() RETURNS trigger AS $$
BEGIN NEW.tsv := to_tsvector('english', COALESCE(NEW.content,'')); RETURN NEW; END $$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS trg_chunks_tsv ON workshop_chunks;
CREATE TRIGGER trg_chunks_tsv
BEFORE INSERT OR UPDATE OF content ON workshop_chunks
FOR EACH ROW EXECUTE FUNCTION chunks_tsv_update();

-- Indexes for retrieval
-- FIX: remove ivfflat index on workshop_chunks.embedding (column no longer exists)
-- CREATE INDEX ON workshop_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100); -- ❌ remove
CREATE INDEX IF NOT EXISTS workshop_chunks_trgm_idx ON workshop_chunks USING GIN (content gin_trgm_ops);
CREATE INDEX IF NOT EXISTS workshop_chunks_tsv_idx  ON workshop_chunks USING GIN (tsv);
CREATE INDEX IF NOT EXISTS workshop_chunks_doc_idx  ON workshop_chunks (document_id, chunk_index);

-- Embeddings decoupled
CREATE TABLE IF NOT EXISTS workshop_embeddings (
  chunk_id BIGINT PRIMARY KEY REFERENCES workshop_chunks(id) ON DELETE CASCADE,
  model TEXT NOT NULL,
  dims INT  NOT NULL,
  embedding vector(1024) NOT NULL
  -- FIX: enforce dims match vector size
  ,CONSTRAINT workshop_embeddings_dims_ck CHECK (dims = 1024)
);
CREATE INDEX IF NOT EXISTS workshop_embeddings_ivf
  ON workshop_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS workshop_embeddings_model_idx ON workshop_embeddings(model);

-- Ingest jobs
CREATE TABLE IF NOT EXISTS document_ingest_jobs (
  id BIGSERIAL PRIMARY KEY,
  document_id UUID NOT NULL REFERENCES workshop_documents(id) ON DELETE CASCADE,
  try_count INT NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','processing','done','error')),
  error TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
DROP TRIGGER IF EXISTS trg_touch_ingest_jobs ON document_ingest_jobs;
CREATE TRIGGER trg_touch_ingest_jobs
BEFORE UPDATE ON document_ingest_jobs FOR EACH ROW EXECUTE FUNCTION touch_updated_at();


CREATE TABLE IF NOT EXISTS game_contexts (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  group_id INT REFERENCES groups(id) ON DELETE CASCADE,

  -- Section 1: Basic Game Information
  game_title VARCHAR(255) NOT NULL,
  studio_name VARCHAR(255),
  game_summary TEXT,
  platforms TEXT[], -- ['PC', 'Console', 'Mobile', 'VR']
  engine_tech VARCHAR(255),

  -- Section 2: Core Identity
  primary_genre VARCHAR(100),
  subgenre VARCHAR(100),
  key_mechanics TEXT, -- comma-separated or JSON
  playtime_length VARCHAR(100), -- e.g., "short session", "mid-length campaign"
  art_style VARCHAR(100),
  tone VARCHAR(100),

  -- Section 3: Target Audience
  intended_audience TEXT,
  age_range VARCHAR(100),
  player_motivation TEXT,
  comparable_games TEXT, -- comma-separated game names

  -- Section 4: Marketing Goals
  marketing_objective VARCHAR(255), -- 'awareness', 'wishlist', 'demo', etc.
  key_events_dates TEXT, -- JSON or text describing events
  call_to_action VARCHAR(255),

  -- Section 5: Restrictions / Boundaries
  content_restrictions TEXT,
  competitors_to_avoid TEXT,
  additional_info TEXT,
  -- Metadata
  extraction_method VARCHAR(20) DEFAULT 'manual', -- 'manual' or 'ai_extracted'
  original_file_name VARCHAR(255),
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Index for faster queries by user and group
CREATE INDEX IF NOT EXISTS idx_game_contexts_user_id ON game_contexts(user_id);
CREATE INDEX IF NOT EXISTS idx_game_contexts_group_id ON game_contexts(group_id);

-- Step 1: Create the new competitor_profiles table
CREATE TABLE competitor_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  competitor_id UUID NOT NULL REFERENCES competitors(id) ON DELETE CASCADE,
  platform VARCHAR(50) NOT NULL,
  handle VARCHAR(255) NOT NULL,
  profile_url TEXT,
  followers BIGINT DEFAULT 0,
  engagement_rate NUMERIC(5,2) DEFAULT 0.0,
  growth_rate NUMERIC(5,2) DEFAULT 0.0,
  posting_frequency NUMERIC(5,2) DEFAULT 0.0,
  last_checked TIMESTAMP,
  UNIQUE (competitor_id, platform)
);

-- Step 2: Migrate existing data from competitors to competitor_profiles
INSERT INTO competitor_profiles (competitor_id, platform, handle, profile_url, followers, engagement_rate, growth_rate, posting_frequency, last_checked)
SELECT id, platform, username, profile_url, followers, engagement_rate, growth_rate, posting_frequency, last_checked
FROM competitors;

-- Step 3: Add display name column to competitors (the entity name)
ALTER TABLE competitors ADD COLUMN IF NOT EXISTS display_name VARCHAR(255);

-- Step 4: Set display_name from existing username before dropping
UPDATE competitors SET display_name = username;

-- Step 5: Drop old columns from competitors (now stored in profiles)
ALTER TABLE competitors DROP COLUMN IF EXISTS platform;
ALTER TABLE competitors DROP COLUMN IF EXISTS username;
ALTER TABLE competitors DROP COLUMN IF EXISTS profile_url;
ALTER TABLE competitors DROP COLUMN IF EXISTS followers;
ALTER TABLE competitors DROP COLUMN IF EXISTS engagement_rate;
ALTER TABLE competitors DROP COLUMN IF EXISTS growth_rate;
ALTER TABLE competitors DROP COLUMN IF EXISTS posting_frequency;

-- Step 6: Update competitor_posts to reference profiles instead
ALTER TABLE competitor_posts ADD COLUMN IF NOT EXISTS profile_id UUID REFERENCES competitor_profiles(id) ON DELETE CASCADE;

-- Step 7: Backfill profile_id in competitor_posts
UPDATE competitor_posts cp
SET profile_id = (
  SELECT cpr.id 
  FROM competitor_profiles cpr 
  WHERE cpr.competitor_id = cp.competitor_id 
    AND cpr.platform = cp.platform
  LIMIT 1
);

-- Step 8: Create index for faster profile lookups
CREATE INDEX IF NOT EXISTS idx_competitor_profiles_competitor_id ON competitor_profiles(competitor_id);
CREATE INDEX IF NOT EXISTS idx_competitor_posts_profile_id ON competitor_posts(profile_id);
-- 000002_campaigns.up.sql
-- Campaign workflow tables for structured marketing automation

-- Campaigns: stores wizard-created campaign configurations
CREATE TABLE campaigns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  group_id INT REFERENCES groups(id) ON DELETE SET NULL,
  name VARCHAR(255) NOT NULL,
  goal TEXT NOT NULL CHECK (goal IN ('wishlist', 'discord', 'demo', 'trailer', 'awareness', 'launch')),
  audience JSONB NOT NULL DEFAULT '{}'::jsonb,
  pillars JSONB NOT NULL DEFAULT '[]'::jsonb,
  cadence JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'paused', 'completed')),
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_campaigns_user_id ON campaigns(user_id);
CREATE INDEX idx_campaigns_group_id ON campaigns(group_id);
CREATE INDEX idx_campaigns_status ON campaigns(status);

-- Campaign assets: uploaded media with tags
CREATE TABLE campaign_assets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  storage_url TEXT NOT NULL,
  filename TEXT NOT NULL,
  mime_type TEXT,
  size_bytes BIGINT,
  tags JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_campaign_assets_campaign_id ON campaign_assets(campaign_id);

-- Post drafts: AI-generated structured content
CREATE TABLE post_drafts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  platform TEXT NOT NULL,
  post_type TEXT NOT NULL DEFAULT 'standard',
  hook TEXT,
  caption TEXT,
  hashtags TEXT[] DEFAULT '{}',
  cta TEXT,
  time_window JSONB,
  reason_codes TEXT[] DEFAULT '{}',
  confidence NUMERIC(4,2) DEFAULT 0.0,
  status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'scheduled', 'posted', 'rejected')),
  scheduled_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_post_drafts_campaign_id ON post_drafts(campaign_id);
CREATE INDEX idx_post_drafts_status ON post_drafts(status);
CREATE INDEX idx_post_drafts_platform ON post_drafts(platform);

-- Post metrics: performance snapshots for feedback loop
CREATE TABLE post_metrics (
  id BIGSERIAL PRIMARY KEY,
  group_id INT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
  platform TEXT NOT NULL,
  post_id TEXT NOT NULL,
  draft_id UUID REFERENCES post_drafts(id) ON DELETE SET NULL,
  captured_at TIMESTAMP NOT NULL DEFAULT NOW(),
  metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (group_id, platform, post_id, captured_at)
);

CREATE INDEX idx_post_metrics_group_id ON post_metrics(group_id);
CREATE INDEX idx_post_metrics_draft_id ON post_metrics(draft_id);
CREATE INDEX idx_post_metrics_captured_at ON post_metrics(captured_at);

-- Trigger to update updated_at on campaigns
DROP TRIGGER IF EXISTS trg_touch_campaigns ON campaigns;
CREATE TRIGGER trg_touch_campaigns
BEFORE UPDATE ON campaigns FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

-- Trigger to update updated_at on post_drafts
DROP TRIGGER IF EXISTS trg_touch_post_drafts ON post_drafts;
CREATE TRIGGER trg_touch_post_drafts
BEFORE UPDATE ON post_drafts FOR EACH ROW EXECUTE FUNCTION touch_updated_at();




-- Reddit Listener Pipeline
-- Migration: 000003_reddit_listener.up.sql
-- Creates tables for Reddit ingestion: sources, items (posts), comments, chunks, cards, alerts

-- ═══════════════════════════════════════════════════════════════════════════════
-- reddit_sources: Configured subreddit/keyword sources to monitor
-- Enforcing lowercase value/subreddit to avoid case duplicates
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE reddit_sources (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  group_id INT REFERENCES groups(id) ON DELETE SET NULL,
  type VARCHAR(20) NOT NULL CHECK (type IN ('subreddit', 'keyword')),
  value TEXT NOT NULL CHECK (value = LOWER(value)),       -- Enforce lowercase
  subreddit TEXT CHECK (subreddit IS NULL OR subreddit = LOWER(subreddit)), -- Enforce lowercase if set
  enabled BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  
  -- Prevent empty string for subreddit, force NULL instead
  CONSTRAINT chk_subreddit_not_empty CHECK (subreddit IS NULL OR LENGTH(subreddit) > 0)
);

-- Partial unique indexes to correctly handle NULL group_id
-- When group_id IS NULL: unique on (user_id, type, value, subreddit)
CREATE UNIQUE INDEX idx_reddit_sources_unique_no_group 
  ON reddit_sources(user_id, type, value, COALESCE(subreddit, ''))
  WHERE group_id IS NULL;

-- When group_id IS NOT NULL: unique on (user_id, group_id, type, value, subreddit)
CREATE UNIQUE INDEX idx_reddit_sources_unique_with_group 
  ON reddit_sources(user_id, group_id, type, value, COALESCE(subreddit, ''))
  WHERE group_id IS NOT NULL;

CREATE INDEX idx_reddit_sources_user ON reddit_sources(user_id);
CREATE INDEX idx_reddit_sources_enabled ON reddit_sources(enabled) WHERE enabled = TRUE;

-- ═══════════════════════════════════════════════════════════════════════════════
-- reddit_items: Reddit POSTS only (no comments stored here)
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE reddit_items (
  id SERIAL PRIMARY KEY,
  source_id INT NOT NULL REFERENCES reddit_sources(id) ON DELETE CASCADE,
  platform VARCHAR(20) DEFAULT 'reddit',
  subreddit TEXT NOT NULL,
  external_id TEXT NOT NULL,              -- Reddit's thing ID (e.g., t3_abc123)
  external_url TEXT NOT NULL,             -- Permalink for provenance
  title TEXT,
  body TEXT,                              -- selftext
  author TEXT,
  author_flair TEXT,
  score INT DEFAULT 0,
  num_comments INT DEFAULT 0,
  created_utc TIMESTAMPTZ NOT NULL,
  fetched_at TIMESTAMPTZ DEFAULT NOW(),
  quality_score FLOAT DEFAULT 0.0,
  nsfw BOOLEAN DEFAULT FALSE,
  removed BOOLEAN DEFAULT FALSE,
  raw_json JSONB,                         -- Pruned JSON kept valid
  UNIQUE (platform, external_id)
);

CREATE INDEX idx_reddit_items_source_created ON reddit_items(source_id, created_utc DESC);
CREATE INDEX idx_reddit_items_source_quality ON reddit_items(source_id, quality_score DESC);
CREATE INDEX idx_reddit_items_subreddit ON reddit_items(subreddit);

-- ═══════════════════════════════════════════════════════════════════════════════
-- reddit_comments: Comments on Reddit posts
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE reddit_comments (
  id SERIAL PRIMARY KEY,
  item_id INT NOT NULL REFERENCES reddit_items(id) ON DELETE CASCADE,
  external_id TEXT NOT NULL,              -- Reddit comment ID (e.g., t1_xyz789)
  parent_external_id TEXT,                -- Parent comment ID or post ID
  body TEXT,
  author TEXT,
  author_flair TEXT,
  score INT DEFAULT 0,
  created_utc TIMESTAMPTZ NOT NULL,
  fetched_at TIMESTAMPTZ DEFAULT NOW(),
  removed BOOLEAN DEFAULT FALSE,
  raw_json JSONB,                         -- Pruned JSON kept valid
  UNIQUE (item_id, external_id)
);

CREATE INDEX idx_reddit_comments_item_score ON reddit_comments(item_id, score DESC);
CREATE INDEX idx_reddit_comments_item_created ON reddit_comments(item_id, created_utc DESC);

-- ═══════════════════════════════════════════════════════════════════════════════
-- reddit_chunks: RAG-ready text chunks
-- comment_id uses ON DELETE SET NULL to prevent cascade surprises
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE reddit_chunks (
  id SERIAL PRIMARY KEY,
  item_id INT NOT NULL REFERENCES reddit_items(id) ON DELETE CASCADE,
  comment_id INT REFERENCES reddit_comments(id) ON DELETE SET NULL,
  chunk_text TEXT NOT NULL,
  chunk_hash VARCHAR(64) NOT NULL,        -- SHA256 hex
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (chunk_hash)
);

CREATE INDEX idx_reddit_chunks_item ON reddit_chunks(item_id);

-- ═══════════════════════════════════════════════════════════════════════════════
-- strategy_cards: Extracted marketing tactics from Reddit content
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE strategy_cards (
  id SERIAL PRIMARY KEY,
  source VARCHAR(20) DEFAULT 'reddit',
  item_id INT REFERENCES reddit_items(id) ON DELETE CASCADE,
  comment_id INT REFERENCES reddit_comments(id) ON DELETE SET NULL,
  platform_targets TEXT[],                -- e.g., ['tiktok', 'instagram']
  niche TEXT,                             -- e.g., 'indie games' or 'general'
  tactic TEXT,                            -- Short statement of the tactic
  steps JSONB,                            -- [{"step":1,"action":"..."}]
  preconditions JSONB,                    -- {"needs_high_posting_frequency": true}
  metrics JSONB,                          -- {"primary":"watch_time","secondary":["shares"]}
  risks JSONB,                            -- ["shadowban risk", ...]
  confidence FLOAT DEFAULT 0.0,           -- 0..1
  evidence JSONB,                         -- {"quote_snippets":[], "permalink":"..."}
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_strategy_cards_item ON strategy_cards(item_id);
CREATE INDEX idx_strategy_cards_created ON strategy_cards(created_at DESC);

-- ═══════════════════════════════════════════════════════════════════════════════
-- listener_state: Track last fetch position per source
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE listener_state (
  id SERIAL PRIMARY KEY,
  source_id INT NOT NULL REFERENCES reddit_sources(id) ON DELETE CASCADE,
  last_seen_created_utc TIMESTAMPTZ,
  last_run_at TIMESTAMPTZ,
  UNIQUE (source_id)
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- reddit_alerts: Spike detection alerts ("ears on what's going on")
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE reddit_alerts (
  id SERIAL PRIMARY KEY,
  source_id INT NOT NULL REFERENCES reddit_sources(id) ON DELETE CASCADE,
  window_start TIMESTAMPTZ NOT NULL,
  window_end TIMESTAMPTZ NOT NULL,
  metric VARCHAR(50) NOT NULL,            -- e.g., 'item_volume_24h'
  current_value FLOAT NOT NULL,
  previous_value FLOAT NOT NULL,
  factor FLOAT NOT NULL,                  -- current/previous ratio
  top_item_ids JSONB,                     -- [external_id1, external_id2, ...]
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_reddit_alerts_source_created ON reddit_alerts(source_id, created_at DESC);
-- Migration: Upload Automation
-- Adds columns for automated content posting pipeline with state machine, retry handling, and job locking

-- Add AI hook for generated opening lines
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS ai_hook TEXT;

-- Retry tracking
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS retry_count INT DEFAULT 0;
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS max_retries INT DEFAULT 3;
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS error_message TEXT;
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS error_at TIMESTAMP WITH TIME ZONE;

-- Post tracking (result after successful upload)
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS posted_url TEXT;
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS platform_post_id TEXT;

-- Worker locking (for atomic job claiming)
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS locked_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS locked_by TEXT;

-- Enforce valid status values via CHECK constraint
-- Note: Using DO block to handle case where constraint already exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'valid_upload_status'
    ) THEN
        ALTER TABLE upload_jobs ADD CONSTRAINT valid_upload_status CHECK (
            status IN (
                'queued',
                'generating',
                'needs_review',
                'scheduled',
                'posting',
                'posted',
                'failed',
                'canceled',
                'needs_reauth'
            )
        );
    END IF;
END $$;

-- Index for scheduler polling (scheduled jobs ready to post)
CREATE INDEX IF NOT EXISTS idx_upload_jobs_scheduled_ready 
ON upload_jobs (scheduled_date) 
WHERE status = 'scheduled';

-- Index for queued jobs awaiting AI generation
CREATE INDEX IF NOT EXISTS idx_upload_jobs_queued 
ON upload_jobs (created_at) 
WHERE status = 'queued';

-- Index for failed jobs (for retry monitoring)
CREATE INDEX IF NOT EXISTS idx_upload_jobs_failed 
ON upload_jobs (error_at) 
WHERE status = 'failed';
-- Migration 000005: Fix upload_jobs state machine
-- Fixes time types, status constraints, and backfills legacy statuses

-- A) Fix time types: DATE -> TIMESTAMPTZ for scheduled_date
ALTER TABLE upload_jobs 
ALTER COLUMN scheduled_date TYPE TIMESTAMPTZ 
USING CASE 
    WHEN scheduled_date IS NULL THEN NULL
    ELSE (scheduled_date::timestamp AT TIME ZONE 'UTC')
END;

-- Fix time types: TIMESTAMP -> TIMESTAMPTZ for ai_post_time
ALTER TABLE upload_jobs 
ALTER COLUMN ai_post_time TYPE TIMESTAMPTZ 
USING CASE 
    WHEN ai_post_time IS NULL THEN NULL
    ELSE (ai_post_time AT TIME ZONE 'UTC')
END;

-- B) Drop old check constraints if they exist
ALTER TABLE upload_jobs DROP CONSTRAINT IF EXISTS upload_jobs_status_check;
ALTER TABLE upload_jobs DROP CONSTRAINT IF EXISTS valid_upload_status;

-- Backfill existing rows with legacy statuses
UPDATE upload_jobs
SET status = CASE status
    WHEN 'pending' THEN 'queued'
    WHEN 'uploading' THEN 'posting'
    WHEN 'done' THEN 'posted'
    WHEN 'failed' THEN 'failed'
    ELSE status
END;

-- Set status default
ALTER TABLE upload_jobs ALTER COLUMN status SET DEFAULT 'queued';

-- Add canonical status check constraint
ALTER TABLE upload_jobs
ADD CONSTRAINT upload_jobs_status_check
CHECK (status IN ('queued','generating','needs_review','scheduled','posting','posted','failed','canceled','needs_reauth'));

-- Add needs_reauth column if not exists
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS needs_reauth BOOLEAN DEFAULT FALSE;
-- ============================================================
-- VIRAL CONTENT DISCOVERY SYSTEM
-- Migration: 000006_viral_outliers
-- Created: 2026-01-01
-- ============================================================
-- This migration creates:
--   1. viral_outliers table for storing detected viral content
--   2. unified_posts view for normalizing competitor_posts and hashtag_posts
--   3. Required indexes for 15-minute scan performance
-- ============================================================

BEGIN;

-- ============================================================
-- 1. CREATE VIRAL_OUTLIERS TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS viral_outliers (
    id SERIAL PRIMARY KEY,
    source_table VARCHAR(50) NOT NULL,
    source_id INT NOT NULL,
    
    -- Metrics
    multiplier INT NOT NULL,
    median_engagement BIGINT NOT NULL,
    actual_engagement BIGINT NOT NULL,
    
    -- Availability tracking
    available_count INT NOT NULL,  -- How many metrics were available (1-3)
    support_count INT NOT NULL,    -- How many metrics were outliers
    
    -- Content
    hook TEXT,
    cta TEXT,
    platform VARCHAR(50),
    username TEXT,
    
    -- Timestamps (UTC)
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC'),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- AI analysis results
    ai_analysis JSONB DEFAULT '{}',
    
    -- Constraints
    UNIQUE (source_table, source_id),
    CONSTRAINT valid_multiplier CHECK (multiplier IN (5, 10, 50, 100)),
    CONSTRAINT positive_median CHECK (median_engagement > 0),
    CONSTRAINT positive_engagement CHECK (actual_engagement >= 0),
    CONSTRAINT valid_available CHECK (available_count BETWEEN 1 AND 3),
    CONSTRAINT valid_support CHECK (support_count >= 0 AND support_count <= available_count),
    CONSTRAINT valid_expiry CHECK (expires_at > analyzed_at)
);

-- ============================================================
-- 2. CREATE INDEXES FOR viral_outliers
-- ============================================================

-- Query performance indexes
CREATE INDEX IF NOT EXISTS idx_viral_outliers_multiplier ON viral_outliers(multiplier DESC);
CREATE INDEX IF NOT EXISTS idx_viral_outliers_platform ON viral_outliers(platform);
CREATE INDEX IF NOT EXISTS idx_viral_outliers_username ON viral_outliers(username);

-- Cleanup job index (CRITICAL for daily cleanup)
CREATE INDEX IF NOT EXISTS idx_viral_outliers_expires ON viral_outliers(expires_at);

-- ============================================================
-- 3. CREATE INDEXES FOR SOURCE TABLES (15-min scan performance)
-- ============================================================

-- Competitor posts scan indexes
CREATE INDEX IF NOT EXISTS idx_competitor_posts_scan 
    ON competitor_posts(platform, username, posted_at DESC);

CREATE INDEX IF NOT EXISTS idx_competitor_posts_posted_at 
    ON competitor_posts(posted_at DESC);

-- Hashtag posts scan indexes
CREATE INDEX IF NOT EXISTS idx_hashtag_posts_scan 
    ON hashtag_posts(platform, username, posted_at DESC);

CREATE INDEX IF NOT EXISTS idx_hashtag_posts_posted_at 
    ON hashtag_posts(posted_at DESC);

-- ============================================================
-- 4. CREATE UNIFIED_POSTS VIEW
-- ============================================================
-- Normalizes competitor_posts and hashtag_posts into a single view
-- for outlier detection queries

CREATE OR REPLACE VIEW unified_posts AS
-- competitor_posts (JSONB engagement)
SELECT 
    'competitor_posts' as source_table,
    id as source_id,
    username,
    platform,
    content,
    posted_at,
    COALESCE((engagement->>'likes')::bigint, 0) as likes,
    COALESCE((engagement->>'comments')::bigint, 0) as comments,
    -- Views: NULL when key doesn't exist (NOT 0!)
    CASE
        WHEN engagement ? 'views' THEN (engagement->>'views')::bigint
        ELSE NULL
    END as views
FROM competitor_posts
WHERE posted_at >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '30 days'

UNION ALL

-- hashtag_posts (direct BIGINT columns)
SELECT 
    'hashtag_posts' as source_table,
    id as source_id,
    username,
    platform,
    content,
    posted_at,
    COALESCE(likes, 0) as likes,
    COALESCE(comments_count, 0) as comments,
    NULL::bigint as views  -- hashtag_posts doesn't have views
FROM hashtag_posts
WHERE posted_at >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '30 days';

-- ============================================================
-- 5. CREATE TASK_LOCKS TABLE (for preventing task overlap)
-- ============================================================

CREATE TABLE IF NOT EXISTS task_locks (
    task_name VARCHAR(100) PRIMARY KEY,
    locked_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    locked_by VARCHAR(255),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC') + INTERVAL '1 hour'
);

COMMIT;
