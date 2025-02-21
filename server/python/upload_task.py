import psycopg2
from celery import Celery
import subprocess



# Configure Celery with Redis
celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",  # Redis as broker
    backend="redis://localhost:6379/0"  # Store job results
)


DB_CONN = "dbname=yourdb user=youruser password=yourpassword host=localhost"

