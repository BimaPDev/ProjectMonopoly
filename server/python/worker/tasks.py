from .celery_app import app
from socialmedia.tiktok import upload_tiktok_video
# from ai import generate_ai_suggestions
from .db import update_job_status
from worker.config import UPLOADS_DIR
import os

@app.task(name="worker.tasks.process_upload_job", queue="celery")
def process_upload_job(job_data):
    print(f"👷 Running upload job: {job_data['id']} for {job_data['platform']}")
    try:
        job_id = job_data["id"]
        platform = job_data["platform"].lower()
        session_id = job_data["session_id"]
        
        
        # Use the correct full path
        rel_path = job_data["video_path"]  # e.g., "uploads/1/video.mp4"
        full_path = os.path.join(UPLOADS_DIR, os.path.relpath(rel_path, "uploads"))

        if not os.path.exists(full_path):
            raise FileNotFoundError(f"📁 Video not found at: {full_path}")

        print(f"📂 Uploading from: {full_path}")

        # Caption handling: title + hashtags
        title = job_data.get("user_title", "").strip()
        hashtags = job_data.get("user_hashtags", [])
        if not isinstance(hashtags, list):
            hashtags = []

        hashtag_str = " ".join([f"#{tag}" for tag in hashtags])
        caption = f"{title} {hashtag_str}".strip()

        print(f"🚀 Starting upload for user {job_data['user_id']}, job {job_id}, platform: {platform}")

        # AI logic (disabled for now)
        # ai = generate_ai_suggestions(video_path)

        if platform == "tiktok":
            upload_tiktok_video(session_id, full_path, caption)
        else:
            raise Exception(f"Unsupported platform: {platform}")

        update_job_status(job_id, "done", {
            "title": "",
            "hashtags": [],
            "post_time": None
        })

        print(f"✅ Upload complete for job {job_id}")
        return {"status": "success", "job_id": job_id}

    except Exception as e:
        print(f"❌ Upload failed for job {job_data['id']}: {str(e)}")
        update_job_status(job_data["id"], "failed", {
            "title": "",
            "hashtags": [],
            "post_time": None
        })
        return {"status": "failed", "job_id": job_data["id"], "error": str(e)}
