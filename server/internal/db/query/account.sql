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
  $1, $2, $3, $4, $5, $6, $7, $8, $9,$10, $11,NOW(), NOW()
)
RETURNING id, user_id, platform, video_path, storage_type, file_url, status, user_title, user_hashtags, created_at, updated_at, group_id;

-- Get upload job by ID
-- name: GetUploadJob :one
SELECT id, user_id, platform, video_path, storage_type, file_url, status, created_at, updated_at
FROM upload_jobs
WHERE id = $1;

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

-- List all upload jobs for a user
-- name: ListUserUploadJobs :many
SELECT id, platform, video_path, storage_type, file_url, status, created_at, updated_at
FROM upload_jobs
WHERE user_id = $1
ORDER BY created_at DESC;

-- name: InsertGroupItemIfNotExists :execrows
INSERT INTO group_items (group_id,platform,data, created_at, updated_at)
VALUES ($1,$2,$3, NOW(), NOW())
ON CONFLICT (group_id, platform) DO NOTHING;


-- name: GetGroupItemByGroupID :many
SELECT id, group_id, platform, data, created_at, updated_at
FROM group_items
WHERE group_id = $1;

-- name: GetGroupByID :one
SELECT id, user_id, name, description, created_at, updated_at
FROM groups
WHERE id = $1;

-- name: CreateGroup :one
INSERT INTO groups (user_id, name, description, created_at, updated_at)
VALUES ($1, $2, $3, NOW(), NOW())
RETURNING id, user_id, name, description, created_at, updated_at;

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

-- name: CreateCompetitor :one
INSERT INTO competitors (platform, username, profile_url, last_checked)
VALUES ($1, $2, $3, NULL)
RETURNING *;

-- name: GetGroupCompetitors :many
SELECT c.*
FROM competitors c
JOIN user_competitors uc ON uc.competitor_id = c.id
WHERE uc.user_id = $1;

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

-- name: GetUploadJobByGID :many
 select id, group_id,platform,status, created_at
 from upload_jobs 
 where group_id = $1 order by id;

--uploding group items

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
  $2,      -- platform    (VARCHAR)
  $3,       -- type        (VARCHAR)
  $4::jsonb,-- data        (JSONB)
  NOW(),
  NOW()
);


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

-- name: UpdateSocialMediaData :exec
UPDATE socialmedia_data
SET
  platform   = $2,
  data       = $3::jsonb,
  updated_at = NOW()
WHERE id = $1;

-- name: DeleteSocialMediaData :exec
DELETE FROM socialmedia_data
WHERE id = $1;


-- name: GetUserIDByUsernameEmail :one
SELECT id
FROM users
WHERE username = $1
  AND email    = $2;

-- name: InsertFollowerCount :exec
insert into daily_followers(
  record_date,
  follower_count
) values (
  $1, -- record_date (INT)
  $2  -- date           (timestamp)
);

-- name: GetFollowerByDate :one
SELECT follower_count
FROM daily_followers
ORDER BY record_date DESC
LIMIT 1;



-- name: LinkUserToCompetitor :exec
INSERT INTO user_competitors (user_id, group_id, competitor_id, visibility)
VALUES ($1, $2, $3, $4)
ON CONFLICT DO NOTHING;

-- name: ListUserCompetitors :many
SELECT c.*
FROM competitors c
JOIN user_competitors uc ON uc.competitor_id = c.id
WHERE uc.user_id = $1;

-- name: ListGroupCompetitors :many
SELECT c.*
FROM competitors c
JOIN user_competitors uc ON uc.competitor_id = c.id
WHERE uc.user_id = $1 AND uc.group_id = $2;

-- name: ListAvailableCompetitorsToUser :many
SELECT *
FROM competitors
WHERE id NOT IN (
  SELECT competitor_id FROM user_competitors WHERE user_id = $1
);

-- name: GetCompetitorByPlatformUsername :one
SELECT * FROM competitors
WHERE platform = $1 AND LOWER(username) = LOWER($2);

-- name: UpdateGroupItemData :exec
UPDATE group_items
SET data = @data::jsonb, updated_at = NOW()
WHERE group_id = @group_id AND platform = @platform;

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
    $21, $22 , $23
)
RETURNING *;

-- name: GetGameContextByGroupID :one
SELECT * FROM game_contexts
WHERE group_id = $1
ORDER BY created_at DESC
LIMIT 1;

-- name: GetGameContextByUserID :one
SELECT * FROM game_contexts
WHERE user_id = $1
ORDER BY created_at DESC
LIMIT 1;

-- name: ListGameContextsByUser :many
SELECT * FROM game_contexts
WHERE user_id = $1
ORDER BY created_at DESC;
