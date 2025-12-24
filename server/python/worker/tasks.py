from .celery_app import app
#from socialmedia.tiktok import upload_tiktok_video
from socialmedia.instagram_post import upload_instagram_media
from .db import update_job_status  # keeps your existing upload status updates
from worker.config import UPLOADS_DIR  # e.g., "/data/uploads"
import os 
import logging
import hashlib
from .cookie_prep import prepare_cookies # preparing cookies for instagram 

# --- RAG deps ---
import psycopg
import fitz  # PyMuPDF

# DATABASE_URL like: postgresql://root:secret@db:5432/project_monopoly?sslmode=disable
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://root:secret@db:5432/project_monopoly?sslmode=disable")

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ---------- helpers ----------
def _resolve_local_path(rel_or_abs: str) -> str:
    """Accept absolute path or path under UPLOADS_DIR."""
    if os.path.isabs(rel_or_abs):
        return rel_or_abs
    # strip leading slashes and 'uploads/' if present
    p = rel_or_abs.lstrip("/")

    if p.startswith("uploads/"):
        p = p[len("uploads/"):]
    return os.path.join(UPLOADS_DIR, p)

def _sha1_text(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", "ignore")).hexdigest()

def _split_text(txt: str, size: int = 3000, overlap: int = 500):
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

## ---------- existing video upload task ----------
@app.task(name="worker.tasks.process_upload_job", queue="celery")
def process_upload_job(job_data):
    """Upload media to platform from local disk."""
    print(f"Running upload job: {job_data.get('id')} for {job_data.get('platform')}")
    try:
        job_id = job_data["id"]
        platform = job_data["platform"].lower()

        # Handle media_path - can be single file or list of files
        media_paths = job_data.get("media_path") or job_data.get("video_path")  # support both keys
        if not media_paths:
            raise ValueError("media_path or video_path is required")
        
        # Convert to list if single path
        if isinstance(media_paths, str):
            media_paths = [media_paths]
        elif not isinstance(media_paths, list):
            media_paths = [str(media_paths)]
        
        # Resolve all paths
        full_paths = []
        for rel_path in media_paths:
            full_path = _resolve_local_path(rel_path)
            if not os.path.exists(full_path):
                raise FileNotFoundError(f"Media not found at: {full_path}")
            full_paths.append(full_path)
        
        print(f"Posting {len(full_paths)} file(s) from: {full_paths}")

        # Build caption from title and hashtags
        title = (job_data.get("user_title") or "").strip()
        hashtags = job_data.get("user_hashtags") or []
        if not isinstance(hashtags, list):
            hashtags = []
        caption = (title + " " + " ".join(f"#{t}" for t in hashtags)).strip()

        print(f"Starting post for user {job_data['user_id']}, job {job_id}, platform: {platform}")

        # Determine headless mode (default to True for production)
        headless = job_data.get("headless", True)

        if platform == "instagram":
            # Use single path or list based on number of files
            media_path = full_paths[0] if len(full_paths) == 1 else full_paths
            upload_instagram_media(media_path, caption, headless=headless)
        elif platform == "tiktok":
            # TikTok requires session_id and single file
            if len(full_paths) > 1:
                raise ValueError("TikTok uploads support only one file at a time")
            session_id = job_data.get("session_id")
            if not session_id:
                raise ValueError("session_id is required for TikTok uploads")
            # Uncomment when TikTok upload is needed:
            # upload_tiktok_video(session_id, full_paths[0], caption)
            raise NotImplementedError("TikTok upload is currently disabled. Uncomment upload_tiktok_video import and call.")
        else:
            raise Exception(f"Unsupported platform: {platform}")

        update_job_status(job_id, "done", {"title": "", "hashtags": [], "post_time": None})
        print(f"Post complete for job {job_id}")
        return {"status": "success", "job_id": job_id, "files_uploaded": len(full_paths)}

    except Exception as e:
        print(f"Post failed for job {job_data.get('id')}: {str(e)}")
        log.exception("Upload job failed")
        try:
            update_job_status(job_data["id"], "failed", {"title": "", "hashtags": [], "post_time": None})
        except Exception:
            pass
        return {"status": "failed", "job_id": job_data.get("id"), "error": str(e)}

# ---------- NEW: PDF ingest for RAG ----------
@app.task(name="worker.tasks.process_document", queue="celery")
def process_document(document_id: str, job_id: int | None = None):
    """
    Ingest a PDF into workshop_chunks.
    Args:
      document_id: UUID from workshop_documents.id
      job_id: optional document_ingest_jobs.id to update status
    """
    log.info("Ingest start doc=%s job=%s", document_id, job_id)
    with psycopg.connect(DATABASE_URL, autocommit=False) as conn:
        try:
            with conn.cursor() as cur:
                # if a job row was created, mark processing
                if job_id is not None:
                    cur.execute(
                        "UPDATE document_ingest_jobs SET status='processing', updated_at=NOW() "
                        "WHERE id=%s AND status IN ('queued','processing')",
                        (job_id,),
                    )

                # fetch path + group
                cur.execute(
                    "SELECT storage_url, group_id FROM workshop_documents WHERE id=%s",
                    (document_id,),
                )
                row = cur.fetchone()
                if not row:
                    raise RuntimeError("document not found")
                storage_url, group_id = row
                if not storage_url:
                    raise RuntimeError("empty storage_url")
                path = storage_url if os.path.isabs(storage_url) else _resolve_local_path(storage_url)

            if not os.path.exists(path):
                raise FileNotFoundError(f"file not found: {path}")

            doc = fitz.open(path)
            pages = len(doc)

            with conn.cursor() as cur:
                chunk_index = 0
                for pno in range(pages):
                    text = doc[pno].get_text("text")
                    if not text:
                        continue
                    for piece in _split_text(text, size=3000, overlap=500):
                        content_sha = _sha1_text(piece)
                        token_count = len(piece.split())
                        cur.execute(
                            """
                            INSERT INTO workshop_chunks
                              (document_id, group_id, page, chunk_index, content, token_count, content_sha)
                            VALUES (%s,%s,%s,%s,%s,%s,%s)
                            ON CONFLICT ON CONSTRAINT workshop_chunk_dedupe DO NOTHING
                            """,
                            (document_id, group_id, pno + 1, chunk_index, piece, token_count, content_sha),
                        )
                        chunk_index += 1

                # mark doc done
                cur.execute(
                    "UPDATE workshop_documents SET status='ready', pages=%s, updated_at=NOW() WHERE id=%s",
                    (pages, document_id),
                )
                if job_id is not None:
                    cur.execute(
                        "UPDATE document_ingest_jobs SET status='done', updated_at=NOW() WHERE id=%s",
                        (job_id,),
                    )
            conn.commit()
            doc.close()
            log.info("Ingest done doc=%s pages=%d", document_id, pages)
            return {"status": "success", "document_id": document_id, "pages": pages}

        except Exception as e:
            conn.rollback()
            log.exception("Ingest failed")
            with psycopg.connect(DATABASE_URL) as c2, c2.cursor() as cur2:
                cur2.execute(
                    "UPDATE workshop_documents SET status='error', error=%s, updated_at=NOW() WHERE id=%s",
                    (str(e), document_id),
                )
                if job_id is not None:
                    cur2.execute(
                        "UPDATE document_ingest_jobs SET status='error', error=%s, updated_at=NOW() WHERE id=%s",
                        (str(e), job_id),
                    )
            return {"status": "failed", "document_id": document_id, "error": str(e)}

# ---------- NEW: Weekly Instagram Scraping ----------
@app.task(name="worker.tasks.weekly_instagram_scrape", queue="celery")
def weekly_instagram_scrape():
    """
    Weekly Instagram scraping task that processes all Instagram competitors
    that haven't been scraped in the last 7 days.
    """
    log.info("Starting weekly Instagram scraping task")
    
    try:
        # Imported here to avoid circular imports
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        
        from socialmedia.weekly_scraper import WeeklyInstagramScraper
        
        scraper = WeeklyInstagramScraper()
        scraper.run_weekly_scrape()
        
        log.info("Weekly Instagram scraping task completed successfully")
        return {"status": "success", "message": "Weekly Instagram scraping completed"}
        
    except Exception as e:
        log.exception("Weekly Instagram scraping failed")
        return {"status": "failed", "error": str(e)}

# ---------- Followers Scraping Task ----------
@app.task(name="worker.tasks.scrape_followers", queue="celery")
def scrape_followers():
    """
    Daily task to scrape follower counts from all social media platforms.
    """
    log.info("Starting followers scraping task")
    
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        
        from Followers.getFollowers import get_all_followers, insert_follower_count
        import datetime
        
        total_followers, platform_breakdown = get_all_followers()
        today = datetime.date.today()
        record_id = insert_follower_count(today, total_followers, platform_breakdown)
        
        log.info(f"Followers scraping completed: {total_followers:,} total followers (Record ID: {record_id})")
        return {
            "status": "success",
            "date": today.isoformat(),
            "total_followers": total_followers,
            "platform_breakdown": platform_breakdown,
            "record_id": record_id
        }
        
    except Exception as e:
        log.exception("Followers scraping failed")
        return {"status": "failed", "error": str(e)}

# ---------- AI Web Scraping Task ----------
@app.task(name="worker.tasks.ai_web_scrape", queue="celery")
def ai_web_scrape():
    """
    Task to scrape web content using AI web scraper for marketing and game dev content.
    """
    log.info("Starting AI web scraping task")
    
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        
        # Note: ai_scraper.main() may not return results, so we'll just execute it
        # and handle any results via file output or logging
        import importlib
        scraper_module = importlib.import_module('ai_web.ai_scraper')
        
        # Execute the main function if it exists
        if hasattr(scraper_module, 'main'):
            result = scraper_module.main()
        else:
            log.warning("ai_scraper module doesn't have a main() function")
            result = None
        
        log.info("AI web scraping completed successfully")
        return {"status": "success", "message": "AI web scraping completed", "result": result}
        
    except Exception as e:
        log.exception("AI web scraping failed")
        return {"status": "failed", "error": str(e)}

# ---------- Trends/Hashtag Scraping Task ----------
@app.task(name="worker.tasks.scrape_hashtag_trends", queue="celery")
def scrape_hashtag_trends():
    """
    Task to scrape trending hashtags from TikTok creative center.
    """
    log.info("Starting hashtag trends scraping task")
    
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        
        # Note: This needs to be updated to return results instead of just printing
        from trends.hashtag import scrape_hashtags
        
        trends = scrape_hashtags()
        
        log.info(f"Hashtag trends scraping completed: {len(trends) if trends else 0} trends found")
        return {"status": "success", "trends": trends}
        
    except Exception as e:
        log.exception("Hashtag trends scraping task failed")
        return {"status": "failed", "error": str(e)}




