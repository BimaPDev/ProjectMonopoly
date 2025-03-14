import psycopg2
from psycopg2 import pool
from celery import Celery
from tasks import manager#, analytics_worker  # ✅ Import both tasks

# Celery Configuration
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

#@app.task(queue="boss_queue")
#def boss_check_jobs():
#    """Fetch pending video upload jobs and analytics jobs."""
#    conn = get_db_connection()
#    cursor = conn.cursor()
#
#    # ✅ 1. Fetch video upload jobs
#    cursor.execute("""
#        SELECT id, user_id, platform, video_path, caption 
#        FROM upload_jobs 
#        WHERE status = 'pending'
#    """)
#    video_jobs = cursor.fetchall()
#
#    for job_id, user_id, platform, video_path, caption in video_jobs:
#        print(f"🎥 Assigning video upload job {job_id} ({platform}) to Manager...")
#        manager.delay(job_id, user_id, platform, video_path, caption)  # ✅ Send to Video Manager
#
#    # ✅ 2. Fetch users for analytics tasks
#    #cursor.execute("""
#    #    SELECT id, username, oauth_provider, oauth_id
#    #    FROM users
#    #    WHERE oauth_provider IS NOT NULL
#    #""")
#    #analytics_users = cursor.fetchall()
#
#    #for user_id, username, oauth_provider, oauth_id in analytics_users:
#    #    print(f"📊 Assigning analytics task for {username} on {oauth_provider}...")
#    #    analytics_worker.delay(user_id, username, oauth_provider, oauth_id)  # ✅ Send to Analytics Worker
#
#    cursor.close()
#    release_db_connection(conn)
#

@app.task(queue="boss_queue")
def boss_check_jobs():
    """Fetch pending video upload jobs and analytics jobs."""
    print("📢 Boss started checking for pending jobs...")

    conn = get_db_connection()
    cursor = conn.cursor()

    # ✅ Debug: Print if connection is successful
    print("✅ Connected to Database.")

    # ✅ 1. Fetch video upload jobs
    cursor.execute("""
        SELECT id, user_id, platform, video_path, caption 
        FROM upload_jobs 
        WHERE status = 'pending'
    """)
    video_jobs = cursor.fetchall()

    # ✅ Debug: Print job count
    print(f"🎥 Found {len(video_jobs)} pending video upload jobs.")

    for job_id, user_id, platform, video_path, caption in video_jobs:
        print(f"🎥 Assigning video upload job {job_id} ({platform}) to Manager...")
        manager.delay(job_id, user_id, platform, video_path, caption)  # ✅ Send to Video Manager

    cursor.close()
    release_db_connection(conn)
    print("✅ Boss finished job check.")
    boss_check_jobs.delay()
