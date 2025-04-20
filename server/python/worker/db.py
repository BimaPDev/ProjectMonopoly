import psycopg2
from .config import DB_CONFIG

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def update_job_status(job_id, status, ai):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE upload_jobs
        SET status = %s,
            ai_title = %s,
            ai_hashtags = %s,
            ai_post_time = %s,
            updated_at = now()
        WHERE id = %s
    """, (
        status,
        ai.get("title"),
        ai.get("hashtags"),
        ai.get("post_time"),
        job_id
    ))
    conn.commit()
    cur.close()
    conn.close()
