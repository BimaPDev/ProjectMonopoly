-- this file creates SQL queries for managing competitor posts and competitors in the database
INSERT INTO competitor_posts (
  competitor_id,
  platform,
  post_id,
  content,
  media,
  posted_at,
  engagement,
  hashtags,
  scraped_at
)
VALUES (
  $1, -- competitor_id (UUID)
  $2, -- platform (VARCHAR)
  $3, -- post_id (VARCHAR)
  $4, -- content (TEXT)
  $5::jsonb, -- media (JSONB)
  $6, -- posted_at (TIMESTAMP)
  $7::jsonb, -- engagement (JSONB)
  $8, -- hashtags (TEXT[])
  $9  -- scraped_at (TIMESTAMP)
)
ON CONFLICT (platform, post_id) DO UPDATE SET
  content = EXCLUDED.content,
  media = EXCLUDED.media,
  posted_at = EXCLUDED.posted_at,
  engagement = EXCLUDED.engagement,
  hashtags = EXCLUDED.hashtags,
  scraped_at = EXCLUDED.scraped_at
RETURNING *;

SELECT id, platform, username, profile_url, last_checked, followers, engagement_rate, growth_rate, posting_frequency
FROM competitors
WHERE platform = $1 AND username = $2;

INSERT INTO competitors (platform, username, profile_url, last_checked)
VALUES ($1, $2, $3, NULL)
ON CONFLICT (platform, username) DO UPDATE SET
  profile_url = EXCLUDED.profile_url,
  last_checked = EXCLUDED.last_checked
RETURNING *;

-- name: SearchCompetitorPosts :many
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
  -- Calculate relevance score for ranking
  CASE
    WHEN to_tsvector('english', COALESCE(cp.content, '')) @@ websearch_to_tsquery('english', $3) THEN 3
    WHEN cp.content ILIKE '%' || $3 || '%' THEN 2
    ELSE 1
  END as relevance
FROM competitor_posts cp
JOIN competitors c ON c.id = cp.competitor_id
JOIN competitor_profiles cpr ON cpr.id = cp.profile_id
JOIN user_competitors uc ON uc.competitor_id = c.id
WHERE uc.user_id = $1
  AND (uc.group_id = $2 OR uc.group_id IS NULL)
  AND (
    -- Try exact full-text match first (all terms must match)
    to_tsvector('english', COALESCE(cp.content, '')) @@ websearch_to_tsquery('english', $3)
    -- Or partial ILIKE match
    OR cp.content ILIKE '%' || $3 || '%'
    -- Or match ANY of the terms (more flexible)
    OR to_tsvector('english', COALESCE(cp.content, '')) @@ plainto_tsquery('english', $3)
  )
ORDER BY relevance DESC, cp.posted_at DESC
LIMIT $4;

-- name: GetRecentCompetitorPosts :many
SELECT
  cp.id,
  cp.competitor_id,
  cp.platform,
  cp.post_id,
  cp.content,
  cp.posted_at,
  cp.engagement,
  c.display_name as competitor_name,
  cpr.handle as competitor_handle
FROM competitor_posts cp
JOIN competitors c ON c.id = cp.competitor_id
JOIN competitor_profiles cpr ON cpr.id = cp.profile_id
JOIN user_competitors uc ON uc.competitor_id = c.id
WHERE uc.user_id = $1
  AND (uc.group_id = $2 OR uc.group_id IS NULL)
ORDER BY cp.posted_at DESC
LIMIT $3;

-- name: GetCompetitorAnalytics :many
SELECT
  c.id,
  c.display_name,
  cpr.platform,
  cpr.handle,
  cpr.followers,
  cpr.engagement_rate,
  cpr.growth_rate,
  cpr.posting_frequency
FROM competitors c
JOIN competitor_profiles cpr ON cpr.competitor_id = c.id
JOIN user_competitors uc ON uc.competitor_id = c.id
WHERE uc.user_id = $1
  AND (uc.group_id = $2 OR uc.group_id IS NULL);
