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
def manager(job_id, user_id, platform, video_path, caption):
    """Fetch session token and execute the correct social media script."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Fetch user session token
        cursor.execute("SELECT session_token FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        if not result:
            raise Exception(f"No session token found for user {user_id}")

        session_id = result[0]

        # Update job status to "processing"
        cursor.execute("UPDATE upload_jobs SET status = 'processing', updated_at = NOW() WHERE id = %s", (job_id,))
        conn.commit()
        release_db_connection(conn)

        # Platform-Specific Execution
        platform_scripts = {
            "TikTok": "tiktok_uploader.py",
            "Instagram": "instagram_uploader.py",
            "Facebook": "facebook_uploader.py"
        }

        if platform not in platform_scripts:
            raise Exception(f"Unsupported platform: {platform}")

        script_to_run = platform_scripts[platform]

        # Run the correct script
        print(f"📢 Running {platform} upload script for job {job_id}...")
        process = subprocess.run(
            ["python3", script_to_run, "--sessionid", session_id, "--video", video_path, "--caption", caption],
            capture_output=True,
            text=True
        )

        # Capture script output
        print(f"📜 {platform} script output: {process.stdout}")
        print(f"⚠️ {platform} script errors: {process.stderr}")

        # Check if script succeeded
        status = "completed" if process.returncode == 0 else "failed"

        # Update job status
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE upload_jobs SET status = %s, updated_at = NOW() WHERE id = %s", (status, job_id))
        conn.commit()

    except Exception as e:
        print(f"❌ Error in Manager for job {job_id}: {str(e)}")

    finally:
        cursor.close()
        release_db_connection(conn)
