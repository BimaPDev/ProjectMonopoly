#!/usr/bin/env python3
"""
Force Scrape CLI
================

A command-line utility to manually trigger scraping tasks when automatic
scraping fails or you need immediate results.

Usage:
    # Force scrape all Instagram competitors
    python force_scrape.py instagram
    
    # Force scrape all TikTok competitors  
    python force_scrape.py tiktok
    
    # Force scrape both platforms
    python force_scrape.py all
    
    # Force scrape a specific competitor by handle
    python force_scrape.py instagram --handle @username
    
    # List pending scrapes (competitors that need scraping)
    python force_scrape.py status
    
    # Reset last_checked for a competitor (forces next auto-scrape)
    python force_scrape.py reset --handle @username

Author: ProjectMonopoly Team
Created: 2025-12-29
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

# Add parent directory to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(SCRIPT_DIR, "..", ".env"))

import psycopg

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)
log = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://root:secret@localhost:5433/project_monopoly?sslmode=disable"
)


def get_db_connection():
    """Get a database connection."""
    return psycopg.connect(DATABASE_URL, autocommit=True)


def get_pending_scrapes(platform: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get list of competitors that need scraping.
    
    Args:
        platform: Optional platform filter ('instagram', 'tiktok', or None for all)
        
    Returns:
        List of competitor records needing scrapes
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if platform:
                cur.execute("""
                    SELECT cp.id, cp.competitor_id, cp.platform, cp.handle,
                           cp.followers, cp.last_checked
                    FROM competitor_profiles cp
                    WHERE LOWER(cp.platform) = LOWER(%s)
                      AND (cp.last_checked IS NULL 
                           OR cp.last_checked < NOW() - INTERVAL '7 days')
                    ORDER BY cp.last_checked ASC NULLS FIRST
                """, (platform,))
            else:
                cur.execute("""
                    SELECT cp.id, cp.competitor_id, cp.platform, cp.handle,
                           cp.followers, cp.last_checked
                    FROM competitor_profiles cp
                    WHERE cp.last_checked IS NULL 
                       OR cp.last_checked < NOW() - INTERVAL '7 days'
                    ORDER BY cp.platform, cp.last_checked ASC NULLS FIRST
                """)
            
            columns = ['id', 'competitor_id', 'platform', 'handle', 
                      'followers', 'last_checked']
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def get_all_competitors(platform: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get all competitors, optionally filtered by platform."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if platform:
                cur.execute("""
                    SELECT cp.id, cp.competitor_id, cp.platform, cp.handle,
                           cp.followers, cp.last_checked
                    FROM competitor_profiles cp
                    WHERE LOWER(cp.platform) = LOWER(%s)
                    ORDER BY cp.handle
                """, (platform,))
            else:
                cur.execute("""
                    SELECT cp.id, cp.competitor_id, cp.platform, cp.handle,
                           cp.followers, cp.last_checked
                    FROM competitor_profiles cp
                    ORDER BY cp.platform, cp.handle
                """)
            
            columns = ['id', 'competitor_id', 'platform', 'handle', 
                      'followers', 'last_checked']
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def get_competitor_by_handle(handle: str) -> Optional[Dict[str, Any]]:
    """Get a competitor by their handle."""
    # Remove @ prefix if present
    handle = handle.lstrip('@')
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT cp.id, cp.competitor_id, cp.platform, cp.handle,
                       cp.followers, cp.last_checked
                FROM competitor_profiles cp
                WHERE LOWER(cp.handle) = LOWER(%s)
            """, (handle,))
            
            row = cur.fetchone()
            if row:
                columns = ['id', 'competitor_id', 'platform', 'handle', 
                          'followers', 'last_checked']
                return dict(zip(columns, row))
            return None


def reset_last_checked(handle: str) -> bool:
    """
    Reset last_checked to NULL for a competitor, forcing next auto-scrape.
    
    Args:
        handle: Competitor handle to reset
        
    Returns:
        bool: True if successful
    """
    handle = handle.lstrip('@')
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE competitor_profiles
                SET last_checked = NULL
                WHERE LOWER(handle) = LOWER(%s)
                RETURNING id, handle, platform
            """, (handle,))
            
            row = cur.fetchone()
            if row:
                log.info("✅ Reset last_checked for %s (%s)", row[1], row[2])
                return True
            else:
                log.warning("⚠️  No competitor found with handle: %s", handle)
                return False


def force_instagram_scrape(handle: Optional[str] = None) -> Dict[str, Any]:
    """
    Force an Instagram scrape immediately.
    
    Args:
        handle: Optional specific handle to scrape (scrapes all if not provided)
        
    Returns:
        dict: Result of the scrape operation
    """
    log.info("🔄 Starting forced Instagram scrape...")
    
    try:
        from socialmedia.weekly_scraper import WeeklyInstagramScraper
        
        if handle:
            # Scrape specific competitor
            handle = handle.lstrip('@')
            competitor = get_competitor_by_handle(handle)
            
            if not competitor:
                return {"status": "error", "message": f"No competitor found with handle: {handle}"}
            
            if competitor['platform'].lower() != 'instagram':
                return {"status": "error", "message": f"Competitor {handle} is on {competitor['platform']}, not Instagram"}
            
            log.info("📸 Scraping Instagram profile: @%s", handle)
            
            # Use single-profile scrape with guest mode (no cookies)
            from socialmedia.instaPage import InstagramScraper
            from socialmedia.upload_to_db import save_instagram_data_to_db
            
            scraper = InstagramScraper(use_cookies=False)
            if not scraper.login():
                return {"status": "error", "message": "Failed to initialize Instagram guest mode"}
            
            try:
                profile_url = f"https://www.instagram.com/{handle}/"
                data = scraper.scrape_profile(profile_url, max_posts=30)
                
                if data:
                    save_instagram_data_to_db(data, competitor['competitor_id'])
                    log.info("✅ Successfully scraped and saved @%s", handle)
                    return {
                        "status": "success",
                        "message": f"Scraped @{handle}",
                        "posts_found": len(data.get('posts', []))
                    }
                else:
                    return {"status": "error", "message": f"No data returned for @{handle}"}
            finally:
                scraper.close()
        else:
            # Scrape all pending Instagram competitors
            scraper = WeeklyInstagramScraper()
            result = scraper.run_weekly_scrape()
            
            log.info("✅ Instagram scrape completed")
            return {
                "status": "success",
                "message": "Instagram scrape completed",
                "result": result
            }
            
    except Exception as e:
        log.exception("❌ Instagram scrape failed: %s", e)
        return {"status": "error", "message": str(e)}


def force_tiktok_scrape(handle: Optional[str] = None) -> Dict[str, Any]:
    """
    Force a TikTok scrape immediately.
    
    Args:
        handle: Optional specific handle to scrape (scrapes all if not provided)
        
    Returns:
        dict: Result of the scrape operation
    """
    log.info("🔄 Starting forced TikTok scrape...")
    
    try:
        from socialmedia.weekly_tiktok_scraper import WeeklyTikTokScraper
        
        if handle:
            # Scrape specific competitor
            handle = handle.lstrip('@')
            competitor = get_competitor_by_handle(handle)
            
            if not competitor:
                return {"status": "error", "message": f"No competitor found with handle: {handle}"}
            
            if competitor['platform'].lower() != 'tiktok':
                return {"status": "error", "message": f"Competitor {handle} is on {competitor['platform']}, not TikTok"}
            
            log.info("🎵 Scraping TikTok profile: @%s", handle)
            
            # Use single-profile scrape
            from socialmedia.tiktok_scraper import TikTokScraper
            from socialmedia.upload_to_db import save_tiktok_data_to_db
            
            scraper = TikTokScraper()
            
            try:
                data = scraper.scrape_profile(handle, max_videos=30)
                
                if data:
                    save_tiktok_data_to_db(data, competitor['competitor_id'])
                    log.info("✅ Successfully scraped and saved @%s", handle)
                    return {
                        "status": "success", 
                        "message": f"Scraped @{handle}",
                        "videos_found": len(data.get('videos', []))
                    }
                else:
                    return {"status": "error", "message": f"No data returned for @{handle}"}
            finally:
                scraper.close()
        else:
            # Scrape all pending TikTok competitors
            scraper = WeeklyTikTokScraper()
            result = scraper.run_weekly_scrape()
            
            log.info("✅ TikTok scrape completed")
            return {
                "status": "success",
                "message": "TikTok scrape completed", 
                "result": result
            }
            
    except Exception as e:
        log.exception("❌ TikTok scrape failed: %s", e)
        return {"status": "error", "message": str(e)}


def show_status():
    """Display current scraping status and pending scrapes."""
    print("\n" + "=" * 60)
    print("📊 SCRAPING STATUS")
    print("=" * 60)
    
    # Get all competitors
    all_competitors = get_all_competitors()
    pending_scrapes = get_pending_scrapes()
    
    # Summary stats
    ig_total = len([c for c in all_competitors if c['platform'].lower() == 'instagram'])
    ig_pending = len([c for c in pending_scrapes if c['platform'].lower() == 'instagram'])
    tt_total = len([c for c in all_competitors if c['platform'].lower() == 'tiktok'])
    tt_pending = len([c for c in pending_scrapes if c['platform'].lower() == 'tiktok'])
    
    print(f"\n📸 Instagram: {ig_pending}/{ig_total} pending")
    print(f"🎵 TikTok:    {tt_pending}/{tt_total} pending")
    
    if pending_scrapes:
        print("\n" + "-" * 60)
        print("⏳ PENDING SCRAPES (need update)")
        print("-" * 60)
        print(f"{'Handle':<25} {'Platform':<12} {'Last Checked':<20}")
        print("-" * 60)
        
        for comp in pending_scrapes[:20]:  # Show first 20
            last_checked = comp['last_checked']
            if last_checked:
                last_str = last_checked.strftime("%Y-%m-%d %H:%M")
            else:
                last_str = "Never"
            
            print(f"@{comp['handle']:<24} {comp['platform']:<12} {last_str:<20}")
        
        if len(pending_scrapes) > 20:
            print(f"\n... and {len(pending_scrapes) - 20} more")
    
    # Show recently updated
    recent = [c for c in all_competitors if c['last_checked']]
    recent.sort(key=lambda x: x['last_checked'], reverse=True)
    
    if recent:
        print("\n" + "-" * 60)
        print("✅ RECENTLY SCRAPED")
        print("-" * 60)
        print(f"{'Handle':<25} {'Platform':<12} {'Last Checked':<20}")
        print("-" * 60)
        
        for comp in recent[:10]:  # Show last 10
            last_str = comp['last_checked'].strftime("%Y-%m-%d %H:%M")
            print(f"@{comp['handle']:<24} {comp['platform']:<12} {last_str:<20}")
    
    print("\n" + "=" * 60)


def dispatch_via_celery(platform: str) -> Dict[str, Any]:
    """
    Dispatch scrape task via Celery (if running in Docker/with workers).
    
    Args:
        platform: 'instagram' or 'tiktok'
        
    Returns:
        dict: Task dispatch result
    """
    try:
        from worker.celery_app import app
        
        if platform == 'instagram':
            result = app.send_task(
                "worker.tasks.weekly_instagram_scrape",
                queue="celery"
            )
            log.info("📤 Instagram scrape task dispatched: task_id=%s", result.id)
        elif platform == 'tiktok':
            result = app.send_task(
                "worker.tasks.weekly_tiktok_scrape",
                queue="celery"
            )
            log.info("📤 TikTok scrape task dispatched: task_id=%s", result.id)
        else:
            return {"status": "error", "message": f"Unknown platform: {platform}"}
        
        return {
            "status": "dispatched",
            "task_id": result.id,
            "message": f"{platform.title()} scrape task sent to workers"
        }
        
    except Exception as e:
        log.warning("Celery dispatch failed: %s. Running directly instead.", e)
        return {"status": "fallback", "message": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Force scrape competitors when automatic scraping fails",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python force_scrape.py instagram          # Scrape all Instagram competitors
  python force_scrape.py tiktok             # Scrape all TikTok competitors
  python force_scrape.py all                # Scrape all platforms
  python force_scrape.py instagram -H user  # Scrape specific Instagram user
  python force_scrape.py status             # Show scraping status
  python force_scrape.py reset -H username  # Reset competitor for next auto-scrape
  python force_scrape.py instagram --celery # Dispatch via Celery workers
        """
    )
    
    parser.add_argument(
        "action",
        choices=["instagram", "tiktok", "all", "status", "reset"],
        help="Action to perform"
    )
    
    parser.add_argument(
        "-H", "--handle",
        type=str,
        help="Specific competitor handle to scrape (e.g., @username)"
    )
    
    parser.add_argument(
        "--celery",
        action="store_true",
        help="Dispatch task via Celery instead of running directly"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Handle actions
    if args.action == "status":
        show_status()
        return 0
    
    if args.action == "reset":
        if not args.handle:
            print("❌ Error: --handle is required for reset action")
            return 1
        success = reset_last_checked(args.handle)
        return 0 if success else 1
    
    # Scraping actions
    results = []
    
    if args.action in ("instagram", "all"):
        if args.celery and not args.handle:
            result = dispatch_via_celery("instagram")
            if result["status"] == "fallback":
                result = force_instagram_scrape(args.handle)
        else:
            result = force_instagram_scrape(args.handle)
        results.append(("Instagram", result))
    
    if args.action in ("tiktok", "all"):
        if args.celery and not args.handle:
            result = dispatch_via_celery("tiktok")
            if result["status"] == "fallback":
                result = force_tiktok_scrape(args.handle)
        else:
            result = force_tiktok_scrape(args.handle)
        results.append(("TikTok", result))
    
    # Print results
    print("\n" + "=" * 60)
    print("📋 SCRAPE RESULTS")
    print("=" * 60)
    
    exit_code = 0
    for platform, result in results:
        status = result.get("status", "unknown")
        message = result.get("message", "No message")
        
        if status in ("success", "dispatched"):
            print(f"✅ {platform}: {message}")
        else:
            print(f"❌ {platform}: {message}")
            exit_code = 1
    
    print("=" * 60)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
