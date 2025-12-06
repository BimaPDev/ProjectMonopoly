import os
from celery import Celery

BROKER = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//")
BACKEND = os.getenv("CELERY_RESULT_BACKEND", "rpc://")

app = Celery("worker", broker=BROKER, backend=BACKEND, include=["worker.tasks"])

app.conf.update(
    task_default_queue="celery",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=os.getenv("TZ", "UTC"),
    enable_utc=True,

    # Reliability and throughput
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=200,
    # broker_transport_options={"visibility_timeout": 3600},  # Redis ack timeout
    result_expires=3600,
)

# Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'weekly-instagram-scrape': {
        'task': 'worker.tasks.weekly_instagram_scrape',
        'schedule': 60.0 * 60.0 * 24.0 * 7.0,  # Every 7 days (in seconds)
        'options': {
            'queue': 'celery',
            'priority': 5,  # Lower priority than urgent tasks
        }
    },
}
