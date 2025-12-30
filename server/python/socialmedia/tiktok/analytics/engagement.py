# TikTok Analytics Module
# Platform-specific analytics for TikTok data
"""
TikTok-specific engagement and trend analytics.

Key differences from Instagram:
- Views are the primary reach metric (not followers)
- Watch time and completion rate matter
- Shares have higher weight in virality
- Sound/hashtag trends are critical
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

log = logging.getLogger(__name__)


def calculate_engagement_rate(
    likes: int, 
    comments: int, 
    shares: int, 
    views: int
) -> float:
    """
    Calculate TikTok engagement rate.
    
    TikTok engagement = (likes + comments + shares) / views
    This differs from Instagram which uses followers as denominator.
    
    Args:
        likes: Number of likes
        comments: Number of comments  
        shares: Number of shares
        views: Number of views
        
    Returns:
        float: Engagement rate as a decimal (0.0 to 1.0+)
    """
    if views <= 0:
        return 0.0
    
    total_engagement = likes + comments + shares
    return round(total_engagement / views, 4)


def calculate_virality_score(
    likes: int,
    comments: int, 
    shares: int,
    saves: int,
    views: int,
    followers: int = 0
) -> float:
    """
    Calculate TikTok virality score.
    
    Weights shares heavily since TikTok's algorithm prioritizes
    content that gets shared to other platforms.
    
    Args:
        likes, comments, shares, saves, views: Video metrics
        followers: Creator's follower count (optional)
        
    Returns:
        float: Virality score (0-100)
    """
    if views <= 0:
        return 0.0
    
    # Weight shares 3x, saves 2x, comments 1.5x, likes 1x
    weighted_engagement = (
        likes * 1.0 +
        comments * 1.5 +
        shares * 3.0 +
        saves * 2.0
    )
    
    # Base score from engagement rate
    engagement_rate = weighted_engagement / views
    base_score = min(engagement_rate * 100, 50)  # Cap at 50
    
    # Bonus for view-to-follower ratio (content reaching beyond followers)
    if followers > 0:
        reach_multiplier = views / followers
        if reach_multiplier > 1:
            # Bonus points for reaching beyond follower base
            reach_bonus = min(reach_multiplier * 5, 30)
            base_score += reach_bonus
    
    # Bonus for high absolute shares (viral indicator)
    if shares > 1000:
        base_score += 10
    elif shares > 100:
        base_score += 5
    
    return round(min(base_score, 100), 2)


def calculate_trend_score(post_data: Dict[str, Any]) -> float:
    """
    Calculate trend score for a TikTok video.
    
    Factors:
    - Recency: Newer content scores higher
    - Engagement rate
    - Virality indicators (shares, saves)
    - Growth velocity (if historical data available)
    
    Args:
        post_data: Dict with video metrics
        
    Returns:
        float: Trend score (0-100)
    """
    likes = int(post_data.get('likes_count') or post_data.get('likes', 0) or 0)
    comments = int(post_data.get('comments_count') or post_data.get('comments', 0) or 0)
    shares = int(post_data.get('shared_count') or post_data.get('shares', 0) or 0)
    saves = int(post_data.get('saved_count') or post_data.get('saves', 0) or 0)
    views = int(post_data.get('views') or post_data.get('play_count', 0) or 0)
    
    # Calculate base engagement score
    engagement = calculate_engagement_rate(likes, comments, shares, views)
    engagement_score = min(engagement * 200, 40)  # Max 40 points
    
    # Virality component (shares + saves)
    virality_ratio = (shares + saves) / max(views, 1)
    virality_score = min(virality_ratio * 500, 30)  # Max 30 points
    
    # Recency bonus
    recency_score = 0
    post_date = post_data.get('post_date') or post_data.get('timestamp')
    if post_date:
        try:
            if isinstance(post_date, str):
                post_dt = datetime.fromisoformat(post_date.replace('Z', '+00:00'))
            else:
                post_dt = post_date
            
            days_old = (datetime.now() - post_dt.replace(tzinfo=None)).days
            if days_old <= 1:
                recency_score = 30
            elif days_old <= 3:
                recency_score = 25
            elif days_old <= 7:
                recency_score = 15
            elif days_old <= 14:
                recency_score = 5
        except Exception:
            pass
    
    total = engagement_score + virality_score + recency_score
    return round(min(total, 100), 2)


def analyze_video(video_data: Dict[str, Any], follower_count: int = 0) -> Dict[str, Any]:
    """
    Analyze a TikTok video and return comprehensive metrics.
    
    Args:
        video_data: Raw video data from scraper
        follower_count: Creator's follower count
        
    Returns:
        dict: Analytics results
    """
    likes = int(video_data.get('likes_count') or video_data.get('likes', 0) or 0)
    comments = int(video_data.get('comments_count') or video_data.get('comments', 0) or 0)
    shares = int(video_data.get('shared_count') or video_data.get('shares', 0) or 0)
    saves = int(video_data.get('saved_count') or video_data.get('saves', 0) or 0)
    views = int(video_data.get('views') or video_data.get('play_count', 0) or 0)
    
    return {
        'url': video_data.get('url', ''),
        'description': video_data.get('description', ''),
        'likes': likes,
        'comments': comments,
        'shares': shares,
        'saves': saves,
        'views': views,
        'engagement_rate': calculate_engagement_rate(likes, comments, shares, views),
        'virality_score': calculate_virality_score(likes, comments, shares, saves, views, follower_count),
        'trend_score': calculate_trend_score(video_data),
        'hashtags': video_data.get('hashtags', []),
    }


def extract_trending_sounds(videos: list) -> Dict[str, int]:
    """
    Extract and count sounds/music from a list of videos.
    
    Sounds are a key TikTok trend indicator.
    
    Args:
        videos: List of video data dicts
        
    Returns:
        dict: Sound name -> usage count
    """
    sounds = {}
    for video in videos:
        sound = video.get('sound') or video.get('music') or video.get('audio')
        if sound:
            sounds[sound] = sounds.get(sound, 0) + 1
    
    # Sort by count descending
    return dict(sorted(sounds.items(), key=lambda x: x[1], reverse=True))


def extract_trending_hashtags(videos: list) -> Dict[str, int]:
    """
    Extract and count hashtags from a list of videos.
    
    Args:
        videos: List of video data dicts
        
    Returns:
        dict: Hashtag -> usage count
    """
    hashtags = {}
    for video in videos:
        tags = video.get('hashtags', [])
        for tag in tags:
            clean_tag = tag.lstrip('#').lower()
            if clean_tag:
                hashtags[clean_tag] = hashtags.get(clean_tag, 0) + 1
    
    return dict(sorted(hashtags.items(), key=lambda x: x[1], reverse=True))
