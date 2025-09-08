import os
from celery import Celery

BROKER = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
BACKEND = os.getenv("CELERY_RESULT_BACKEND", BROKER)

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
    broker_transport_options={"visibility_timeout": 3600},  # Redis ack timeout
    result_expires=3600,
)
