-- ============================================================
-- VIRAL CONTENT DISCOVERY SYSTEM - ROLLBACK
-- Migration: 000006_viral_outliers
-- ============================================================

BEGIN;

-- Drop task locks table
DROP TABLE IF EXISTS task_locks;

-- Drop unified posts view
DROP VIEW IF EXISTS unified_posts;

-- Drop viral outliers table
DROP TABLE IF EXISTS viral_outliers;

-- Drop source table indexes (only if they don't exist in other migrations)
DROP INDEX IF EXISTS idx_competitor_posts_scan;
DROP INDEX IF EXISTS idx_competitor_posts_posted_at;
DROP INDEX IF EXISTS idx_hashtag_posts_scan;
DROP INDEX IF EXISTS idx_hashtag_posts_posted_at;

COMMIT;
