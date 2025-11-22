from .celery_app import app
# from socialmedia.tiktok import upload_tiktok_video
from .db import update_job_status  # keeps your existing upload status updates

import os
import logging
import hashlib
import socket
import time

# --- RAG deps ---
import psycopg
import fitz  # PyMuPDF

# Try to import config constants, but keep safe fallbacks
try:
    from worker.config import UPLOADS_DIR, DOCS_DIR  # e.g., "/data/uploads", "/data/docs"
except Exception:
    UPLOADS_DIR = os.getenv("UPLOADS_DIR", "/data/uploads")
    DOCS_DIR = os.getenv("DOCS_DIR", "/data/docs")

# DATABASE_URL like: postgresql://root:secret@postgres:5432/project_monopoly?sslmode=disable
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://root:secret@postgres:5432/project_monopoly?sslmode=disable"
)

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ---------- helpers ----------
def _resolve_upload_path(rel_or_abs: str) -> str:
    """Accept absolute path or path under UPLOADS_DIR."""
    if os.path.isabs(rel_or_abs):
        return rel_or_abs
    p = rel_or_abs.lstrip("/")
    if p.startswith("uploads/"):
        p = p[len("uploads/"):]
    return os.path.join(UPLOADS_DIR, p)

def _resolve_doc_path(rel_or_abs: str) -> str:
    """Accept absolute path or path under DOCS_DIR."""
    if os.path.isabs(rel_or_abs):
        return rel_or_abs
    p = rel_or_abs.lstrip("/")

    # normalize common legacy prefixes if backend stored them
    if p.startswith("uploads/"):
        p = p[len("uploads/"):]
    if p.startswith("docs/"):
        p = p[len("docs/"):]

    return os.path.join(DOCS_DIR, p)

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
# @app.task(name="worker.tasks.process_upload_job", queue="celery")
# def process_upload_job(job_data):
#     """Upload video to platform from local disk."""
#     print(f"Running upload job: {job_data.get('id')} for {job_data.get('platform')}")
#     try:
#         job_id = job_data["id"]
#         platform = job_data["platform"].lower()
#         session_id = job_data["session_id"]
#
#         rel_path = job_data["video_path"]  # can be 'uploads/1/video.mp4' or absolute
#         full_path = _resolve_upload_path(rel_path)
#
#         if not os.path.exists(full_path):
#             raise FileNotFoundError(f"Video not found at: {full_path}")
#         print(f"Uploading from: {full_path}")
#
#         title = (job_data.get("user_title") or "").strip()
#         hashtags = job_data.get("user_hashtags") or []
#         if not isinstance(hashtags, list):
#             hashtags = []
#         caption = (title + " " + " ".join(f"#{t}" for t in hashtags)).strip()
#
#         print(f"Starting upload for user {job_data['user_id']}, job {job_id}, platform: {platform}")
#
#         if platform == "tiktok":
#             upload_tiktok_video(session_id, full_path, caption)
#         else:
#             raise Exception(f"Unsupported platform: {platform}")
#
#         update_job_status(job_id, "done", {"title": "", "hashtags": [], "post_time": None})
#         print(f"Upload complete for job {job_id}")
#         return {"status": "success", "job_id": job_id}
#
#     except Exception as e:
#         print(f"Upload failed for job {job_data.get('id')}: {str(e)}")
#         try:
#             update_job_status(job_data["id"], "failed", {"title": "", "hashtags": [], "post_time": None})
#         except Exception:
#             pass
#         return {"status": "failed", "job_id": job_data.get("id"), "error": str(e)}

# ---------- NEW: PDF ingest for RAG ----------
@app.task(name="worker.tasks.process_document", queue="celery")
def process_document(document_id: str, job_id: int | None = None):
    """
    Ingest a PDF into workshop_chunks.
    Args:
      document_id: UUID from workshop_documents.id
      job_id: optional document_ingest_jobs.id to update status
    """
    log.info("ingest start doc=%s job=%s", document_id, job_id)

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

                # ---- IMPORTANT FIX ----
                # If DB has legacy absolute paths like /app/uploads/docs/...,
                # map them into DOCS_DIR (/data/docs) which is the shared volume.
                if os.path.isabs(storage_url):
                    if storage_url.startswith("/app/uploads/docs/"):
                        rel = storage_url[len("/app/uploads/docs/"):]
                        path = os.path.join(DOCS_DIR, rel)
                    else:
                        path = storage_url
                else:
                    path = _resolve_doc_path(storage_url)

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
            log.info("ingest done doc=%s pages=%d", document_id, pages)
            return {"status": "success", "document_id": document_id, "pages": pages}

        except Exception as e:
            conn.rollback()
            log.exception("ingest failed")
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
        log.exception("Weekly Instagram scraping task failed")
        return {"status": "failed", "error": str(e)}
