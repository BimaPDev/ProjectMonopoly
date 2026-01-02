#!/usr/bin/env python3
"""
Weekly Scheduler Configuration
==============================

Configures Celery Beat periodic task schedules for automated tasks.
This module defines when recurring tasks are executed.

Scheduled Tasks:
    1. Weekly Instagram Scrape: Scrapes competitor data every Monday at 1 AM UTC
    2. Daily Followers Scrape: Collects follower counts every day at 3 AM UTC
    3. Hashtag Trends: Scrapes trending hashtags twice daily

Schedule Configuration:
    Schedules use crontab syntax:
    - minute: 0-59
    - hour: 0-23
    - day_of_week: 0-6 (0=Sunday, 1=Monday, etc.)
    - day_of_month: 1-31
    - month_of_year: 1-12

Usage:
    This module is imported by celery_app.py to configure beat_schedule.
    Do not run this module directly.

Author: ProjectMonopoly Team
Last Updated: 2025-12-27
"""

import os
import logging
from datetime import timedelta
from celery.schedules import crontab

from .celery_app import app
from .config import HASHTAG_DISCOVERY_INTERVAL

# ─────────────────────────────────────────────────────────────────────────────
# Logging Configuration
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Timezone Configuration
# ─────────────────────────────────────────────────────────────────────────────
TIMEZONE = os.getenv("TZ", "UTC")
app.conf.timezone = TIMEZONE

# ─────────────────────────────────────────────────────────────────────────────
# Schedule Definitions
# ─────────────────────────────────────────────────────────────────────────────
# Note: These schedules are merged with those in celery_app.py
# If there are duplicates, this file's schedules take precedence when imported last

BEAT_SCHEDULES = {
    # ─────────────────────────────────────────────────────────────────────────
    # Weekly Instagram Scraping
    # Runs every Monday at 1:00 AM UTC
    # ─────────────────────────────────────────────────────────────────────────
    'weekly-instagram-scrape-cron': {
        'task': 'worker.tasks.weekly_instagram_scrape',
        'schedule': crontab(
            hour=1,
            minute=0,
            day_of_week=1  # Monday
        ),
        'options': {
            'queue': 'celery',
            'priority': 5,
        },
        'description': 'Weekly Instagram competitor scraping - Mondays 1 AM UTC'
    },
    
    # ─────────────────────────────────────────────────────────────────────────
    # Daily Follower Count
    # Runs every day at 3:00 AM UTC
    # ─────────────────────────────────────────────────────────────────────────
    'daily-followers-cron': {
        'task': 'worker.tasks.scrape_followers',
        'schedule': crontab(
            hour=3,
            minute=0
        ),
        'options': {
            'queue': 'low_priority',
            'priority': 3,
        },
        'description': 'Daily follower count scraping - 3 AM UTC'
    },
    
    # ─────────────────────────────────────────────────────────────────────────
    # Hashtag Trends (Twice Daily)
    # Runs at 8 AM and 8 PM UTC
    # ─────────────────────────────────────────────────────────────────────────
    'hashtag-trends-morning': {
        'task': 'worker.tasks.scrape_hashtag_trends',
        'schedule': crontab(
            hour=8,
            minute=0
        ),
        'options': {
            'queue': 'low_priority',
            'priority': 2,
        },
        'description': 'Morning hashtag trends scraping - 8 AM UTC'
    },
    'hashtag-trends-evening': {
        'task': 'worker.tasks.scrape_hashtag_trends',
        'schedule': crontab(
            hour=20,
            minute=0
        ),
        'options': {
            'queue': 'low_priority',
            'priority': 2,
        },
        'description': 'Evening hashtag trends scraping - 8 PM UTC'
    },
    
    # ─────────────────────────────────────────────────────────────────────────
    # Recursive Hashtag Discovery (TikTok)
    # Runs every X hours (default 5)
    # ─────────────────────────────────────────────────────────────────────────
    'hashtag-discovery-tiktok-recursive': {
        'task': 'worker.tasks.discover_and_scrape_hashtags',
        'schedule': timedelta(hours=HASHTAG_DISCOVERY_INTERVAL),
        'kwargs': {
            'platform': 'tiktok',
            'recursive': True,
            'max_iterations': 3,
            'max_posts_per_hashtag': 10
        },
        'options': {
            'queue': 'celery',
            'priority': 4,
        },
        'description': f'Recursive TikTok hashtag discovery - Every {HASHTAG_DISCOVERY_INTERVAL} hours'
    },
}


def configure_schedules():
    """
    Apply the schedule configuration to the Celery app.
    
    This merges our schedules with any existing schedules in the app.
    """
    existing = app.conf.beat_schedule or {}
    merged = {**existing, **BEAT_SCHEDULES}
    app.conf.beat_schedule = merged
    
    log.info("✅ Weekly scheduler configured with %d tasks:", len(BEAT_SCHEDULES))
    for name, config in BEAT_SCHEDULES.items():
        desc = config.get('description', 'No description')
        log.info("   - %s: %s", name, desc)


def get_schedule_info() -> dict:
    """
    Get information about configured schedules.
    
    Returns:
        dict: Schedule information including task names and timing
    """
    schedules = []
    
    for name, config in BEAT_SCHEDULES.items():
        schedule = config.get('schedule')
        
        # Format schedule for display
        if isinstance(schedule, crontab):
            schedule_str = f"cron({schedule._orig_minute}, {schedule._orig_hour}, {schedule._orig_day_of_week})"
        else:
            schedule_str = str(schedule)
        
        schedules.append({
            'name': name,
            'task': config.get('task'),
            'schedule': schedule_str,
            'queue': config.get('options', {}).get('queue', 'celery'),
            'description': config.get('description', '')
        })
    
    return {
        'timezone': TIMEZONE,
        'schedules': schedules
    }


def start_weekly_scheduler():
    """
    Initialize the weekly scheduler.
    
    This function is called when the module is run directly or imported
    to ensure schedules are properly configured.
    
    Note:
        Celery Beat is started separately by run_all.py.
        This function only configures the schedules.
    """
    log.info("Initializing weekly scheduler...")
    configure_schedules()
    log.info("✅ Weekly scheduler ready - Celery Beat will execute schedules")


# ─────────────────────────────────────────────────────────────────────────────
# Auto-configure on import
# ─────────────────────────────────────────────────────────────────────────────
configure_schedules()


# ─────────────────────────────────────────────────────────────────────────────
# Entry Point (for testing)
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    start_weekly_scheduler()
    
    # Print schedule info
    info = get_schedule_info()
    print(f"\nTimezone: {info['timezone']}")
    print("\nConfigured schedules:")
    for s in info['schedules']:
        print(f"  - {s['name']}")
        print(f"    Task: {s['task']}")
        print(f"    Schedule: {s['schedule']}")
        print(f"    Queue: {s['queue']}")
        print(f"    Description: {s['description']}")
        print()
