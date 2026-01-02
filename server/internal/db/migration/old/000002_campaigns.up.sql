-- 000002_campaigns.up.sql
-- Campaign workflow tables for structured marketing automation

-- Campaigns: stores wizard-created campaign configurations
CREATE TABLE campaigns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  group_id INT REFERENCES groups(id) ON DELETE SET NULL,
  name VARCHAR(255) NOT NULL,
  goal TEXT NOT NULL CHECK (goal IN ('wishlist', 'discord', 'demo', 'trailer', 'awareness', 'launch')),
  audience JSONB NOT NULL DEFAULT '{}'::jsonb,
  pillars JSONB NOT NULL DEFAULT '[]'::jsonb,
  cadence JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'paused', 'completed')),
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_campaigns_user_id ON campaigns(user_id);
CREATE INDEX idx_campaigns_group_id ON campaigns(group_id);
CREATE INDEX idx_campaigns_status ON campaigns(status);

-- Campaign assets: uploaded media with tags
CREATE TABLE campaign_assets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  storage_url TEXT NOT NULL,
  filename TEXT NOT NULL,
  mime_type TEXT,
  size_bytes BIGINT,
  tags JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_campaign_assets_campaign_id ON campaign_assets(campaign_id);

-- Post drafts: AI-generated structured content
CREATE TABLE post_drafts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  platform TEXT NOT NULL,
  post_type TEXT NOT NULL DEFAULT 'standard',
  hook TEXT,
  caption TEXT,
  hashtags TEXT[] DEFAULT '{}',
  cta TEXT,
  time_window JSONB,
  reason_codes TEXT[] DEFAULT '{}',
  confidence NUMERIC(4,2) DEFAULT 0.0,
  status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'scheduled', 'posted', 'rejected')),
  scheduled_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_post_drafts_campaign_id ON post_drafts(campaign_id);
CREATE INDEX idx_post_drafts_status ON post_drafts(status);
CREATE INDEX idx_post_drafts_platform ON post_drafts(platform);

-- Post metrics: performance snapshots for feedback loop
CREATE TABLE post_metrics (
  id BIGSERIAL PRIMARY KEY,
  group_id INT NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
  platform TEXT NOT NULL,
  post_id TEXT NOT NULL,
  draft_id UUID REFERENCES post_drafts(id) ON DELETE SET NULL,
  captured_at TIMESTAMP NOT NULL DEFAULT NOW(),
  metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
  UNIQUE (group_id, platform, post_id, captured_at)
);

CREATE INDEX idx_post_metrics_group_id ON post_metrics(group_id);
CREATE INDEX idx_post_metrics_draft_id ON post_metrics(draft_id);
CREATE INDEX idx_post_metrics_captured_at ON post_metrics(captured_at);

-- Trigger to update updated_at on campaigns
DROP TRIGGER IF EXISTS trg_touch_campaigns ON campaigns;
CREATE TRIGGER trg_touch_campaigns
BEFORE UPDATE ON campaigns FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

-- Trigger to update updated_at on post_drafts
DROP TRIGGER IF EXISTS trg_touch_post_drafts ON post_drafts;
CREATE TRIGGER trg_touch_post_drafts
BEFORE UPDATE ON post_drafts FOR EACH ROW EXECUTE FUNCTION touch_updated_at();




