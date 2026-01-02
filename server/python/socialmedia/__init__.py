# Social Media Package
# Provides platform-specific scrapers and shared utilities

# New module structure exports
from .instagram import InstagramScraper, WeeklyInstagramScraper
from .tiktok import TikTokScraper, WeeklyTikTokScraper

# Legacy aliases for backward compatibility
# These allow existing code to use:
#   from socialmedia.instaPage import InstagramScraper
#   from socialmedia.tiktok_scraper import TikTokScraper
from .instagram.scraper import profile_scraper as instaPage
from .tiktok.scraper import profile_scraper as tiktok_scraper
from .instagram.scraper import weekly_scheduler as weekly_scraper
from .tiktok.scraper import weekly_scheduler as weekly_tiktok_scraper

__all__ = [
    'InstagramScraper', 
    'WeeklyInstagramScraper',
    'TikTokScraper', 
    'WeeklyTikTokScraper',
    'instaPage',
    'tiktok_scraper',
    'weekly_scraper',
    'weekly_tiktok_scraper',
] 