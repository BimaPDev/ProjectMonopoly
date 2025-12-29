"""
Celery Application Configuration
================================

Configures the Celery distributed task queue for ProjectMonopoly.

Environment Variables:
    CELERY_BROKER_URL: RabbitMQ connection URL (default: amqp://guest:guest@localhost:5672//)
    CELERY_RESULT_BACKEND: Result backend URL (default: rpc://)

Usage:
    from worker.celery_app import app
    
    @app.task
    def my_task():
        pass

Author: ProjectMonopoly Team
Last Updated: 2025-12-27
"""

import os
import logging
from celery import Celery

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Broker and Backend Configuration
# ─────────────────────────────────────────────────────────────────────────────
BROKER = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//")
BACKEND = os.getenv("CELERY_RESULT_BACKEND", "rpc://")

log.info("Initializing Celery with broker: %s", BROKER.split("@")[-1] if "@" in BROKER else BROKER)

# ─────────────────────────────────────────────────────────────────────────────
# Celery App Instance
# ─────────────────────────────────────────────────────────────────────────────
app = Celery(
    "worker",
    broker=BROKER,
    backend=BACKEND,
    include=["worker.tasks", "worker.cookie_prep"]  # Include all task modules
)

# ─────────────────────────────────────────────────────────────────────────────
# Core Celery Configuration
# ─────────────────────────────────────────────────────────────────────────────
app.conf.update(
    # Default queue and routing
    task_default_queue="celery",
    task_default_exchange="celery",
    task_default_routing_key="celery",
    
    # Serialization settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone settings
    timezone=os.getenv("TZ", "UTC"),
    enable_utc=True,
    
    # ─────────────────────────────────────────────────────────────────────────
    # Reliability Settings
    # ─────────────────────────────────────────────────────────────────────────
    # Acknowledge task AFTER completion (prevents task loss on worker crash)
    task_acks_late=True,
    
    # Prefetch only 1 task at a time (prevents task hoarding)
    worker_prefetch_multiplier=1,
    
    # Restart worker after N tasks (prevents memory leaks)
    worker_max_tasks_per_child=200,
    
    # Result expiration (1 hour)
    result_expires=3600,
    
    # ─────────────────────────────────────────────────────────────────────────
    # Connection Settings
    # ─────────────────────────────────────────────────────────────────────────
    # Retry connection on startup
    broker_connection_retry_on_startup=True,
    
    # Task time limit (10 minutes soft, 15 minutes hard)
    task_soft_time_limit=600,
    task_time_limit=900,
    
    # Track task state
    task_track_started=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Beat Schedule (Periodic Tasks)
# ─────────────────────────────────────────────────────────────────────────────
app.conf.beat_schedule = {
    # Weekly Instagram scraping - runs every 7 days
    'weekly-instagram-scrape': {
        'task': 'worker.tasks.weekly_instagram_scrape',
        'schedule': 60.0 * 60.0 * 24.0 * 7.0,  # Every 7 days (in seconds)
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Connection Verification
# ─────────────────────────────────────────────────────────────────────────────
def verify_broker_connection() -> bool:
    """
    Verify that the RabbitMQ broker is reachable.
    
    Returns:
        bool: True if connection is successful, False otherwise.
    """
    try:
        conn = app.connection()
        conn.ensure_connection(max_retries=3)
        conn.release()
        log.info("✅ RabbitMQ broker connection verified")
        return True
    except Exception as e:
        log.error("❌ Failed to connect to RabbitMQ broker: %s", e)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Export
# ─────────────────────────────────────────────────────────────────────────────
__all__ = ["app", "verify_broker_connection"]
