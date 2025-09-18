package db

import (
	"context"
	"database/sql"
	"encoding/json"

	"github.com/google/uuid"
	"github.com/lib/pq"
)

const createCompetitorIfNotExists = `-- name: CreateCompetitorIfNotExists :one
INSERT INTO competitors (platform, username, profile_url, last_checked)
VALUES ($1, $2, $3, NOW())
ON CONFLICT (platform, username) DO UPDATE SET
  profile_url = EXCLUDED.profile_url,
  last_checked = EXCLUDED.last_checked
RETURNING id, platform, username, profile_url, last_checked, followers, engagement_rate, growth_rate, posting_frequency
`

type CreateCompetitorIfNotExistsParams struct {
	Platform   string `json:"platform"`
	Username   string `json:"username"`
	ProfileUrl string `json:"profile_url"`
}

func (q *Queries) CreateCompetitorIfNotExists(ctx context.Context, arg CreateCompetitorIfNotExistsParams) (Competitor, error) {
	row := q.db.QueryRowContext(ctx, createCompetitorIfNotExists, arg.Platform, arg.Username, arg.ProfileUrl)
	var i Competitor
	err := row.Scan(
		&i.ID,
		&i.Platform,
		&i.Username,
		&i.ProfileUrl,
		&i.LastChecked,
		&i.Followers,
		&i.EngagementRate,
		&i.GrowthRate,
		&i.PostingFrequency,
	)
	return i, err
}

const createCompetitorPost = `-- name: CreateCompetitorPost :one
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
RETURNING id, competitor_id, platform, post_id, content, media, posted_at, engagement, hashtags, scraped_at
`

type CreateCompetitorPostParams struct {
	CompetitorID uuid.NullUUID   `json:"competitor_id"`
	Platform     string          `json:"platform"`
	PostID       string          `json:"post_id"`
	Content      sql.NullString  `json:"content"`
	Column5      json.RawMessage `json:"column_5"`
	PostedAt     sql.NullTime    `json:"posted_at"`
	Column7      json.RawMessage `json:"column_7"`
	Hashtags     []string        `json:"hashtags"`
	ScrapedAt    sql.NullTime    `json:"scraped_at"`
}

func (q *Queries) CreateCompetitorPost(ctx context.Context, arg CreateCompetitorPostParams) (CompetitorPost, error) {
	row := q.db.QueryRowContext(ctx, createCompetitorPost,
		arg.CompetitorID,
		arg.Platform,
		arg.PostID,
		arg.Content,
		arg.Column5,
		arg.PostedAt,
		arg.Column7,
		pq.Array(arg.Hashtags),
		arg.ScrapedAt,
	)
	var i CompetitorPost
	err := row.Scan(
		&i.ID,
		&i.CompetitorID,
		&i.Platform,
		&i.PostID,
		&i.Content,
		&i.Media,
		&i.PostedAt,
		&i.Engagement,
		pq.Array(&i.Hashtags),
		&i.ScrapedAt,
	)
	return i, err
}


const getCompetitorByUsername = `-- name: GetCompetitorByUsername :one
SELECT id, platform, username, profile_url, last_checked, followers, engagement_rate, growth_rate, posting_frequency
FROM competitors
WHERE platform = $1 AND username = $2
`

type GetCompetitorByUsernameParams struct {
	Platform string `json:"platform"`
	Username string `json:"username"`
}

func (q *Queries) GetCompetitorByUsername(ctx context.Context, arg GetCompetitorByUsernameParams) (Competitor, error) {
	row := q.db.QueryRowContext(ctx, getCompetitorByUsername, arg.Platform, arg.Username)
	var i Competitor
	err := row.Scan(
		&i.ID,
		&i.Platform,
		&i.Username,
		&i.ProfileUrl,
		&i.LastChecked,
		&i.Followers,
		&i.EngagementRate,
		&i.GrowthRate,
		&i.PostingFrequency,
	)
	return i, err
}
