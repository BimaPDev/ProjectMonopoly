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
