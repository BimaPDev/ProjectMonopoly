-- name: ListVisibleCompetitorPosts :many
SELECT cp.*
FROM competitor_posts cp
JOIN user_competitors uc ON uc.competitor_id = cp.competitor_id
WHERE uc.user_id = @user_id
  AND (
    uc.visibility = 'global'
    OR uc.visibility = 'user'
    OR (uc.visibility = 'group' AND uc.group_id = @group_id)
  )
ORDER BY cp.posted_at DESC;
