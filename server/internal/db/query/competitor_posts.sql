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
VALUES ($1, $2, $3, NOW())
ON CONFLICT (platform, username) DO UPDATE SET
  profile_url = EXCLUDED.profile_url,
  last_checked = EXCLUDED.last_checked
RETURNING *;
