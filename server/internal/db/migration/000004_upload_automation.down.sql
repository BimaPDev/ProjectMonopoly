-- Rollback: Upload Automation

-- Remove indexes
DROP INDEX IF EXISTS idx_upload_jobs_failed;
DROP INDEX IF EXISTS idx_upload_jobs_queued;
DROP INDEX IF EXISTS idx_upload_jobs_scheduled_ready;

-- Remove constraint
ALTER TABLE upload_jobs DROP CONSTRAINT IF EXISTS valid_upload_status;

-- Remove columns
ALTER TABLE upload_jobs DROP COLUMN IF EXISTS locked_by;
ALTER TABLE upload_jobs DROP COLUMN IF EXISTS locked_at;
ALTER TABLE upload_jobs DROP COLUMN IF EXISTS platform_post_id;
ALTER TABLE upload_jobs DROP COLUMN IF EXISTS posted_url;
ALTER TABLE upload_jobs DROP COLUMN IF EXISTS error_at;
ALTER TABLE upload_jobs DROP COLUMN IF EXISTS error_message;
ALTER TABLE upload_jobs DROP COLUMN IF EXISTS max_retries;
ALTER TABLE upload_jobs DROP COLUMN IF EXISTS retry_count;
ALTER TABLE upload_jobs DROP COLUMN IF EXISTS ai_hook;
