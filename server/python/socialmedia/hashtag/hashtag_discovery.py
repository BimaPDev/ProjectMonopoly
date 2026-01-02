#!/usr/bin/env python3
"""
Hashtag Discovery System
Automatically discovers and scrapes hashtags from competitor posts.
- Extract hashtags from competitor posts
- Find hashtags we haven't scraped yet
- Scrape those hashtags
"""
import os
import sys
import psycopg
import logging
from typing import List, Set, Dict, Any
from datetime import datetime

# Set default DATABASE_URL if not already set
if not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "postgresql://root:secret@localhost:5434/project_monopoly?sslmode=disable"

DATABASE_URL = os.getenv("DATABASE_URL")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class HashtagDiscovery:
    """
    Discovers new hashtags from competitor posts and scrapes them.
    """
    
    # Hard limit to prevent infinite scraping - cannot be exceeded regardless of input
    MAX_ITERATIONS_LIMIT = 10
    
    def __init__(self, user_id: int = None, group_id: int = None, max_posts_per_hashtag: int = 50, platform: str = 'instagram', proxy: str = None, seed_hashtags: List[str] = None):
        self.database_url = DATABASE_URL
        self.user_id = user_id
        self.group_id = group_id
        self.max_posts_per_hashtag = max_posts_per_hashtag
        self.platform = platform.lower()
        self.proxy = proxy
        self.seed_hashtags = seed_hashtags or []
        
        # Handle special "DIRECT" value - means skip proxy entirely
        if self.proxy == "DIRECT":
            log.info("Direct connection mode enabled (no proxy)")
            self.proxy = None
        # If no explicit proxy provided, try to get one from ProxyManager
        # This is for scraping only - Docker/general app does not use proxies
        elif not self.proxy:
            try:
                # Add parent path to allow relative imports when run as script
                import sys
                import os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
                from socialmedia.drivers.proxy_manager import proxy_manager
                
                # First, try to get a proxy from existing verified list
                self.proxy = proxy_manager.get_working_proxy()
                
                # If no verified proxies exist, trigger a fresh validation
                if not self.proxy:
                    log.info("No verified proxies found. Fetching and validating fresh proxy list...")
                    proxy_manager.validate_all_proxies()
                    self.proxy = proxy_manager.get_working_proxy()
                
                if self.proxy:
                    log.info(f"Using auto-selected proxy from ProxyManager: {self.proxy}")
                else:
                    log.warning("ProxyManager found no working proxies. Scraping will use direct connection.")
            except Exception as e:
                log.warning(f"Failed to get proxy from ProxyManager: {e}. Scraping will use direct connection.")


        
    def get_competitor_hashtags(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get hashtags from competitor posts. Returns list of hashtags with their frequency.
        """
        log.info(f"Extracting hashtags from competitor posts (Platform: {self.platform})...")
        
        try:
            with psycopg.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    # Get hashtags from competitor posts
                    # If user_id is provided, filter by user's competitors
                    if self.user_id:
                        cur.execute("""
                            SELECT 
                                hashtag,
                                COUNT(*)::bigint as frequency
                            FROM (
                                SELECT UNNEST(hashtags) as hashtag
                                FROM competitor_posts cp
                                JOIN competitors c ON c.id = cp.competitor_id
                                JOIN user_competitors uc ON uc.competitor_id = c.id
                                WHERE uc.user_id = %s
                                  AND (uc.group_id = %s OR uc.group_id IS NULL)
                                  AND cp.posted_at >= NOW() - INTERVAL '28 days'
                                  AND cp.platform = %s
                                  AND cp.hashtags IS NOT NULL
                                  AND array_length(cp.hashtags, 1) > 0
                            ) as tags
                            WHERE LENGTH(hashtag) > 2
                            GROUP BY hashtag
                            ORDER BY frequency DESC
                            LIMIT %s
                        """, (self.user_id, self.group_id, self.platform, limit))
                    else:
                        # Get all hashtags from all competitor posts
                        cur.execute("""
                            SELECT 
                                hashtag,
                                COUNT(*)::bigint as frequency
                            FROM (
                                SELECT UNNEST(hashtags) as hashtag
                                FROM competitor_posts cp
                                WHERE cp.posted_at >= NOW() - INTERVAL '28 days'
                                  AND cp.platform = %s
                                  AND cp.hashtags IS NOT NULL
                                  AND array_length(cp.hashtags, 1) > 0
                            ) as tags
                            WHERE LENGTH(hashtag) > 2
                            GROUP BY hashtag
                            ORDER BY frequency DESC
                            LIMIT %s
                        """, (self.platform, limit,))
                    
                    results = []
                    for row in cur.fetchall():
                        results.append({
                            'hashtag': row[0],
                            'frequency': row[1]
                        })
                    
                    log.info(f"Found {len(results)} unique hashtags from competitor posts")
                    return results
                    
        except Exception as e:
            log.error(f"Error extracting competitor hashtags: {e}")
            return []
    
    def get_hashtag_posts_hashtags(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Extract unique hashtags from hashtag_posts in database (posts we've already scraped).
        Returns list of hashtags with their frequency.
        This enables recursive discovery - finding new hashtags from already scraped hashtag posts.
        """
        log.info(f"Extracting hashtags from hashtag posts (Platform: {self.platform})...")
        results = []
        # If seed hashtags are provided, use them
        if self.seed_hashtags:
            log.info(f"Using {len(self.seed_hashtags)} seed hashtags: {self.seed_hashtags}")
            for tag in self.seed_hashtags:
                results.append({"hashtag": tag.strip('#'), "frequency": 999})
        
        # If no seeds or we want more, fetch from DB
        try:
            with psycopg.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    # Get hashtags from hashtag_posts
                    cur.execute("""
                        SELECT 
                            hashtag,
                            COUNT(*)::bigint as frequency
                        FROM (
                            SELECT UNNEST(hashtags) as hashtag
                            FROM hashtag_posts hp
                            WHERE hp.posted_at >= NOW() - INTERVAL '28 days'
                              AND hp.platform = %s
                              AND hp.hashtags IS NOT NULL
                              AND array_length(hp.hashtags, 1) > 0
                        ) as tags
                        WHERE LENGTH(hashtag) > 2
                        GROUP BY hashtag
                        ORDER BY frequency DESC
                        LIMIT %s
                    """, (self.platform, limit,))
                    
                    # results = [] # Removed to preserve seed hashtags
                    for row in cur.fetchall():
                        results.append({
                            'hashtag': row[0],
                            'frequency': row[1]
                        })
                    
                    log.info(f"Found {len(results)} unique hashtags from hashtag posts")
                    return results
                    
        except Exception as e:
            log.error(f"Error extracting hashtag posts hashtags: {e}")
            return results  # Return what we have (e.g. seeds) even if DB fails
    
    def get_scraped_hashtags(self) -> Set[str]:
        """
        Get set of hashtags we've already scraped.
        """
        log.info(f"Checking which hashtags have already been scraped for {self.platform}...")
        
        try:
            with psycopg.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT DISTINCT hashtag
                        FROM hashtag_posts
                        WHERE platform = %s
                    """, (self.platform,))
                    
                    scraped = {row[0].lower() for row in cur.fetchall()}
                    log.info(f"Found {len(scraped)} already scraped hashtags")
                    return scraped
                    
        except Exception as e:
            log.error(f"Error getting scraped hashtags: {e}")
            return set()
    
    def get_unscraped_hashtags(self, limit: int = 20, include_hashtag_posts: bool = True) -> List[Dict[str, Any]]:
        """
        Find hashtags from competitors and hashtag_posts that we haven't scraped yet.
        Returns list of hashtags to scrape, ordered by frequency.
        """
        # Get hashtags from competitor posts
        competitor_hashtags = self.get_competitor_hashtags(limit * 2)  # Get more to filter
        
        # Get hashtags from hashtag_posts if recursive discovery is enabled
        hashtag_posts_hashtags = []
        if include_hashtag_posts:
            hashtag_posts_hashtags = self.get_hashtag_posts_hashtags(limit * 2)
        
        # Combine and deduplicate by hashtag, summing frequencies
        all_hashtags_dict = {}
        for ht in competitor_hashtags:
            hashtag_lower = ht['hashtag'].lower()
            if hashtag_lower not in all_hashtags_dict:
                all_hashtags_dict[hashtag_lower] = {
                    'hashtag': ht['hashtag'],  # Keep original case
                    'frequency': ht['frequency']
                }
            else:
                all_hashtags_dict[hashtag_lower]['frequency'] += ht['frequency']
        
        for ht in hashtag_posts_hashtags:
            hashtag_lower = ht['hashtag'].lower()
            if hashtag_lower not in all_hashtags_dict:
                all_hashtags_dict[hashtag_lower] = {
                    'hashtag': ht['hashtag'],
                    'frequency': ht['frequency']
                }
            else:
                all_hashtags_dict[hashtag_lower]['frequency'] += ht['frequency']
        
        # Convert back to list and sort by frequency
        all_hashtags = list(all_hashtags_dict.values())
        all_hashtags.sort(key=lambda x: x['frequency'], reverse=True)
        
        # Filter out already scraped hashtags
        scraped_hashtags = self.get_scraped_hashtags()
        
        unscraped = []
        for ht in all_hashtags:
            hashtag_lower = ht['hashtag'].lower()
            if hashtag_lower not in scraped_hashtags:
                unscraped.append(ht)
                if len(unscraped) >= limit:
                    break
        
        log.info(f"Found {len(unscraped)} unscraped hashtags to scrape")
        return unscraped
    
    def scrape_new_hashtags(self, max_hashtags: int = 10, include_hashtag_posts: bool = True) -> Dict[str, Any]:
        """
        Discover and scrape new hashtags from competitor posts and hashtag_posts.
        
        Args:
            max_hashtags: Maximum number of new hashtags to scrape
            include_hashtag_posts: If True, also check hashtag_posts for new hashtags (recursive discovery)
            
        Returns:
            Dictionary with scraping results
        """
        log.info("=" * 60)
        log.info(f"Starting Hashtag Discovery Process (Platform: {self.platform})")
        log.info("=" * 60)
        
        # Get unscraped hashtags (from both competitor posts and hashtag_posts)
        unscraped = self.get_unscraped_hashtags(limit=max_hashtags, include_hashtag_posts=include_hashtag_posts)
        
        if not unscraped:
            log.info("No new hashtags to scrape!")
            return {
                "status": "success",
                "hashtags_scraped": 0,
                "message": "No new hashtags found"
            }
        
        log.info(f"Found {len(unscraped)} new hashtags to scrape:")
        for ht in unscraped[:5]:  # Show first 5
            log.info(f"  - #{ht['hashtag']} (frequency: {ht['frequency']})")
        
        # Import scraper based on platform
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        
        scraper = None
        max_retries = 3
        import time
        from socialmedia.hashtag.upload_hashtag_posts_to_db import upload_hashtag_posts_to_db
        
        if self.platform == 'instagram':
            from socialmedia.instagram.scraper.profile_scraper import InstagramScraper
            from selenium.common.exceptions import NoSuchWindowException
            
            # Initialize scraper with retry logic for browser window closing issues
            username = os.getenv("INSTAGRAM_USERNAME")
            password = os.getenv("INSTAGRAM_PASSWORD")
            
            # Use headless mode unless explicitly disabled (for local testing, set HEADLESS=false)
            headless = os.getenv("HEADLESS", "true").lower() not in ("false", "0", "no")
            
            # Check if we have credentials - if not, use guest mode
            use_login = username and password
            
            for attempt in range(1, max_retries + 1):
                try:
                    if attempt > 1:
                        log.info(f"Retry attempt {attempt}/{max_retries} for scraper initialization...")
                        time.sleep(3)  # Wait before retrying
                        # Clean up previous scraper if it exists
                        if scraper:
                            try:
                                scraper.close()
                            except:
                                pass
                    
                    # Use guest mode (no cookies/login) if no credentials
                    scraper = InstagramScraper(
                        username=username if use_login else None, 
                        password=password if use_login else None, 
                        headless=headless, 
                        proxy=self.proxy,
                        use_cookies=use_login  # Only use cookies if we have login credentials
                    )
                    
                    # Only attempt login if we have credentials
                    if use_login:
                        if not scraper.login():
                            log.error("Failed to login to Instagram")
                            if scraper:
                                scraper.close()
                            if attempt < max_retries:
                                continue  # Retry
                            return {"status": "failed", "error": "Failed to login"}
                    else:
                        log.info("Running Instagram scraper in guest mode (no login)")
                    
                    # Success, exit retry loop
                    break

                    
                except Exception as e:
                    # Generic error handling primarily for window closed exceptions
                    error_msg = str(e)
                    log.warning(f"Error initializing scraper (possibly window closed): {e} (attempt {attempt}/{max_retries})")
                    if scraper:
                        try:
                            scraper.close()
                        except:
                            pass
                    if attempt < max_retries:
                        continue  # Retry
                    else:
                        return {"status": "failed", "error": f"Scraper initialization failed after {max_retries} attempts: {e}"}

        elif self.platform == 'tiktok':
            from socialmedia.tiktok.scraper.profile_scraper import TikTokScraper
            
            # TikTok usually doesn't need login for public hashtag access
            # But we can pass headless param
            headless = os.getenv("HEADLESS", "true").lower() not in ("false", "0", "no")
            
            # Smart proxy retry logic - try up to 3 different proxies if one fails
            max_proxy_attempts = 3
            for proxy_attempt in range(1, max_proxy_attempts + 1):
                try:
                    current_proxy = self.proxy
                    
                    # If retrying, get a new proxy from the manager
                    if proxy_attempt > 1:
                        log.info(f"Proxy attempt {proxy_attempt}/{max_proxy_attempts}: Getting new proxy...")
                        try:
                            from socialmedia.drivers.proxy_manager import proxy_manager
                            current_proxy = proxy_manager.get_working_proxy()
                            if current_proxy:
                                log.info(f"Switched to proxy: {current_proxy}")
                            else:
                                log.warning("No more proxies available, using direct connection")
                        except Exception as pe:
                            log.warning(f"Failed to get new proxy: {pe}")
                            current_proxy = None
                    
                    scraper = TikTokScraper(headless=headless, use_cookies=False, proxy=current_proxy)
                    
                    # Test the scraper by doing a quick navigation test
                    # If this succeeds, we have a working setup
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    is_timeout = 'timeout' in error_msg or 'timed_out' in error_msg or 'err_timed_out' in error_msg
                    
                    log.warning(f"TikTok scraper init failed (attempt {proxy_attempt}/{max_proxy_attempts}): {e}")
                    
                    if scraper:
                        try:
                            scraper.close()
                        except:
                            pass
                        scraper = None
                    
                    if proxy_attempt < max_proxy_attempts and is_timeout:
                        log.info("Timeout detected - will try a different proxy...")
                        continue  # Try again with new proxy
                    elif proxy_attempt >= max_proxy_attempts:
                        log.error(f"Failed to initialize TikTok scraper after {max_proxy_attempts} proxy attempts")
                        return {"status": "failed", "error": f"TikTok scraper init failed after {max_proxy_attempts} attempts: {e}"}

        
        else:
            return {"status": "failed", "error": f"Unsupported platform: {self.platform}"}
            
        
        if not scraper:
            return {"status": "failed", "error": "Failed to initialize scraper"}
        
        results = {
            "status": "success",
            "hashtags_scraped": 0,
            "hashtags_failed": 0,
            "total_posts_scraped": 0,
            "details": []
        }
        
        # Scrape each hashtag
        for ht_info in unscraped:
            hashtag = ht_info['hashtag']
            try:
                log.info(f"\nScraping hashtag: #{hashtag}")
                
                # Disable auto-upload (we'll do it manually)
                original_upload = os.getenv("UPLOAD_AFTER_SCRAPE", "1")
                os.environ["UPLOAD_AFTER_SCRAPE"] = "0"
                
                # Scrape the hashtag
                if self.platform == 'instagram':
                    posts_data = scraper.scrape_hashtag(hashtag, max_posts=self.max_posts_per_hashtag)
                elif self.platform == 'tiktok':
                    # Smart retry with proxy rotation for TikTok
                    # Free proxies have low success rate on TikTok, so we try many
                    posts_data = None
                    max_scrape_retries = 25  # Try up to 25 different proxies


                    
                    for scrape_attempt in range(1, max_scrape_retries + 1):
                        try:
                            posts_data = scraper.scrape_hashtag(hashtag, max_posts=self.max_posts_per_hashtag)
                            if posts_data and len(posts_data) > 0:
                                break  # Success - got actual data
                            else:
                                # Empty results - likely proxy failure (page didn't load)
                                log.warning(f"Scrape attempt {scrape_attempt}/{max_scrape_retries} returned 0 results (proxy may have failed)")
                                
                                # Take screenshot to see what's happening
                                try:
                                    screenshot_path = f"/app/screenshots/proxy_fail_{scrape_attempt}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                                    os.makedirs("/app/screenshots", exist_ok=True)
                                    scraper.driver.save_screenshot(screenshot_path)
                                    log.info(f"Screenshot saved to: {screenshot_path}")
                                except Exception as ss_err:
                                    log.warning(f"Failed to save screenshot: {ss_err}")
                                
                                if scrape_attempt < max_scrape_retries:
                                    log.info("Empty results - reinitializing scraper with new proxy...")
                                    try:
                                        scraper.close()
                                    except:
                                        pass

                                    
                                    # Get a new proxy
                                    try:
                                        from socialmedia.drivers.proxy_manager import proxy_manager
                                        new_proxy = proxy_manager.get_working_proxy()
                                        if new_proxy:
                                            log.info(f"Switched to proxy: {new_proxy}")
                                        else:
                                            log.warning("No more proxies, trying direct connection")
                                            new_proxy = None
                                    except Exception as pe:
                                        log.warning(f"Failed to get new proxy: {pe}")
                                        new_proxy = None
                                    
                                    # Reinitialize scraper with new proxy
                                    from socialmedia.tiktok.scraper.profile_scraper import TikTokScraper
                                    headless = os.getenv("HEADLESS", "true").lower() not in ("false", "0", "no")
                                    scraper = TikTokScraper(headless=headless, use_cookies=False, proxy=new_proxy)
                                    continue
                                    
                        except Exception as scrape_error:
                            error_msg = str(scrape_error).lower()
                            # Detect proxy-related failures: timeout, aborted, context destroyed, connection errors
                            # Also detect page-load failures (null properties = page didn't load)
                            is_proxy_failure = any(pattern in error_msg for pattern in [
                                'timeout', 'timed_out', 'err_timed_out', 'err_aborted',
                                'context was destroyed', 'navigation', 'net::err_',
                                'connection refused', 'connection reset', 'proxy',
                                'properties of null', 'scrollheight', 'typeerror',
                                'something went wrong'  # TikTok error page
                            ])

                            
                            log.warning(f"Scrape attempt {scrape_attempt}/{max_scrape_retries} failed: {scrape_error}")
                            
                            # Take screenshot to see what's happening
                            try:
                                screenshot_path = f"/app/screenshots/exception_{scrape_attempt}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                                os.makedirs("/app/screenshots", exist_ok=True)
                                scraper.driver.save_screenshot(screenshot_path)
                                log.info(f"Screenshot saved to: {screenshot_path}")
                            except Exception as ss_err:
                                log.warning(f"Failed to save screenshot: {ss_err}")
                            
                            if scrape_attempt < max_scrape_retries and is_proxy_failure:
                                log.info("Proxy failure detected - reinitializing scraper with new proxy...")

                                try:
                                    scraper.close()
                                except:
                                    pass
                                
                                # Get a new proxy
                                try:
                                    from socialmedia.drivers.proxy_manager import proxy_manager
                                    new_proxy = proxy_manager.get_working_proxy()
                                    if new_proxy:
                                        log.info(f"Switched to proxy: {new_proxy}")
                                    else:
                                        log.warning("No more proxies, trying direct connection")
                                        new_proxy = None
                                except Exception as pe:
                                    log.warning(f"Failed to get new proxy: {pe}")
                                    new_proxy = None
                                
                                # Reinitialize scraper with new proxy
                                from socialmedia.tiktok.scraper.profile_scraper import TikTokScraper
                                headless = os.getenv("HEADLESS", "true").lower() not in ("false", "0", "no")
                                scraper = TikTokScraper(headless=headless, use_cookies=False, proxy=new_proxy)
                                continue
                            else:
                                raise scrape_error  # Re-raise if not proxy failure or out of retries


                
                # Restore upload setting
                os.environ["UPLOAD_AFTER_SCRAPE"] = original_upload
                
                if posts_data:
                    # Find the JSON file that was just created
                    import glob
                    scrape_result_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scrape_result")
                    
                    if self.platform == 'instagram':
                         json_files = glob.glob(os.path.join(scrape_result_dir, f"{hashtag}_hashtag_posts_*.json"))
                    elif self.platform == 'tiktok':
                        # Pattern likely: {hashtag}_tiktoks_{timestamp}.json or similar depending on implementation
                        # But wait, scrape_hashtag in tiktok wasn't saving to file in the snippet I saw?
                        # Let's assume it might not save to file OR saves with different name.
                        # Actually standard practice here is to save manually if not saved, but upload script takes a file path.
                        # So we MUST save it to a temp file if it wasn't saved.
                        # However, let's look for any recently modified json files if we are unsure.
                        # Or better, save it right here to be safe.
                        
                        # Just in case the scraper didn't save it (or used a hard-to-guess name), let's save it ourselves to be deterministic
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{hashtag}_tiktoks_{timestamp}.json"
                        filepath = os.path.join(scrape_result_dir, filename)
                        
                        # TikTok scraper might have saved it, but let's overwrite/create new one to be sure for upload
                        with open(filepath, 'w', encoding='utf-8') as f:
                            json.dump({
                                "hashtag_info": {"hashtag": hashtag, "platform": "tiktok"},
                                "posts": posts_data
                            }, f, default=str)
                        
                        json_files = [filepath]

                    if json_files:
                        # Get the most recent file
                        latest_file = max(json_files, key=os.path.getctime)
                        
                        # Upload to database
                        success = upload_hashtag_posts_to_db(latest_file)
                        
                        if success:
                            results["hashtags_scraped"] += 1
                            results["total_posts_scraped"] += len(posts_data)
                            results["details"].append({
                                "hashtag": hashtag,
                                "status": "success",
                                "posts": len(posts_data)
                            })
                            log.info(f"Successfully scraped and uploaded {len(posts_data)} posts for #{hashtag}")
                        else:
                            results["hashtags_failed"] += 1
                            results["details"].append({
                                "hashtag": hashtag,
                                "status": "upload_failed",
                                "posts": len(posts_data)
                            })
                    else:
                        log.warning(f"Could not find JSON file for #{hashtag}")
                        # Fallback: try to upload from memory if we had logic for it, but upload_hashtag_posts_to_db takes file path
                        results["hashtags_failed"] += 1
                else:
                    log.warning(f"No posts found for #{hashtag}")
                    results["hashtags_failed"] += 1
                    results["details"].append({
                        "hashtag": hashtag,
                        "status": "no_posts",
                        "posts": 0
                    })
                
                # Small delay between hashtags
                import time
                time.sleep(5)
                
            except Exception as e:
                log.error(f"Error scraping #{hashtag}: {e}")
                results["hashtags_failed"] += 1
                results["details"].append({
                    "hashtag": hashtag,
                    "status": "error",
                    "error": str(e)
                })
        
        # Close scraper
        try:
            if hasattr(scraper, 'close'):
                scraper.close()
            elif hasattr(scraper, 'driver') and hasattr(scraper.driver, 'quit'):
                scraper.driver.quit()
        except:
            pass
        
        log.info("\n" + "=" * 60)
        log.info("Hashtag Discovery Complete")
        log.info(f"  Hashtags scraped: {results['hashtags_scraped']}")
        log.info(f"  Hashtags failed: {results['hashtags_failed']}")
        log.info(f"  Total posts scraped: {results['total_posts_scraped']}")
        log.info("=" * 60)
        
        return results
    
    def discover_and_scrape_recursive(self, max_iterations: int = 3, max_hashtags_per_iteration: int = 10) -> Dict[str, Any]:
        """
        Recursively discover and scrape hashtags.
        
        Workflow:
        - Extract hashtags from competitor posts
        - Find hashtags we haven't scraped yet
        - Scrape those hashtags
        - Extract hashtags from the scraped posts
        - Find new hashtags from those
        - Repeat until max_iterations or no new hashtags found
        
        Note:
            max_iterations is capped at MAX_ITERATIONS_LIMIT (10) to prevent infinite loops.
            
        Returns:
            Dictionary with scraping results across all iterations
        """
        # Enforce hard limit to prevent infinite scraping
        if max_iterations > self.MAX_ITERATIONS_LIMIT:
            log.warning(f"Requested {max_iterations} iterations exceeds limit of {self.MAX_ITERATIONS_LIMIT}. Capping at {self.MAX_ITERATIONS_LIMIT}.")
            max_iterations = self.MAX_ITERATIONS_LIMIT
        
        log.info("=" * 60)
        log.info(f"Starting RECURSIVE Hashtag Discovery Process (Platform: {self.platform})")
        log.info(f"Max iterations: {max_iterations} (hard limit: {self.MAX_ITERATIONS_LIMIT})")
        log.info("=" * 60)
        
        all_results = {
            "status": "success",
            "iterations": 0,
            "total_hashtags_scraped": 0,
            "total_hashtags_failed": 0,
            "total_posts_scraped": 0,
            "iteration_details": []
        }
        
        for iteration in range(1, max_iterations + 1):
            log.info(f"\n{'='*60}")
            log.info(f"ITERATION {iteration}/{max_iterations}")
            log.info(f"{'='*60}")
            
            # First iteration: check both competitor posts and hashtag_posts
            # Subsequent iterations: only check hashtag_posts (recursive discovery)
            include_hashtag_posts = True  # Always include hashtag_posts for recursive discovery
            
            iteration_result = self.scrape_new_hashtags(
                max_hashtags=max_hashtags_per_iteration,
                include_hashtag_posts=include_hashtag_posts
            )
            
            all_results["iterations"] = iteration
            all_results["total_hashtags_scraped"] += iteration_result.get("hashtags_scraped", 0)
            all_results["total_hashtags_failed"] += iteration_result.get("hashtags_failed", 0)
            all_results["total_posts_scraped"] += iteration_result.get("total_posts_scraped", 0)
            all_results["iteration_details"].append({
                "iteration": iteration,
                "hashtags_scraped": iteration_result.get("hashtags_scraped", 0),
                "hashtags_failed": iteration_result.get("hashtags_failed", 0),
                "posts_scraped": iteration_result.get("total_posts_scraped", 0),
                "details": iteration_result.get("details", [])
            })
            
            # If no hashtags were scraped in this iteration, stop
            if iteration_result.get("hashtags_scraped", 0) == 0:
                log.info(f"\nNo new hashtags found in iteration {iteration}. Stopping recursive discovery.")
                break
            
            # Small delay between iterations
            import time
            if iteration < max_iterations:
                log.info(f"\nWaiting 10 seconds before next iteration...")
                time.sleep(10)
        
        log.info("\n" + "=" * 60)
        log.info("RECURSIVE Hashtag Discovery Complete")
        log.info(f"  Total iterations: {all_results['iterations']}")
        log.info(f"  Total hashtags scraped: {all_results['total_hashtags_scraped']}")
        log.info(f"  Total hashtags failed: {all_results['total_hashtags_failed']}")
        log.info(f"  Total posts scraped: {all_results['total_posts_scraped']}")
        log.info("=" * 60)
        
        return all_results

def main():
    # for testing
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Discover and scrape hashtags from competitor posts")
    parser.add_argument(
        "--user-id",
        type=int,
        default=None,
        help="User ID to filter competitors (optional)"
    )
    parser.add_argument(
        "--group-id",
        type=int,
        default=None,
        help="Group ID to filter competitors (optional)"
    )
    parser.add_argument(
        "--max-hashtags",
        type=int,
        default=10,
        help="Maximum number of new hashtags to scrape (default: 10)"
    )
    parser.add_argument(
        "--max-posts",
        type=int,
        default=50,
        help="Maximum posts to scrape per hashtag (default: 50)"
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Enable recursive discovery (extract hashtags from scraped posts and repeat)"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum iterations for recursive discovery (default: 3)"
    )
    parser.add_argument(
        "--platform",
        type=str,
        default="instagram",
        choices=["instagram", "tiktok"],
        help="Platform to scrape (instagram or tiktok)"
    )
    parser.add_argument(
        "--proxy",
        type=str,
        default=None,
        help="Proxy URL (e.g. http://user:pass@host:port)"
    )
    parser.add_argument(
        "--no-proxy",
        action="store_true",
        help="Disable automatic proxy selection (use direct connection)"
    )
    parser.add_argument(
        "--seed",
        type=str,
        default=None,
        help="Seed hashtags (comma-separated, e.g. 'indiegame,gamedev')"
    )

    
    args = parser.parse_args()
    
    # User requested top 10 iteration, so if platform is tiktok and max_posts wasn't explicitly set (it defaults to 50),
    # let's respect that request if the user implies default behavior should be 10 for tiktok.
    # But cli args override defaults. So we'll trust the caller to pass --max-posts 10.
    
    
    # Parse seed hashtags if provided (comma-separated CLI arg)
    seed_hashtags = []
    if args.seed:
        seed_hashtags = [t.strip() for t in args.seed.split(',')]
    
    # Handle --no-proxy flag: use special value to disable auto-proxy
    proxy_value = args.proxy
    if args.no_proxy:
        proxy_value = "DIRECT"  # Special value to indicate direct connection
        log.info("--no-proxy flag set: Using direct connection (no proxy)")
        
    discovery = HashtagDiscovery(
        user_id=args.user_id,
        group_id=args.group_id,
        max_posts_per_hashtag=args.max_posts,
        platform=args.platform,
        proxy=proxy_value,
        seed_hashtags=seed_hashtags
    )

    
    if args.recursive:
        results = discovery.discover_and_scrape_recursive(
            max_iterations=args.max_iterations,
            max_hashtags_per_iteration=args.max_hashtags
        )
        if results["status"] == "success":
            print(f"\nRecursive discovery complete!")
            print(f"   Iterations: {results['iterations']}")
            print(f"   Total hashtags scraped: {results['total_hashtags_scraped']}")
            print(f"   Total posts: {results['total_posts_scraped']}")
        else:
            print(f"\nError: {results.get('error', 'Unknown error')}")
            sys.exit(1)
    else:
        results = discovery.scrape_new_hashtags(max_hashtags=args.max_hashtags)
        if results["status"] == "success":
            print(f"\nSuccessfully scraped {results['hashtags_scraped']} hashtags")
            print(f"   Total posts: {results['total_posts_scraped']}")
        else:
            print(f"\nError: {results.get('error', 'Unknown error')}")
            sys.exit(1)

if __name__ == "__main__":
    main()

