"""
Celery Tasks
============

All asynchronous tasks for the ProjectMonopoly worker system.
These tasks are dispatched via RabbitMQ and executed by Celery workers.

Task Categories:
    1. Upload Tasks: Media upload to social platforms (Instagram, TikTok)
    2. Document Tasks: PDF ingestion for RAG system
    3. Scraping Tasks: Competitor and follower data collection
    4. Cookie Tasks: Session cookie extraction and management

Task Design Principles:
    - Idempotent: Safe to retry without side effects
    - Self-contained: All dependencies resolved within task
    - Observable: Comprehensive logging for debugging
    - Resilient: Graceful error handling with status updates

Author: ProjectMonopoly Team
Last Updated: 2025-12-27
"""

import os
import sys
import logging
import hashlib
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date

import psycopg
import fitz  # PyMuPDF

from .celery_app import app
from .db import update_job_status, get_db_connection
from .config import UPLOADS_DIR, DATABASE_URL

# ─────────────────────────────────────────────────────────────────────────────
# Logging Configuration
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────
def _resolve_local_path(rel_or_abs: str) -> str:
    """
    Resolve a file path to an absolute path.
    
    Handles:
    - Absolute paths (returned as-is)
    - Relative paths (resolved under UPLOADS_DIR)
    - Paths with 'uploads/' prefix (stripped before resolution)
    
    Args:
        rel_or_abs: Relative or absolute file path
        
    Returns:
        str: Absolute file path
        
    Example:
        >>> _resolve_local_path("/data/file.mp4")
        '/data/file.mp4'
        >>> _resolve_local_path("uploads/1/video.mp4")
        '/app/uploads/1/video.mp4'
    """
    if not rel_or_abs:
        raise ValueError("Empty path provided")
    
    if os.path.isabs(rel_or_abs):
        return rel_or_abs
    
    # Strip leading slashes and 'uploads/' prefix
    p = rel_or_abs.lstrip("/")
    if p.startswith("uploads/"):
        p = p[len("uploads/"):]
    
    return os.path.join(UPLOADS_DIR, p)


def _sha1_text(s: str) -> str:
    """
    Generate SHA1 hash of text for deduplication.
    
    Args:
        s: Input text
        
    Returns:
        str: SHA1 hex digest
    """
    return hashlib.sha1(s.encode("utf-8", "ignore")).hexdigest()


def _split_text(txt: str, size: int = 3000, overlap: int = 500) -> List[str]:
    """
    Split text into overlapping chunks for RAG ingestion.
    
    Args:
        txt: Input text to split
        size: Maximum chunk size in characters
        overlap: Overlap between chunks for context continuity
        
    Returns:
        list: List of text chunks
        
    Note:
        Overlap ensures context is preserved across chunk boundaries,
        improving retrieval quality for RAG queries.
    """
    txt = (txt or "").strip()
    if not txt:
        return []
    
    out, i, n = [], 0, len(txt)
    while i < n:
        j = min(i + size, n)
        out.append(txt[i:j])
        if j == n:
            break
        i = max(0, j - overlap)
    
    return out


def _validate_media_paths(paths: List[str]) -> List[str]:
    """
    Validate and resolve media file paths.
    
    Args:
        paths: List of file paths to validate
        
    Returns:
        list: List of resolved absolute paths
        
    Raises:
        FileNotFoundError: If any file doesn't exist
        ValueError: If paths list is empty
    """
    if not paths:
        raise ValueError("No media paths provided")
    
    resolved = []
    for path in paths:
        full_path = _resolve_local_path(path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Media file not found: {full_path}")
        if not os.path.isfile(full_path):
            raise ValueError(f"Path is not a file: {full_path}")
        resolved.append(full_path)
    
    return resolved


# ─────────────────────────────────────────────────────────────────────────────
# Content Generation Task
# ─────────────────────────────────────────────────────────────────────────────
@app.task(
    name="worker.tasks.process_content_generation",
    queue="celery",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def process_content_generation(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate AI content for an upload job.
    
    This task:
    1. Aggregates all context (game, docs, competitors, Reddit)
    2. Generates caption, hook, and hashtags via LLM
    3. Calculates optimal posting time
    4. Updates job with AI content and sets status to needs_review
    
    Args:
        job_data: Job data containing:
            - id: Job ID
            - user_id: Owner user ID
            - group_id: Group ID
            - platform: Target platform
            
    Returns:
        dict: Result with status and generated content
    """
    job_id = job_data.get("id")
    user_id = job_data.get("user_id")
    group_id = job_data.get("group_id")
    platform = (job_data.get("platform") or "instagram").lower()
    
    log.info("🤖 Generating AI content: job_id=%s platform=%s", job_id, platform)
    
    try:
        from .context_aggregator import aggregate_context
        from .ai_content import generate_content
        
        # 1. Aggregate all context (tenant-scoped)
        context = aggregate_context(user_id, group_id, platform)
        
        if not context.has_data:
            raise RuntimeError("No game context available for content generation")
        
        # 2. Generate content via LLM
        content = generate_content(context, platform)
        
        if content.error:
            raise RuntimeError(f"Content generation failed: {content.error}")
        
        # 3. Calculate optimal posting time
        from datetime import datetime, timedelta
        import pytz
        
        # Use best posting day from competitor analysis
        best_day_map = {
            "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
            "Friday": 4, "Saturday": 5, "Sunday": 6
        }
        target_dow = best_day_map.get(context.best_posting_day, 2)  # Default Wednesday
        
        # Platform-specific times
        if platform == "instagram":
            post_hour = 19  # 7 PM
        elif platform == "tiktok":
            post_hour = 15  # 3 PM
        else:
            post_hour = 18  # 6 PM
        
        # Calculate next occurrence of target day
        now = datetime.now(pytz.UTC)
        days_ahead = (target_dow - now.weekday()) % 7
        if days_ahead == 0 and now.hour >= post_hour:
            days_ahead = 7  # Next week if today's slot passed
        
        optimal_time = now.replace(
            hour=post_hour, minute=0, second=0, microsecond=0
        ) + timedelta(days=days_ahead)
        
        # 4. Update job in database
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE upload_jobs
                    SET ai_title = %s,
                        ai_hook = %s,
                        ai_hashtags = %s,
                        ai_post_time = %s,
                        status = 'needs_review',
                        locked_at = NULL,
                        locked_by = NULL,
                        updated_at = NOW()
                    WHERE id = %s
                """, (
                    content.title,
                    content.hook,
                    content.hashtags,
                    optimal_time,
                    job_id
                ))
            conn.commit()
        
        log.info(
            "✅ AI content generated: job_id=%s hook=%s schedule=%s",
            job_id, content.hook[:30] + "..." if content.hook else "N/A", optimal_time
        )
        
        return {
            "status": "success",
            "job_id": job_id,
            "hook": content.hook,
            "hashtags": content.hashtags,
            "scheduled_for": optimal_time.isoformat(),
            "confidence": content.confidence
        }
        
    except Exception as e:
        error_msg = str(e)
        log.exception("❌ Content generation failed: job_id=%s error=%s", job_id, error_msg)
        
        # Update job status to failed
        try:
            with psycopg.connect(DATABASE_URL) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE upload_jobs
                        SET status = CASE WHEN retry_count >= max_retries THEN 'failed' ELSE 'queued' END,
                            error_message = %s,
                            error_at = NOW(),
                            retry_count = retry_count + 1,
                            locked_at = NULL,
                            locked_by = NULL,
                            updated_at = NOW()
                        WHERE id = %s
                    """, (error_msg, job_id))
                conn.commit()
        except Exception as update_error:
            log.error("Failed to update job status: %s", update_error)
        
        # Retry if within limits
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30 * (self.request.retries + 1))
        
        return {
            "status": "failed",
            "job_id": job_id,
            "error": error_msg
        }


# ─────────────────────────────────────────────────────────────────────────────
# Upload Task
# ─────────────────────────────────────────────────────────────────────────────
@app.task(
    name="worker.tasks.process_upload_job",
    queue="celery",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(ConnectionError, TimeoutError),
    acks_late=True,
)
def process_upload_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Upload media to a social media platform.
    
    This task handles:
    - Single file uploads
    - Multi-file carousel uploads (Instagram)
    - Caption building from AI content
    - Idempotency checks
    - Proper error state handling
    
    Args:
        job_data: Job configuration dict containing job details
    
    Returns:
        dict: Result containing status and upload info
    """
    job_id = job_data.get("id")
    platform = (job_data.get("platform") or "").lower()
    
    log.info("📤 Processing upload job: id=%s platform=%s", job_id, platform)
    
    try:
        # Validate required fields
        if not job_id:
            raise ValueError("job_data must contain 'id'")
        if not platform:
            raise ValueError("job_data must contain 'platform'")
        
        # Idempotency check: re-fetch job and verify status is 'posting'
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT status, ai_title, ai_hook, ai_hashtags, video_path
                    FROM upload_jobs WHERE id = %s
                """, (job_id,))
                row = cur.fetchone()
                if not row:
                    log.warning("Job not found: %s", job_id)
                    return {"status": "skipped", "job_id": job_id, "reason": "not_found"}
                
                current_status, ai_title, ai_hook, ai_hashtags, video_path = row
                
                if current_status != "posting":
                    log.info("Job status is '%s', not 'posting'. Skipping.", current_status)
                    return {"status": "skipped", "job_id": job_id, "reason": f"status={current_status}"}
        
        # Handle media_path
        media_paths = job_data.get("media_path") or job_data.get("video_path") or video_path
        if not media_paths:
            raise ValueError("media_path or video_path is required")
        
        # Normalize to list
        if isinstance(media_paths, str):
            media_paths = [media_paths]
        elif not isinstance(media_paths, list):
            media_paths = [str(media_paths)]
        
        # Validate and resolve paths
        full_paths = _validate_media_paths(media_paths)
        log.info("Uploading %d file(s): %s", len(full_paths), full_paths)
        
        # Build caption: prefer ai_title, fallback to ai_hook, append hashtags
        caption_parts = []
        if ai_title:
            caption_parts.append(ai_title)
        elif ai_hook:
            caption_parts.append(ai_hook)
        
        # Append hashtags
        if ai_hashtags and isinstance(ai_hashtags, list):
            hashtag_str = " ".join(f"#{t}" for t in ai_hashtags if t and not t.startswith("#"))
            if hashtag_str:
                caption_parts.append(hashtag_str)
        
        caption = " ".join(caption_parts).strip()
        if not caption:
            caption = job_data.get("user_title", "") or "Check this out!"
        
        # Headless mode (default True for production)
        headless = job_data.get("headless", True)
        
        log.info("Caption: %s (headless=%s)", caption[:50] + "..." if len(caption) > 50 else caption, headless)
        
        # Platform-specific upload
        if platform == "instagram":
            from socialmedia.instagram_post import upload_instagram_media
            
            media_arg = full_paths[0] if len(full_paths) == 1 else full_paths
            upload_instagram_media(media_arg, caption, headless=headless)
            
        elif platform == "tiktok":
            if len(full_paths) > 1:
                raise ValueError("TikTok uploads support only one file at a time")
            
            session_id = job_data.get("session_id")
            if not session_id:
                raise ValueError("session_id is required for TikTok uploads")
            
            raise NotImplementedError("TikTok upload is currently disabled.")
        else:
            raise ValueError(f"Unsupported platform: {platform}")
        
        # Update job status to posted, clear errors
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE upload_jobs
                    SET status = 'posted',
                        error_message = NULL,
                        error_at = NULL,
                        locked_at = NULL,
                        locked_by = NULL,
                        updated_at = NOW()
                    WHERE id = %s
                """, (job_id,))
            conn.commit()
        
        log.info("✅ Upload complete: job_id=%s files=%d", job_id, len(full_paths))
        
        return {
            "status": "success",
            "job_id": job_id,
            "files_uploaded": len(full_paths),
            "platform": platform
        }
        
    except Exception as e:
        error_msg = str(e)
        log.exception("❌ Upload failed: job_id=%s error=%s", job_id, error_msg)
        
        # Detect auth/cookie errors
        is_auth_error = any(x in error_msg.lower() for x in ["cookie", "login", "auth", "session", "expired"])
        
        try:
            with psycopg.connect(DATABASE_URL) as conn:
                with conn.cursor() as cur:
                    if is_auth_error:
                        # MarkJobNeedsReauth semantics
                        cur.execute("""
                            UPDATE upload_jobs
                            SET status = 'needs_reauth',
                                needs_reauth = true,
                                error_message = %s,
                                error_at = NOW(),
                                locked_at = NULL,
                                locked_by = NULL,
                                updated_at = NOW()
                            WHERE id = %s
                        """, (error_msg, job_id))
                    else:
                        # MarkJobPostingFailed: retry to scheduled if retries remain
                        cur.execute("""
                            UPDATE upload_jobs
                            SET status = CASE WHEN retry_count >= max_retries THEN 'failed' ELSE 'scheduled' END,
                                error_message = %s,
                                error_at = NOW(),
                                retry_count = retry_count + 1,
                                locked_at = NULL,
                                locked_by = NULL,
                                updated_at = NOW()
                            WHERE id = %s
                        """, (error_msg, job_id))
                conn.commit()
        except Exception as update_error:
            log.error("Failed to update job status: %s", update_error)
        
        return {
            "status": "failed",
            "job_id": job_id,
            "error": error_msg
        }


# ─────────────────────────────────────────────────────────────────────────────
# Document Processing Task
# ─────────────────────────────────────────────────────────────────────────────
@app.task(
    name="worker.tasks.process_document",
    queue="celery",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    acks_late=True,
)
def process_document(
    self,
    document_id: str,
    job_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Ingest a PDF document into the RAG system.
    
    This task:
    1. Fetches document metadata from workshop_documents
    2. Extracts text from each page using PyMuPDF
    3. Splits text into overlapping chunks
    4. Stores chunks in workshop_chunks with deduplication
    5. Updates document and job status
    
    Args:
        document_id: UUID from workshop_documents.id
        job_id: Optional document_ingest_jobs.id to update status
        
    Returns:
        dict: Result containing:
            - status: 'success' or 'failed'
            - document_id: The document UUID
            - pages: Number of pages processed
            - chunks: Number of chunks created
            - error: Error message (if failed)
    
    Example:
        >>> process_document.delay(
        ...     document_id="550e8400-e29b-41d4-a716-446655440000",
        ...     job_id=42
        ... )
    """
    log.info("📄 Processing document: doc_id=%s job_id=%s", document_id, job_id)
    
    try:
        with psycopg.connect(DATABASE_URL, autocommit=False) as conn:
            try:
                with conn.cursor() as cur:
                    # Mark job as processing
                    if job_id is not None:
                        cur.execute(
                            """
                            UPDATE document_ingest_jobs 
                            SET status = 'processing', updated_at = NOW()
                            WHERE id = %s AND status IN ('queued', 'processing')
                            """,
                            (job_id,)
                        )
                    
                    # Fetch document metadata
                    cur.execute(
                        "SELECT storage_url, group_id FROM workshop_documents WHERE id = %s",
                        (document_id,)
                    )
                    row = cur.fetchone()
                    
                    if not row:
                        raise RuntimeError(f"Document not found: {document_id}")
                    
                    storage_url, group_id = row
                    if not storage_url:
                        raise RuntimeError("Document has empty storage_url")
                    
                    # Resolve file path
                    path = storage_url if os.path.isabs(storage_url) else _resolve_local_path(storage_url)
                
                # Validate file exists
                if not os.path.exists(path):
                    raise FileNotFoundError(f"PDF file not found: {path}")
                
                # Process PDF
                doc = fitz.open(path)
                pages = len(doc)
                chunk_count = 0
                
                log.info("Extracting text from %d pages: %s", pages, path)
                
                with conn.cursor() as cur:
                    for page_num in range(pages):
                        text = doc[page_num].get_text("text")
                        if not text or not text.strip():
                            continue
                        
                        chunks = _split_text(text, size=3000, overlap=500)
                        
                        for chunk_index, piece in enumerate(chunks):
                            content_sha = _sha1_text(piece)
                            token_count = len(piece.split())
                            
                            cur.execute(
                                """
                                INSERT INTO workshop_chunks
                                    (document_id, group_id, page, chunk_index, content, token_count, content_sha)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT ON CONSTRAINT workshop_chunk_dedupe DO NOTHING
                                """,
                                (document_id, group_id, page_num + 1, chunk_index, piece, token_count, content_sha)
                            )
                            chunk_count += 1
                    
                    # Mark document as ready
                    cur.execute(
                        """
                        UPDATE workshop_documents 
                        SET status = 'ready', pages = %s, updated_at = NOW() 
                        WHERE id = %s
                        """,
                        (pages, document_id)
                    )
                    
                    # Mark job as done
                    if job_id is not None:
                        cur.execute(
                            """
                            UPDATE document_ingest_jobs 
                            SET status = 'done', updated_at = NOW() 
                            WHERE id = %s
                            """,
                            (job_id,)
                        )
                
                conn.commit()
                doc.close()
                
                log.info("✅ Document processed: doc_id=%s pages=%d chunks=%d", 
                        document_id, pages, chunk_count)
                
                return {
                    "status": "success",
                    "document_id": document_id,
                    "pages": pages,
                    "chunks": chunk_count
                }
                
            except Exception as e:
                conn.rollback()
                raise
                
    except Exception as e:
        error_msg = str(e)
        log.exception("❌ Document processing failed: doc_id=%s error=%s", document_id, error_msg)
        
        # Update status to error
        try:
            with psycopg.connect(DATABASE_URL) as error_conn:
                with error_conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE workshop_documents 
                        SET status = 'error', error = %s, updated_at = NOW() 
                        WHERE id = %s
                        """,
                        (error_msg, document_id)
                    )
                    
                    if job_id is not None:
                        cur.execute(
                            """
                            UPDATE document_ingest_jobs 
                            SET status = 'error', error = %s, updated_at = NOW() 
                            WHERE id = %s
                            """,
                            (error_msg, job_id)
                        )
                error_conn.commit()
        except Exception as update_error:
            log.error("Failed to update error status: %s", update_error)
        
        return {
            "status": "failed",
            "document_id": document_id,
            "error": error_msg
        }


# ─────────────────────────────────────────────────────────────────────────────
# Weekly Instagram Scraping Task
# ─────────────────────────────────────────────────────────────────────────────
@app.task(
    name="worker.tasks.weekly_instagram_scrape",
    queue="celery",
    bind=True,
    max_retries=1,
    soft_time_limit=1800,  # 30 minute soft limit
    time_limit=2100,       # 35 minute hard limit
    acks_late=True,
)
def weekly_instagram_scrape(self) -> Dict[str, Any]:
    """
    Scrape Instagram competitors that haven't been updated recently.
    
    This task:
    1. Queries for competitors with stale or missing data
    2. Initializes the Instagram scraper
    3. Scrapes profile data & posts for each competitor
    4. Stores results in database
    5. Updates last_checked timestamps
    
    Returns:
        dict: Result containing:
            - status: 'success' or 'failed'
            - message: Description of outcome
            - competitors_scraped: Count (if successful)
            - error: Error message (if failed)
    
    Note:
        This task is resource-intensive and uses undetected-chromedriver
        to bypass bot detection. It should be scheduled during low-traffic hours.
    """
    log.info("🔄 Starting weekly Instagram scraping task")
    
    try:
        # Add parent directory to path for imports
        parent_dir = os.path.join(os.path.dirname(__file__), '..')
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        from socialmedia.instagram.scraper.weekly_scheduler import WeeklyInstagramScraper
        
        scraper = WeeklyInstagramScraper()
        result = scraper.run_weekly_scrape()
        
        log.info("✅ Weekly Instagram scraping completed successfully")
        
        return {
            "status": "success",
            "message": "Weekly Instagram scraping completed",
            "result": result
        }
        
    except Exception as e:
        error_msg = str(e)
        log.exception("❌ Weekly Instagram scraping failed: %s", error_msg)
        
        # Retry on specific recoverable errors
        if "Connection" in error_msg or "Timeout" in error_msg:
            raise self.retry(countdown=300, max_retries=1)
        
        return {
            "status": "failed",
            "error": error_msg
        }


# ─────────────────────────────────────────────────────────────────────────────
# Weekly TikTok Scraping Task
# ─────────────────────────────────────────────────────────────────────────────
@app.task(
    name="worker.tasks.weekly_tiktok_scrape",
    queue="celery",
    bind=True,
    max_retries=1,
    soft_time_limit=1800,  # 30 minute soft limit
    time_limit=2100,       # 35 minute hard limit
    acks_late=True,
)
def weekly_tiktok_scrape(self) -> Dict[str, Any]:
    """
    Scrape TikTok competitors that haven't been updated recently.
    
    This task:
    1. Queries for TikTok competitors with stale or missing data
    2. Initializes the TikTok scraper (guest mode, no login required)
    3. Scrapes profile data & posts for each competitor
    4. Stores results in database
    5. Updates last_checked timestamps
    
    Returns:
        dict: Result containing:
            - status: 'success' or 'failed'
            - message: Description of outcome
            - scraped: Number of competitors scraped (if successful)
            - error: Error message (if failed)
    
    Note:
        This task uses SeleniumBase CDP mode with xvfb for headless scraping.
        TikTok blocks true headless Chrome, so a virtual display is used.
    """
    log.info("🔄 Starting weekly TikTok scraping task")
    
    try:
        # Add parent directory to path for imports
        parent_dir = os.path.join(os.path.dirname(__file__), '..')
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        from socialmedia.tiktok.scraper.weekly_scheduler import WeeklyTikTokScraper
        
        scraper = WeeklyTikTokScraper()
        result = scraper.run_weekly_scrape()
        
        log.info("✅ Weekly TikTok scraping completed successfully")
        
        return {
            "status": "success",
            "message": "Weekly TikTok scraping completed",
            "result": result
        }
        
    except Exception as e:
        error_msg = str(e)
        log.exception("❌ Weekly TikTok scraping failed: %s", error_msg)
        
        # Retry on specific recoverable errors
        if "Connection" in error_msg or "Timeout" in error_msg:
            raise self.retry(countdown=300, max_retries=1)
        
        return {
            "status": "failed",
            "error": error_msg
        }


# ─────────────────────────────────────────────────────────────────────────────
# Followers Scraping Task
# ─────────────────────────────────────────────────────────────────────────────
@app.task(
    name="worker.tasks.scrape_followers",
    queue="celery",
    bind=True,
    max_retries=2,
    default_retry_delay=300,
    acks_late=True,
)
def scrape_followers(self) -> Dict[str, Any]:
    """
    Scrape follower counts from all configured social media platforms.
    
    This task:
    1. Fetches follower counts from each platform
    2. Calculates total and per-platform breakdown
    3. Stores daily snapshot in database
    4. Supports historical trend analysis
    
    Returns:
        dict: Result containing:
            - status: 'success' or 'failed'
            - date: Date of the snapshot
            - total_followers: Total follower count
            - platform_breakdown: Dict of platform -> count
            - record_id: Database record ID
            - error: Error message (if failed)
    """
    log.info("👥 Starting followers scraping task")
    
    try:
        # Add parent directory to path
        parent_dir = os.path.join(os.path.dirname(__file__), '..')
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        from Followers.getFollowers import get_all_followers, insert_follower_count
        
        total_followers, platform_breakdown = get_all_followers()
        today = date.today()
        record_id = insert_follower_count(today, total_followers, platform_breakdown)
        
        log.info("✅ Followers scraping completed: %s total followers (record_id=%s)",
                f"{total_followers:,}", record_id)
        
        return {
            "status": "success",
            "date": today.isoformat(),
            "total_followers": total_followers,
            "platform_breakdown": platform_breakdown,
            "record_id": record_id
        }
        
    except ImportError as e:
        log.warning("Followers module not available: %s", e)
        return {
            "status": "skipped",
            "error": f"Module not available: {e}"
        }
        
    except Exception as e:
        error_msg = str(e)
        log.exception("❌ Followers scraping failed: %s", error_msg)
        return {
            "status": "failed",
            "error": error_msg
        }


# ─────────────────────────────────────────────────────────────────────────────
# AI Web Scraping Task
# ─────────────────────────────────────────────────────────────────────────────
@app.task(
    name="worker.tasks.ai_web_scrape",
    queue="celery",
    bind=True,
    max_retries=1,
    soft_time_limit=600,
    time_limit=900,
    acks_late=True,
)
def ai_web_scrape(self) -> Dict[str, Any]:
    """
    Scrape web content using AI-powered scraper for marketing and game dev content.
    
    Returns:
        dict: Result containing:
            - status: 'success', 'skipped', or 'failed'
            - message: Description
            - result: Scraper output (if any)
            - error: Error message (if failed)
    """
    log.info("🤖 Starting AI web scraping task")
    
    try:
        # Add parent directory to path
        parent_dir = os.path.join(os.path.dirname(__file__), '..')
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        # Dynamic import (module uses PascalCase filename)
        import importlib
        scraper_module = importlib.import_module('ai_web.AiScraper')
        
        # Execute main function if available
        if hasattr(scraper_module, 'main'):
            result = scraper_module.main()
            log.info("✅ AI web scraping completed")
            return {
                "status": "success",
                "message": "AI web scraping completed",
                "result": result
            }
        else:
            log.warning("AiScraper module doesn't have a main() function")
            return {
                "status": "skipped",
                "message": "AiScraper.main() not found"
            }
        
    except ImportError as e:
        log.warning("AI scraper module not available: %s", e)
        return {
            "status": "skipped",
            "error": f"Module not available: {e}"
        }
        
    except Exception as e:
        error_msg = str(e)
        log.exception("❌ AI web scraping failed: %s", error_msg)
        return {
            "status": "failed",
            "error": error_msg
        }


# ─────────────────────────────────────────────────────────────────────────────
# Hashtag Trends Scraping Task
# ─────────────────────────────────────────────────────────────────────────────
@app.task(
    name="worker.tasks.scrape_hashtag_trends",
    queue="celery",
    bind=True,
    max_retries=2,
    default_retry_delay=180,
    acks_late=True,
)
def scrape_hashtag_trends(self) -> Dict[str, Any]:
    """
    Scrape trending hashtags from TikTok Creative Center.
    
    Returns:
        dict: Result containing:
            - status: 'success', 'skipped', or 'failed'
            - trends: List of trending hashtags
            - count: Number of trends found
            - error: Error message (if failed)
    """
    log.info("#️⃣ Starting hashtag trends scraping task")
    
    try:
        # Add parent directory to path
        parent_dir = os.path.join(os.path.dirname(__file__), '..')
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        # Note: Original file has typo 'hastag.py' instead of 'hashtag.py'
        from trends.hastag import scrape_hashtags
        
        trends = scrape_hashtags()
        count = len(trends) if trends else 0
        
        log.info("✅ Hashtag trends scraping completed: %d trends found", count)
        
        return {
            "status": "success",
            "trends": trends,
            "count": count
        }
        
    except ImportError as e:
        log.warning("Hashtag trends module not available: %s", e)
        return {
            "status": "skipped",
            "error": f"Module not available: {e}"
        }
        
    except Exception as e:
        error_msg = str(e)
        log.exception("❌ Hashtag trends scraping failed: %s", error_msg)
        return {
            "status": "failed",
            "error": error_msg
        }


# ─────────────────────────────────────────────────────────────────────────────
# Export
# ─────────────────────────────────────────────────────────────────────────────
__all__ = [
    'process_upload_job',
    'process_document',
    'weekly_instagram_scrape',
    'weekly_tiktok_scrape',
    'scrape_followers',
    'ai_web_scrape',
    'scrape_hashtag_trends',
]
