-- Migration 000005 DOWN: Revert upload_jobs state machine changes

-- Drop the new status check constraint
ALTER TABLE upload_jobs DROP CONSTRAINT IF EXISTS upload_jobs_status_check;

-- Change scheduled_date back to DATE
ALTER TABLE upload_jobs 
ALTER COLUMN scheduled_date TYPE DATE 
USING scheduled_date::date;

-- Change ai_post_time back to TIMESTAMP
ALTER TABLE upload_jobs 
ALTER COLUMN ai_post_time TYPE TIMESTAMP 
USING ai_post_time::timestamp;

-- Restore old default (keeping it valid under new constraint would fail, so just remove default)
ALTER TABLE upload_jobs ALTER COLUMN status DROP DEFAULT;

-- Drop needs_reauth column
ALTER TABLE upload_jobs DROP COLUMN IF EXISTS needs_reauth;
