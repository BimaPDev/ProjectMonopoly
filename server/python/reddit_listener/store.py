"""
Database Storage Module
=======================

Upsert operations for Reddit data with ON CONFLICT handling.
Implements Safe JSON pruning to keep raw_json valid and small.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional, Any, Dict
from contextlib import contextmanager

import psycopg
from psycopg.types.json import Jsonb

from .config import DATABASE_URL, RAW_JSON_MAX_BYTES

log = logging.getLogger(__name__)


@contextmanager
def get_connection():
    """Get a database connection context manager."""
    conn = psycopg.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def prune_raw_json(raw_json: Any, max_nested_depth: int = 2) -> Optional[Dict]:
    """
    Prune raw JSON to keep it valid and small.
    
    Instead of truncating the string, we selectively keep important fields
    and discard potentially huge ones like 'all_awardings', 'variants', etc.
    """
    if not isinstance(raw_json, dict):
        return None
    
    # Safe subset of keys to keep for Reddit objects
    # This prevents storing massive unexpected payloads
    SAFE_KEYS = {
        # Common
        "id", "name", "created_utc", "permalink", "url", "score",
        "ups", "downs", "upvote_ratio", "num_comments", "over_18",
        # Text/Content
        "title", "selftext", "body", "link_flair_text", "author_flair_text",
        # Author
        "author", "author_fullname", "is_submitter",
        # Metadata
        "subreddit", "subreddit_id", "domain", "is_self", "is_video",
        "post_hint", "whitelist_status", "parent_id", "link_id",
        # Tree
        "depth", "replies" # Replies usually handled separately but kept if small
    }
    
    pruned = {}
    for k, v in raw_json.items():
        if k in SAFE_KEYS:
            # Recursively prune dictionaries to avoid huge nested structures
            if isinstance(v, dict) and max_nested_depth > 0:
                 pruned[k] = prune_raw_json(v, max_nested_depth - 1)
            elif isinstance(v, list):
                # For lists, only keep a few items and ensure they are simple
                if len(v) > 0 and isinstance(v[0], (str, int, float, bool, type(None))):
                    pruned[k] = v[:10]  # Keep first 10 simple items
                else:
                    pruned[k] = []  # Discard complex lists (like awardings)
            else:
                pruned[k] = v
                
    return pruned


# ═══════════════════════════════════════════════════════════════════════════════
# Source Operations
# ═══════════════════════════════════════════════════════════════════════════════

def create_source(
    user_id: int,
    source_type: str,
    value: str,
    group_id: Optional[int] = None,
    subreddit: Optional[str] = None,
) -> int:
    """
    Create a new Reddit source.
    
    Normalizes inputs:
    - value and subreddit converted to lowercase
    - empty subreddit converted to None
    
    Returns the source ID.
    """
    # Normalize inputs
    value = value.lower().strip()
    if subreddit:
        subreddit = subreddit.lower().strip()
        if not subreddit:
            subreddit = None
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO reddit_sources (user_id, group_id, type, value, subreddit, enabled)
                VALUES (%s, %s, %s, %s, %s, TRUE)
                ON CONFLICT DO NOTHING
                RETURNING id
                """,
                (user_id, group_id, source_type, value, subreddit)
            )
            result = cur.fetchone()
            
            if result:
                return result[0]
            
            # If conflict, fetch existing ID
            if group_id is None:
                query = """
                    SELECT id FROM reddit_sources 
                    WHERE user_id=%s AND group_id IS NULL AND type=%s AND value=%s AND (subreddit=%s OR (subreddit IS NULL AND %s IS NULL))
                """
                params = (user_id, source_type, value, subreddit, subreddit)
            else:
                query = """
                    SELECT id FROM reddit_sources 
                    WHERE user_id=%s AND group_id=%s AND type=%s AND value=%s AND (subreddit=%s OR (subreddit IS NULL AND %s IS NULL))
                """
                params = (user_id, group_id, source_type, value, subreddit, subreddit)
                
            cur.execute(query, params)
            row = cur.fetchone()
            if row:
                return row[0]
            raise ValueError("Could not create or retrieve source")


def get_enabled_sources(user_id: Optional[int] = None) -> list[dict]:
    """Get all enabled sources, optionally filtered by user."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            if user_id:
                cur.execute(
                    """
                    SELECT id, user_id, group_id, type, value, subreddit, created_at
                    FROM reddit_sources
                    WHERE enabled = TRUE AND user_id = %s
                    ORDER BY id
                    """,
                    (user_id,)
                )
            else:
                cur.execute(
                    """
                    SELECT id, user_id, group_id, type, value, subreddit, created_at
                    FROM reddit_sources
                    WHERE enabled = TRUE
                    ORDER BY id
                    """
                )
            
            rows = cur.fetchall()
            return [
                {
                    "id": row[0],
                    "user_id": row[1],
                    "group_id": row[2],
                    "type": row[3],
                    "value": row[4],
                    "subreddit": row[5],
                    "created_at": row[6],
                }
                for row in rows
            ]


def delete_source(source_id: int, user_id: Optional[int] = None) -> bool:
    """
    Delete a source and all related data (cascades).
    
    If user_id provided, only deletes if source belongs to user.
    Returns True if deleted.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            if user_id:
                cur.execute(
                    "DELETE FROM reddit_sources WHERE id = %s AND user_id = %s",
                    (source_id, user_id)
                )
            else:
                cur.execute(
                    "DELETE FROM reddit_sources WHERE id = %s",
                    (source_id,)
                )
            return cur.rowcount > 0


# ═══════════════════════════════════════════════════════════════════════════════
# Item (Post) Operations
# ═══════════════════════════════════════════════════════════════════════════════

def upsert_item(
    source_id: int,
    external_id: str,
    external_url: str,
    subreddit: str,
    title: str,
    body: str,
    author: str,
    author_flair: Optional[str],
    score: int,
    num_comments: int,
    created_utc: datetime,
    quality_score: float,
    nsfw: bool = False,
    removed: bool = False,
    raw_json: Any = None,
) -> int:
    """
    Upsert a Reddit post.
    
    Returns the item ID.
    """
    pruned_json = Jsonb(prune_raw_json(raw_json))
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO reddit_items (
                    source_id, platform, subreddit, external_id, external_url,
                    title, body, author, author_flair, score, num_comments,
                    created_utc, fetched_at, quality_score, nsfw, removed, raw_json
                ) VALUES (
                    %s, 'reddit', %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, NOW(), %s, %s, %s, %s
                )
                ON CONFLICT (platform, external_id) DO UPDATE SET
                    score = EXCLUDED.score,
                    num_comments = EXCLUDED.num_comments,
                    quality_score = EXCLUDED.quality_score,
                    fetched_at = NOW(),
                    removed = EXCLUDED.removed,
                    raw_json = EXCLUDED.raw_json
                RETURNING id
                """,
                (
                    source_id, subreddit, external_id, external_url,
                    title, body, author, author_flair, score, num_comments,
                    created_utc, quality_score, nsfw, removed, pruned_json
                )
            )
            result = cur.fetchone()
            return result[0]


def get_item_by_external_id(external_id: str) -> Optional[dict]:
    """Get an item by its external ID."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, source_id, subreddit, external_id, external_url,
                       title, body, author, score, num_comments, created_utc,
                       quality_score, nsfw, removed
                FROM reddit_items
                WHERE external_id = %s
                """,
                (external_id,)
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "source_id": row[1],
                "subreddit": row[2],
                "external_id": row[3],
                "external_url": row[4],
                "title": row[5],
                "body": row[6],
                "author": row[7],
                "score": row[8],
                "num_comments": row[9],
                "created_utc": row[10],
                "quality_score": row[11],
                "nsfw": row[12],
                "removed": row[13],
            }


def get_items_without_cards(limit: int = 50) -> list[dict]:
    """Get items that don't have a strategy card yet."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT ri.id, ri.source_id, ri.subreddit, ri.external_id, ri.external_url,
                       ri.title, ri.body, ri.author, ri.score, ri.num_comments, ri.created_utc,
                       ri.quality_score, ri.nsfw, ri.removed
                FROM reddit_items ri
                LEFT JOIN strategy_cards sc ON sc.item_id = ri.id
                WHERE sc.id IS NULL
                  AND ri.quality_score >= 0.3
                ORDER BY ri.quality_score DESC
                LIMIT %s
                """,
                (limit,)
            )
            rows = cur.fetchall()
            return [
                {
                    "id": row[0],
                    "source_id": row[1],
                    "subreddit": row[2],
                    "external_id": row[3],
                    "external_url": row[4],
                    "title": row[5],
                    "body": row[6],
                    "author": row[7],
                    "score": row[8],
                    "num_comments": row[9],
                    "created_utc": row[10],
                    "quality_score": row[11],
                    "nsfw": row[12],
                    "removed": row[13],
                }
                for row in rows
            ]


# ═══════════════════════════════════════════════════════════════════════════════
# Comment Operations
# ═══════════════════════════════════════════════════════════════════════════════

def upsert_comment(
    item_id: int,
    external_id: str,
    parent_external_id: Optional[str],
    body: str,
    author: str,
    author_flair: Optional[str],
    score: int,
    created_utc: datetime,
    removed: bool = False,
    raw_json: Any = None,
) -> int:
    """
    Upsert a Reddit comment.
    
    Returns the comment ID.
    """
    pruned_json = Jsonb(prune_raw_json(raw_json))
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO reddit_comments (
                    item_id, external_id, parent_external_id, body, author,
                    author_flair, score, created_utc, fetched_at, removed, raw_json
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, NOW(), %s, %s
                )
                ON CONFLICT (item_id, external_id) DO UPDATE SET
                    body = EXCLUDED.body,
                    score = EXCLUDED.score,
                    fetched_at = NOW(),
                    removed = EXCLUDED.removed,
                    raw_json = EXCLUDED.raw_json
                RETURNING id
                """,
                (
                    item_id, external_id, parent_external_id, body, author,
                    author_flair, score, created_utc, removed, pruned_json
                )
            )
            result = cur.fetchone()
            return result[0]


# ═══════════════════════════════════════════════════════════════════════════════
# Chunk Operations
# ═══════════════════════════════════════════════════════════════════════════════

def insert_chunk(
    item_id: int,
    chunk_text: str,
    chunk_hash: str,
    comment_id: Optional[int] = None,
) -> Optional[int]:
    """
    Insert a chunk if it doesn't exist (by hash).
    
    Returns chunk ID if inserted, None if duplicate.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO reddit_chunks (item_id, comment_id, chunk_text, chunk_hash)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (chunk_hash) DO NOTHING
                    RETURNING id
                    """,
                    (item_id, comment_id, chunk_text, chunk_hash)
                )
                result = cur.fetchone()
                return result[0] if result else None
            except Exception as e:
                log.warning(f"Failed to insert chunk: {e}")
                return None


# ═══════════════════════════════════════════════════════════════════════════════
# Strategy Card Operations
# ═══════════════════════════════════════════════════════════════════════════════

def insert_strategy_card(
    item_id: int,
    platform_targets: list[str],
    niche: str,
    tactic: str,
    steps: list[dict],
    preconditions: dict,
    metrics: dict,
    risks: list[str],
    confidence: float,
    evidence: dict,
    comment_id: Optional[int] = None,
) -> int:
    """
    Insert a strategy card.
    
    Returns the card ID.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO strategy_cards (
                    source, item_id, comment_id, platform_targets, niche, tactic,
                    steps, preconditions, metrics, risks, confidence, evidence
                ) VALUES (
                    'reddit', %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s
                )
                RETURNING id
                """,
                (
                    item_id, comment_id, platform_targets, niche, tactic,
                    Jsonb(steps), 
                    Jsonb(preconditions),
                    Jsonb(metrics), 
                    Jsonb(risks),
                    confidence, 
                    Jsonb(evidence)
                )
            )
            result = cur.fetchone()
            return result[0]


# ═══════════════════════════════════════════════════════════════════════════════
# Listener State Operations
# ═══════════════════════════════════════════════════════════════════════════════

def get_listener_state(source_id: int) -> Optional[dict]:
    """Get the listener state for a source."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT last_seen_created_utc, last_run_at
                FROM listener_state
                WHERE source_id = %s
                """,
                (source_id,)
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "last_seen_created_utc": row[0],
                "last_run_at": row[1],
            }


def update_listener_state(
    source_id: int,
    last_seen_created_utc: datetime,
    last_run_at: Optional[datetime] = None,
) -> None:
    """Update the listener state for a source."""
    if last_run_at is None:
        last_run_at = datetime.now(timezone.utc)
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO listener_state (source_id, last_seen_created_utc, last_run_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (source_id) DO UPDATE SET
                    last_seen_created_utc = EXCLUDED.last_seen_created_utc,
                    last_run_at = EXCLUDED.last_run_at
                """,
                (source_id, last_seen_created_utc, last_run_at)
            )


# ═══════════════════════════════════════════════════════════════════════════════
# Alert Operations
# ═══════════════════════════════════════════════════════════════════════════════

def insert_alert(
    source_id: int,
    window_start: datetime,
    window_end: datetime,
    metric: str,
    current_value: float,
    previous_value: float,
    factor: float,
    top_item_ids: list[str], # list of external_ids
) -> int:
    """Insert a spike alert."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO reddit_alerts (
                    source_id, window_start, window_end, metric,
                    current_value, previous_value, factor, top_item_ids
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    source_id, window_start, window_end, metric,
                    current_value, previous_value, factor,
                    Jsonb(top_item_ids)
                )
            )
            result = cur.fetchone()
            return result[0]


def count_items_in_window(
    source_id: int,
    window_start: datetime,
    window_end: datetime,
) -> int:
    """Count items for a source within a time window."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM reddit_items
                WHERE source_id = %s
                  AND created_utc >= %s
                  AND created_utc < %s
                """,
                (source_id, window_start, window_end)
            )
            result = cur.fetchone()
            return result[0] if result else 0


def get_top_items_in_window(
    source_id: int,
    window_start: datetime,
    window_end: datetime,
    limit: int = 5,
) -> list[str]:
    """Get top item external IDs in a window by quality score."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT external_id
                FROM reddit_items
                WHERE source_id = %s
                  AND created_utc >= %s
                  AND created_utc < %s
                ORDER BY quality_score DESC
                LIMIT %s
                """,
                (source_id, window_start, window_end, limit)
            )
            return [row[0] for row in cur.fetchall()]
