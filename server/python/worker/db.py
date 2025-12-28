"""
Database Utilities
==================

Database connection and helper functions for the worker services.
Uses psycopg2 for PostgreSQL connections with proper connection pooling
and error handling.

Key Features:
    - Connection pooling for performance
    - Automatic reconnection on connection loss
    - Transaction management utilities
    - Job status update helpers

Author: ProjectMonopoly Team
Last Updated: 2025-12-27
"""

import logging
import time
from typing import Optional, Any, Dict
from contextlib import contextmanager

import psycopg2
from psycopg2 import pool, OperationalError, InterfaceError
from psycopg2.extras import RealDictCursor

from .config import DB_CONFIG, DATABASE_URL

log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Connection Pool (Singleton)
# ─────────────────────────────────────────────────────────────────────────────
_connection_pool: Optional[pool.ThreadedConnectionPool] = None
_pool_min_connections = 1
_pool_max_connections = 10


def get_pool() -> pool.ThreadedConnectionPool:
    """
    Get or create the database connection pool.
    
    Returns:
        ThreadedConnectionPool: The database connection pool.
        
    Raises:
        OperationalError: If connection to database fails.
    """
    global _connection_pool
    
    if _connection_pool is None or _connection_pool.closed:
        log.info("Creating database connection pool...")
        try:
            _connection_pool = pool.ThreadedConnectionPool(
                _pool_min_connections,
                _pool_max_connections,
                **DB_CONFIG
            )
            log.info("✅ Database connection pool created (min=%d, max=%d)", 
                    _pool_min_connections, _pool_max_connections)
        except OperationalError as e:
            log.error("❌ Failed to create connection pool: %s", e)
            raise
    
    return _connection_pool


def close_pool():
    """Close the connection pool and release all connections."""
    global _connection_pool
    if _connection_pool is not None:
        _connection_pool.closeall()
        _connection_pool = None
        log.info("Database connection pool closed")


# ─────────────────────────────────────────────────────────────────────────────
# Connection Management
# ─────────────────────────────────────────────────────────────────────────────
def get_connection(use_pool: bool = True) -> psycopg2.extensions.connection:
    """
    Get a database connection.
    
    Args:
        use_pool: If True, get connection from pool. If False, create new connection.
        
    Returns:
        connection: A psycopg2 database connection.
        
    Raises:
        OperationalError: If connection fails.
    """
    if use_pool:
        return get_pool().getconn()
    else:
        return psycopg2.connect(**DB_CONFIG)


def return_connection(conn: psycopg2.extensions.connection):
    """Return a connection to the pool."""
    try:
        get_pool().putconn(conn)
    except Exception as e:
        log.warning("Failed to return connection to pool: %s", e)


@contextmanager
def get_db_connection(use_dict_cursor: bool = False, autocommit: bool = False):
    """
    Context manager for database connections with automatic cleanup.
    
    Args:
        use_dict_cursor: If True, use RealDictCursor for dict-like rows.
        autocommit: If True, enable autocommit mode.
        
    Yields:
        tuple: (connection, cursor) for database operations.
        
    Example:
        >>> with get_db_connection() as (conn, cur):
        ...     cur.execute("SELECT * FROM users")
        ...     rows = cur.fetchall()
    """
    conn = None
    cur = None
    
    try:
        conn = get_connection(use_pool=True)
        conn.autocommit = autocommit
        
        cursor_factory = RealDictCursor if use_dict_cursor else None
        cur = conn.cursor(cursor_factory=cursor_factory)
        
        yield conn, cur
        
        if not autocommit:
            conn.commit()
            
    except Exception as e:
        if conn and not autocommit:
            conn.rollback()
        log.error("Database operation failed: %s", e)
        raise
        
    finally:
        if cur:
            cur.close()
        if conn:
            return_connection(conn)


# ─────────────────────────────────────────────────────────────────────────────
# Retry Utilities
# ─────────────────────────────────────────────────────────────────────────────
def execute_with_retry(
    query: str,
    params: tuple = None,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    fetch: str = None  # 'one', 'all', or None
) -> Optional[Any]:
    """
    Execute a database query with automatic retry on connection failure.
    
    Args:
        query: SQL query to execute.
        params: Query parameters.
        max_retries: Maximum number of retry attempts.
        retry_delay: Delay between retries (seconds).
        fetch: 'one' for fetchone, 'all' for fetchall, None for no fetch.
        
    Returns:
        Query result based on fetch parameter, or None.
        
    Raises:
        OperationalError: If all retries fail.
        
    Example:
        >>> result = execute_with_retry(
        ...     "SELECT * FROM users WHERE id = %s",
        ...     (user_id,),
        ...     fetch='one'
        ... )
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            with get_db_connection() as (conn, cur):
                cur.execute(query, params)
                
                if fetch == 'one':
                    return cur.fetchone()
                elif fetch == 'all':
                    return cur.fetchall()
                else:
                    return cur.rowcount
                    
        except (OperationalError, InterfaceError) as e:
            last_error = e
            log.warning(
                "Database query failed (attempt %d/%d): %s",
                attempt + 1, max_retries, e
            )
            
            # Reset pool on connection errors
            if attempt < max_retries - 1:
                close_pool()
                time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
    
    log.error("All retry attempts failed: %s", last_error)
    raise last_error


# ─────────────────────────────────────────────────────────────────────────────
# Job Status Updates
# ─────────────────────────────────────────────────────────────────────────────
def update_job_status(
    job_id: int,
    status: str,
    ai: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
) -> bool:
    """
    Update the status of an upload job.
    
    Args:
        job_id: The job ID to update.
        status: New status ('pending', 'uploading', 'done', 'failed').
        ai: Optional AI-generated content dict with keys:
            - title: AI-generated title
            - hashtags: List of AI-generated hashtags
            - post_time: Recommended post time
        error: Optional error message if status is 'failed'.
        
    Returns:
        bool: True if update succeeded, False otherwise.
        
    Example:
        >>> update_job_status(123, "done", {"title": "My Post", "hashtags": ["gaming"]})
    """
    ai = ai or {}
    
    try:
        with get_db_connection() as (conn, cur):
            if error:
                cur.execute("""
                    UPDATE upload_jobs
                    SET status = %s,
                        ai_title = %s,
                        ai_hashtags = %s,
                        ai_post_time = %s,
                        error = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (
                    status,
                    ai.get("title"),
                    ai.get("hashtags"),
                    ai.get("post_time"),
                    error,
                    job_id
                ))
            else:
                cur.execute("""
                    UPDATE upload_jobs
                    SET status = %s,
                        ai_title = %s,
                        ai_hashtags = %s,
                        ai_post_time = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (
                    status,
                    ai.get("title"),
                    ai.get("hashtags"),
                    ai.get("post_time"),
                    job_id
                ))
            
            log.info("Updated job %d status to '%s'", job_id, status)
            return cur.rowcount > 0
            
    except Exception as e:
        log.exception("Failed to update job %d status: %s", job_id, e)
        return False


def get_job_status(job_id: int) -> Optional[Dict[str, Any]]:
    """
    Get the current status of an upload job.
    
    Args:
        job_id: The job ID to query.
        
    Returns:
        dict: Job details or None if not found.
    """
    try:
        with get_db_connection(use_dict_cursor=True) as (conn, cur):
            cur.execute(
                "SELECT id, status, platform, created_at, updated_at FROM upload_jobs WHERE id = %s",
                (job_id,)
            )
            return cur.fetchone()
    except Exception as e:
        log.exception("Failed to get job %d status: %s", job_id, e)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────────────────────────────────────
def check_database_health() -> Dict[str, Any]:
    """
    Check the health of the database connection.
    
    Returns:
        dict: Health status including:
            - healthy (bool): Whether connection is working
            - latency_ms (float): Connection latency in milliseconds
            - pool_size (int): Current pool size
            - error (str, optional): Error message if unhealthy
    """
    status = {
        "healthy": False,
        "latency_ms": None,
        "pool_size": None,
        "error": None
    }
    
    try:
        start = time.time()
        with get_db_connection() as (conn, cur):
            cur.execute("SELECT 1")
            cur.fetchone()
        
        status["healthy"] = True
        status["latency_ms"] = round((time.time() - start) * 1000, 2)
        
        if _connection_pool:
            status["pool_size"] = _connection_pool.maxconn
            
    except Exception as e:
        status["error"] = str(e)
        log.error("Database health check failed: %s", e)
    
    return status


# ─────────────────────────────────────────────────────────────────────────────
# Export
# ─────────────────────────────────────────────────────────────────────────────
__all__ = [
    'get_connection',
    'return_connection',
    'get_db_connection',
    'close_pool',
    'execute_with_retry',
    'update_job_status',
    'get_job_status',
    'check_database_health',
]
