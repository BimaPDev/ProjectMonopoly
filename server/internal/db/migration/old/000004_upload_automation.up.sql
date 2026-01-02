-- Migration: Upload Automation
-- Adds columns for automated content posting pipeline with state machine, retry handling, and job locking

-- Add AI hook for generated opening lines
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS ai_hook TEXT;

-- Retry tracking
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS retry_count INT DEFAULT 0;
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS max_retries INT DEFAULT 3;
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS error_message TEXT;
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS error_at TIMESTAMP WITH TIME ZONE;

-- Post tracking (result after successful upload)
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS posted_url TEXT;
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS platform_post_id TEXT;

-- Worker locking (for atomic job claiming)
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS locked_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS locked_by TEXT;

-- Enforce valid status values via CHECK constraint
-- Note: Using DO block to handle case where constraint already exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'valid_upload_status'
    ) THEN
        ALTER TABLE upload_jobs ADD CONSTRAINT valid_upload_status CHECK (
            status IN (
                'queued',
                'generating',
                'needs_review',
                'scheduled',
                'posting',
                'posted',
                'failed',
                'canceled',
                'needs_reauth'
            )
        );
    END IF;
END $$;

-- Index for scheduler polling (scheduled jobs ready to post)
CREATE INDEX IF NOT EXISTS idx_upload_jobs_scheduled_ready 
ON upload_jobs (scheduled_date) 
WHERE status = 'scheduled';

-- Index for queued jobs awaiting AI generation
CREATE INDEX IF NOT EXISTS idx_upload_jobs_queued 
ON upload_jobs (created_at) 
WHERE status = 'queued';

-- Index for failed jobs (for retry monitoring)
CREATE INDEX IF NOT EXISTS idx_upload_jobs_failed 
ON upload_jobs (error_at) 
WHERE status = 'failed';
