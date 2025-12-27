-- Campaigns CRUD

-- name: CreateCampaign :one
INSERT INTO campaigns (user_id, group_id, name, goal, audience, pillars, cadence, status)
VALUES (
  sqlc.arg(user_id),
  sqlc.arg(group_id),
  sqlc.arg(name),
  sqlc.arg(goal),
  sqlc.arg(audience)::jsonb,
  sqlc.arg(pillars)::jsonb,
  sqlc.arg(cadence)::jsonb,
  sqlc.arg(status)
)
RETURNING *;

-- name: GetCampaignByID :one
SELECT * FROM campaigns WHERE id = $1;

-- name: ListCampaignsByUser :many
SELECT * FROM campaigns
WHERE user_id = $1
ORDER BY created_at DESC;

-- name: ListCampaignsByGroup :many
SELECT * FROM campaigns
WHERE group_id = $1
ORDER BY created_at DESC;

-- name: UpdateCampaignStatus :exec
UPDATE campaigns SET status = $2 WHERE id = $1;

-- name: UpdateCampaign :one
UPDATE campaigns
SET name = sqlc.arg(name),
    goal = sqlc.arg(goal),
    audience = sqlc.arg(audience)::jsonb,
    pillars = sqlc.arg(pillars)::jsonb,
    cadence = sqlc.arg(cadence)::jsonb
WHERE id = sqlc.arg(id)
RETURNING *;

-- name: DeleteCampaign :exec
DELETE FROM campaigns WHERE id = $1;

-- Campaign Assets

-- name: CreateCampaignAsset :one
INSERT INTO campaign_assets (campaign_id, storage_url, filename, mime_type, size_bytes, tags)
VALUES (
  sqlc.arg(campaign_id),
  sqlc.arg(storage_url),
  sqlc.arg(filename),
  sqlc.arg(mime_type),
  sqlc.arg(size_bytes),
  sqlc.arg(tags)::jsonb
)
RETURNING *;

-- name: ListCampaignAssets :many
SELECT * FROM campaign_assets
WHERE campaign_id = $1
ORDER BY created_at DESC;

-- name: DeleteCampaignAsset :exec
DELETE FROM campaign_assets WHERE id = $1;

-- Post Drafts

-- name: CreatePostDraft :one
INSERT INTO post_drafts (
  campaign_id, platform, post_type, hook, caption, hashtags, cta, 
  time_window, reason_codes, confidence, status
)
VALUES (
  sqlc.arg(campaign_id),
  sqlc.arg(platform),
  sqlc.arg(post_type),
  sqlc.arg(hook),
  sqlc.arg(caption),
  sqlc.arg(hashtags),
  sqlc.arg(cta),
  sqlc.arg(time_window)::jsonb,
  sqlc.arg(reason_codes),
  sqlc.arg(confidence),
  sqlc.arg(status)
)
RETURNING *;

-- name: GetPostDraftByID :one
SELECT * FROM post_drafts WHERE id = $1;

-- name: ListDraftsByCampaign :many
SELECT * FROM post_drafts
WHERE campaign_id = $1
ORDER BY created_at DESC;

-- name: ListDraftsByStatus :many
SELECT * FROM post_drafts
WHERE campaign_id = $1 AND status = $2
ORDER BY created_at DESC;

-- name: UpdateDraftStatus :exec
UPDATE post_drafts SET status = $2 WHERE id = $1;

-- name: UpdateDraftSchedule :exec
UPDATE post_drafts SET scheduled_at = $2, status = 'scheduled' WHERE id = $1;

-- name: BulkCreateDraft :exec
INSERT INTO post_drafts (
  campaign_id, platform, post_type, hook, caption, hashtags, cta,
  time_window, reason_codes, confidence, status
) VALUES (
  sqlc.arg(campaign_id),
  sqlc.arg(platform),
  sqlc.arg(post_type),
  sqlc.arg(hook),
  sqlc.arg(caption),
  sqlc.arg(hashtags),
  sqlc.arg(cta),
  sqlc.arg(time_window)::jsonb,
  sqlc.arg(reason_codes),
  sqlc.arg(confidence),
  sqlc.arg(status)
);

-- Post Metrics

-- name: InsertPostMetrics :one
INSERT INTO post_metrics (group_id, platform, post_id, draft_id, metrics, captured_at)
VALUES (
  sqlc.arg(group_id),
  sqlc.arg(platform),
  sqlc.arg(post_id),
  sqlc.arg(draft_id),
  sqlc.arg(metrics)::jsonb,
  COALESCE(sqlc.narg(captured_at), NOW())
)
ON CONFLICT (group_id, platform, post_id, captured_at) DO UPDATE
SET metrics = EXCLUDED.metrics
RETURNING *;

-- name: ListMetricsByGroup :many
SELECT * FROM post_metrics
WHERE group_id = $1 AND captured_at >= $2
ORDER BY captured_at DESC;

-- name: ListMetricsByDraft :many
SELECT * FROM post_metrics
WHERE draft_id = $1
ORDER BY captured_at DESC;

-- name: GetMetricsSummary :one
SELECT
  COUNT(DISTINCT post_id) as total_posts,
  AVG((metrics->>'impressions')::numeric) as avg_impressions,
  AVG((metrics->>'engagement_rate')::numeric) as avg_engagement,
  AVG((metrics->>'likes')::numeric) as avg_likes,
  AVG((metrics->>'comments')::numeric) as avg_comments,
  AVG((metrics->>'shares')::numeric) as avg_shares
FROM post_metrics
WHERE group_id = $1 AND captured_at >= $2;

-- name: GetBestPostingWindows :many
SELECT
  EXTRACT(DOW FROM captured_at)::int as day_of_week,
  EXTRACT(HOUR FROM captured_at)::int as hour_of_day,
  AVG((metrics->>'engagement_rate')::numeric) as avg_engagement,
  COUNT(*) as sample_size
FROM post_metrics
WHERE group_id = $1 AND captured_at >= NOW() - INTERVAL '28 days'
GROUP BY EXTRACT(DOW FROM captured_at), EXTRACT(HOUR FROM captured_at)
HAVING COUNT(*) >= 3
ORDER BY avg_engagement DESC
LIMIT 10;

-- name: GetTopHookPatterns :many
SELECT
  pd.hook,
  AVG((pm.metrics->>'engagement_rate')::numeric) as avg_engagement,
  COUNT(*) as usage_count
FROM post_drafts pd
JOIN post_metrics pm ON pm.draft_id = pd.id
WHERE pd.campaign_id IN (SELECT id FROM campaigns c WHERE c.group_id = sqlc.arg(group_id)::int)
  AND pm.captured_at >= NOW() - INTERVAL '28 days'
  AND pd.hook IS NOT NULL AND pd.hook != ''
GROUP BY pd.hook
HAVING COUNT(*) >= 2
ORDER BY avg_engagement DESC
LIMIT 10;
