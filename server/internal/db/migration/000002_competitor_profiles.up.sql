-- Migration: Add competitor_profiles table for multi-platform support
-- This separates platform-specific data from the competitor entity

-- Step 1: Create the new competitor_profiles table
CREATE TABLE competitor_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  competitor_id UUID NOT NULL REFERENCES competitors(id) ON DELETE CASCADE,
  platform VARCHAR(50) NOT NULL,
  handle VARCHAR(255) NOT NULL,
  profile_url TEXT,
  followers BIGINT DEFAULT 0,
  engagement_rate NUMERIC(5,2) DEFAULT 0.0,
  growth_rate NUMERIC(5,2) DEFAULT 0.0,
  posting_frequency NUMERIC(5,2) DEFAULT 0.0,
  last_checked TIMESTAMP,
  UNIQUE (competitor_id, platform)
);

-- Step 2: Migrate existing data from competitors to competitor_profiles
INSERT INTO competitor_profiles (competitor_id, platform, handle, profile_url, followers, engagement_rate, growth_rate, posting_frequency, last_checked)
SELECT id, platform, username, profile_url, followers, engagement_rate, growth_rate, posting_frequency, last_checked
FROM competitors;

-- Step 3: Add display name column to competitors (the entity name)
ALTER TABLE competitors ADD COLUMN IF NOT EXISTS display_name VARCHAR(255);

-- Step 4: Set display_name from existing username before dropping
UPDATE competitors SET display_name = username;

-- Step 5: Drop old columns from competitors (now stored in profiles)
ALTER TABLE competitors DROP COLUMN IF EXISTS platform;
ALTER TABLE competitors DROP COLUMN IF EXISTS username;
ALTER TABLE competitors DROP COLUMN IF EXISTS profile_url;
ALTER TABLE competitors DROP COLUMN IF EXISTS followers;
ALTER TABLE competitors DROP COLUMN IF EXISTS engagement_rate;
ALTER TABLE competitors DROP COLUMN IF EXISTS growth_rate;
ALTER TABLE competitors DROP COLUMN IF EXISTS posting_frequency;

-- Step 6: Update competitor_posts to reference profiles instead
ALTER TABLE competitor_posts ADD COLUMN IF NOT EXISTS profile_id UUID REFERENCES competitor_profiles(id) ON DELETE CASCADE;

-- Step 7: Backfill profile_id in competitor_posts
UPDATE competitor_posts cp
SET profile_id = (
  SELECT cpr.id 
  FROM competitor_profiles cpr 
  WHERE cpr.competitor_id = cp.competitor_id 
    AND cpr.platform = cp.platform
  LIMIT 1
);

-- Step 8: Create index for faster profile lookups
CREATE INDEX IF NOT EXISTS idx_competitor_profiles_competitor_id ON competitor_profiles(competitor_id);
CREATE INDEX IF NOT EXISTS idx_competitor_posts_profile_id ON competitor_posts(profile_id);
