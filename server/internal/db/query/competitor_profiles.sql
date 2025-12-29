-- Competitor Profiles SQLC Queries

-- name: CreateCompetitorProfile :one
INSERT INTO competitor_profiles (competitor_id, platform, handle, profile_url)
VALUES ($1, $2, $3, $4)
RETURNING *;

-- name: GetCompetitorProfileByID :one
SELECT * FROM competitor_profiles
WHERE id = $1;

-- name: ListProfilesByCompetitor :many
SELECT * FROM competitor_profiles
WHERE competitor_id = $1
ORDER BY platform;

-- name: UpdateCompetitorProfile :one
UPDATE competitor_profiles
SET handle = $2,
    profile_url = $3,
    followers = $4,
    engagement_rate = $5,
    growth_rate = $6,
    posting_frequency = $7,
    last_checked = $8
WHERE id = $1
RETURNING *;

-- name: DeleteCompetitorProfile :exec
DELETE FROM competitor_profiles
WHERE id = $1;

-- name: GetProfileByCompetitorAndPlatform :one
SELECT * FROM competitor_profiles
WHERE competitor_id = $1 AND platform = $2;

-- name: ListCompetitorsWithProfiles :many
SELECT 
  c.id,
  c.display_name,
  c.last_checked,
  c.total_posts
FROM competitors c
JOIN user_competitors uc ON uc.competitor_id = c.id
WHERE uc.user_id = $1 
  AND (
    uc.group_id = $2 
    OR uc.group_id IS NULL
    OR $2 IS NULL
  )
ORDER BY c.display_name;

-- name: GetCompetitorWithAllProfiles :one
SELECT c.*
FROM competitors c
WHERE c.id = $1;

-- name: CreateCompetitorEntity :one
INSERT INTO competitors (display_name)
VALUES ($1)
RETURNING *;

-- name: UpdateCompetitorDisplayName :one
UPDATE competitors
SET display_name = $2
WHERE id = $1
RETURNING *;

-- name: DeleteCompetitor :exec
DELETE FROM competitors
WHERE id = $1;

-- name: GetProfileStats :many
SELECT 
  cp.id,
  cp.platform,
  cp.handle,
  cp.profile_url,
  cp.followers,
  cp.engagement_rate,
  cp.growth_rate,
  cp.posting_frequency,
  cp.last_checked
FROM competitor_profiles cp
WHERE cp.competitor_id = $1
ORDER BY cp.platform;
