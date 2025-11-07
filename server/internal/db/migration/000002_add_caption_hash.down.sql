-- Remove caption hash field and constraints
ALTER TABLE competitor_posts DROP CONSTRAINT IF EXISTS unique_competitor_caption;
DROP INDEX IF EXISTS idx_competitor_posts_caption_hash;
ALTER TABLE competitor_posts DROP COLUMN IF EXISTS caption_hash;
