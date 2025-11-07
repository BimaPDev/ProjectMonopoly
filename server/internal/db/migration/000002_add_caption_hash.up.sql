-- Add caption hash field for deduplication
ALTER TABLE competitor_posts ADD COLUMN caption_hash VARCHAR(64);

-- Create index for fast caption hash lookups
CREATE INDEX idx_competitor_posts_caption_hash ON competitor_posts(competitor_id, caption_hash);

-- Update existing posts with caption hashes
UPDATE competitor_posts 
SET caption_hash = encode(sha256(COALESCE(content, '')::bytea), 'hex')
WHERE caption_hash IS NULL;

-- Add unique constraint for caption-based deduplication
ALTER TABLE competitor_posts 
ADD CONSTRAINT unique_competitor_caption UNIQUE (competitor_id, caption_hash);
