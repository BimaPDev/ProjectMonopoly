from celery import Celery

# Initialize Celery app
app = Celery('tasks', broker='pyamqp://guest@localhost//', backend='rpc://')

@app.task
def upload_video(video_path):
    print(f"Uploading video: {video_path}")
    return f"Uploaded {video_path}"
