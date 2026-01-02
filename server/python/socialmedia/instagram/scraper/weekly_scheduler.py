#!/usr/bin/env python3
"""
Weekly Instagram Scraper
This scraper is intigrated with the existing instaPage.py scraper to automatically scrape
Instagram competitors on a weekly basis.
"""

import os
import sys
import logging
import psycopg
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

# Add the parent directory to the path to import instaPage
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from socialmedia.instagram.scraper.profile_scraper import InstagramScraper

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://root:secret@localhost:5432/project_monopoly?sslmode=disable")

# Logging setup
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class WeeklyInstagramScraper:
    """
    Weekly Instagram scraper that processes all Instagram competitors
    that haven't been scraped in the last 7 days.
    """
    
    def __init__(self):
        self.database_url = DATABASE_URL
        self.scraper = None
        self.max_posts_per_profile = int(os.getenv("WEEKLY_MAX_POSTS", "10"))
        self.scrape_interval_days = float(os.getenv("WEEKLY_SCRAPE_INTERVAL", "7"))
        
    def get_competitors_to_scrape(self) -> List[Dict[str, Any]]:
        """
        Query the database for Instagram competitors that need scraping.
        Returns competitors that haven't been scraped in the last N days.
        """
        log.info("🔍 Querying database for competitors to scrape...")
        
        try:
            with psycopg.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    # Query for Instagram competitors that need scraping
                    # Updated for new schema: competitors table no longer has platform/username
                    # These are now in competitor_profiles table
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
                        WHERE LOWER(cp.platform) = 'instagram'
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
                    
                    log.info(f"📊 Found {len(competitors)} Instagram competitors to scrape")
                    return competitors
                    
        except Exception as e:
            log.error(f"❌ Error querying competitors: {e}")
            return []
    
    def initialize_scraper(self) -> bool:
        """
        Initialize the Instagram scraper in guest mode (no cookies/login).
        """
        try:
            log.info("🔧 Initializing Instagram scraper in guest mode...")
            
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
            
            # Initialize with use_cookies=False for pure guest mode
            # No credentials needed - Instagram profiles are publicly accessible
            self.scraper = InstagramScraper(use_cookies=False, proxy=proxy)
            
            
            # Attempt to login (which will go straight to guest mode)
            if not self.scraper.login():
                log.error("❌ Failed to initialize Instagram guest mode")
                return False
            
            log.info("✅ Instagram scraper initialized successfully")
            return True
            
        except Exception as e:
            log.error(f"❌ Error initializing scraper: {e}")
            return False
    
    def scrape_competitor(self, competitor: Dict[str, Any]) -> bool:
        """
        Scrape a single competitor's Instagram profile.
        """
        username = competitor['username']
        profile_url = competitor['profile_url']
        
        log.info(f"🕷️ Scraping competitor: @{username}")
        
        try:
            # Use the existing scrape_profile method from instaPage.py
            posts_data = self.scraper.scrape_profile(
                profile_url=profile_url,
                max_posts=self.max_posts_per_profile
            )
            
            if not posts_data:
                log.warning(f"⚠️ No posts found for @{username}")
                return False
            
            # Update the competitor profile's last_checked timestamp
            self.update_competitor_last_checked(competitor['profile_id'])
            
            log.info(f"✅ Successfully scraped {len(posts_data)} posts for @{username}")
            return True
            
        except Exception as e:
            log.error(f"❌ Error scraping @{username}: {e}")
            return False
    
    def update_competitor_last_checked(self, competitor_profile_id: str):
        """
        Update the last_checked timestamp for a competitor profile.
        This should be called after an attempt to scrape, regardless of success.
        Updated for new schema: last_checked is now in competitor_profiles table.
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
    
    def run_weekly_scrape(self):
        """
        Main method to run the weekly scraping process.
        """
        log.info("🚀 Starting weekly Instagram scraping process")
        
        # Get competitors that need scraping
        competitors = self.get_competitors_to_scrape()
        
        if not competitors:
            log.info("ℹ️ No competitors need scraping at this time")
            return
            
        # CRITICAL: Mark all competitor profiles as checked immediately to prevent auto_dispatch
        # from spawning multiple tasks for the same competitors while we are starting up.
        log.info(f"🔒 Locking {len(competitors)} competitor profiles to prevent duplicate scraping...")
        for comp in competitors:
            self.update_competitor_last_checked(comp['profile_id'])
        
        if not self.initialize_scraper():
            log.error("❌ Failed to initialize scraper, aborting weekly scrape")
            return
        
        try:
            # Scrape each competitor
            successful_scrapes = 0
            failed_scrapes = 0
            
            for competitor in competitors:
                try:
                    if self.scrape_competitor(competitor):
                        successful_scrapes += 1
                    else:
                        failed_scrapes += 1
                        
                    # Add a small delay between competitors to be respectful
                    import time
                    time.sleep(5)
                    
                except Exception as e:
                    log.error(f"❌ Unexpected error scraping {competitor['username']}: {e}")
                    failed_scrapes += 1
            
            log.info(f"📊 Weekly scraping completed: {successful_scrapes} successful, {failed_scrapes} failed")
        
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
                        log.info(f"🗑️ Cleaned up {len(json_files)} scrape result JSON files")
            except Exception as e:
                log.warning(f"⚠️ Failed to clean up scrape results: {e}")
            
        finally:
            # Clean up the scraper
            if self.scraper:
                self.scraper.close()
                log.info("🧹 Scraper cleaned up")

def main():
    """
    Standalone execution for testing purposes.
    """
    scraper = WeeklyInstagramScraper()
    scraper.run_weekly_scrape()

if __name__ == "__main__":
    main()
