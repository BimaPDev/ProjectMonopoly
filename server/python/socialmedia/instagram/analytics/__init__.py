# Instagram Analytics Module
# Platform-specific analytics for Instagram data

from .engagement import analyze_post, calculate_engagement_rate
from .trend_scoring import calculate_trend_score
from .classifier import classify_caption

__all__ = [
    'analyze_post',
    'calculate_engagement_rate', 
    'calculate_trend_score',
    'classify_caption',
]
