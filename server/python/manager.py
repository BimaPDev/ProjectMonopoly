import subprocess
import psycopg2
from psycopg2 import pool
from celery import Celery

app = Celery("tasks", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0")

# Database Connection Pool
DB_POOL = pool.SimpleConnectionPool(
    minconn=1, maxconn=10,
    dbname="project_monopoly",
    user="root",
    password="secret",
    host="localhost",
    port="5432",
)

def get_db_connection():
    return DB_POOL.getconn()

def release_db_connection(conn):
    DB_POOL.putconn(conn)

@app.task(queue="manager_queue")
def manager(job_id, user_id, video_path, caption):
    """Fetch session token and execute TikTok script."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Fetch session token
        cursor.execute("SELECT session_token FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        if not result:
            raise Exception(f"No session token found for user {user_id}")

        session_id = result[0]

        # Update job status to "processing"
        cursor.execute("UPDATE upload_jobs SET status = 'processing' WHERE id = %s", (job_id,))
        conn.commit()
        release_db_connection(conn)  # Release DB before calling script

        # Run the standalone TikTok script
        print(f"📢 Running TikTok upload script for job {job_id}...")
        process = subprocess.run(
            ["python3", "tiktok_uploader.py", "--sessionid", session_id, "--video", video_path, "--caption", caption],
            capture_output=True,
            text=True
        )

        # Capture script output
        print(f"📜 TikTok script output: {process.stdout}")
        print(f"⚠️ TikTok script errors: {process.stderr}")

        # Check if script succeeded
        if process.returncode == 0:
            status = "completed"
        else:
            status = "failed"

        # Update job status
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE upload_jobs SET status = %s WHERE id = %s", (status, job_id))
        conn.commit()

    except Exception as e:
        print(f"❌ Error in Manager for job {job_id}: {str(e)}")

    finally:
        cursor.close()
        release_db_connection(conn)
