"""
Worker Package
==============

Celery worker module for ProjectMonopoly background task processing.
"""

# Version
__version__ = "1.0.0"

# Expose Celery app
from .celery_app import app

# Task imports will be done by Celery autodiscover
