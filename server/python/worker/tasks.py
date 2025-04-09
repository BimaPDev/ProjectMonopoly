from .celery_app import app
from socialmedia.tiktok import upload_tiktok_video
# from ai import generate_ai_suggestions
from .db import update_job_status

@app.task
def process_upload_job(job_data):
    try:
        job_id = job_data["id"]
        platform = job_data["platform"]
        session_id = job_data["session_id"]
        video_path = job_data["video_path"]
        caption = job_data["caption"]

        # ai = generate_ai_suggestions(video_path)

        if platform == "tiktok":
            upload_tiktok_video(session_id, video_path, caption)
        else:
            raise Exception(f"Unsupported platform: {platform}")

        update_job_status(job_id, "done", {
            "title": "",
            "hashtags": [],
            "post_time": None
        })
        return {"status": "success", "job_id": job_id}

    except Exception as e:
        update_job_status(job_data["id"], "failed", {
            "title": "",
            "hashtags": [],
            "post_time": None
        })
        return {"status": "failed", "job_id": job_data["id"], "error": str(e)}
