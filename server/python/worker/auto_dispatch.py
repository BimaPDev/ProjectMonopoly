import os, time, logging
import psycopg
from worker.celery_app import app

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
DSN = os.getenv("DATABASE_URL", "postgresql://root:secret@db:5432/project_monopoly?sslmode=disable")
SLEEP = float(os.getenv("DISPATCH_SLEEP", "1.0"))

SQL_NEXT_UPLOAD = """
WITH next AS (
  SELECT j.id, j.user_id, j.group_id, j.platform, j.video_path,
         j.user_hashtags, j.user_title,
         gi.data->>'token' AS session_token
  FROM upload_jobs j
  JOIN groups g ON g.id = j.group_id AND g.user_id = j.user_id
  JOIN group_items gi
    ON gi.group_id = j.group_id
   AND LOWER(gi.platform) = LOWER(j.platform)      -- FIX: platform, not type
  WHERE j.status = 'pending'
    AND gi.data ? 'token' AND COALESCE(gi.data->>'token','') <> ''
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

def dispatch_loop():
    while True:
        did_work = False
        try:
            with psycopg.connect(DSN, autocommit=True) as conn, conn.cursor() as cur:
                # Upload job
                cur.execute(SQL_NEXT_UPLOAD)
                row = cur.fetchone()
                if row:
                    (job_id, user_id, group_id, platform,
                     video_path, user_hashtags, user_title, session_token) = row
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
                    res = app.send_task("worker.tasks.process_upload_job", kwargs={"job_data": payload}, queue="celery")
                    logging.info("upload job queued job_id=%s task_id=%s", job_id, res.id)
                    did_work = True

                # Document ingest job
                cur.execute(SQL_NEXT_DOC)
                row = cur.fetchone()
                if row:
                    doc_job_id, document_id = row
                    res = app.send_task(
                        "worker.tasks.process_document",
                        kwargs={"document_id": str(document_id), "job_id": doc_job_id},
                        queue="celery",
                    )
                    logging.info("doc job queued job_id=%s doc_id=%s task_id=%s", doc_job_id, document_id, res.id)
                    did_work = True

        except Exception as e:
            logging.exception("dispatcher error: %s", e)

        if not did_work:
            time.sleep(SLEEP)

if __name__ == "__main__":
    logging.info("dispatcher starting")
    dispatch_loop()
