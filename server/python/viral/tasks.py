"""
Viral Content Discovery Celery Tasks
=====================================

Celery tasks for viral content scanning and cleanup.

Tasks:
    - scan_viral_content: Run every 15 minutes to detect outliers
    - cleanup_expired_outliers: Run daily to remove expired records

Author: ProjectMonopoly Team
Created: 2026-01-01
"""

import logging
from celery import shared_task

from .outlier_detector import OutlierDetector

log = logging.getLogger(__name__)


@shared_task(
    name="viral.tasks.scan_viral_content",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=600,  # 10 minutes
    time_limit=900,  # 15 minutes hard limit
)
def scan_viral_content(self):
    """
    Scan for viral content outliers.
    
    This task:
    1. Acquires a lock to prevent overlapping runs
    2. Detects outliers using per-metric analysis
    3. Upserts results to the viral_outliers table
    4. Releases the lock
    
    Scheduled to run every 15 minutes via Celery Beat.
    
    Returns:
        dict: Scan results including outlier counts and status.
    """
    log.info("Starting viral content scan")
    
    try:
        detector = OutlierDetector()
        result = detector.run_scan()
        
        if result["status"] == "skipped":
            log.info(f"Viral scan skipped: {result['reason']}")
        else:
            log.info(
                f"Viral scan complete: found {result['outliers_found']} outliers "
                f"(100x: {result['by_multiplier']['100x']}, "
                f"50x: {result['by_multiplier']['50x']}, "
                f"10x: {result['by_multiplier']['10x']}, "
                f"5x: {result['by_multiplier']['5x']})"
            )
        
        return result
        
    except Exception as e:
        log.error(f"Viral content scan failed: {e}")
        raise self.retry(exc=e)


@shared_task(
    name="viral.tasks.cleanup_expired_outliers",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def cleanup_expired_outliers(self):
    """
    Remove expired viral outliers from the database.
    
    Scheduled to run daily at 3 AM UTC via Celery Beat.
    
    Returns:
        dict: Cleanup results with deleted count.
    """
    log.info("Starting expired outliers cleanup")
    
    try:
        detector = OutlierDetector()
        deleted = detector.cleanup_expired()
        
        log.info(f"Cleaned up {deleted} expired outliers")
        
        return {"status": "success", "deleted": deleted}
        
    except Exception as e:
        log.error(f"Outlier cleanup failed: {e}")
        raise self.retry(exc=e)
