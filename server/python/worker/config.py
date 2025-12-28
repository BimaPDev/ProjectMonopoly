"""
Configuration Module
====================

Centralized configuration for the ProjectMonopoly Python worker services.
All settings are loaded from environment variables with sensible defaults.

Environment Variables:
    Database:
        DB_NAME: Database name (default: project_monopoly)
        DB_USER: Database user (default: root)
        DB_PASSWORD: Database password (default: secret)
        DB_HOST: Database host (default: db for docker-compose)
        DB_PORT: Database port (default: 5432)
        DB_SSLMODE: SSL mode (default: disable)
        DATABASE_URL: Full PostgreSQL connection URL (overrides individual settings)
    
    Message Broker:
        CELERY_BROKER_URL: RabbitMQ connection URL
    
    Workers:
        CELERY_CONCURRENCY: Number of worker processes (default: 4)
        DISPATCH_SLEEP: Sleep interval for dispatcher loop (default: 1.0)
        WEEKLY_SCRAPE_INTERVAL: Days between scrapes (default: 7)
    
    Storage:
        UPLOADS_DIR: Directory for uploaded files
        DOCS_DIR: Directory for documents

Author: ProjectMonopoly Team
Last Updated: 2025-12-27
"""

import os
import logging
from typing import Optional
from urllib.parse import urlparse

log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Database Configuration
# ─────────────────────────────────────────────────────────────────────────────
# Individual DB settings (used if DATABASE_URL is not set)
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'project_monopoly'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'secret'),
    'host': os.getenv('DB_HOST', 'db'),  # Default to 'db' for docker-compose
    'port': int(os.getenv('DB_PORT', '5432')),
    'sslmode': os.getenv('DB_SSLMODE', 'disable')
}

# Full DATABASE_URL (takes precedence if set)
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}?sslmode={DB_CONFIG['sslmode']}"
)


def parse_database_url(url: str) -> dict:
    """
    Parse a PostgreSQL connection URL into its components.
    
    Args:
        url: PostgreSQL connection URL
        
    Returns:
        dict: Parsed components including host, port, dbname, user, password
        
    Example:
        >>> config = parse_database_url("postgresql://user:pass@host:5432/db")
        >>> print(config['host'])
        'host'
    """
    parsed = urlparse(url)
    return {
        'host': parsed.hostname or 'localhost',
        'port': parsed.port or 5432,
        'dbname': parsed.path.lstrip('/').split('?')[0] or 'project_monopoly',
        'user': parsed.username or 'root',
        'password': parsed.password or 'secret',
    }


# ─────────────────────────────────────────────────────────────────────────────
# RabbitMQ Configuration
# ─────────────────────────────────────────────────────────────────────────────
RABBITMQ_BROKER_URL = os.getenv(
    'CELERY_BROKER_URL',
    'amqp://guest:guest@rabbitmq:5672//'
)

# Connection retry settings for RabbitMQ
RABBITMQ_RETRY_SETTINGS = {
    'max_retries': int(os.getenv('RABBITMQ_MAX_RETRIES', '10')),
    'retry_delay': float(os.getenv('RABBITMQ_RETRY_DELAY', '2.0')),
    'retry_backoff': float(os.getenv('RABBITMQ_RETRY_BACKOFF', '1.5')),
    'max_delay': float(os.getenv('RABBITMQ_MAX_DELAY', '30.0')),
}


# ─────────────────────────────────────────────────────────────────────────────
# Worker Configuration
# ─────────────────────────────────────────────────────────────────────────────
# Celery worker concurrency
CELERY_CONCURRENCY = int(os.getenv('CELERY_CONCURRENCY', '4'))

# Dispatcher loop sleep interval (seconds)
DISPATCH_SLEEP = float(os.getenv('DISPATCH_SLEEP', '1.0'))

# Weekly scrape interval (days)
WEEKLY_SCRAPE_INTERVAL = int(os.getenv('WEEKLY_SCRAPE_INTERVAL', '7'))

# Maximum task execution time (seconds)
TASK_TIMEOUT = int(os.getenv('TASK_TIMEOUT', '600'))  # 10 minutes


# ─────────────────────────────────────────────────────────────────────────────
# Storage Configuration
# ─────────────────────────────────────────────────────────────────────────────
# Base directory: goes up TWO levels from /worker/config.py -> /python -> /server
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Uploads directory
UPLOADS_DIR = os.getenv('UPLOADS_DIR', os.path.join(BASE_DIR, "uploads"))

# Documents directory
DOCS_DIR = os.getenv('DOCS_DIR', os.path.join(BASE_DIR, "uploads", "docs"))

# Cookies directory (for session cookies)
COOKIES_DIR = os.getenv('COOKIES_DIR', os.path.join(os.path.dirname(__file__), "..", "cookies"))


# ─────────────────────────────────────────────────────────────────────────────
# Scraper Configuration
# ─────────────────────────────────────────────────────────────────────────────
# Instagram credentials (optional - for authenticated scraping)
INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME', '')
INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD', '')

# Chrome/Selenium settings
SELENIUM_HEADLESS = os.getenv('SELENIUM_HEADLESS', 'true').lower() in ('true', '1', 'yes')
SELENIUM_TIMEOUT = int(os.getenv('SELENIUM_TIMEOUT', '30'))


# ─────────────────────────────────────────────────────────────────────────────
# Logging Configuration
# ─────────────────────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_FORMAT = os.getenv('LOG_FORMAT', '%(asctime)s %(levelname)s %(name)s: %(message)s')


# ─────────────────────────────────────────────────────────────────────────────
# Validation Utilities
# ─────────────────────────────────────────────────────────────────────────────
def validate_config() -> list[str]:
    """
    Validate the current configuration and return a list of warnings.
    
    Returns:
        list: Warning messages for any configuration issues.
        
    Example:
        >>> warnings = validate_config()
        >>> if warnings:
        ...     for w in warnings:
        ...         print(f"Warning: {w}")
    """
    warnings = []
    
    # Check upload directory exists
    if not os.path.exists(UPLOADS_DIR):
        warnings.append(f"UPLOADS_DIR does not exist: {UPLOADS_DIR}")
    
    # Check docs directory exists
    if not os.path.exists(DOCS_DIR):
        warnings.append(f"DOCS_DIR does not exist: {DOCS_DIR}")
    
    # Check for default credentials (security warning)
    if DB_CONFIG['password'] == 'secret':
        warnings.append("Using default database password 'secret' - not recommended for production")
    
    if 'guest:guest' in RABBITMQ_BROKER_URL:
        warnings.append("Using default RabbitMQ credentials 'guest:guest' - not recommended for production")
    
    return warnings


def get_config_summary() -> dict:
    """
    Get a summary of the current configuration (with sensitive data masked).
    
    Returns:
        dict: Configuration summary safe for logging.
    """
    return {
        'database': {
            'host': DB_CONFIG['host'],
            'port': DB_CONFIG['port'],
            'dbname': DB_CONFIG['dbname'],
            'user': DB_CONFIG['user'],
            'password': '***' if DB_CONFIG['password'] else None,
        },
        'rabbitmq': {
            'url': RABBITMQ_BROKER_URL.split('@')[-1] if '@' in RABBITMQ_BROKER_URL else RABBITMQ_BROKER_URL,
        },
        'worker': {
            'concurrency': CELERY_CONCURRENCY,
            'dispatch_sleep': DISPATCH_SLEEP,
            'weekly_scrape_interval': WEEKLY_SCRAPE_INTERVAL,
        },
        'storage': {
            'uploads_dir': UPLOADS_DIR,
            'docs_dir': DOCS_DIR,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Export
# ─────────────────────────────────────────────────────────────────────────────
__all__ = [
    'DB_CONFIG',
    'DATABASE_URL',
    'RABBITMQ_BROKER_URL',
    'RABBITMQ_RETRY_SETTINGS',
    'CELERY_CONCURRENCY',
    'DISPATCH_SLEEP',
    'WEEKLY_SCRAPE_INTERVAL',
    'BASE_DIR',
    'UPLOADS_DIR',
    'DOCS_DIR',
    'COOKIES_DIR',
    'INSTAGRAM_USERNAME',
    'INSTAGRAM_PASSWORD',
    'SELENIUM_HEADLESS',
    'SELENIUM_TIMEOUT',
    'LOG_LEVEL',
    'LOG_FORMAT',
    'parse_database_url',
    'validate_config',
    'get_config_summary',
]
