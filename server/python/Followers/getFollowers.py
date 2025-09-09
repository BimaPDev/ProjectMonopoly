import time
import json
import random
import concurrent.futures
import sys
import datetime
import re
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from contextlib import contextmanager

import requests
from bs4 import BeautifulSoup

import psycopg2
from psycopg2.extras import RealDictCursor

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# ── CONFIGURATION ─────────────────────────────────────────────────────────────

@dataclass
class Config:
    """Configuration settings for the scraper."""
    db_connection_string: str = "dbname=project_monopoly user=root password=secret host=localhost port=5432 sslmode=disable"
    request_timeout: int = 10
    selenium_timeout: int = 15
    max_retries: int = 3
    retry_delay: int = 2
    max_workers: int = 1  # Reduced to 1 to avoid Chrome conflicts completely
    
    # User agents for rotation
    user_agents: list = None
    
    def __post_init__(self):
        if self.user_agents is None:
            self.user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            ]

config = Config()

# ── LOGGING SETUP ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ── DATABASE OPERATIONS ───────────────────────────────────────────────────────

@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = None
    try:
        conn = psycopg2.connect(config.db_connection_string)
        conn.autocommit = True
        yield conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()

INSERT_FOLLOWER_SQL = """
INSERT INTO daily_followers (
  record_date,
  follower_count,
  platform_breakdown
) VALUES (
  %s,
  %s,
  %s
)
ON CONFLICT (record_date) 
DO UPDATE SET 
  follower_count = EXCLUDED.follower_count,
  platform_breakdown = EXCLUDED.platform_breakdown,
  updated_at = CURRENT_TIMESTAMP
RETURNING id;
"""

def insert_follower_count(record_date: datetime.date, total_followers: int, breakdown: Dict[str, int]) -> int:
    """Insert follower count with platform breakdown."""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(INSERT_FOLLOWER_SQL, (
                    record_date, 
                    total_followers, 
                    json.dumps(breakdown)
                ))
                result = cur.fetchone()
                return result["id"] if result else None
    except Exception as e:
        logger.error(f"Failed to insert follower count: {e}")
        raise

# ── UTILITIES ─────────────────────────────────────────────────────────────────

def parse_number(text: str) -> int:
    """Normalize strings like '1.2M', '34.5K', '1,234' into an integer."""
    if not text:
        return 0
        
    text = text.replace(",", "").strip().lower()
    
    # Handle different formats
    multipliers = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}
    
    for suffix, multiplier in multipliers.items():
        if text.endswith(suffix):
            try:
                number = float(text[:-1])
                return int(number * multiplier)
            except ValueError:
                continue
    
    # Extract just numbers
    numbers = re.findall(r'\d+\.?\d*', text)
    if numbers:
        try:
            return int(float(numbers[0]))
        except ValueError:
            pass
    
    return 0

def retry_on_failure(max_retries: int = 3, delay: int = 2):
    """Decorator for retrying failed operations."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}: {e}")
            
            raise last_exception
        return wrapper
    return decorator

@contextmanager
def get_selenium_driver():
    """Context manager for Selenium WebDriver."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Random user agent
    user_agent = random.choice(config.user_agents)
    options.add_argument(f"--user-agent={user_agent}")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(config.selenium_timeout)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        yield driver
    except Exception as e:
        logger.error(f"WebDriver setup error: {e}")
        raise
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.warning(f"Error closing WebDriver: {e}")

def wait_for_element(driver, xpath: str, timeout: int = 10) -> Optional[str]:
    """Wait for element and return its text."""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return element.text.strip()
    except TimeoutException:
        logger.warning(f"Element not found with xpath: {xpath}")
        return None

# ── PLATFORM SCRAPERS ─────────────────────────────────────────────────────────

class PlatformScraper:
    """Base class for platform scrapers."""
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
    
    def get_followers(self, identifier: str) -> int:
        """Override this method in subclasses."""
        raise NotImplementedError

@retry_on_failure(max_retries=config.max_retries, delay=config.retry_delay)
def get_instagram_followers(username: str) -> int:
    """Scrape Instagram followers using meta tags and API fallback."""
    url = f"https://www.instagram.com/{username}/"
    headers = {
        "User-Agent": random.choice(config.user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }
    
    try:
        # Add random delay to seem more human-like
        time.sleep(random.uniform(1, 3))
        
        response = requests.get(url, headers=headers, timeout=config.request_timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Try multiple methods to extract follower count
        methods = [
            lambda: soup.find("meta", property="og:description"),
            lambda: soup.find("meta", attrs={"name": "description"}),
        ]
        
        for method in methods:
            try:
                meta_tag = method()
                if meta_tag and meta_tag.get("content"):
                    content = meta_tag["content"]
                    # Look for follower patterns
                    patterns = [
                        r"([\d,\.]+[KMB]?)\s+Followers",
                        r"([\d,\.]+[KMB]?)\s+followers",
                        r"(\d{1,3}(?:,\d{3})*)\s+Followers"
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, content, re.IGNORECASE)
                        if match:
                            return parse_number(match.group(1))
            except Exception as e:
                logger.debug(f"Instagram extraction method failed: {e}")
                continue
        
        logger.warning("No follower count found in Instagram meta tags")
        return 0
        
    except requests.RequestException as e:
        logger.error(f"Instagram request failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Instagram scraping error: {e}")
        raise

@retry_on_failure(max_retries=config.max_retries, delay=config.retry_delay)
def get_linkedin_followers(company_name: str) -> int:
    """Scrape LinkedIn company followers."""
    try:
        with get_selenium_driver() as driver:
            url = f"https://www.linkedin.com/company/{company_name}/"
            driver.get(url)
            
            # Wait for page to load
            time.sleep(random.uniform(2, 4))
            
            # Multiple xpath patterns to try
            xpath_patterns = [
                "//div[contains(@class, 'org-top-card-summary-info-list__info-item')]/div[contains(text(), 'followers')]",
                "//div[contains(text(), 'followers')]",
                "//span[contains(text(), 'followers')]",
            ]
            
            for xpath in xpath_patterns:
                text = wait_for_element(driver, xpath, 5)
                if text and 'followers' in text.lower():
                    # Extract number from text like "1,234 followers"
                    follower_text = text.replace("followers", "").replace("Followers", "").strip()
                    return parse_number(follower_text)
            
            logger.warning(f"No follower count found for LinkedIn company: {company_name}")
            return 0
            
    except Exception as e:
        logger.error(f"LinkedIn scraping error: {e}")
        raise

@retry_on_failure(max_retries=config.max_retries, delay=config.retry_delay)
def get_facebook_followers(page_name: str) -> int:
    """Scrape Facebook page followers."""
    try:
        with get_selenium_driver() as driver:
            url = f"https://www.facebook.com/{page_name}"
            driver.get(url)
            
            time.sleep(random.uniform(3, 5))
            
            # Try multiple selectors
            xpath_patterns = [
                "//a[contains(@href, 'followers')]//*[contains(text(), 'followers')]",
                "//*[contains(text(), 'followers') and contains(text(), 'people')]",
                "//div[contains(text(), 'followers')]",
            ]
            
            for xpath in xpath_patterns:
                text = wait_for_element(driver, xpath, 5)
                if text and 'followers' in text.lower():
                    return parse_number(text.replace("followers", ""))
            
            logger.warning(f"No follower count found for Facebook page: {page_name}")
            return 0
            
    except Exception as e:
        logger.error(f"Facebook scraping error: {e}")
        raise

@retry_on_failure(max_retries=config.max_retries, delay=config.retry_delay)
def get_twitch_followers(username: str) -> int:
    """Scrape Twitch followers."""
    try:
        with get_selenium_driver() as driver:
            url = f"https://twitch.tv/{username}/about"
            driver.get(url)
            
            time.sleep(random.uniform(2, 4))
            
            xpath_patterns = [
                "//*[contains(@class, 'about-section')]//p[contains(text(), 'Followers')]",
                "//*[contains(text(), 'Followers')]/preceding-sibling::*[1]",
                "//*[contains(@data-a-target, 'followers')]",
            ]
            
            for xpath in xpath_patterns:
                text = wait_for_element(driver, xpath, 5)
                if text:
                    return parse_number(text)
            
            logger.warning(f"No follower count found for Twitch user: {username}")
            return 0
            
    except Exception as e:
        logger.error(f"Twitch scraping error: {e}")
        raise

@retry_on_failure(max_retries=config.max_retries, delay=config.retry_delay)
def get_youtube_subscribers(channel_id: str) -> int:
    """Scrape YouTube subscribers."""
    try:
        with get_selenium_driver() as driver:
            # Try different URL formats
            urls = [
                f"https://www.youtube.com/c/{channel_id}",
                f"https://www.youtube.com/@{channel_id}",
                f"https://www.youtube.com/channel/{channel_id}",
            ]
            
            for url in urls:
                try:
                    driver.get(url)
                    time.sleep(random.uniform(2, 4))
                    
                    xpath_patterns = [
                        "//*[@id='subscriber-count']",
                        "//*[contains(@class, 'subscriber-count')]",
                        "//*[contains(text(), 'subscriber')]/preceding-sibling::*[1]",
                        "//yt-formatted-string[contains(@class, 'subscriber-count')]",
                    ]
                    
                    for xpath in xpath_patterns:
                        text = wait_for_element(driver, xpath, 5)
                        if text:
                            return parse_number(text)
                            
                except Exception as e:
                    logger.debug(f"YouTube URL {url} failed: {e}")
                    continue
            
            logger.warning(f"No subscriber count found for YouTube channel: {channel_id}")
            return 0
            
    except Exception as e:
        logger.error(f"YouTube scraping error: {e}")
        raise

# ── MAIN ORCHESTRATOR ─────────────────────────────────────────────────────────

def get_all_followers() -> Tuple[int, Dict[str, int]]:
    """Get follower counts from all platforms."""
    
    # Platform configurations
    platforms = {
        "instagram": (get_instagram_followers, "dogwood_gaming"),
        "twitch": (get_twitch_followers, "dogwoodgaming"),
        "youtube": (get_youtube_subscribers, "DogwoodGaming"),
        "facebook": (get_facebook_followers, "DogwoodGaming"),
        "linkedin": (get_linkedin_followers, "dogwood-gaming"),
    }
    
    followers = {}
    
    # Use ThreadPoolExecutor with limited workers to be respectful
    with concurrent.futures.ThreadPoolExecutor(max_workers=config.max_workers) as executor:
        # Submit all tasks
        future_to_platform = {
            executor.submit(scraper_func, identifier): platform_name
            for platform_name, (scraper_func, identifier) in platforms.items()
        }
        
        # Collect results with timeout
        for future in concurrent.futures.as_completed(future_to_platform, timeout=60):
            platform = future_to_platform[future]
            try:
                result = future.result(timeout=30)
                followers[platform] = result
                logger.info(f"{platform.capitalize()}: {result:,} followers")
            except Exception as e:
                logger.error(f"Failed to get {platform} followers: {e}")
                followers[platform] = 0
    
    total_followers = sum(followers.values())
    return total_followers, followers

def main():
    """Main execution function."""
    start_time = time.time()
    
    try:
        logger.info("Starting social media follower scraping...")
        
        # Get follower counts
        total_followers, platform_breakdown = get_all_followers()
        
        # Save to database
        today = datetime.date.today()
        record_id = insert_follower_count(today, total_followers, platform_breakdown)
        
        # Log results
        logger.info(f"Successfully recorded {total_followers:,} total followers (Record ID: {record_id})")
        logger.info(f"Platform breakdown: {platform_breakdown}")
        
        # Return JSON result
        result = {
            "success": True,
            "date": today.isoformat(),
            "total_followers": total_followers,
            "platform_breakdown": platform_breakdown,
            "record_id": record_id,
            "execution_time_seconds": round(time.time() - start_time, 2)
        }
        
        print(json.dumps(result, indent=2))
        return result
        
    except Exception as e:
        logger.error(f"Script execution failed: {e}")
        error_result = {
            "success": False,
            "error": str(e),
            "execution_time_seconds": round(time.time() - start_time, 2)
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()
