"""
Quality Scoring Module
======================

Computes quality scores for Reddit posts using weighted signals.
Provides filtering based on configurable thresholds.
"""

import math
import logging
from datetime import datetime, timezone
from typing import Optional

from .config import (
    MIN_QUALITY_SCORE,
    MIN_SCORE,
    MIN_COMMENTS,
    MAX_AGE_HOURS,
    QUALITY_SCORE_WEIGHT,
    QUALITY_COMMENTS_WEIGHT,
    QUALITY_RECENCY_WEIGHT,
    QUALITY_FLAIR_BONUS,
    QUALITY_NSFW_PENALTY,
    QUALITY_REMOVED_PENALTY,
)

log = logging.getLogger(__name__)


def compute_quality_score(
    score: int,
    num_comments: int,
    created_utc: datetime,
    author_flair: Optional[str] = None,
    nsfw: bool = False,
    removed: bool = False,
) -> float:
    """
    Compute a quality score for a Reddit post.
    
    Formula:
        base = log1p(score) * SCORE_WEIGHT + log1p(comments) * COMMENTS_WEIGHT
        + recency_boost * RECENCY_WEIGHT
        + flair_bonus (if author_flair present)
        - nsfw_penalty (if nsfw)
        - removed_penalty (if removed)
    
    Args:
        score: Reddit upvote score
        num_comments: Number of comments
        created_utc: Post creation time (timezone-aware)
        author_flair: Author flair text (if any)
        nsfw: Is the post NSFW
        removed: Is the post removed
        
    Returns:
        Quality score (0.0 to ~5.0 typically, can go negative for bad posts)
    """
    # Normalize score and comments using log1p for diminishing returns
    score_component = math.log1p(max(0, score)) * QUALITY_SCORE_WEIGHT
    comments_component = math.log1p(max(0, num_comments)) * QUALITY_COMMENTS_WEIGHT
    
    # Recency boost: decays over time
    # Full boost for posts < 1 hour old, decays to 0 at MAX_AGE_HOURS
    now = datetime.now(timezone.utc)
    if created_utc.tzinfo is None:
        created_utc = created_utc.replace(tzinfo=timezone.utc)
    
    age_hours = (now - created_utc).total_seconds() / 3600
    if age_hours < 0:
        age_hours = 0
    
    if age_hours >= MAX_AGE_HOURS:
        recency_boost = 0.0
    else:
        # Linear decay
        recency_boost = (1 - age_hours / MAX_AGE_HOURS) * QUALITY_RECENCY_WEIGHT
    
    # Flair bonus: indicates engaged community member
    flair_bonus = QUALITY_FLAIR_BONUS if author_flair else 0.0
    
    # Penalties
    nsfw_penalty = QUALITY_NSFW_PENALTY if nsfw else 0.0
    removed_penalty = QUALITY_REMOVED_PENALTY if removed else 0.0
    
    quality = (
        score_component
        + comments_component
        + recency_boost
        + flair_bonus
        - nsfw_penalty
        - removed_penalty
    )
    
    return round(quality, 4)


def passes_quality_filter(
    score: int,
    num_comments: int,
    created_utc: datetime,
    quality_score: Optional[float] = None,
    nsfw: bool = False,
    removed: bool = False,
) -> bool:
    """
    Check if a post passes quality thresholds.
    
    A post must meet ALL criteria:
    - score >= MIN_SCORE
    - num_comments >= MIN_COMMENTS  
    - age <= MAX_AGE_HOURS
    - quality_score >= MIN_QUALITY_SCORE (if provided)
    - not removed
    
    Args:
        score: Reddit upvote score
        num_comments: Number of comments
        created_utc: Post creation time
        quality_score: Pre-computed quality score (optional)
        nsfw: Is the post NSFW (not a blocker, just affects score)
        removed: Is the post removed
        
    Returns:
        True if post passes filter
    """
    # Removed posts never pass
    if removed:
        return False
    
    # Check minimum score
    if score < MIN_SCORE:
        return False
    
    # Check minimum comments
    if num_comments < MIN_COMMENTS:
        return False
    
    # Check age
    now = datetime.now(timezone.utc)
    if created_utc.tzinfo is None:
        created_utc = created_utc.replace(tzinfo=timezone.utc)
    
    age_hours = (now - created_utc).total_seconds() / 3600
    if age_hours > MAX_AGE_HOURS:
        return False
    
    # Check quality score if provided
    if quality_score is not None and quality_score < MIN_QUALITY_SCORE:
        return False
    
    return True


def is_high_quality(quality_score: float) -> bool:
    """
    Check if a post is high-quality (worth fetching comments for).
    
    Uses a higher threshold than the minimum filter.
    """
    # High quality = significantly above minimum (2x the threshold)
    return quality_score >= MIN_QUALITY_SCORE * 2


def get_quality_tier(quality_score: float) -> str:
    """
    Get a human-readable quality tier for a score.
    
    Returns: 'low', 'medium', 'high', or 'exceptional'
    """
    if quality_score < MIN_QUALITY_SCORE:
        return "low"
    elif quality_score < MIN_QUALITY_SCORE * 2:
        return "medium"
    elif quality_score < MIN_QUALITY_SCORE * 3:
        return "high"
    else:
        return "exceptional"
