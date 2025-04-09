from celery import Celery
from .config import REDIS_BROKER_URL, REDIS_BACKEND_URL
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

app = Celery(
    'celery',
    broker=REDIS_BROKER_URL,
    backend=REDIS_BACKEND_URL,
    include=['worker.tasks']  # 👈 Tell Celery where to find your tasks
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)
