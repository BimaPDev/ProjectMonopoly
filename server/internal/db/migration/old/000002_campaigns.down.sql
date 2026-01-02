-- 000002_campaigns.down.sql
DROP TRIGGER IF EXISTS trg_touch_post_drafts ON post_drafts;
DROP TRIGGER IF EXISTS trg_touch_campaigns ON campaigns;
DROP TABLE IF EXISTS post_metrics;
DROP TABLE IF EXISTS post_drafts;
DROP TABLE IF EXISTS campaign_assets;
DROP TABLE IF EXISTS campaigns;




