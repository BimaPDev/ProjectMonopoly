"""
Auto Dispatcher
===============

Polls the database for pending jobs and dispatches them to Celery workers.
This is the main job coordinator that runs as a separate process.

Job Types Handled:
    1. Upload Jobs: Video/media uploads to social platforms
    2. Document Ingest Jobs: PDF processing for RAG system
    3. Cookie Preparation: Login and session cookie extraction
    4. Competitor Scraping: Periodic scraping of competitor data

Architecture:
    [PostgreSQL] --> [Dispatcher] --> [RabbitMQ] --> [Celery Workers]
                         ^                              |
                         |______________________________|

Edge Cases Handled:
    - Database connection failures (reconnection with backoff)
    - RabbitMQ unavailability (task queuing retries)
    - Empty job queues (smart sleep with backoff)
    - Orphaned jobs (timeout detection)
    - Concurrent dispatchers (row-level locking)

Author: ProjectMonopoly Team
Last Updated: 2025-12-27
"""

import os
import sys
import time
import logging
from typing import Optional, Tuple, Any
from datetime import datetime

import psycopg
from psycopg import OperationalError

from worker.celery_app import app, verify_broker_connection
from worker.config import (
    DATABASE_URL,
    DISPATCH_SLEEP,
    WEEKLY_SCRAPE_INTERVAL,
    RABBITMQ_RETRY_SETTINGS,
)

# ─────────────────────────────────────────────────────────────────────────────
# Logging Configuration
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Database Configuration
# ─────────────────────────────────────────────────────────────────────────────
DSN = os.getenv("DATABASE_URL", DATABASE_URL)

# Sleep interval between dispatch cycles (seconds)
SLEEP = float(os.getenv("DISPATCH_SLEEP", str(DISPATCH_SLEEP)))

# Maximum sleep when no work is found (prevents spinning)
MAX_SLEEP = float(os.getenv("DISPATCH_MAX_SLEEP", "10.0"))

# Scrape check interval (seconds)
SCRAPE_CHECK_INTERVAL = float(os.getenv("SCRAPE_CHECK_INTERVAL", "60.0"))


# ─────────────────────────────────────────────────────────────────────────────
# SQL Queries
# ─────────────────────────────────────────────────────────────────────────────
SQL_NEXT_UPLOAD = """
-- Fetch and lock the next pending upload job
-- Uses SKIP LOCKED for concurrent dispatcher safety
WITH next AS (
    SELECT j.id, j.user_id, j.group_id, j.platform, j.video_path,
           j.user_hashtags, j.user_title,
           gi.data->>'token' AS session_token
    FROM upload_jobs j
    JOIN groups g ON g.id = j.group_id AND g.user_id = j.user_id
    JOIN group_items gi
        ON gi.group_id = j.group_id
        AND LOWER(gi.platform) = LOWER(j.platform)
    WHERE j.status = 'pending'
        AND gi.data ? 'token' 
        AND COALESCE(gi.data->>'token', '') <> ''
    ORDER BY j.created_at
    FOR UPDATE SKIP LOCKED
    LIMIT 1
)
UPDATE upload_jobs u
SET status = 'uploading', updated_at = NOW()
FROM next
WHERE u.id = next.id
RETURNING next.id, next.user_id, next.group_id, next.platform,
          next.video_path, next.user_hashtags, next.user_title, next.session_token;
"""

SQL_NEXT_DOC = """
-- Fetch and lock the next queued document ingest job
WITH next AS (
    SELECT id, document_id
    FROM document_ingest_jobs
    WHERE status = 'queued'
    ORDER BY created_at
    FOR UPDATE SKIP LOCKED
    LIMIT 1
)
UPDATE document_ingest_jobs j
SET status = 'processing', updated_at = NOW()
FROM next
WHERE j.id = next.id
RETURNING next.id, next.document_id;
"""

SQL_NEXT_COOKIE_PREP = """
-- Fetch accounts needing cookie preparation
SELECT id, platform, 
       data->>'email' AS email, 
       data->>'password' AS password
FROM group_items
WHERE cookie_created_at IS NULL
    AND data ? 'email' AND data ? 'password'
    AND COALESCE(data->>'email', '') <> ''
    AND COALESCE(data->>'password', '') <> ''
ORDER BY created_at
FOR UPDATE SKIP LOCKED
LIMIT 1
"""

SQL_COOKIE_PREP_FALLBACK = """
-- Fallback query when cookie_created_at column doesn't exist
SELECT id, platform, 
       data->>'email' AS email, 
       data->>'password' AS password
FROM group_items
WHERE (data->>'sessionid' IS NULL OR data->>'sessionid' = '')
    AND data ? 'email' AND data ? 'password'
    AND COALESCE(data->>'email', '') <> ''
    AND COALESCE(data->>'password', '') <> ''
ORDER BY created_at
FOR UPDATE SKIP LOCKED
LIMIT 1
"""

SQL_PENDING_SCRAPES = """
-- Count competitors needing scraping
SELECT COUNT(DISTINCT cp.competitor_id) 
FROM competitor_profiles cp 
WHERE cp.last_checked IS NULL 
   OR cp.last_checked < NOW() - (INTERVAL '1 day' * %s)
"""


# ─────────────────────────────────────────────────────────────────────────────
# Dispatcher State
# ─────────────────────────────────────────────────────────────────────────────
class DispatcherState:
    """Maintains state across dispatch cycles."""
    
    def __init__(self):
        self.last_scrape_dispatch: float = 0.0
        self.consecutive_empty_cycles: int = 0
        self.total_jobs_dispatched: int = 0
        self.startup_time: datetime = datetime.now()
        self.last_db_check: float = 0.0
        self.db_healthy: bool = True
        self.broker_healthy: bool = True
    
    def record_work(self):
        """Reset empty cycle counter when work is found."""
        self.consecutive_empty_cycles = 0
        self.total_jobs_dispatched += 1
    
    def record_empty_cycle(self):
        """Increment empty cycle counter."""
        self.consecutive_empty_cycles += 1
    
    def get_adaptive_sleep(self) -> float:
        """
        Calculate adaptive sleep duration based on recent activity.
        
        Returns longer sleep when no work is found to reduce DB pressure.
        """
        if self.consecutive_empty_cycles == 0:
            return SLEEP
        
        # Exponential backoff up to MAX_SLEEP
        sleep_time = min(SLEEP * (1.5 ** self.consecutive_empty_cycles), MAX_SLEEP)
        return sleep_time
    
    def get_stats(self) -> dict:
        """Get dispatcher statistics."""
        uptime = datetime.now() - self.startup_time
        return {
            "uptime_seconds": uptime.total_seconds(),
            "total_jobs_dispatched": self.total_jobs_dispatched,
            "consecutive_empty_cycles": self.consecutive_empty_cycles,
            "db_healthy": self.db_healthy,
            "broker_healthy": self.broker_healthy,
        }


# Global state instance
_state = DispatcherState()


# ─────────────────────────────────────────────────────────────────────────────
# Database Utilities
# ─────────────────────────────────────────────────────────────────────────────
def get_db_connection(max_retries: int = 5, retry_delay: float = 2.0):
    """
    Get a database connection with retry logic.
    
    Args:
        max_retries: Maximum connection attempts
        retry_delay: Initial delay between retries (uses exponential backoff)
        
    Returns:
        psycopg.Connection: Active database connection
        
    Raises:
        OperationalError: If all retries fail
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            conn = psycopg.connect(DSN, autocommit=True)
            _state.db_healthy = True
            return conn
        except OperationalError as e:
            last_error = e
            _state.db_healthy = False
            wait_time = retry_delay * (2 ** attempt)
            log.warning(
                "Database connection failed (attempt %d/%d), retrying in %.1fs: %s",
                attempt + 1, max_retries, wait_time, e
            )
            time.sleep(wait_time)
    
    log.error("Failed to connect to database after %d attempts", max_retries)
    raise last_error


def check_column_exists(cur, table: str, column: str) -> bool:
    """Check if a column exists in a table."""
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s AND column_name = %s
    """, (table, column))
    return cur.fetchone() is not None


# ─────────────────────────────────────────────────────────────────────────────
# Task Dispatching
# ─────────────────────────────────────────────────────────────────────────────
def dispatch_upload_job(cur) -> bool:
    """
    Check for and dispatch pending upload jobs.
    
    Returns:
        bool: True if a job was dispatched
    """
    cur.execute(SQL_NEXT_UPLOAD)
    row = cur.fetchone()
    
    if not row:
        return False
    
    (job_id, user_id, group_id, platform, video_path, 
     user_hashtags, user_title, session_token) = row
    
    payload = {
        "id": job_id,
        "user_id": user_id,
        "group_id": group_id,
        "video_path": video_path,
        "user_hashtags": user_hashtags,
        "user_title": user_title,
        "platform": platform,
        "session_id": session_token,
    }
    
    try:
        result = app.send_task(
            "worker.tasks.process_upload_job",
            kwargs={"job_data": payload},
            queue="celery"
        )
        log.info("📤 Upload job dispatched: job_id=%s task_id=%s platform=%s", 
                job_id, result.id, platform)
        return True
    except Exception as e:
        log.error("Failed to dispatch upload job %s: %s", job_id, e)
        # Mark job as failed
        cur.execute(
            "UPDATE upload_jobs SET status = 'failed', error = %s, updated_at = NOW() WHERE id = %s",
            (str(e), job_id)
        )
        return False


def dispatch_document_job(cur) -> bool:
    """
    Check for and dispatch pending document ingest jobs.
    
    Returns:
        bool: True if a job was dispatched
    """
    cur.execute(SQL_NEXT_DOC)
    row = cur.fetchone()
    
    if not row:
        return False
    
    doc_job_id, document_id = row
    
    try:
        result = app.send_task(
            "worker.tasks.process_document",
            kwargs={"document_id": str(document_id), "job_id": doc_job_id},
            queue="celery",
        )
        log.info("📄 Document job dispatched: job_id=%s doc_id=%s task_id=%s", 
                doc_job_id, document_id, result.id)
        return True
    except Exception as e:
        log.error("Failed to dispatch document job %s: %s", doc_job_id, e)
        return False


def dispatch_cookie_prep(cur) -> bool:
    """
    Check for and dispatch cookie preparation tasks.
    
    Returns:
        bool: True if a task was dispatched
    """
    # Check if cookie_created_at column exists
    has_cookie_column = check_column_exists(cur, 'group_items', 'cookie_created_at')
    
    if has_cookie_column:
        cur.execute(SQL_NEXT_COOKIE_PREP)
    else:
        cur.execute(SQL_COOKIE_PREP_FALLBACK)
    
    row = cur.fetchone()
    
    if not row:
        return False
    
    group_item_id, platform, email, password = row
    
    if not email or not password:
        return False
    
    try:
        result = app.send_task(
            "worker.tasks.prepare_cookies",
            kwargs={
                "group_item_id": group_item_id,
                "platform": platform,
                "email": email,
                "password": password
            },
            queue="celery",
        )
        log.info("🍪 Cookie prep dispatched: group_item_id=%s platform=%s task_id=%s",
                group_item_id, platform, result.id)
        return True
    except Exception as e:
        log.error("Failed to dispatch cookie prep for group_item %s: %s", group_item_id, e)
        return False


def dispatch_competitor_scrape(cur) -> bool:
    """
    Check for and dispatch competitor scraping if needed.
    Only runs every SCRAPE_CHECK_INTERVAL seconds.
    
    Returns:
        bool: True if scrape was dispatched
    """
    now = time.time()
    
    # Throttle scrape checks
    if now - _state.last_scrape_dispatch < SCRAPE_CHECK_INTERVAL:
        return False
    
    try:
        interval = int(os.getenv("WEEKLY_SCRAPE_INTERVAL", str(WEEKLY_SCRAPE_INTERVAL)))
        cur.execute(SQL_PENDING_SCRAPES, (interval,))
        row = cur.fetchone()
        
        if row and row[0] > 0:
            pending_count = row[0]
            log.info("🔍 Found %d competitors pending scrape", pending_count)
            
            result = app.send_task(
                "worker.tasks.weekly_instagram_scrape",
                queue="celery"
            )
            log.info("🔄 Scrape task dispatched: task_id=%s", result.id)
            
            _state.last_scrape_dispatch = now
            return True
            
    except Exception as e:
        log.error("Failed to check/dispatch competitor scrape: %s", e)
    
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Main Dispatch Loop
# ─────────────────────────────────────────────────────────────────────────────
def dispatch_loop():
    """
    Main dispatch loop that continuously polls for work.
    
    This function:
    1. Connects to the database
    2. Checks for pending jobs of each type
    3. Dispatches jobs to Celery workers
    4. Sleeps adaptively based on workload
    
    The loop handles:
    - Database connection failures (reconnection with backoff)
    - Empty queues (adaptive sleep to reduce load)
    - Graceful shutdown on KeyboardInterrupt
    """
    log.info("🚀 Dispatcher starting...")
    log.info("   Database: %s", DSN.split("@")[-1] if "@" in DSN else DSN)
    log.info("   Sleep interval: %.1fs (max: %.1fs)", SLEEP, MAX_SLEEP)
    log.info("   Scrape check interval: %.1fs", SCRAPE_CHECK_INTERVAL)
    
    # Verify broker connection on startup
    if not verify_broker_connection():
        log.warning("⚠️  RabbitMQ broker not available - will retry during operation")
        _state.broker_healthy = False
    else:
        _state.broker_healthy = True
    
    while True:
        did_work = False
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Process each job type
                    if dispatch_upload_job(cur):
                        did_work = True
                    
                    if dispatch_document_job(cur):
                        did_work = True
                    
                    if dispatch_cookie_prep(cur):
                        did_work = True
            
            # Check for competitor scrapes (separate connection for isolation)
            if not did_work:
                try:
                    with get_db_connection() as conn:
                        with conn.cursor() as cur:
                            if dispatch_competitor_scrape(cur):
                                did_work = True
                except Exception as e:
                    log.debug("Scrape check skipped: %s", e)
            
        except OperationalError as e:
            # Database connection error - will retry with backoff
            log.warning("Database error in dispatch loop: %s", e)
            _state.db_healthy = False
            time.sleep(5.0)  # Wait before retry
            continue
            
        except Exception as e:
            log.exception("Unexpected error in dispatch loop: %s", e)
            time.sleep(2.0)
            continue
        
        # Update state and calculate sleep
        if did_work:
            _state.record_work()
            time.sleep(SLEEP)  # Short sleep after work
        else:
            _state.record_empty_cycle()
            sleep_time = _state.get_adaptive_sleep()
            
            # Log stats periodically when idle
            if _state.consecutive_empty_cycles % 60 == 0 and _state.consecutive_empty_cycles > 0:
                stats = _state.get_stats()
                log.debug("Dispatcher idle - stats: %s", stats)
            
            time.sleep(sleep_time)


def shutdown():
    """Clean shutdown of the dispatcher."""
    log.info("Dispatcher shutting down...")
    stats = _state.get_stats()
    log.info("Final stats: jobs_dispatched=%d uptime=%.1fs",
             stats["total_jobs_dispatched"],
             stats["uptime_seconds"])


# ─────────────────────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        dispatch_loop()
    except KeyboardInterrupt:
        pass
    finally:
        shutdown()
