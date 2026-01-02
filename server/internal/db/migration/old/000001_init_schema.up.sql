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
