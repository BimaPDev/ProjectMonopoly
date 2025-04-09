import sys, os
import psycopg2
from worker.config import DB_CONFIG
from worker.tasks import process_upload_job
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def fetch_pending_jobs():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        SELECT
            j.id,
            j.user_id,
            j.group_id,
            j.video_path,
            j.caption,
            j.platform,
            gi.data->>'token' AS session_id
        FROM upload_jobs j
        JOIN groups g
          ON j.group_id = g.id AND j.user_id = g.user_id
        JOIN group_items gi
          ON gi.group_id = j.group_id AND gi.type = j.platform
        WHERE j.status = 'pending';
    """)

    jobs = cur.fetchall()
    cur.close()
    conn.close()
    return jobs



def dispatch_jobs():
    jobs = fetch_pending_jobs()
    print(f"📦 Found {len(jobs)} pending jobs with valid session_id.")

    for job in jobs:
        job_data = {
        "id": job[0],
        "user_id": job[1],
        "group_id": job[2],
        "video_path": job[3],
        "caption": job[4],
        "platform": job[5],
        "session_id": job[6],  # <- from group_items.data
    }


        print(f"🚀 Dispatching job {job_data['id']} for user {job_data['user_id']}")
        process_upload_job.delay(job_data)

if __name__ == "__main__":
    print("🔁 Auto-dispatcher running...")
    while True:
        dispatch_jobs()
        print("🕒 Sleeping for 10 seconds...")
        time.sleep(10)
