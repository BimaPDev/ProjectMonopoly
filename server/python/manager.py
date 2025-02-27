import time
import psycopg2
from celery.result import AsyncResult
from celery import Celery
from tasks import upload_video

# Database connection configuration
DB_CONFIG = {
    "dbname": "project_monopoly",
    "user": "root",
    "password": "secret",
    "host": "localhost",
    "port": "5432",
}

def connect_db():
    #"""Connect to the PostgreSQL database."""
    #try:
    #    conn = psycopg2.connect(**DB_CONFIG)
    #    return conn
    #except Exception as e:
    #    print(f"Error connecting to database: {e}")
    #    return None
    return psycopg2.connect(**DB_CONFIG)

def get_task():
    connect = psycopg2.connect(**DB_CONFIG)
    cursor = connect.cursor()
    cursor.execute("SELECT id, user_id, video_path FROM upload_jobs WHERE status = 'pending'")
    jobs = cursor.fetchall() 
    cursor.close()
    connect.close()
    return jobs

def update_status(job_id, status, task_id=None):
    connect = psycopg2.connect(**DB_CONFIG)
    cursor = connect.cursor()
    cursor.execute(
        "UPDATE upload_jobs SET status = %s WHERE id = %s",
        (status, job_id),
    )
    connect.commit()
    cursor.close()
    connect.close()
    
def run(job_id, user_id, video_path):
    """Check running jobs and update their statuses."""
    print(f"Running job: {job_id} for user: {user_id}, video: {video_path}")
    update_status(job_id, "running")
    
    time.sleep(5)  # Simulating work (e.g., video processing)

    # Mark job as "completed"
    update_status(job_id, "completed")
    print(f"Job {job_id} completed!")
    

def manage_loop():
    """Continuously checks for new jobs and assigns them."""
    while True:
        jobs = get_task()  # Get pending jobs
        if jobs:
            for job in jobs:
                job_id, user_id, video_path = job
                run(job_id, user_id, video_path)
        
        time.sleep(5)  # Adjust interval as needed

if __name__ == "__main__":
    manage_loop()
