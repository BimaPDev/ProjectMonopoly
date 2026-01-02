"""
Viral Content Discovery Module
==============================

Detects viral outliers in competitor and hashtag posts using per-metric
analysis with configurable floors and multipliers.

Author: ProjectMonopoly Team
Created: 2026-01-01
"""

__version__ = "1.0.0"

from .outlier_detector import OutlierDetector

__all__ = ["OutlierDetector"]
