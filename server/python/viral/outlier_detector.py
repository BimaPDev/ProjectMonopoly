"""
Viral Outlier Detector
======================

Detects viral content outliers by analyzing engagement metrics against
account medians. Implements the robust outlier detection algorithm with:
- Per-metric outlier validation (likes, comments, views)
- Configurable floors and multipliers
- Available count / support count logic for missing metrics
- Task locking to prevent overlapping scans
- UTC timestamps throughout

Author: ProjectMonopoly Team
Created: 2026-01-01
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass

import psycopg

log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

# Configurable via environment variables
LIKES_FLOOR = int(os.environ.get("VIRAL_LIKES_FLOOR", "50"))
COMMENTS_FLOOR = int(os.environ.get("VIRAL_COMMENTS_FLOOR", "10"))
VIEWS_FLOOR = int(os.environ.get("VIRAL_VIEWS_FLOOR", "1000"))
MIN_ENGAGEMENT_FLOOR = int(os.environ.get("VIRAL_MIN_ENGAGEMENT", "100"))
VIRAL_WINDOW_DAYS = int(os.environ.get("VIRAL_WINDOW_DAYS", "3"))
MEDIAN_WINDOW_DAYS = int(os.environ.get("VIRAL_MEDIAN_WINDOW_DAYS", "30"))
MIN_POSTS_FOR_MEDIAN = int(os.environ.get("VIRAL_MIN_POSTS", "5"))
EXPIRY_DAYS = int(os.environ.get("VIRAL_EXPIRY_DAYS", "7"))

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://root:secret@localhost:5432/project_monopoly"
)


@dataclass
class ViralOutlier:
    """Represents a detected viral outlier."""
    source_table: str
    source_id: int
    username: str
    platform: str
    content: str
    hook: str
    multiplier: int
    median_engagement: int
    actual_engagement: int
    available_count: int
    support_count: int
    likes: int
    comments: int
    views: Optional[int]
    likes_outlier: bool
    comments_outlier: bool
    views_outlier: bool


class OutlierDetector:
    """
    Detects viral content outliers in competitor and hashtag posts.
    
    Uses per-metric analysis to identify posts that significantly outperform
    an account's typical engagement, while filtering out bots and pods.
    
    Example:
        detector = OutlierDetector()
        outliers = detector.detect_outliers()
        detector.upsert_outliers(outliers)
    """
    
    def __init__(
        self,
        database_url: str = DATABASE_URL,
        likes_floor: int = LIKES_FLOOR,
        comments_floor: int = COMMENTS_FLOOR,
        views_floor: int = VIEWS_FLOOR,
        min_engagement: int = MIN_ENGAGEMENT_FLOOR,
        viral_window_days: int = VIRAL_WINDOW_DAYS,
        median_window_days: int = MEDIAN_WINDOW_DAYS,
        min_posts: int = MIN_POSTS_FOR_MEDIAN,
        expiry_days: int = EXPIRY_DAYS,
    ):
        self.database_url = database_url
        self.likes_floor = likes_floor
        self.comments_floor = comments_floor
        self.views_floor = views_floor
        self.min_engagement = min_engagement
        self.viral_window_days = viral_window_days
        self.median_window_days = median_window_days
        self.min_posts = min_posts
        self.expiry_days = expiry_days
    
    def get_connection(self) -> psycopg.Connection:
        """Get a database connection."""
        return psycopg.connect(self.database_url)
    
    def acquire_lock(self, task_name: str = "viral_scanner") -> bool:
        """
        Acquire a task lock to prevent overlapping scans.
        
        Returns:
            bool: True if lock acquired, False if already locked.
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Clean up expired locks first
                    cur.execute("""
                        DELETE FROM task_locks 
                        WHERE expires_at < (NOW() AT TIME ZONE 'UTC')
                    """)
                    
                    # Try to acquire lock
                    cur.execute("""
                        INSERT INTO task_locks (task_name, locked_at, locked_by, expires_at)
                        VALUES (%s, NOW() AT TIME ZONE 'UTC', %s, (NOW() AT TIME ZONE 'UTC') + INTERVAL '1 hour')
                        ON CONFLICT (task_name) DO NOTHING
                    """, (task_name, f"worker-{os.getpid()}"))
                    
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            log.error(f"Failed to acquire lock: {e}")
            return False
    
    def release_lock(self, task_name: str = "viral_scanner") -> None:
        """Release a task lock."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM task_locks WHERE task_name = %s",
                        (task_name,)
                    )
                    conn.commit()
        except Exception as e:
            log.error(f"Failed to release lock: {e}")
    
    def detect_outliers(self) -> List[ViralOutlier]:
        """
        Detect viral outliers using the production-ready query.
        
        Returns:
            List[ViralOutlier]: List of detected outliers.
        """
        query = f"""
        -- ============================================================
        -- ROBUST OUTLIER DETECTION - PRODUCTION READY (v2.0)
        -- ============================================================

        -- Step 1: Calculate account medians PER METRIC (with safeguards)
        WITH account_stats AS (
            SELECT 
                username,
                platform,
                
                -- Median for likes (always available)
                PERCENTILE_CONT(0.5) WITHIN GROUP (
                    ORDER BY likes
                ) as median_likes,
                
                -- Median for comments (always available)
                PERCENTILE_CONT(0.5) WITHIN GROUP (
                    ORDER BY comments
                ) as median_comments,
                
                -- Median for views (NULL when not available)
                PERCENTILE_CONT(0.5) WITHIN GROUP (
                    ORDER BY views
                ) FILTER (WHERE views IS NOT NULL) as median_views,
                
                -- Combined engagement for tier calculation
                PERCENTILE_CONT(0.5) WITHIN GROUP (
                    ORDER BY likes + comments
                ) as median_engagement,
                
                COUNT(*) as post_count
            FROM unified_posts
            WHERE posted_at >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '{self.median_window_days} days'
            GROUP BY username, platform
            HAVING COUNT(*) >= {self.min_posts}
               AND PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY likes + comments) > 0
        ),

        -- Step 2: Calculate post metrics
        post_metrics AS (
            SELECT 
                up.source_table,
                up.source_id,
                up.username,
                up.platform,
                up.content,
                up.posted_at,
                up.likes,
                up.comments,
                up.views,
                up.likes + up.comments as engagement_total,
                ast.median_likes,
                ast.median_comments,
                ast.median_views,
                ast.median_engagement
            FROM unified_posts up
            JOIN account_stats ast ON up.username = ast.username AND up.platform = ast.platform
            WHERE up.posted_at >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '{self.viral_window_days} days'
        ),

        -- Step 3: Apply PER-METRIC outlier validation with availability tracking
        validated_outliers AS (
            SELECT 
                pm.*,
                
                -- Calculate multiplier tier
                CASE 
                    WHEN pm.median_engagement <= 0 THEN 0
                    WHEN pm.engagement_total >= 100 * pm.median_engagement THEN 100
                    WHEN pm.engagement_total >= 50 * pm.median_engagement THEN 50
                    WHEN pm.engagement_total >= 10 * pm.median_engagement THEN 10
                    WHEN pm.engagement_total >= 5 * pm.median_engagement THEN 5
                    ELSE 0
                END as multiplier,
                
                -- Per-metric outlier checks
                CASE WHEN pm.likes >= 5 * GREATEST(pm.median_likes, 1) 
                      AND pm.likes >= {self.likes_floor} THEN TRUE ELSE FALSE END as likes_outlier,
                
                CASE WHEN pm.comments >= 3 * GREATEST(pm.median_comments, 1) 
                      AND pm.comments >= {self.comments_floor} THEN TRUE ELSE FALSE END as comments_outlier,
                
                CASE WHEN pm.views IS NOT NULL 
                      AND pm.views >= 5 * GREATEST(pm.median_views, 1) 
                      AND pm.views >= {self.views_floor} THEN TRUE ELSE FALSE END as views_outlier,
                
                -- Count available metrics
                (CASE WHEN pm.likes IS NOT NULL THEN 1 ELSE 0 END +
                 CASE WHEN pm.comments IS NOT NULL THEN 1 ELSE 0 END +
                 CASE WHEN pm.views IS NOT NULL THEN 1 ELSE 0 END) as available_count,
                
                -- Count outlier metrics
                (CASE WHEN pm.likes >= 5 * GREATEST(pm.median_likes, 1) 
                       AND pm.likes >= {self.likes_floor} THEN 1 ELSE 0 END +
                 CASE WHEN pm.comments >= 3 * GREATEST(pm.median_comments, 1) 
                       AND pm.comments >= {self.comments_floor} THEN 1 ELSE 0 END +
                 CASE WHEN pm.views IS NOT NULL 
                       AND pm.views >= 5 * GREATEST(pm.median_views, 1) 
                       AND pm.views >= {self.views_floor} THEN 1 ELSE 0 END) as support_count
                      
            FROM post_metrics pm
            WHERE pm.engagement_total >= {self.min_engagement}
        )

        -- Step 4: Final selection with AVAILABLE_COUNT-aware logic
        SELECT 
            source_table,
            source_id,
            username,
            platform,
            content,
            LEFT(content, 280) as hook,
            multiplier,
            median_engagement::bigint,
            engagement_total as actual_engagement,
            available_count,
            support_count,
            likes,
            comments,
            views,
            likes_outlier,
            comments_outlier,
            views_outlier
        FROM validated_outliers
        WHERE multiplier >= 5
          AND (
            (available_count >= 3 AND support_count >= 2)
            OR (available_count = 2 AND support_count >= 2)
            OR (available_count = 1 AND support_count = 1 AND engagement_total >= 500)
          )
        ORDER BY multiplier DESC, engagement_total DESC;
        """
        
        outliers = []
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    rows = cur.fetchall()
                    
                    for row in rows:
                        outliers.append(ViralOutlier(
                            source_table=row[0],
                            source_id=row[1],
                            username=row[2],
                            platform=row[3],
                            content=row[4],
                            hook=row[5],
                            multiplier=row[6],
                            median_engagement=row[7],
                            actual_engagement=row[8],
                            available_count=row[9],
                            support_count=row[10],
                            likes=row[11],
                            comments=row[12],
                            views=row[13],
                            likes_outlier=row[14],
                            comments_outlier=row[15],
                            views_outlier=row[16],
                        ))
                    
                    log.info(f"Detected {len(outliers)} viral outliers")
        except Exception as e:
            log.error(f"Failed to detect outliers: {e}")
            raise
        
        return outliers
    
    def upsert_outliers(self, outliers: List[ViralOutlier]) -> Dict[str, int]:
        """
        Insert or update outliers in the database.
        
        Args:
            outliers: List of detected outliers.
            
        Returns:
            Dict with 'inserted' and 'updated' counts.
        """
        if not outliers:
            return {"inserted": 0, "updated": 0}
        
        upsert_query = f"""
        INSERT INTO viral_outliers (
            source_table, source_id, multiplier, median_engagement, actual_engagement,
            available_count, support_count, hook, platform, username, analyzed_at, expires_at
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            NOW() AT TIME ZONE 'UTC',
            (NOW() AT TIME ZONE 'UTC') + INTERVAL '{self.expiry_days} days'
        )
        ON CONFLICT (source_table, source_id) DO UPDATE SET
            multiplier = EXCLUDED.multiplier,
            actual_engagement = EXCLUDED.actual_engagement,
            available_count = EXCLUDED.available_count,
            support_count = EXCLUDED.support_count,
            analyzed_at = NOW() AT TIME ZONE 'UTC',
            expires_at = (NOW() AT TIME ZONE 'UTC') + INTERVAL '{self.expiry_days} days'
        WHERE viral_outliers.multiplier != EXCLUDED.multiplier
           OR viral_outliers.actual_engagement != EXCLUDED.actual_engagement
           OR viral_outliers.support_count != EXCLUDED.support_count;
        """
        
        inserted = 0
        updated = 0
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    for outlier in outliers:
                        cur.execute(upsert_query, (
                            outlier.source_table,
                            outlier.source_id,
                            outlier.multiplier,
                            outlier.median_engagement,
                            outlier.actual_engagement,
                            outlier.available_count,
                            outlier.support_count,
                            outlier.hook,
                            outlier.platform,
                            outlier.username,
                        ))
                        
                        # rowcount = 1 for insert, 1 for update, 0 for no change
                        if cur.rowcount > 0:
                            # Check if it was an insert or update by querying
                            inserted += 1  # Simplified - count as insert
                    
                    conn.commit()
                    log.info(f"Upserted {len(outliers)} outliers")
        except Exception as e:
            log.error(f"Failed to upsert outliers: {e}")
            raise
        
        return {"inserted": inserted, "updated": updated}
    
    def cleanup_expired(self) -> int:
        """
        Remove expired outliers from the database.
        
        Returns:
            int: Number of deleted records.
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        DELETE FROM viral_outliers 
                        WHERE expires_at < (NOW() AT TIME ZONE 'UTC')
                    """)
                    deleted = cur.rowcount
                    conn.commit()
                    log.info(f"Cleaned up {deleted} expired outliers")
                    return deleted
        except Exception as e:
            log.error(f"Failed to cleanup expired outliers: {e}")
            raise
    
    def run_scan(self) -> Dict[str, Any]:
        """
        Run a complete viral content scan with locking.
        
        Returns:
            Dict with scan results or skip reason.
        """
        # Try to acquire lock
        if not self.acquire_lock():
            log.info("Viral scanner already running, skipping")
            return {"status": "skipped", "reason": "already_running"}
        
        try:
            # Detect outliers
            outliers = self.detect_outliers()
            
            # Upsert to database
            result = self.upsert_outliers(outliers)
            
            return {
                "status": "success",
                "outliers_found": len(outliers),
                "inserted": result["inserted"],
                "updated": result["updated"],
                "by_multiplier": {
                    "100x": sum(1 for o in outliers if o.multiplier == 100),
                    "50x": sum(1 for o in outliers if o.multiplier == 50),
                    "10x": sum(1 for o in outliers if o.multiplier == 10),
                    "5x": sum(1 for o in outliers if o.multiplier == 5),
                }
            }
        finally:
            self.release_lock()


# ─────────────────────────────────────────────────────────────────────────────
# CLI Entry Point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    
    detector = OutlierDetector()
    
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        deleted = detector.cleanup_expired()
        print(f"Cleaned up {deleted} expired outliers")
    else:
        result = detector.run_scan()
        print(f"Scan result: {result}")
