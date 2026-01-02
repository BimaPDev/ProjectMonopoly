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
    os.environ["DATABASE_URL"] = "postgresql://root:secret@localhost:5432/project_monopoly?sslmode=disable"

DATABASE_URL = os.getenv("DATABASE_URL")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class HashtagDiscovery:
    """
    Discovers new hashtags from competitor posts and scrapes them.
    """
    
    # Hard limit to prevent infinite scraping - cannot be exceeded regardless of input
    MAX_ITERATIONS_LIMIT = 10
    
    def __init__(self, user_id: int = None, group_id: int = None, max_posts_per_hashtag: int = 50):
        self.database_url = DATABASE_URL
        self.user_id = user_id
        self.group_id = group_id
        self.max_posts_per_hashtag = max_posts_per_hashtag
        
    def get_competitor_hashtags(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get hashtags from competitor posts. Returns list of hashtags with their frequency.
        """
        log.info("Extracting hashtags from competitor posts...")
        
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
                                  AND cp.hashtags IS NOT NULL
                                  AND array_length(cp.hashtags, 1) > 0
                            ) as tags
                            WHERE LENGTH(hashtag) > 2
                            GROUP BY hashtag
                            ORDER BY frequency DESC
                            LIMIT %s
                        """, (self.user_id, self.group_id, limit))
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
                                  AND cp.hashtags IS NOT NULL
                                  AND array_length(cp.hashtags, 1) > 0
                            ) as tags
                            WHERE LENGTH(hashtag) > 2
                            GROUP BY hashtag
                            ORDER BY frequency DESC
                            LIMIT %s
                        """, (limit,))
                    
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
        log.info("Extracting hashtags from hashtag posts...")
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
                              AND hp.hashtags IS NOT NULL
                              AND array_length(hp.hashtags, 1) > 0
                        ) as tags
                        WHERE LENGTH(hashtag) > 2
                        GROUP BY hashtag
                        ORDER BY frequency DESC
                        LIMIT %s
                    """, (limit,))
                    
                    results = []
                    for row in cur.fetchall():
                        results.append({
                            'hashtag': row[0],
                            'frequency': row[1]
                        })
                    
                    log.info(f"Found {len(results)} unique hashtags from hashtag posts")
                    return results
                    
        except Exception as e:
            log.error(f"Error extracting hashtag posts hashtags: {e}")
            return []
    
    def get_scraped_hashtags(self) -> Set[str]:
        """
        Get set of hashtags we've already scraped.
        """
        log.info("Checking which hashtags have already been scraped...")
        
        try:
            with psycopg.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT DISTINCT hashtag
                        FROM hashtag_posts
                        WHERE platform = 'instagram'
                    """)
                    
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
        log.info("Starting Hashtag Discovery Process")
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
        
        # Import scraper
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from socialmedia.instagram.scraper.profile_scraper import InstagramScraper
        from socialmedia.hashtag.upload_hashtag_posts_to_db import upload_hashtag_posts_to_db
        from selenium.common.exceptions import NoSuchWindowException
        
        # Initialize scraper with retry logic for browser window closing issues
        username = os.getenv("INSTAGRAM_USERNAME")
        password = os.getenv("INSTAGRAM_PASSWORD")
        
        # Use headless mode unless explicitly disabled (for local testing, set HEADLESS=false)
        headless = os.getenv("HEADLESS", "true").lower() not in ("false", "0", "no")
        
        scraper = None
        max_retries = 3
        import time
        
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
                
                scraper = InstagramScraper(username, password, headless=headless)
                
                if not scraper.login():
                    log.error("Failed to login to Instagram")
                    if scraper:
                        scraper.close()
                    if attempt < max_retries:
                        continue  # Retry
                    return {"status": "failed", "error": "Failed to login"}
                
                # Success, exit retry loop
                break
                
            except NoSuchWindowException as e:
                # Browser window closed unexpectedly - retry
                log.warning(f"Browser window closed unexpectedly (attempt {attempt}/{max_retries})")
                if scraper:
                    try:
                        scraper.close()
                    except:
                        pass
                if attempt < max_retries:
                    continue  # Retry
                else:
                    return {"status": "failed", "error": f"Browser window closed after {max_retries} attempts"}
            except Exception as e:
                error_msg = str(e)
                # Check if it's a window-related error even if not NoSuchWindowException
                if "no such window" in error_msg.lower() or "target window already closed" in error_msg.lower():
                    log.warning(f"Browser window closed unexpectedly (attempt {attempt}/{max_retries})")
                    if scraper:
                        try:
                            scraper.close()
                        except:
                            pass
                    if attempt < max_retries:
                        continue  # Retry
                    else:
                        return {"status": "failed", "error": f"Browser window closed after {max_retries} attempts"}
                else:
                    # Different error, don't retry
                    log.error(f"Error initializing scraper: {e}")
                    if scraper:
                        try:
                            scraper.close()
                        except:
                            pass
                    return {"status": "failed", "error": str(e)}
        
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
                posts_data = scraper.scrape_hashtag(hashtag, max_posts=self.max_posts_per_hashtag)
                
                # Restore upload setting
                os.environ["UPLOAD_AFTER_SCRAPE"] = original_upload
                
                if posts_data:
                    # Find the JSON file that was just created
                    import glob
                    scrape_result_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scrape_result")
                    json_files = glob.glob(os.path.join(scrape_result_dir, f"{hashtag}_hashtag_posts_*.json"))
                    
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
        
        scraper.close()
        
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
        log.info("Starting RECURSIVE Hashtag Discovery Process")
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
    
    args = parser.parse_args()
    
    discovery = HashtagDiscovery(
        user_id=args.user_id,
        group_id=args.group_id,
        max_posts_per_hashtag=args.max_posts
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

