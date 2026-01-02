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
import json
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
    - Caption and hashtag formatting
    - Platform-specific requirements
    
    Args:
        job_data: Job configuration dict containing:
            - id (int): Job ID in database
            - user_id (int): Owner user ID
            - platform (str): Target platform ('instagram', 'tiktok')
            - media_path (str|list): Path(s) to media file(s)
            - user_title (str, optional): Post title/caption
            - user_hashtags (list, optional): Hashtags to include
            - session_id (str, optional): TikTok session token
            - headless (bool, optional): Run browser headless (default: True)
    
    Returns:
        dict: Result containing:
            - status: 'success' or 'failed'
            - job_id: The job ID
            - files_uploaded: Number of files uploaded
            - error: Error message (if failed)
    
    Example:
        >>> process_upload_job.delay({
        ...     "id": 123,
        ...     "user_id": 1,
        ...     "platform": "instagram",
        ...     "media_path": "1/video.mp4",
        ...     "user_title": "Check this out!",
        ...     "user_hashtags": ["gaming", "indiedev"]
        ... })
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
        
        # Handle media_path - can be single file or list
        media_paths = job_data.get("media_path") or job_data.get("video_path")
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
        
        # Build caption
        title = (job_data.get("user_title") or "").strip()
        hashtags = job_data.get("user_hashtags") or []
        if not isinstance(hashtags, list):
            hashtags = []
        
        hashtag_str = " ".join(f"#{t}" for t in hashtags if t)
        caption = f"{title} {hashtag_str}".strip()
        
        # Headless mode (default True for production)
        headless = job_data.get("headless", True)
        
        log.info("Caption: %s (headless=%s)", caption[:50] + "..." if len(caption) > 50 else caption, headless)
        
        # Platform-specific upload
        if platform == "instagram":
            # Import here to avoid circular imports
            from socialmedia.instagram_post import upload_instagram_media
            
            # Use single path or list based on file count
            media_arg = full_paths[0] if len(full_paths) == 1 else full_paths
            upload_instagram_media(media_arg, caption, headless=headless)
            
        elif platform == "tiktok":
            # TikTok only supports single file uploads
            if len(full_paths) > 1:
                raise ValueError("TikTok uploads support only one file at a time")
            
            session_id = job_data.get("session_id")
            if not session_id:
                raise ValueError("session_id is required for TikTok uploads")
            
            # TikTok upload is currently disabled
            # from socialmedia.tiktok import upload_tiktok_video
            # upload_tiktok_video(session_id, full_paths[0], caption)
            raise NotImplementedError(
                "TikTok upload is currently disabled. "
                "Enable by uncommenting the import and function call."
            )
        else:
            raise ValueError(f"Unsupported platform: {platform}")
        
        # Update job status to done
        update_job_status(job_id, "done", {
            "title": title,
            "hashtags": hashtags,
            "post_time": datetime.now().isoformat()
        })
        
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
        
        # Update job status to failed
        try:
            update_job_status(job_id, "failed", {
                "title": "",
                "hashtags": [],
                "post_time": None
            }, error=error_msg)
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
        log.exception("Hashtag trends scraping task failed")
        return {"status": "failed", "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# State Management for Scheduling
# ─────────────────────────────────────────────────────────────────────────────
STATE_FILE = os.path.join(os.path.dirname(__file__), '..', 'scrape_state.json')

def get_last_scrape_time() -> datetime:
    """Read the last scrape timestamp from the state file."""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                data = json.load(f)
                # Handle cases where file might be empty or corrupted
                if data and 'last_scrape' in data:
                    return datetime.fromisoformat(data['last_scrape'])
    except Exception as e:
        log.error(f"Failed to read scrape state: {e}")
    
    # If no file or error, return a time far in the past to ensure first run
    return datetime.min

def update_last_scrape_time() -> None:
    """Update the state file with the current timestamp."""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump({
                'last_scrape': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }, f)
    except Exception as e:
        log.error(f"Failed to update scrape state: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Full Proxy Validation Task (runs every 3 hours at :00)
# ─────────────────────────────────────────────────────────────────────────────
@app.task(
    name="worker.tasks.validate_all_proxies_task",
    queue="celery",
    bind=True,
    max_retries=1,
    acks_late=True,
)
def validate_all_proxies_task(self) -> Dict[str, Any]:
    """
    Validates ALL proxies from all sources and stores working ones to a file.
    This is called every 3 hours by the beat scheduler.
    The scraper task (at :30) will then only pick from the verified list.
    """
    log.info("🔍 Starting scheduled FULL proxy validation...")
    
    try:
        from socialmedia.drivers.proxy_manager import proxy_manager
        
        working = proxy_manager.validate_all_proxies()
        
        return {
            "status": "success",
            "total_checked": len(proxy_manager.proxies),
            "working_count": len(working),
            "success_rate": f"{len(working)/max(len(proxy_manager.proxies),1)*100:.1f}%"
        }
    except Exception as e:
        log.exception("Full proxy validation failed")
        return {"status": "failed", "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# Proxy Refresh & Scheduled Scrape Task
@app.task(
    name="worker.tasks.refresh_proxies_and_scheduled_scrape",
    queue="celery",
    bind=True,
    max_retries=3,
    acks_late=True,
)
def refresh_proxies_and_scheduled_scrape(self) -> Dict[str, Any]:
    """
    Smart Scheduling Logic:
    1. Runs every 3 hours.
    2. Refreshes proxies.
    3. TRIGGER LOGIC:
       - IF proxies available -> Scrape (High Frequency Mode)
       - IF NO proxies -> Check if 12h passed since last scrape.
         - YES (>12h) -> Scrape using Local IP (Fallback Mode)
         - NO (<12h) -> Skip (Safety Mode)
    """
    log.info("🔄 Starting proxy refresh and scrape coordination task")
    
    try:
        # Import here to avoid circular dependencies if any
        from socialmedia.drivers.proxy_manager import proxy_manager
        
        # 1. Force refresh proxies
        log.info("1️⃣ forcing proxy refresh...")
        try:
            proxy_manager.refresh_proxies(force=True)
            proxy_count = len(proxy_manager.proxies)
            log.info(f"   → Proxy refresh complete. Available: {proxy_count}")

            # 2. Evaluate Trigger Logic
            should_scrape = False
            trigger_reason = ""
            
            last_scrape = get_last_scrape_time()
            time_since_scrape = datetime.now() - last_scrape
            hours_since_scrape = time_since_scrape.total_seconds() / 3600
            
            log.info(f"   ⏱️ Time since last scrape: {hours_since_scrape:.2f} hours")

            if proxy_count > 0:
                should_scrape = True
                trigger_reason = f"✅ Proxies available ({proxy_count})"
            elif hours_since_scrape >= 12:
                should_scrape = True
                trigger_reason = "⚠️ Fallback: No proxies but >12h since last run"
                log.warning("   ⚠️ No proxies found. Triggering 12h fallback using LOCAL IP.")
            else:
                should_scrape = False
                trigger_reason = "Skipping: No proxies and <12h since last scrape"

            if should_scrape:
                log.info(f"2️⃣ Triggering scrapers. Reason: {trigger_reason}")
                
                # Trigger Instagram Scrape
                try:
                    weekly_instagram_scrape.delay()
                    log.info("   → Triggered weekly_instagram_scrape")
                except Exception as e:
                    log.error(f"   ❌ Failed to trigger Instagram scrape: {e}")

                # Trigger TikTok Scrape
                try:
                    weekly_tiktok_scrape.delay()
                    log.info("   → Triggered weekly_tiktok_scrape")
                except Exception as e:
                     log.error(f"   ❌ Failed to trigger TikTok scrape: {e}")
                
                # Update state
                update_last_scrape_time()
                
                # Note: Proxy cleanup is now handled by the individual scrapers after they complete

                return {
                    "status": "success",
                    "message": f"Scrapers triggered: {trigger_reason}",
                    "proxy_count": proxy_count,
                    "mode": "proxy" if proxy_count > 0 else "fallback_local"
                }
            else:
                log.warning(f"🛑 {trigger_reason}")
                return {
                    "status": "skipped",
                    "message": trigger_reason,
                    "proxy_count": 0
                }

        except Exception as e:
            log.error(f"❌ Proxy refresh logic failed: {e}")
            raise

    except Exception as e:
        log.exception("❌ Proxy refresh task failed: %s", e)
        # Retry in 5 minutes if it was a network glitch fetching list
        raise self.retry(countdown=300)

# ---------- Instagram Hashtag Scraping Task ----------
@app.task(name="worker.tasks.scrape_instagram_hashtag", queue="celery")
def scrape_instagram_hashtag(hashtag, max_posts=50):
    log.info(f"Starting Instagram hashtag scraping task for #{hashtag}")
    
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        
        from socialmedia.instagram.scraper.profile_scraper import InstagramScraper
        
        # Get credentials from environment variables
        username = os.getenv("INSTAGRAM_USERNAME")
        password = os.getenv("INSTAGRAM_PASSWORD")
        
        scraper = InstagramScraper(username, password)
        
        # Attempt to login (which will handle guest mode if no creds)
        if not scraper.login():
            log.error("Failed to login to Instagram (even guest mode failed)")
            scraper.close()
            return {"status": "failed", "error": "Failed to login to Instagram"}
        
        # Scrape the hashtag
        posts_data = scraper.scrape_hashtag(hashtag, max_posts=max_posts)
        
        scraper.close()
        
        log.info(f"Instagram hashtag scraping completed: {len(posts_data)} posts scraped for #{hashtag}")
        return {
            "status": "success",
            "hashtag": hashtag,
            "posts_scraped": len(posts_data),
            "message": f"Successfully scraped {len(posts_data)} posts for #{hashtag}"
        }
        
    except Exception as e:
        log.exception(f"Instagram hashtag scraping failed for #{hashtag}")
        return {"status": "failed", "hashtag": hashtag, "error": str(e)}

# ---------- Hashtag Discovery Task ----------
# Hard limit for recursive iterations to prevent infinite loops
MAX_ITERATIONS_LIMIT = 10

@app.task(name="worker.tasks.discover_and_scrape_hashtags", queue="celery")
def discover_and_scrape_hashtags(user_id=None, group_id=None, max_hashtags=10, max_posts_per_hashtag=50, recursive=False, max_iterations=3):
    """
    Task to discover and scrape hashtags from competitor posts.
    
    Note:
        max_iterations is capped at 10 to prevent infinite scraping loops.
    """
    log.info("Starting hashtag discovery and scraping task")
    
    # Enforce hard limit at task level (defense in depth)
    if max_iterations > MAX_ITERATIONS_LIMIT:
        log.warning(f"Requested {max_iterations} iterations exceeds limit of {MAX_ITERATIONS_LIMIT}. Capping at {MAX_ITERATIONS_LIMIT}.")
        max_iterations = MAX_ITERATIONS_LIMIT
    
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        
        from socialmedia.hashtag.hashtag_discovery import HashtagDiscovery
        
        discovery = HashtagDiscovery(
            user_id=user_id,
            group_id=group_id,
            max_posts_per_hashtag=max_posts_per_hashtag
        )
        
        if recursive:
            log.info(f"Running recursive discovery (max_iterations={max_iterations}, hard_limit={MAX_ITERATIONS_LIMIT})")
            results = discovery.discover_and_scrape_recursive(
                max_iterations=max_iterations,
                max_hashtags_per_iteration=max_hashtags
            )
            log.info(f"Recursive discovery completed: {results['total_hashtags_scraped']} hashtags scraped across {results['iterations']} iterations, {results['total_posts_scraped']} total posts")
        else:
            results = discovery.scrape_new_hashtags(max_hashtags=max_hashtags)
            log.info(f"Hashtag discovery completed: {results['hashtags_scraped']} hashtags scraped, {results['total_posts_scraped']} total posts")
        
        return results
        
    except Exception as e:
        log.exception("Hashtag discovery task failed")
        return {"status": "failed", "error": str(e)}


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
    'scrape_instagram_hashtag',
    'discover_and_scrape_hashtags',
    'refresh_proxies_and_scheduled_scrape',
]
