#!/usr/bin/env python3
"""
Weekly TikTok Scraper
This scraper is integrated with the TikTok scraper to automatically scrape
TikTok competitors on a weekly basis.
"""

import os
import sys
import logging
import psycopg
from datetime import datetime
from typing import List, Dict, Any
import json

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from socialmedia.tiktok.scraper.profile_scraper import TikTokScraper

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://root:secret@localhost:5432/project_monopoly?sslmode=disable")

# Logging setup
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class WeeklyTikTokScraper:
    """
    Weekly TikTok scraper that processes all TikTok competitors
    that haven't been scraped in the last 7 days.
    """
    
    def __init__(self):
        self.database_url = DATABASE_URL
        self.scraper = None
        self.max_posts_per_profile = int(os.getenv("WEEKLY_MAX_POSTS", "10"))  # Default: top 10 videos
        self.scrape_interval_days = float(os.getenv("WEEKLY_SCRAPE_INTERVAL", "7"))
        
    def get_competitors_to_scrape(self) -> List[Dict[str, Any]]:
        """
        Query the database for TikTok competitors that need scraping.
        Returns competitors that haven't been scraped in the last N days.
        """
        log.info("🔍 Querying database for TikTok competitors to scrape...")
        
        try:
            with psycopg.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT
                            c.id,
                            cp.handle as username,
                            cp.profile_url,
                            cp.last_checked,
                            COUNT(posts.id) as post_count,
                            cp.id as profile_id
                        FROM competitors c
                        JOIN competitor_profiles cp ON c.id = cp.competitor_id
                        LEFT JOIN competitor_posts posts ON cp.id = posts.profile_id
                            AND posts.scraped_at >= NOW() - (INTERVAL '1 day' * %s)
                        WHERE LOWER(cp.platform) = 'tiktok'
                        GROUP BY c.id, cp.handle, cp.profile_url, cp.last_checked, cp.id
                        HAVING
                            cp.last_checked IS NULL
                            OR cp.last_checked < NOW() - (INTERVAL '1 day' * %s)
                        ORDER BY cp.last_checked ASC NULLS FIRST
                    """, (self.scrape_interval_days, self.scrape_interval_days))
                    
                    competitors = []
                    for row in cur.fetchall():
                        competitors.append({
                            'id': str(row[0]),
                            'username': row[1],
                            'profile_url': row[2],
                            'last_checked': row[3],
                            'recent_post_count': row[4],
                            'profile_id': str(row[5])
                        })
                    
                    log.info(f"📊 Found {len(competitors)} TikTok competitors to scrape")
                    return competitors
                    
        except Exception as e:
            log.error(f"❌ Error querying competitors: {e}")
            return []
    
    def initialize_scraper(self) -> bool:
        """
        Initialize the TikTok scraper in guest mode (no login required).
        """
        try:
            log.info("🔧 Initializing TikTok scraper in guest mode...")
            
            # --- PROXY INTEGRATION ---
            # Attempt to get a working proxy from the free list
            from socialmedia.drivers.proxy_manager import proxy_manager
            
            # Try to get a proxy (with retries handled by manager)
            proxy = proxy_manager.get_working_proxy()
            
            if proxy:
                log.info(f"🌐 Using proxy: {proxy}")
            else:
                log.warning("⚠️ No working proxy found. Falling back to local IP (DIRECT connection).")
            # -------------------------
            
            # TikTok scraper works in guest mode - no credentials needed
            self.scraper = TikTokScraper(use_cookies=False, headless=True, proxy=proxy)
            
            log.info("✅ TikTok scraper initialized successfully")
            return True
            
        except Exception as e:
            log.error(f"❌ Error initializing scraper: {e}")
            return False
    
    def scrape_competitor(self, competitor: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scrape a single competitor's TikTok profile.
        Returns the scraped data for DB upload.
        """
        username = competitor['username']
        profile_url = competitor.get('profile_url') or f"https://www.tiktok.com/@{username}"
        
        log.info(f"🕷️ Scraping TikTok competitor: @{username}")
        
        try:
            # Use the scrape_profile method from TikTokScraper
            posts_data = self.scraper.scrape_profile(
                profile_url=profile_url,
                max_posts=self.max_posts_per_profile
            )
            
            if not posts_data:
                log.warning(f"⚠️ No posts found for @{username}")
                return None
            
            # Get profile info (followers, following, likes) from scraper
            profile_info = getattr(self.scraper, 'last_profile_info', {})
            followers = profile_info.get('followers', 0)
            
            log.info(f"✅ Successfully scraped {len(posts_data)} posts for @{username} ({followers:,} followers)")
            
            return {
                'username': username,
                'profile_url': profile_url,
                'posts': posts_data,
                'competitor_id': competitor['id'],
                'profile_id': competitor['profile_id'],
                'followers': followers,
                'profile_info': profile_info
            }
            
        except Exception as e:
            log.error(f"❌ Error scraping @{username}: {e}")
            return None
    
    def update_competitor_last_checked(self, competitor_profile_id: str):
        """
        Update the last_checked timestamp for a competitor profile.
        """
        try:
            with psycopg.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE competitor_profiles
                        SET last_checked = NOW()
                        WHERE id = %s
                    """, (competitor_profile_id,))
                    conn.commit()
                    log.debug(f"Updated last_checked for competitor profile {competitor_profile_id}")

        except Exception as e:
            log.error(f"❌ Error updating last_checked for competitor profile {competitor_profile_id}: {e}")
    
    def upload_posts_to_db(self, scrape_result: Dict[str, Any]) -> bool:
        """
        Upload scraped TikTok posts to the database with analytics.
        """
        from socialmedia.shared.upload_to_db import upload_tiktok_data_to_db
        
        try:
            return upload_tiktok_data_to_db(
                scrape_result['posts'],
                scrape_result['username'],
                scrape_result['competitor_id'],
                scrape_result['profile_id'],
                followers=scrape_result.get('followers', 0)
            )
        except Exception as e:
            log.error(f"❌ Error uploading posts to DB: {e}")
            return False
    
    def run_weekly_scrape(self) -> Dict[str, Any]:
        """
        Main method to run the weekly scraping process.
        """
        log.info("🚀 Starting weekly TikTok scraping process")
        
        # Get competitors that need scraping
        competitors = self.get_competitors_to_scrape()
        
        if not competitors:
            log.info("ℹ️ No TikTok competitors need scraping at this time")
            return {"status": "success", "message": "No competitors to scrape", "scraped": 0}
            
        # Mark all competitor profiles as checked immediately to prevent duplicate tasks
        log.info(f"🔒 Locking {len(competitors)} TikTok competitor profiles...")
        for comp in competitors:
            self.update_competitor_last_checked(comp['profile_id'])
        
        if not self.initialize_scraper():
            log.error("❌ Failed to initialize scraper, aborting weekly scrape")
            return {"status": "failed", "error": "Failed to initialize scraper"}
        
        try:
            # Scrape each competitor
            successful_scrapes = 0
            failed_scrapes = 0
            
            for competitor in competitors:
                try:
                    scrape_result = self.scrape_competitor(competitor)
                    
                    if scrape_result and scrape_result.get('posts'):
                        # Upload to database
                        if self.upload_posts_to_db(scrape_result):
                            successful_scrapes += 1
                        else:
                            failed_scrapes += 1
                    else:
                        failed_scrapes += 1
                        
                    # Add delay between competitors
                    import time
                    time.sleep(5)
                    
                except Exception as e:
                    log.error(f"❌ Unexpected error scraping {competitor['username']}: {e}")
                    failed_scrapes += 1
            
            log.info(f"📊 Weekly TikTok scraping completed: {successful_scrapes} successful, {failed_scrapes} failed")
        
            # Clear verified proxies after scraping is done
            try:
                from socialmedia.drivers.proxy_manager import proxy_manager
                proxy_manager.clear_verified_proxies()
            except Exception as e:
                log.warning(f"⚠️ Failed to clear verified proxies: {e}")
            
            # Clean up scrape_result JSON files
            try:
                import glob
                scrape_result_dir = os.path.join(os.path.dirname(__file__), "scrape_result")
                if os.path.exists(scrape_result_dir):
                    json_files = glob.glob(os.path.join(scrape_result_dir, "*.json"))
                    for f in json_files:
                        os.remove(f)
                    if json_files:
                        log.info(f"🗑️ Cleaned up {len(json_files)} TikTok scrape result JSON files")
            except Exception as e:
                log.warning(f"⚠️ Failed to clean up scrape results: {e}")
            
            return {
                "status": "success",
                "message": "Weekly TikTok scraping completed",
                "scraped": successful_scrapes,
                "failed": failed_scrapes
            }
            
        finally:
            # Clean up the scraper
            if self.scraper:
                self.scraper.close()
                log.info("🧹 TikTok scraper cleaned up")


def main():
    """
    Standalone execution for testing purposes.
    """
    scraper = WeeklyTikTokScraper()
    result = scraper.run_weekly_scrape()
    print(f"Result: {result}")


if __name__ == "__main__":
    main()
