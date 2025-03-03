from celery import Celery

# ✅ Use Redis or RabbitMQ as broker
app = Celery('tasks', broker='redis://localhost:6379/0', backend='rpc://')

@app.task
def upload_video(video_path):
    print(f"Uploading video: {video_path}")
    return f"Uploaded {video_path}"
