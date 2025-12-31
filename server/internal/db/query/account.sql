-- ============================================================================
-- USER MANAGEMENT
-- ============================================================================

-- Register a new user with a password
-- name: CreateUserWithPassword :one
INSERT INTO users (username, email, password_hash, created_at, updated_at)
VALUES ($1, $2, $3, NOW(), NOW())
RETURNING id, username, email, created_at, updated_at;

-- Register a new OAuth user (if they don't exist, update username if needed)
-- name: CreateOAuthUser :one
INSERT INTO users (username, email, oauth_provider, oauth_id, created_at, updated_at)
VALUES ($1, $2, $3, $4, NOW(), NOW())
ON CONFLICT (email) 
DO UPDATE SET username = EXCLUDED.username, updated_at = NOW()
RETURNING id, username, email, oauth_provider, oauth_id, created_at, updated_at;

-- Get user by ID
-- name: GetUserByID :one
SELECT id, username, email, created_at, updated_at
FROM users
WHERE id = $1;

-- Get user by email (for password login)
-- name: GetUserByEmailWithPassword :one
SELECT id, username, email, password_hash, created_at, updated_at
FROM users
WHERE email = $1;

-- Get user by email (for OAuth login)
-- name: GetOAuthUserByEmail :one
SELECT id, username, email, oauth_provider, oauth_id, created_at, updated_at
FROM users
WHERE email = $1;

-- Get user ID by username and email
-- name: GetUserIDByUsernameEmail :one
SELECT id
FROM users
WHERE username = $1
  AND email    = $2;

-- List all users
-- name: ListUsers :many
SELECT id, username, email, created_at, updated_at
FROM users
ORDER BY created_at DESC;

-- Update user details
-- name: UpdateUser :one
UPDATE users
SET username = $2,
    email = $3,
    updated_at = NOW()
WHERE id = $1
RETURNING id, username, email, created_at, updated_at;

-- Delete a user
-- name: DeleteUser :exec
DELETE FROM users
WHERE id = $1;

-- Check if username or email exists
-- name: CheckUsernameOrEmailExists :one
SELECT COUNT(*) > 0 AS exists
FROM users
WHERE username = $1 OR email = $2;

-- Check if only email exists (for OAuth)
-- name: CheckEmailExists :one
SELECT COUNT(*) > 0 AS exists
FROM users
WHERE email = $1;


-- ============================================================================
-- SESSION MANAGEMENT
-- ============================================================================

-- Create a new session with configurable expiration
-- name: CreateSession :one
INSERT INTO sessions (user_id, expires_at)
VALUES ($1, NOW() + INTERVAL '24 hours')
RETURNING id, user_id, created_at, expires_at;

-- Get session by ID
-- name: GetSession :one
SELECT id, user_id, created_at, expires_at 
FROM sessions 
WHERE id = $1;

-- Delete a session (logout)
-- name: DeleteSession :exec
DELETE FROM sessions WHERE id = $1;


-- ============================================================================
-- GROUP MANAGEMENT
-- ============================================================================

-- Create a new group
-- name: CreateGroup :one
INSERT INTO groups (user_id, name, description, created_at, updated_at)
VALUES ($1, $2, $3, NOW(), NOW())
RETURNING id, user_id, name, description, created_at, updated_at;

-- Get group by ID
-- name: GetGroupByID :one
SELECT id, user_id, name, description, created_at, updated_at
FROM groups
WHERE id = $1;

-- List all groups for a user
-- name: ListGroupsByUser :many
SELECT
  id,
  user_id,
  name,
  description,
  created_at,
  updated_at
FROM groups
WHERE user_id = $1
ORDER BY id;


-- ============================================================================
-- GROUP ITEMS
-- ============================================================================

-- Insert group item if not exists
-- name: InsertGroupItemIfNotExists :execrows
INSERT INTO group_items (group_id, platform, data, created_at, updated_at)
VALUES ($1, $2, $3, NOW(), NOW())
ON CONFLICT (group_id, platform) DO NOTHING;

-- Get group items by group ID
-- name: GetGroupItemByGroupID :many
SELECT id, group_id, platform, data, created_at, updated_at
FROM group_items
WHERE group_id = $1;

-- Update group item data
-- name: UpdateGroupItemData :exec
UPDATE group_items
SET data = @data::jsonb, updated_at = NOW()
WHERE group_id = @group_id AND platform = @platform;


-- ============================================================================
-- UPLOAD JOBS
-- ============================================================================

-- Delete an existing upload job
-- name: DeleteUploadJob :exec
DELETE from upload_jobs where id = $1;
-- Create a new upload job
-- name: CreateUploadJob :one
INSERT INTO upload_jobs (
  id,
  user_id,
  platform,
  video_path,
  storage_type,
  file_url,
  scheduled_date,
  status,
  user_title,
  user_hashtags,
  group_id,
  created_at,
  updated_at
)
VALUES (
  $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), NOW()
)
RETURNING id, user_id, platform, video_path, storage_type, file_url, status, user_title, user_hashtags, created_at, updated_at, group_id;

-- Get upload job by ID
-- name: GetUploadJob :one
SELECT id, user_id, platform, video_path, storage_type, file_url, status, created_at, updated_at
FROM upload_jobs
WHERE id = $1;

-- Get upload jobs by group ID
-- name: GetUploadJobByGID :many
SELECT id, group_id, platform, status, created_at
FROM upload_jobs 
WHERE group_id = $1 
ORDER BY id;

-- List all upload jobs for a user
-- name: ListUserUploadJobs :many
SELECT id, platform, video_path, storage_type, file_url, status, created_at, updated_at
FROM upload_jobs
WHERE user_id = $1
ORDER BY created_at DESC;

-- Update upload job status
-- name: UpdateUploadJobStatus :exec
UPDATE upload_jobs
SET status = $2,
    updated_at = NOW()
WHERE id = $1;

-- Update upload job file URL
-- name: UpdateUploadJobFileURL :exec
UPDATE upload_jobs
SET file_url = $2,
    updated_at = NOW()
WHERE id = $1;

-- Fetch next pending job (with lock)
-- name: FetchNextPendingJob :one
UPDATE upload_jobs
SET status = 'processing'
WHERE id = (
    SELECT id FROM upload_jobs
    WHERE status = 'pending' AND session_id IS NOT NULL
    ORDER BY created_at
    LIMIT 1
    FOR UPDATE SKIP LOCKED
)
RETURNING *;


-- ============================================================================
-- SOCIAL MEDIA DATA
-- ============================================================================

-- Create social media data entry
-- name: CreateSocialMediaData :exec
INSERT INTO socialmedia_data (
  group_id,
  platform,
  type,
  data,
  created_at,
  updated_at
)
VALUES (
  $1,       -- group_id    (INT)
  $2,       -- platform    (VARCHAR)
  $3,       -- type        (VARCHAR)
  $4::jsonb,-- data        (JSONB)
  NOW(),
  NOW()
);

-- List social media data by group
-- name: ListSocialMediaDataByGroup :many
SELECT
  id,
  group_id,
  platform,
  type,
  data,
  created_at,
  updated_at
FROM socialmedia_data
WHERE group_id = $1
ORDER BY created_at DESC;

-- Update social media data
-- name: UpdateSocialMediaData :exec
UPDATE socialmedia_data
SET
  platform   = $2,
  data       = $3::jsonb,
  updated_at = NOW()
WHERE id = $1;

-- Delete social media data
-- name: DeleteSocialMediaData :exec
DELETE FROM socialmedia_data
WHERE id = $1;


-- ============================================================================
-- FOLLOWER TRACKING
-- ============================================================================

-- Insert daily follower count
-- name: InsertFollowerCount :exec
INSERT INTO daily_followers(
  record_date,
  follower_count
) VALUES (
  $1, -- record_date (INT)
  $2  -- follower_count
);

-- Get most recent follower count
-- name: GetFollowerByDate :one
SELECT follower_count
FROM daily_followers
ORDER BY record_date DESC
LIMIT 1;


-- ============================================================================
-- COMPETITOR MANAGEMENT
-- ============================================================================

-- Create a new competitor
-- name: CreateCompetitor :one
INSERT INTO competitors (display_name)
VALUES ($1)
RETURNING *;
-- Get a competitor from user competitors
-- name: GetUserCompetitorByCompetitorID :one
SELECT * FROM user_competitors
where competitor_id = $1;
-- Delete an existing competitor
-- name: DeleteCompetitorByID :exec
DELETE from competitors 
where id = $1;
-- Get competitor by platform and username
-- name: GetCompetitorByPlatformUsername :one
SELECT c.* FROM competitors c
JOIN competitor_profiles cp ON cp.competitor_id = c.id
WHERE cp.platform = $1 AND LOWER(cp.handle) = LOWER($2);

-- Link user to competitor
-- name: LinkUserToCompetitor :exec
INSERT INTO user_competitors (user_id, group_id, competitor_id, visibility)
VALUES ($1, $2, $3, $4)
ON CONFLICT DO NOTHING;

-- List all competitors for a user
-- name: ListUserCompetitors :many
SELECT
  c.id,
  c.display_name,
  c.last_checked,
  c.total_posts,
  cp.id as profile_id,
  cp.platform,
  cp.handle as username,
  cp.profile_url,
  cp.followers,
  cp.engagement_rate,
  cp.growth_rate,
  cp.posting_frequency
FROM competitors c
JOIN user_competitors uc ON uc.competitor_id = c.id
LEFT JOIN competitor_profiles cp ON cp.competitor_id = c.id
WHERE uc.user_id = $1;

-- List competitors for a specific group
-- name: ListGroupCompetitors :many
SELECT
  c.id,
  c.display_name,
  c.last_checked,
  c.total_posts,
  cp.id as profile_id,
  cp.platform,
  cp.handle as username,
  cp.profile_url,
  cp.followers,
  cp.engagement_rate,
  cp.growth_rate,
  cp.posting_frequency
FROM competitors c
JOIN user_competitors uc ON uc.competitor_id = c.id
LEFT JOIN competitor_profiles cp ON cp.competitor_id = c.id
WHERE uc.user_id = $1 AND uc.group_id = $2;

-- List competitors available to add for a user
-- name: ListAvailableCompetitorsToUser :many
SELECT
  c.id,
  c.display_name,
  c.last_checked,
  c.total_posts
FROM competitors c
WHERE c.id NOT IN (
  SELECT competitor_id FROM user_competitors WHERE user_id = $1
);

-- Get group competitors (duplicate - consider removing)
-- name: GetGroupCompetitors :many
SELECT
  c.id,
  c.display_name,
  c.last_checked,
  c.total_posts,
  cp.id as profile_id,
  cp.platform,
  cp.handle as username,
  cp.profile_url,
  cp.followers,
  cp.engagement_rate,
  cp.growth_rate,
  cp.posting_frequency
FROM competitors c
JOIN user_competitors uc ON uc.competitor_id = c.id
LEFT JOIN competitor_profiles cp ON cp.competitor_id = c.id
WHERE uc.user_id = $1;


-- ============================================================================
-- GAME CONTEXT
-- ============================================================================

-- Create game context
-- name: CreateGameContext :one
INSERT INTO game_contexts (
    user_id, group_id,
    game_title, studio_name, game_summary, platforms, engine_tech,
    primary_genre, subgenre, key_mechanics, playtime_length, art_style, tone,
    intended_audience, age_range, player_motivation, comparable_games,
    marketing_objective, key_events_dates, call_to_action,
    content_restrictions, competitors_to_avoid, additional_info
)
VALUES (
    $1, $2,
    $3, $4, $5, $6, $7,
    $8, $9, $10, $11, $12, $13,
    $14, $15, $16, $17,
    $18, $19, $20,
    $21, $22, $23
)
RETURNING *;
-- Update game context
-- name: UpdateGameContextByID :exec
UPDATE game_contexts
SET game_title = $2, studio_name = $3, game_summary = $4, platforms = $5, engine_tech = $6,
    primary_genre = $7, subgenre = $8, key_mechanics = $9, playtime_length = $10, art_style = $11, tone = $12,
    intended_audience = $13, age_range = $14, player_motivation = $15, comparable_games = $16,
    marketing_objective = $17, key_events_dates = $18, call_to_action = $19,
    content_restrictions = $20, competitors_to_avoid = $21, additional_info = $22, 
    updated_at = NOW()
where id = $1;

-- Delete Game Context
-- name: DeleteGameContextByID :exec
DELETE from game_contexts
where id = $1;

-- Get Game Context by ID
-- name: GetGameContextByID :one
SELECT * from game_contexts
where id = $1
limit 1;

-- Get game context by group ID
-- name: GetGameContextByGroupID :one
SELECT * FROM game_contexts
WHERE group_id = $1
ORDER BY created_at DESC
LIMIT 1;

-- Get all game context by group ID
-- name: GetAllGameContextByGroupID :many
SELECT *
FROM game_contexts
WHERE group_id = $1
ORDER BY created_at DESC;

-- Get game context by user ID
-- name: GetGameContextByUserID :one
SELECT * FROM game_contexts
WHERE user_id = $1
ORDER BY created_at DESC
LIMIT 1;

-- List all game contexts for a user
-- name: ListGameContextsByUser :many
SELECT * FROM game_contexts
WHERE user_id = $1
ORDER BY created_at DESC;