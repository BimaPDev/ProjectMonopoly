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
