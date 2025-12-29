"""
Cookie Preparation Task
=======================

Automated login and session cookie extraction for social media platforms.
This module handles:
- Instagram login via Selenium with anti-detection measures
- Session cookie extraction (sessionid)
- Secure storage of cookies in database

Security Notes:
    - Credentials are stored in group_items.data (encrypted in transit via HTTPS)
    - Session cookies replace passwords for subsequent operations
    - Cookies are refreshed automatically when expired

Anti-Detection Measures:
    - Uses undetected-chromedriver behavior patterns
    - Randomized delays between actions
    - Stealth JavaScript injection
    - Headless mode with proper window size

Supported Platforms:
    - Instagram (fully implemented)
    - TikTok (placeholder - requires implementation)

Author: ProjectMonopoly Team
Last Updated: 2025-12-27
"""

import os
import json
import time
import random
import logging
from typing import Optional, Dict, Any

import psycopg
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
    ElementClickInterceptedException,
)

from .celery_app import app
from .config import DATABASE_URL, SELENIUM_HEADLESS, SELENIUM_TIMEOUT

# ─────────────────────────────────────────────────────────────────────────────
# Logging Configuration
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Chrome Driver Setup
# ─────────────────────────────────────────────────────────────────────────────
def create_stealth_driver(headless: bool = True) -> webdriver.Chrome:
    """
    Create a Chrome WebDriver with anti-detection measures.
    
    Args:
        headless: Run browser in headless mode (default: True)
        
    Returns:
        webdriver.Chrome: Configured Chrome driver
        
    Raises:
        WebDriverException: If Chrome driver cannot be initialized
    """
    log.info("Initializing Chrome driver (headless=%s)", headless)
    
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument("--headless=new")
    
    # Window and display settings
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--start-maximized")
    
    # Anti-detection settings
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    
    # Container compatibility
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # Experimental options for stealth
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # User agent (realistic desktop browser)
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # Inject JavaScript to hide webdriver property
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """
    })
    
    log.info("Chrome driver initialized successfully")
    return driver


def random_delay(min_sec: float = 0.5, max_sec: float = 2.0):
    """Add a random delay to simulate human behavior."""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)


# ─────────────────────────────────────────────────────────────────────────────
# Instagram Login
# ─────────────────────────────────────────────────────────────────────────────
def login_instagram(driver: webdriver.Chrome, email: str, password: str) -> Optional[str]:
    """
    Log into Instagram and extract the sessionid cookie.
    
    Args:
        driver: Selenium WebDriver instance
        email: Instagram username or email
        password: Instagram password
        
    Returns:
        str: The sessionid cookie value, or None if login failed
        
    Raises:
        TimeoutException: If login elements not found or login failed
    """
    log.info("Starting Instagram login for: %s", email[:3] + "***")
    
    # Navigate to login page
    driver.get("https://www.instagram.com/accounts/login/")
    random_delay(3, 5)  # Wait for page load and possible redirects
    
    # Handle cookie consent dialog (multiple possible button texts)
    cookie_xpaths = [
        "//button[contains(text(), 'Accept')]",
        "//button[contains(text(), 'Allow')]",
        "//button[contains(text(), 'Only allow essential')]",
        "//button[contains(text(), 'Accept All')]",
        "//button[contains(text(), 'Decline')]",  # Some regions show this
    ]
    
    for xpath in cookie_xpaths:
        try:
            btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            btn.click()
            log.debug("Clicked cookie consent button")
            random_delay(0.5, 1.0)
            break
        except TimeoutException:
            continue
        except ElementClickInterceptedException:
            continue
    
    # Find and fill username field
    try:
        username_input = WebDriverWait(driver, SELENIUM_TIMEOUT).until(
            EC.visibility_of_element_located((By.NAME, "username"))
        )
    except TimeoutException:
        log.error("Username input not found - page structure may have changed")
        raise
    
    # Find password field
    try:
        password_input = driver.find_element(By.NAME, "password")
    except NoSuchElementException:
        log.error("Password input not found")
        raise
    
    # Clear and fill credentials with human-like delays
    username_input.clear()
    random_delay(0.3, 0.7)
    
    # Type username character by character (more human-like)
    for char in email:
        username_input.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))
    
    random_delay(0.5, 1.0)
    
    password_input.clear()
    random_delay(0.3, 0.7)
    
    # Type password
    for char in password:
        password_input.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))
    
    random_delay(0.5, 1.5)
    
    # Submit login
    password_input.send_keys(Keys.RETURN)
    log.info("Login form submitted, waiting for response...")
    
    # Wait for successful login (multiple possible success indicators)
    success_indicators = [
        "//nav//a[contains(@href, '/explore')]",
        "//a[contains(@href, '/direct/inbox')]",
        "//svg[@aria-label='Home']",
        "//*[@aria-label='New post']",
    ]
    
    login_successful = False
    for indicator in success_indicators:
        try:
            WebDriverWait(driver, SELENIUM_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, indicator))
            )
            login_successful = True
            log.info("Login successful!")
            break
        except TimeoutException:
            continue
    
    if not login_successful:
        # Check for error messages
        error_indicators = [
            "//p[@id='slfErrorAlert']",
            "//*[contains(text(), 'incorrect')]",
            "//*[contains(text(), 'Sorry')]",
            "//*[contains(text(), 'suspicious')]",
        ]
        
        for indicator in error_indicators:
            try:
                error_elem = driver.find_element(By.XPATH, indicator)
                log.error("Login error detected: %s", error_elem.text[:100])
                raise Exception(f"Instagram login failed: {error_elem.text[:100]}")
            except NoSuchElementException:
                continue
        
        log.error("Login failed - no success indicators found")
        raise TimeoutException("Login did not complete successfully")
    
    # Extract sessionid cookie
    random_delay(1, 2)  # Wait for cookies to be set
    
    cookies = driver.get_cookies()
    sessionid = None
    
    for cookie in cookies:
        if cookie.get("name") == "sessionid":
            sessionid = cookie.get("value")
            log.info("Successfully extracted sessionid cookie")
            break
    
    if not sessionid:
        log.warning("sessionid cookie not found in response")
    
    return sessionid


# ─────────────────────────────────────────────────────────────────────────────
# TikTok Login (Placeholder)
# ─────────────────────────────────────────────────────────────────────────────
def login_tiktok(driver: webdriver.Chrome, email: str, password: str) -> Optional[str]:
    """
    Log into TikTok and extract the sessionid cookie.
    
    Note:
        TikTok login is more complex due to CAPTCHA and verification requirements.
        This is a placeholder that should be implemented based on specific needs.
    
    Args:
        driver: Selenium WebDriver instance
        email: TikTok username or email
        password: TikTok password
        
    Returns:
        str: The sessionid cookie value, or None if login failed
    """
    log.warning("TikTok login not fully implemented - placeholder only")
    
    driver.get("https://www.tiktok.com/login")
    random_delay(3, 5)
    
    # TikTok login is complex and often requires:
    # 1. Clicking through multiple login options
    # 2. Handling CAPTCHA challenges
    # 3. SMS/Email verification
    # 4. Device verification
    
    # Extract cookies (may not include sessionid without full login)
    cookies = driver.get_cookies()
    
    for cookie in cookies:
        if cookie.get("name") in ("sessionid", "session_id"):
            return cookie.get("value")
    
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Database Operations
# ─────────────────────────────────────────────────────────────────────────────
def update_group_item_cookie(
    group_item_id: int,
    sessionid: str,
    platform: str
) -> bool:
    """
    Update group_items.data with the extracted sessionid.
    
    Args:
        group_item_id: The group_items.id to update
        sessionid: The session cookie value
        platform: Platform name for logging
        
    Returns:
        bool: True if update succeeded
    """
    log.info("Storing sessionid for group_item_id=%s", group_item_id)
    
    try:
        with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                # Get current data
                cur.execute(
                    "SELECT data FROM group_items WHERE id = %s",
                    (group_item_id,)
                )
                row = cur.fetchone()
                
                if not row:
                    log.error("group_item %d not found", group_item_id)
                    return False
                
                current_data = row[0] if row[0] else {}
                
                # Update data with sessionid (preserve existing fields)
                current_data["sessionid"] = sessionid
                current_data["cookie_updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
                
                # Check if cookie_created_at column exists
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'group_items' AND column_name = 'cookie_created_at'
                """)
                has_cookie_column = cur.fetchone() is not None
                
                # Update database
                if has_cookie_column:
                    cur.execute(
                        """
                        UPDATE group_items 
                        SET data = %s::jsonb, 
                            cookie_created_at = NOW(),
                            updated_at = NOW()
                        WHERE id = %s
                        """,
                        (json.dumps(current_data), group_item_id)
                    )
                else:
                    cur.execute(
                        """
                        UPDATE group_items 
                        SET data = %s::jsonb, 
                            updated_at = NOW()
                        WHERE id = %s
                        """,
                        (json.dumps(current_data), group_item_id)
                    )
                
                log.info("Successfully stored sessionid for group_item_id=%s", group_item_id)
                return True
                
    except Exception as e:
        log.exception("Failed to store sessionid: %s", e)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Celery Task
# ─────────────────────────────────────────────────────────────────────────────
@app.task(
    name="worker.tasks.prepare_cookies",
    queue="celery",
    bind=True,
    max_retries=2,
    default_retry_delay=300,  # 5 minute delay before retry
    soft_time_limit=120,      # 2 minute soft limit
    time_limit=180,           # 3 minute hard limit
    acks_late=True,
)
def prepare_cookies(
    self,
    group_item_id: int,
    platform: str,
    email: str,
    password: str
) -> Dict[str, Any]:
    """
    Login to a platform and extract session cookies.
    
    This task:
    1. Creates a stealth Chrome driver
    2. Performs platform-specific login
    3. Extracts the sessionid cookie
    4. Stores the cookie in group_items.data
    5. Cleans up browser resources
    
    Args:
        group_item_id: The group_items.id to update
        platform: Target platform ('instagram', 'tiktok')
        email: Login username/email
        password: Login password
        
    Returns:
        dict: Result containing:
            - status: 'success' or 'failed'
            - group_item_id: The group item ID
            - platform: Target platform
            - error: Error message (if failed)
    
    Example:
        >>> prepare_cookies.delay(
        ...     group_item_id=42,
        ...     platform="instagram",
        ...     email="user@example.com",
        ...     password="secret"
        ... )
    """
    log.info("🍪 Starting cookie preparation: group_item_id=%s platform=%s", 
             group_item_id, platform)
    
    driver = None
    
    try:
        # Validate inputs
        if not email or not password:
            raise ValueError("Email and password are required")
        
        platform_lower = platform.lower()
        if platform_lower not in ("instagram", "tiktok"):
            raise ValueError(f"Unsupported platform: {platform}")
        
        # Create browser driver
        driver = create_stealth_driver(headless=SELENIUM_HEADLESS)
        
        # Platform-specific login
        if platform_lower == "instagram":
            sessionid = login_instagram(driver, email, password)
        elif platform_lower == "tiktok":
            sessionid = login_tiktok(driver, email, password)
        else:
            raise ValueError(f"Unsupported platform: {platform}")
        
        # Validate sessionid was obtained
        if not sessionid:
            raise Exception("Failed to extract sessionid cookie")
        
        # Store in database
        if not update_group_item_cookie(group_item_id, sessionid, platform):
            raise Exception("Failed to store sessionid in database")
        
        log.info("✅ Cookie preparation completed: group_item_id=%s", group_item_id)
        
        return {
            "status": "success",
            "group_item_id": group_item_id,
            "platform": platform
        }
        
    except WebDriverException as e:
        error_msg = f"Browser error: {str(e)[:200]}"
        log.exception("❌ Cookie preparation failed (browser): %s", error_msg)
        
        # Retry on browser errors (may be transient)
        raise self.retry(countdown=60, max_retries=2, exc=e)
        
    except TimeoutException as e:
        error_msg = f"Login timeout: {str(e)[:200]}"
        log.exception("❌ Cookie preparation failed (timeout): %s", error_msg)
        
        return {
            "status": "failed",
            "group_item_id": group_item_id,
            "platform": platform,
            "error": error_msg
        }
        
    except Exception as e:
        error_msg = str(e)[:500]
        log.exception("❌ Cookie preparation failed: %s", error_msg)
        
        return {
            "status": "failed",
            "group_item_id": group_item_id,
            "platform": platform,
            "error": error_msg
        }
        
    finally:
        # Always clean up browser
        if driver:
            try:
                driver.quit()
                log.debug("Browser closed")
            except Exception as e:
                log.warning("Failed to close browser: %s", e)


# ─────────────────────────────────────────────────────────────────────────────
# Export
# ─────────────────────────────────────────────────────────────────────────────
__all__ = ['prepare_cookies']
