#!/usr/bin/env python3
"""
Weekly Scraper Idle Process
Runs the weekly scraper immediately on startup, then periodically checks for competitors to scrape.
"""
import os
import sys
import time
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from socialmedia.weekly_scraper import WeeklyInstagramScraper

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

IDLE_CHECK_INTERVAL = int(os.getenv("WEEKLY_SCRAPER_IDLE_INTERVAL", "3600"))  # Default: 1 hour

def main():
    log.info("weekly scraper idle process started")
    log.info(f"   Will check for competitors to scrape every {IDLE_CHECK_INTERVAL} seconds")
    
    # Run immediately on startup
    log.info("running initial weekly scrape...")
    try:
        scraper = WeeklyInstagramScraper()
        scraper.run_weekly_scrape()
        log.info("initial weekly scrape completed")
    except Exception as e:
        log.error(f"initial weekly scrape failed: {e}")
    
    # Then run periodically on idle
    while True:
        try:
            time.sleep(IDLE_CHECK_INTERVAL)
            log.info("checking for competitors to scrape (idle check)...")
            scraper = WeeklyInstagramScraper()
            scraper.run_weekly_scrape()
            log.info("idle scrape check completed")
        except KeyboardInterrupt:
            log.info("weekly scraper idle process stopped")
            break
        except Exception as e:
            log.error(f"idle scrape check failed: {e}")
            # Continue running even if one check fails
            time.sleep(60)  # Wait 1 minute before retrying

if __name__ == "__main__":
    main()

