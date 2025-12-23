-- Optimized Competitor Analytics Queries for Marketing AI Pipeline
-- Implements time-boxing (14 days), relevance filtering, and engagement aggregation

-- name: GetTimeBoxedCompetitorInsights :many
-- Fetches competitor posts from the last 14 days, excluding technical content
SELECT
  cp.id,
  cp.competitor_id,
  cp.platform,
  cp.post_id,
  cp.content,
  cp.posted_at,
  cp.engagement,
  c.display_name as competitor_name,
  cpr.handle as competitor_handle,
  -- Extract engagement metrics from JSONB
  COALESCE((cp.engagement->>'likes')::bigint, 0) + 
  COALESCE((cp.engagement->>'comments')::bigint, 0) as total_engagement
FROM competitor_posts cp
JOIN competitors c ON c.id = cp.competitor_id
JOIN competitor_profiles cpr ON cpr.id = cp.profile_id
JOIN user_competitors uc ON uc.competitor_id = c.id
WHERE uc.user_id = $1
  AND (uc.group_id = $2 OR uc.group_id IS NULL)
  -- Constraint A: Time-box to last 14 days
  AND cp.posted_at >= NOW() - INTERVAL '14 days'
  -- Constraint B: Exclude technical posts (Patch Notes, Hotfix, Steam Deck, 1080p)
  AND NOT (
    cp.content ILIKE '%Patch Notes%' OR
    cp.content ILIKE '%Hotfix%' OR
    cp.content ILIKE '%Steam Deck%' OR
    cp.content ILIKE '%1080p%' OR
    cp.content ILIKE '%patch%note%' OR
    cp.content ILIKE '%hot%fix%'
  )
ORDER BY total_engagement DESC
LIMIT $3;

-- name: GetBestPostingHour :one
-- Constraint C: Return the best posting hour (0-23) based on average engagement
-- Uses the same 14-day window and relevance filters
SELECT
  EXTRACT(HOUR FROM cp.posted_at)::int as best_hour,
  AVG(
    COALESCE((cp.engagement->>'likes')::bigint, 0) + 
    COALESCE((cp.engagement->>'comments')::bigint, 0)
  )::float8 as avg_engagement,
  COUNT(*)::bigint as sample_size
FROM competitor_posts cp
JOIN competitors c ON c.id = cp.competitor_id
JOIN user_competitors uc ON uc.competitor_id = c.id
WHERE uc.user_id = $1
  AND (uc.group_id = $2 OR uc.group_id IS NULL)
  AND cp.posted_at >= NOW() - INTERVAL '14 days'
  AND cp.posted_at IS NOT NULL
  AND NOT (
    cp.content ILIKE '%Patch Notes%' OR
    cp.content ILIKE '%Hotfix%' OR
    cp.content ILIKE '%Steam Deck%' OR
    cp.content ILIKE '%1080p%'
  )
GROUP BY EXTRACT(HOUR FROM cp.posted_at)
ORDER BY avg_engagement DESC
LIMIT 1;

-- name: GetTopCompetitorHooks :many
-- Returns the highest-engagement captions for inspiration (first 280 chars as hook)
SELECT
  cp.id,
  c.display_name as competitor_name,
  cpr.handle as competitor_handle,
  cp.platform,
  LEFT(cp.content, 280) as hook,
  cp.posted_at,
  COALESCE((cp.engagement->>'likes')::bigint, 0) + 
  COALESCE((cp.engagement->>'comments')::bigint, 0) as total_engagement
FROM competitor_posts cp
JOIN competitors c ON c.id = cp.competitor_id
JOIN competitor_profiles cpr ON cpr.id = cp.profile_id
JOIN user_competitors uc ON uc.competitor_id = c.id
WHERE uc.user_id = $1
  AND (uc.group_id = $2 OR uc.group_id IS NULL)
  AND cp.posted_at >= NOW() - INTERVAL '14 days'
  AND cp.content IS NOT NULL
  AND LENGTH(cp.content) > 20  -- Filter out empty/minimal content
  AND NOT (
    cp.content ILIKE '%Patch Notes%' OR
    cp.content ILIKE '%Hotfix%' OR
    cp.content ILIKE '%Steam Deck%' OR
    cp.content ILIKE '%1080p%'
  )
ORDER BY total_engagement DESC
LIMIT $3;

-- name: GetCompetitorPostCount14Days :one
-- Helper to check if we have any relevant data in the 14-day window
SELECT COUNT(*)::bigint as post_count
FROM competitor_posts cp
JOIN competitors c ON c.id = cp.competitor_id
JOIN user_competitors uc ON uc.competitor_id = c.id
WHERE uc.user_id = $1
  AND (uc.group_id = $2 OR uc.group_id IS NULL)
  AND cp.posted_at >= NOW() - INTERVAL '14 days';

-- name: GetBestPostingDay :one
-- Returns the best day of week (1=Monday, 7=Sunday) based on average likes
-- Uses 28-day window (4 weeks) for reliable weekly patterns
-- NOTE: We only have DATE from scraper, not TIME, so ISODOW is the only reliable metric
SELECT
  EXTRACT(ISODOW FROM cp.posted_at)::int as best_day,
  AVG(COALESCE((cp.engagement->>'likes')::bigint, 0))::float8 as avg_likes,
  COUNT(*)::bigint as sample_size
FROM competitor_posts cp
JOIN competitors c ON c.id = cp.competitor_id
JOIN user_competitors uc ON uc.competitor_id = c.id
WHERE uc.user_id = $1
  AND (uc.group_id = $2 OR uc.group_id IS NULL)
  AND cp.posted_at >= NOW() - INTERVAL '28 days'
  AND cp.posted_at IS NOT NULL
  AND NOT (
    cp.content ILIKE '%Patch Notes%' OR
    cp.content ILIKE '%Hotfix%' OR
    cp.content ILIKE '%Steam Deck%' OR
    cp.content ILIKE '%1080p%'
  )
GROUP BY EXTRACT(ISODOW FROM cp.posted_at)
ORDER BY avg_likes DESC
LIMIT 1;

-- name: GetPostingFrequency28Days :one
-- Returns total posts and posts per week over 28 days for competitor cadence analysis
SELECT
  COUNT(*)::bigint as total_posts,
  (COUNT(*) / 4.0)::float8 as posts_per_week
FROM competitor_posts cp
JOIN competitors c ON c.id = cp.competitor_id
JOIN user_competitors uc ON uc.competitor_id = c.id
WHERE uc.user_id = $1
  AND (uc.group_id = $2 OR uc.group_id IS NULL)
  AND cp.posted_at >= NOW() - INTERVAL '28 days';
