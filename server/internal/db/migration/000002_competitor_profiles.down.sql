-- Rollback: Remove competitor_profiles and restore competitors table

-- Step 1: Restore columns to competitors table
ALTER TABLE competitors ADD COLUMN IF NOT EXISTS platform VARCHAR(50);
ALTER TABLE competitors ADD COLUMN IF NOT EXISTS username VARCHAR(100);
ALTER TABLE competitors ADD COLUMN IF NOT EXISTS profile_url TEXT;
ALTER TABLE competitors ADD COLUMN IF NOT EXISTS followers BIGINT DEFAULT 0;
ALTER TABLE competitors ADD COLUMN IF NOT EXISTS engagement_rate NUMERIC(4,2) DEFAULT 0.0;
ALTER TABLE competitors ADD COLUMN IF NOT EXISTS growth_rate NUMERIC(4,2) DEFAULT 0.0;
ALTER TABLE competitors ADD COLUMN IF NOT EXISTS posting_frequency NUMERIC(5,2) DEFAULT 0.0;

-- Step 2: Restore data from first profile (best effort)
UPDATE competitors c
SET 
  platform = cp.platform,
  username = cp.handle,
  profile_url = cp.profile_url,
  followers = cp.followers,
  engagement_rate = cp.engagement_rate,
  growth_rate = cp.growth_rate,
  posting_frequency = cp.posting_frequency
FROM (
  SELECT DISTINCT ON (competitor_id) *
  FROM competitor_profiles
  ORDER BY competitor_id, last_checked DESC NULLS LAST
) cp
WHERE c.id = cp.competitor_id;

-- Step 3: Remove profile_id from competitor_posts
ALTER TABLE competitor_posts DROP COLUMN IF EXISTS profile_id;

-- Step 4: Drop competitor_profiles table
DROP TABLE IF EXISTS competitor_profiles;

-- Step 5: Drop display_name column
ALTER TABLE competitors DROP COLUMN IF EXISTS display_name;

-- Step 6: Drop indexes
DROP INDEX IF EXISTS idx_competitor_profiles_competitor_id;
DROP INDEX IF EXISTS idx_competitor_posts_profile_id;
