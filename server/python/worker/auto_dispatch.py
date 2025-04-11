import sys, os
import psycopg2
from worker.config import DB_CONFIG
from worker.tasks import process_upload_job
import time
import traceback

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def fetch_next_job_atomically(conn):
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                WITH next_job AS (
                    SELECT j.id
                    FROM upload_jobs j
                    JOIN groups g ON g.id = j.group_id AND g.user_id = j.user_id
                    JOIN group_items gi ON gi.group_id = j.group_id AND LOWER(gi.type) = LOWER(j.platform)
                    WHERE j.status = 'pending'
                      AND gi.data->>'token' IS NOT NULL
                    ORDER BY j.created_at
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                )
                UPDATE upload_jobs
                SET status = 'uploading',
                    updated_at = NOW()
                WHERE id = (SELECT id FROM next_job)
                RETURNING id, user_id, group_id, platform, video_path, user_hashtags, user_title;
            """)
            job = cur.fetchone()
            if not job:
                return None

            job_id, user_id, group_id, platform, video_path, hashtags, user_title = job

            # Fetch session_id separately
            cur.execute("""
                SELECT data->>'token'
                FROM group_items
                WHERE group_id = %s AND LOWER(type) = LOWER(%s)
                LIMIT 1;
            """, (group_id, platform))
            result = cur.fetchone()
            session_id = result[0] if result else None

            return {
                "id": job_id,
                "user_id": user_id,
                "group_id": group_id,
                "video_path": video_path,
                "user_hashtags": hashtags,
                "user_title": user_title,
                "platform": platform,
                "session_id": session_id
            }


def run_dispatch_loop():
    conn = psycopg2.connect(**DB_CONFIG)

    try:
        while True:
            try:
                job = fetch_next_job_atomically(conn)
                if not job:
                    print("📭 No jobs to dispatch. Sleeping...")
                    time.sleep(10)
                    continue

                print(f"🚀 Dispatching job {job['id']} for user {job['user_id']} on platform {job['platform']}")
                result = process_upload_job.delay(job)
                print(f"📨 Task sent to Celery: task_id={result.id}")

            except Exception as inner_e:
                print(f"🔥 Error dispatching a job: {inner_e}")
                print(traceback.format_exc())

    except Exception as e:
        print(f"❌ Dispatcher crashed: {e}")
        print(traceback.format_exc())

    finally:
        conn.close()


if __name__ == "__main__":
    print("🔁 Auto-dispatcher running...")
    run_dispatch_loop()
