-- Migration 000005: Fix upload_jobs state machine
-- Fixes time types, status constraints, and backfills legacy statuses

-- A) Fix time types: DATE -> TIMESTAMPTZ for scheduled_date
ALTER TABLE upload_jobs 
ALTER COLUMN scheduled_date TYPE TIMESTAMPTZ 
USING CASE 
    WHEN scheduled_date IS NULL THEN NULL
    ELSE (scheduled_date::timestamp AT TIME ZONE 'UTC')
END;

-- Fix time types: TIMESTAMP -> TIMESTAMPTZ for ai_post_time
ALTER TABLE upload_jobs 
ALTER COLUMN ai_post_time TYPE TIMESTAMPTZ 
USING CASE 
    WHEN ai_post_time IS NULL THEN NULL
    ELSE (ai_post_time AT TIME ZONE 'UTC')
END;

-- B) Drop old check constraints if they exist
ALTER TABLE upload_jobs DROP CONSTRAINT IF EXISTS upload_jobs_status_check;
ALTER TABLE upload_jobs DROP CONSTRAINT IF EXISTS valid_upload_status;

-- Backfill existing rows with legacy statuses
UPDATE upload_jobs
SET status = CASE status
    WHEN 'pending' THEN 'queued'
    WHEN 'uploading' THEN 'posting'
    WHEN 'done' THEN 'posted'
    WHEN 'failed' THEN 'failed'
    ELSE status
END;

-- Set status default
ALTER TABLE upload_jobs ALTER COLUMN status SET DEFAULT 'queued';

-- Add canonical status check constraint
ALTER TABLE upload_jobs
ADD CONSTRAINT upload_jobs_status_check
CHECK (status IN ('queued','generating','needs_review','scheduled','posting','posted','failed','canceled','needs_reauth'));

-- Add needs_reauth column if not exists
ALTER TABLE upload_jobs ADD COLUMN IF NOT EXISTS needs_reauth BOOLEAN DEFAULT FALSE;
