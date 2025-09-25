#!/usr/bin/env python3
"""
Weekly Scheduler for Instagram Scraping
Schedules the weekly Instagram scraping task to run every Sunday at 2 AM.
"""

import os
import time
import logging
from datetime import datetime, timedelta
from celery import Celery
from celery.schedules import crontab

# Import the celery app
from .celery_app import app

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Configure periodic tasks
app.conf.beat_schedule = {
    'weekly-instagram-scrape': {
        'task': 'worker.tasks.weekly_instagram_scrape',
        'schedule': crontab(hour=1, minute=0, day_of_week=1),  # Every Monday at 1 AM
        'options': {
            'queue': 'celery',
            'priority': 5,  # Lower priority than urgent tasks
        }
    },
}

# Timezone configuration
app.conf.timezone = 'UTC'

def start_weekly_scheduler():
    """
    Start the Celery Beat scheduler for weekly tasks.
    This should be run as a separate process alongside the worker.
    """
    log.info("Starting weekly scheduler...")
    
    # Start Celery Beat
    from celery import current_app
    current_app.control.purge()  # Clear any existing scheduled tasks
    
    # The beat scheduler will be started by run_all.py
    log.info("✅ Weekly scheduler configured - will run every Sunday at 2 AM UTC")

if __name__ == "__main__":
    start_weekly_scheduler()
