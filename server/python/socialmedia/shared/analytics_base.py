# Base Analytics Module
# Common analytics interfaces and utilities for all platforms
"""
Base analytics classes and utilities shared across platforms.

Platform-specific implementations should:
1. Inherit from BaseAnalytics when applicable
2. Override platform-specific calculation methods
3. Use common utility functions for date handling, etc.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

log = logging.getLogger(__name__)


class BaseAnalytics(ABC):
    """Abstract base class for platform analytics."""
    
    @abstractmethod
    def calculate_engagement_rate(self, **kwargs) -> float:
        """Calculate platform-specific engagement rate."""
        pass
    
    @abstractmethod
    def calculate_trend_score(self, post_data: Dict[str, Any]) -> float:
        """Calculate trend score for a post/video."""
        pass
    
    @abstractmethod
    def analyze_post(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single post and return metrics."""
        pass


def calculate_growth_rate(
    current_followers: int, 
    previous_followers: int,
    days_between: int = 7
) -> float:
    """
    Calculate follower growth rate.
    
    Args:
        current_followers: Current follower count
        previous_followers: Previous follower count
        days_between: Days between measurements
        
    Returns:
        float: Growth rate as percentage
    """
    if previous_followers <= 0:
        return 0.0
    
    growth = current_followers - previous_followers
    growth_rate = (growth / previous_followers) * 100
    
    # Annualize if needed
    if days_between > 0 and days_between != 365:
        daily_rate = growth_rate / days_between
        # Return weekly rate for consistency
        return round(daily_rate * 7, 2)
    
    return round(growth_rate, 2)


def calculate_posting_frequency(
    posts: List[Dict[str, Any]], 
    days: int = 28
) -> float:
    """
    Calculate average posts per week.
    
    Args:
        posts: List of posts with timestamps
        days: Period to analyze
        
    Returns:
        float: Average posts per week
    """
    if not posts:
        return 0.0
    
    cutoff = datetime.now() - timedelta(days=days)
    recent_posts = []
    
    for post in posts:
        post_date = post.get('post_date') or post.get('timestamp') or post.get('created_at')
        if not post_date:
            continue
        
        try:
            if isinstance(post_date, str):
                dt = datetime.fromisoformat(post_date.replace('Z', '+00:00'))
            else:
                dt = post_date
            
            if dt.replace(tzinfo=None) >= cutoff:
                recent_posts.append(dt)
        except Exception:
            continue
    
    if not recent_posts:
        return 0.0
    
    weeks = days / 7
    return round(len(recent_posts) / weeks, 2)


def parse_count(value: Any) -> int:
    """
    Parse a count value that might be string, int, or formatted.
    
    Handles: "1.2K", "5M", "1,234", 1234, "1234"
    
    Args:
        value: Count value in various formats
        
    Returns:
        int: Parsed count
    """
    if value is None:
        return 0
    
    if isinstance(value, (int, float)):
        return int(value)
    
    if not isinstance(value, str):
        return 0
    
    value = value.strip().upper().replace(',', '')
    
    try:
        if value.endswith('K'):
            return int(float(value[:-1]) * 1_000)
        elif value.endswith('M'):
            return int(float(value[:-1]) * 1_000_000)
        elif value.endswith('B'):
            return int(float(value[:-1]) * 1_000_000_000)
        else:
            return int(float(value))
    except (ValueError, TypeError):
        return 0


def extract_hashtags(text: str) -> List[str]:
    """
    Extract hashtags from text.
    
    Args:
        text: Text containing hashtags
        
    Returns:
        list: List of hashtags (without #)
    """
    import re
    if not text:
        return []
    
    # Unicode-aware hashtag regex
    pattern = r'#([\w\u0080-\uFFFF]+)'
    matches = re.findall(pattern, text, re.UNICODE)
    return [m.lower() for m in matches if m]
