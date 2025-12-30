# Instagram Platform Module
from .scraper.profile_scraper import InstagramScraper
from .scraper.weekly_scheduler import WeeklyInstagramScraper

__all__ = ['InstagramScraper', 'WeeklyInstagramScraper']
