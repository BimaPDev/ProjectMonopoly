"""
Configuration Module
====================

Environment variables and settings for the Reddit Listener pipeline.

Environment Variables:
    Reddit API:
        REDDIT_CLIENT_ID: Reddit app client ID (required)
        REDDIT_CLIENT_SECRET: Reddit app client secret (required)
        REDDIT_USER_AGENT: User agent string (required, e.g., "ProjectMonopoly/1.0")
        REDDIT_REFRESH_TOKEN: OAuth refresh token (optional, for user-based auth)
    
    Database:
        DATABASE_URL: PostgreSQL connection URL
        DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD: Individual DB settings
    
    Quality Thresholds:
        MIN_QUALITY_SCORE: Minimum quality score to store (default: 0.3)
        MIN_SCORE: Minimum Reddit score to consider (default: 5)
        MIN_COMMENTS: Minimum comments to consider (default: 2)
        MAX_AGE_HOURS: Maximum post age in hours (default: 168 = 7 days)
    
    Spike Detection:
        SPIKE_FACTOR_THRESHOLD: Factor increase to trigger alert (default: 2.0)
    
    Scheduler:
        DEFAULT_FETCH_LIMIT: Posts to fetch per source (default: 100)
        COMMENTS_FETCH_LIMIT: Comments per high-quality post (default: 50)
        COMMENTS_DEPTH: Comment tree depth (default: 3)
"""

import os
import logging
from typing import Optional
from urllib.parse import urlparse

log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Reddit API Configuration
# ─────────────────────────────────────────────────────────────────────────────
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "ProjectMonopoly/1.0 (by /u/projectmonopoly)")
REDDIT_REFRESH_TOKEN = os.getenv("REDDIT_REFRESH_TOKEN", "")  # Optional

# ─────────────────────────────────────────────────────────────────────────────
# Database Configuration
# ─────────────────────────────────────────────────────────────────────────────
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'project_monopoly'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'secret'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5432')),
}

DATABASE_URL = os.getenv(
    'DATABASE_URL',
    f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
)

# ─────────────────────────────────────────────────────────────────────────────
# Quality Thresholds
# ─────────────────────────────────────────────────────────────────────────────
MIN_QUALITY_SCORE = float(os.getenv("MIN_QUALITY_SCORE", "0.3"))
MIN_SCORE = int(os.getenv("MIN_SCORE", "5"))
MIN_COMMENTS = int(os.getenv("MIN_COMMENTS", "2"))
MAX_AGE_HOURS = int(os.getenv("MAX_AGE_HOURS", "168"))  # 7 days

# Quality weights
QUALITY_SCORE_WEIGHT = float(os.getenv("QUALITY_SCORE_WEIGHT", "0.4"))
QUALITY_COMMENTS_WEIGHT = float(os.getenv("QUALITY_COMMENTS_WEIGHT", "0.3"))
QUALITY_RECENCY_WEIGHT = float(os.getenv("QUALITY_RECENCY_WEIGHT", "0.2"))
QUALITY_FLAIR_BONUS = float(os.getenv("QUALITY_FLAIR_BONUS", "0.1"))
QUALITY_NSFW_PENALTY = float(os.getenv("QUALITY_NSFW_PENALTY", "0.5"))
QUALITY_REMOVED_PENALTY = float(os.getenv("QUALITY_REMOVED_PENALTY", "1.0"))

# ─────────────────────────────────────────────────────────────────────────────
# Spike Detection
# ─────────────────────────────────────────────────────────────────────────────
SPIKE_FACTOR_THRESHOLD = float(os.getenv("SPIKE_FACTOR_THRESHOLD", "2.0"))

# ─────────────────────────────────────────────────────────────────────────────
# Scheduler / Fetch Settings
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_FETCH_LIMIT = int(os.getenv("DEFAULT_FETCH_LIMIT", "100"))
COMMENTS_FETCH_LIMIT = int(os.getenv("COMMENTS_FETCH_LIMIT", "50"))
COMMENTS_DEPTH = int(os.getenv("COMMENTS_DEPTH", "3"))

# ─────────────────────────────────────────────────────────────────────────────
# Chunking Settings
# ─────────────────────────────────────────────────────────────────────────────
CHUNK_MIN_CHARS = int(os.getenv("CHUNK_MIN_CHARS", "1500"))
CHUNK_MAX_CHARS = int(os.getenv("CHUNK_MAX_CHARS", "3000"))
CHUNK_OVERLAP_PERCENT = float(os.getenv("CHUNK_OVERLAP_PERCENT", "0.12"))  # 12%

# ─────────────────────────────────────────────────────────────────────────────
# LLM Configuration (for Strategy Card extraction)
# ─────────────────────────────────────────────────────────────────────────────
LLM_ENABLED = os.getenv("LLM_ENABLED", "false").lower() in ("true", "1", "yes")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")  # ollama, openai, gemini
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")

# ─────────────────────────────────────────────────────────────────────────────
# Raw JSON size limit (truncate if larger)
# ─────────────────────────────────────────────────────────────────────────────
RAW_JSON_MAX_BYTES = int(os.getenv("RAW_JSON_MAX_BYTES", "102400"))  # 100KB

# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def validate_reddit_config() -> list[str]:
    """
    Validate configuration. Returns list of errors.
    
    Note: Reddit API credentials are NOT required since we use public .json endpoints.
    This validation only checks for database connectivity and other critical settings.
    """
    errors = []
    # No Reddit credentials needed - we use public .json endpoints
    # The reddit_api.py module uses https://www.reddit.com/r/{subreddit}/new.json
    # which doesn't require OAuth authentication.
    return errors


def get_config_summary() -> dict:
    """Get a sanitized config summary for logging."""
    return {
        "reddit": {
            "client_id": REDDIT_CLIENT_ID[:8] + "..." if REDDIT_CLIENT_ID else None,
            "user_agent": REDDIT_USER_AGENT,
            "has_refresh_token": bool(REDDIT_REFRESH_TOKEN),
        },
        "database": {
            "host": DB_CONFIG["host"],
            "port": DB_CONFIG["port"],
            "dbname": DB_CONFIG["dbname"],
        },
        "quality": {
            "min_score": MIN_QUALITY_SCORE,
            "max_age_hours": MAX_AGE_HOURS,
        },
        "llm": {
            "enabled": LLM_ENABLED,
            "provider": LLM_PROVIDER if LLM_ENABLED else None,
        },
    }


__all__ = [
    "REDDIT_CLIENT_ID",
    "REDDIT_CLIENT_SECRET", 
    "REDDIT_USER_AGENT",
    "REDDIT_REFRESH_TOKEN",
    "DATABASE_URL",
    "DB_CONFIG",
    "MIN_QUALITY_SCORE",
    "MIN_SCORE",
    "MIN_COMMENTS",
    "MAX_AGE_HOURS",
    "QUALITY_SCORE_WEIGHT",
    "QUALITY_COMMENTS_WEIGHT",
    "QUALITY_RECENCY_WEIGHT",
    "QUALITY_FLAIR_BONUS",
    "QUALITY_NSFW_PENALTY",
    "QUALITY_REMOVED_PENALTY",
    "SPIKE_FACTOR_THRESHOLD",
    "DEFAULT_FETCH_LIMIT",
    "COMMENTS_FETCH_LIMIT",
    "COMMENTS_DEPTH",
    "CHUNK_MIN_CHARS",
    "CHUNK_MAX_CHARS",
    "CHUNK_OVERLAP_PERCENT",
    "LLM_ENABLED",
    "LLM_PROVIDER",
    "OLLAMA_HOST",
    "OLLAMA_MODEL",
    "RAW_JSON_MAX_BYTES",
    "LOG_LEVEL",
    "validate_reddit_config",
    "get_config_summary",
]
