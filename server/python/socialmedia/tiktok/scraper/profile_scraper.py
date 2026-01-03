from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
import os
import pickle
import re
from datetime import datetime, timedelta
import datetime as dt
import random
import logging

# Import the driver factory for SeleniumBase + Playwright fallback
from ...drivers import get_driver, switch_to_fallback, BotDetectedError

log = logging.getLogger(__name__)


def parse_shorthand(value: str) -> str:
    """Convert notation (K, M, B) to full numbers"""
    val = value.strip().upper().replace(",", "")
    if val.endswith("K"):
        try:
            return str(int(float(val[:-1]) * 1_000))
        except ValueError:
            return val
    if val.endswith("M"):
        try:
            return str(int(float(val[:-1]) * 1_000_000))
        except ValueError:
            return val
    if val.endswith("B"):
        try:
            return str(int(float(val[:-1]) * 1_000_000_000))
        except ValueError:
            return val
    return val


def calculate_post_date(relative_time_str: str) -> str:
    if not relative_time_str or "ago" not in relative_time_str.lower():
        return ""
    
    # Remove bullet point and clean up
    relative_time_str = relative_time_str.replace("·", "").strip().lower()
    
    # Remove "ago" and get the time part
    relative_time_str = relative_time_str.replace("ago", "").strip()
    
    now = datetime.now()
    
    # Try to match patterns like "6d", "2h", "30m", "5 days", "2 hours", "30 minutes"
    # Pattern 1: "6d", "2h", "30m" (shorthand)
    match = re.search(r'(\d+)\s*([dhm])', relative_time_str)
    if match:
        value = int(match.group(1))
        unit = match.group(2)
        
        if unit == 'd':
            # Days ago
            post_date = now - timedelta(days=value)
            return post_date.strftime("%Y-%m-%d %H:%M:%S")
        elif unit == 'h':
            # Hours ago
            post_date = now - timedelta(hours=value)
            return post_date.strftime("%Y-%m-%d %H:%M:%S")
        elif unit == 'm':
            # Minutes ago
            post_date = now - timedelta(minutes=value)
            return post_date.strftime("%Y-%m-%d %H:%M:%S")
    
    # Pattern 2: "5 days", "2 hours", "30 minutes" (full words)
    match = re.search(r'(\d+)\s*(day|hour|minute|days|hours|minutes)', relative_time_str)
    if match:
        value = int(match.group(1))
        unit = match.group(2).lower()
        
        if 'day' in unit:
            post_date = now - timedelta(days=value)
            return post_date.strftime("%Y-%m-%d %H:%M:%S")
        elif 'hour' in unit:
            post_date = now - timedelta(hours=value)
            return post_date.strftime("%Y-%m-%d %H:%M:%S")
        elif 'minute' in unit:
            post_date = now - timedelta(minutes=value)
            return post_date.strftime("%Y-%m-%d %H:%M:%S")
    
    # If we can't parse it, return empty string
    return ""

# Random delay function to avoid detection
def random_delay(min_seconds=1, max_seconds=3):
    time.sleep(random.uniform(min_seconds, max_seconds))


class TikTokScraper:
    def __init__(self, cookies_path="cookies/tiktok_cookies.pkl", use_cookies=False, headless=True, proxy=None, driver_type='undetected'):
        """
        Initialize TikTok scraper.
        
        Args:
            cookies_path: Path to save/load cookies (only used if use_cookies=True)
            use_cookies: If True, use cookies for authenticated scraping. If False, scrape as guest.
            headless: Run browser in headless mode (recommended for server)
            proxy: Optional proxy string (e.g. "http://1.2.3.4:8080")
            driver_type: Driver to use - 'undetected', 'seleniumbase', or 'playwright'
        """
        self.cookies_path = cookies_path
        self.use_cookies = use_cookies
        self.headless = headless
        self.proxy = proxy
        self.driver = None
        self.driver_type = None  # Will be set by setup_driver
        self.preferred_driver = driver_type.lower()  # 'undetected', 'seleniumbase' or 'playwright'
        self._raw_driver = None  # The underlying driver object
        self.setup_driver()
        
    def setup_driver(self):
        """Initialize scraper using the preferred driver type."""
        driver_name = self.preferred_driver
        print(f"Setting up TikTok scraper driver (requested: {driver_name})... Proxy: {self.proxy if self.proxy else 'None'}")
        
        try:
            # Select driver based on preference
            force_undetected = (driver_name == 'undetected')
            force_playwright = (driver_name == 'playwright')
            
            self._raw_driver, self.driver_type = get_driver(
                headless=self.headless, 
                proxy=self.proxy,
                force_undetected=force_undetected,
                force_playwright=force_playwright
            )
            
            # The driver now uses Playwright's page object directly
            # All methods like get(), find_element(), page_source work on both
            self.driver = self._raw_driver
            
            self._raw_driver.set_page_load_timeout(60)
            print(f"TikTok scraper driver initialized successfully (using: {self.driver_type})")
            
        except Exception as e:
            print(f"Failed to initialize TikTok scraper driver: {e}")
            raise
    
    def _switch_to_fallback(self):
        """Switch to Playwright fallback if bot detection is triggered."""
        print("Bot detection suspected. Switching to Playwright fallback...")
        
        try:
            self._raw_driver, self.driver_type = switch_to_fallback(self._raw_driver, headless=self.headless, proxy=self.proxy)
            
            if self.driver_type == 'seleniumbase':
                self.driver = self._raw_driver.driver
            else:
                self.driver = self._raw_driver
            
            self._raw_driver.set_page_load_timeout(60)
            print(f"Switched to fallback driver: {self.driver_type}")
            return True
        except Exception as e:
            print(f"Failed to switch to fallback: {e}")
            return False
    
    def _check_bot_detection(self) -> bool:
        """Check if bot detection has been triggered."""
        return self._raw_driver.is_bot_detected()
    
    def _try_solve_captcha(self) -> bool:
        """Try to solve a captcha if one is detected.
        
        Returns:
            bool: True if captcha was solved, False otherwise
        """
        if hasattr(self._raw_driver, 'solve_captcha'):
            print("🔓 Attempting to solve captcha...")
            result = self._raw_driver.solve_captcha()
            if result:
                print("✅ Captcha solving completed")
                time.sleep(2)  # Wait for page to update
            return result
        return False
    
    def _handle_bot_detection(self) -> bool:
        """Handle bot detection by trying captcha solving first, then fallback.
        
        Returns:
            bool: True if bot detection was handled successfully
        """
        if not self._check_bot_detection():
            return True  # No bot detection
        
        print("⚠️ Bot detection triggered!")
        
        # First try to solve captcha
        if self._try_solve_captcha():
            time.sleep(2)
            if not self._check_bot_detection():
                print("✅ Captcha solved - continuing")
                return True
        
        # If captcha solving didn't work, try switching to fallback driver
        return self._switch_to_fallback()
        
    def save_cookies(self):
        pickle.dump(self.driver.get_cookies(), open(self.cookies_path, "wb"))
        print("Cookies saved successfully!")
        
    def load_cookies(self):
        if os.path.exists(self.cookies_path):
            cookies = pickle.load(open(self.cookies_path, "rb"))
            self.driver.get("https://www.tiktok.com")
            time.sleep(3)
            for cookie in cookies:
                try:
                    cookie.pop("sameSite", None)
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"Error adding cookie: {e}")
            print("Cookies loaded successfully!")
            self.driver.refresh()
            time.sleep(3)
            return True
        return False
        
    def accept_cookies_and_setup(self):
        """Handle initial TikTok page setup - accept cookie consent and dismiss popups."""
        import logging
        log = logging.getLogger(__name__)
        
        # Use retry logic for navigation
        if not self._navigate_with_retry("https://www.tiktok.com"):
            raise Exception("Failed to navigate to TikTok home page after retries")
        
        time.sleep(2)
        
        # Use different method based on driver type
        if self.driver_type == 'playwright':
            # Playwright-specific selectors
            try:
                accept_selectors = [
                    "button:has-text('Accept')",
                    "button:has-text('Agree')",
                    "button:has-text('Accept all')",
                ]
                for selector in accept_selectors:
                    try:
                        locator = self.driver.page.locator(selector)
                        if locator.count() > 0:
                            locator.first.click(timeout=5000)
                            log.info("Accepted cookies dialog (Playwright)")
                            time.sleep(2)
                            break
                    except Exception:
                        continue
            except Exception as e:
                log.warning(f"No cookie dialog found: {e}")
        else:
            # Selenium-compatible approach (for undetected-chromedriver and seleniumbase)
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            accept_xpaths = [
                "//button[contains(text(), 'Accept')]",
                "//button[contains(text(), 'Agree')]",
                "//button[contains(text(), 'Accept all')]",
                "//button[contains(text(), 'Accept All')]",
            ]
            
            # Use explicit wait with short timeout to avoid hanging
            for xpath in accept_xpaths:
                try:
                    # Wait up to 3 seconds for the button
                    btn = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    if btn and btn.is_displayed():
                        btn.click()
                        log.info("Accepted cookies dialog (Selenium)")
                        time.sleep(2)
                        break
                except Exception:
                    # Timeout or not found - just continue to next selector
                    continue
        
        # Close any popup dialogs
        self._dismiss_popups()
        
        # Only save cookies if we're using cookie mode
        if self.use_cookies:
            self.save_cookies()
        
        log.info("Setup completed successfully")
        return True
    
    def _navigate_with_retry(self, url, max_retries=3, timeout=30):
        """Navigate to a URL with retry logic and timeout handling."""
        import logging
        import time
        log = logging.getLogger(__name__)
        
        for attempt in range(max_retries):
            try:
                log.info(f"Navigating to {url} (Attempt {attempt+1}/{max_retries})...")
                
                # Set page load timeout if supported
                if hasattr(self.driver, 'set_page_load_timeout'):
                    self.driver.set_page_load_timeout(timeout)
                
                self.driver.get(url)
                
                # Reset timeout to default
                if hasattr(self.driver, 'set_page_load_timeout'):
                    self.driver.set_page_load_timeout(60)
                    
                log.info("Navigation successful")
                return True
            except Exception as e:
                log.warning(f"Navigation failed (Attempt {attempt+1}): {e}")
                
                # If it was a timeout, try to stop loading and check if we have content
                if "timeout" in str(e).lower():
                    try:
                        self.driver.execute_script("window.stop();")
                        log.info("Stopped page load after timeout, proceeding...")
                        return True
                    except:
                        pass
                
                time.sleep(2)
        
        log.error(f"Failed to navigate to {url} after {max_retries} attempts")
        return False
    
    def _dismiss_popups(self):
        """Dismiss any popup dialogs (login prompts, notifications, etc.)."""
        if self.driver_type == 'playwright':
            # Playwright-specific
            popup_selectors = [
                "[aria-label='Close']",
                "div[role='dialog'] button:has-text('close')",
                "button:has-text('Not now')",
                "button:has-text('Maybe later')",
            ]
            for selector in popup_selectors:
                try:
                    locator = self.driver.page.locator(selector)
                    if locator.count() > 0:
                        locator.first.click(timeout=2000)
                        time.sleep(0.5)
                        print(f"Dismissed popup using: {selector}")
                except Exception:
                    pass
        else:
            # Selenium-compatible
            from selenium.webdriver.common.by import By
            popup_xpaths = [
                "//*[@aria-label='Close']",
                "//div[@role='dialog']//button[contains(text(), 'close')]",
                "//button[contains(text(), 'Not now')]",
                "//button[contains(text(), 'Maybe later')]",
            ]
            for xpath in popup_xpaths:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for el in elements:
                        if el.is_displayed():
                            el.click()
                            time.sleep(0.5)
                            print(f"Dismissed popup (Selenium)")
                            break
                except Exception:
                    pass
    
    def scrape_profile(self, profile_url, max_posts=None):
        """Scrape TikTok profile posts (public access, no login required).
        
        Returns:
            list: List of post dictionaries with profile_info added as first element metadata
        """
        if not profile_url.startswith("https://www.tiktok.com/"):
            profile_url = profile_url.lstrip("@")
            profile_url = f"https://www.tiktok.com/@{profile_url.strip('/')}"
            
        print(f"Navigating to profile: {profile_url}")
        
        # Cookie handling - only if use_cookies is enabled
        if self.use_cookies:
            if not self.load_cookies():
                self.accept_cookies_and_setup()
        else:
            # Guest mode - just accept cookie consent dialog
            self.accept_cookies_and_setup()
            
        self.driver.get(profile_url)
        random_delay(5, 8)  # Longer wait for headless mode
        
        try:
            profile_name = re.search(r"tiktok\.com/@([^/?]+)", profile_url).group(1)
        except:
            profile_name = "tiktok_profile"
        
        # ─────────────────────────────────────────────────────────────────────
        # Extract Profile Info (Followers, Following, Likes)
        # ─────────────────────────────────────────────────────────────────────
        profile_info = self._extract_profile_stats(profile_name)
        
        # Check for refresh button and click it if visible
        try:
            # Use Playwright-compatible approach
            refresh_locator = self.driver.page.locator("xpath=//button[contains(text(), 'Refresh')]")
            if refresh_locator.count() > 0 and refresh_locator.first.is_visible():
                print("Refresh button found, clicking it...")
                refresh_locator.first.click()
                random_delay(2, 3)
        except Exception as e:
            print(f"No refresh button found, proceeding... ({e})")
        
        # Wait for video container to appear (important for headless mode)
        try:
            self.driver.page.wait_for_selector("[data-e2e='user-post-item']", timeout=15000)
            print("Video container found, starting extraction...")
        except Exception:
            print("Video container not found, trying anyway...")
            
        posts_data = []
        video_links = set()
        
        print("Finding videos...")
        
        # Scroll to load videos
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scroll_attempts = 20
        
        while scroll_attempts < max_scroll_attempts:
            try:
                # Find video elements - TikTok uses different selectors
                video_elements = self.driver.find_elements(By.XPATH, "//div[@data-e2e='user-post-item']//a")
                
                for el in video_elements:
                    href = el.get_attribute("href")
                    if href and "/video/" in href:
                        video_links.add(href)
                        
                print(f"Found {len(video_links)} videos so far...")
                
                if max_posts and len(video_links) >= max_posts:
                    break
                    
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                random_delay(2, 4)
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    scroll_attempts += 1
                    # If no new content after 3 attempts
                    if scroll_attempts >= 3: 
                        break
                else:
                    last_height = new_height
                    scroll_attempts = 0
                    
            except Exception as e:
                print(f"Error while scrolling: {e}")
                scroll_attempts += 1
                
        video_links = list(video_links)
        if max_posts:
            video_links = video_links[:max_posts]
        print(f"Found {len(video_links)} videos in total.")
        
        for idx, video_url in enumerate(video_links, start=1):
            try:
                print(f"Processing video {idx}/{len(video_links)}: {video_url}")
                data = self.scrape_video(video_url, retries=2)
                if data:
                    posts_data.append(data)
                else:
                    print(f"Skipping video {idx} due to scraping failure")
                
                # Longer delay between videos to avoid rate limiting
                if idx < len(video_links):  # Don't delay after the last video
                    random_delay(5, 10)
                    
            except Exception as e:
                print(f"Error processing {video_url}: {e}")
                # Try to continue with next video
                continue
        
        # Store profile_info as attribute for access by weekly scraper
        self.last_profile_info = profile_info
                
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Ensure output directory exists
        output_dir = os.path.join(os.path.dirname(__file__), "scrape_result")
        os.makedirs(output_dir, exist_ok=True)
        
        json_filename = os.path.join(output_dir, f"{profile_name}_tiktoks_{timestamp}.json")
        
        # Save with profile info
        output_data = {
            "profile_info": profile_info,
            "posts": posts_data
        }
        with open(json_filename, "w", encoding="utf-8") as jf:
            json.dump(output_data, jf, ensure_ascii=False, indent=4)
        print(f"Saved all videos to {json_filename}")
        
        return posts_data
    
    def _extract_profile_stats(self, username):
        """Extract follower, following, and likes counts from profile page."""
        profile_info = {
            "username": username,
            "followers": 0,
            "following": 0,
            "likes": 0
        }
        
        try:
            # Check if using Playwright (has .page attribute)
            is_playwright = hasattr(self.driver, 'page')
            
            selectors = {
                "followers": "[data-e2e='followers-count']",
                "following": "[data-e2e='following-count']", 
                "likes": "[data-e2e='likes-count']"
            }
            
            for key, selector in selectors.items():
                try:
                    text_value = None
                    if is_playwright:
                        locator = self.driver.page.locator(selector)
                        if locator.count() > 0:
                            text_value = locator.first.text_content()
                    else:
                        # Selenium
                        from selenium.webdriver.common.by import By
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            text_value = elements[0].text
                            
                    if text_value:
                        profile_info[key] = self._parse_count_text(text_value)
                        # print(f"  → {key.capitalize()}: {profile_info[key]}")  # Verbose
                except Exception as e:
                    pass  # Silently continue on extraction errors
            
            # print(f"Profile stats for @{username}: {profile_info['followers']} followers, {profile_info['following']} following, {profile_info['likes']} likes")  # Verbose
            
        except Exception as e:
            pass  # Silently continue on profile stat errors
        
        return profile_info
    
    def _parse_count_text(self, text):
        """Parse TikTok count text (e.g., '1.2M', '500K', '10.5K') to integer."""
        if not text:
            return 0
        
        text = text.strip().upper().replace(",", "")
        
        try:
            if "M" in text:
                return int(float(text.replace("M", "")) * 1_000_000)
            elif "K" in text:
                return int(float(text.replace("K", "")) * 1_000)
            else:
                return int(text)
        except (ValueError, TypeError):
            return 0
    
    def scrape_video(self, video_url, retries=2):
        """
        Scrape one TikTok video with retry logic and better error handling
        """
        for attempt in range(retries + 1):
            try:
                print(f"Attempting to scrape video (attempt {attempt + 1}/{retries + 1}): {video_url}")
                
                try:
                    # print(f"  → Navigating to video...")  # Verbose
                    # Use 20 second timeout for video pages
                    self.driver.get(video_url, timeout=20000)
                    # print(f"  → Navigation complete")  # Verbose
                except Exception as e:
                    print(f"Error navigating to video: {e}")
                    if attempt < retries:
                        random_delay(3, 5)
                        continue
                    return None
                
                # Wait for page to load (reduced delay since we now have proper timeout)
                # print(f"  → Waiting for content...")  # Verbose
                random_delay(2, 4)
                
                video_data = {
                    "url": video_url,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "post_date": "",
                    "description": "",
                    "hashtags": [],
                    "likes_count": "",
                    "comments_count": "",
                    "shared_count": "",
                    "saved_count": "",
                    "author": "",
                    "comments": [],  # List of comment objects
                }
                
                success = False
                
                try:
                    # print(f"  → Extracting video data...")  # Verbose
                    
                    # Extract author
                    author_selectors = [
                        "//span[@data-e2e='browse-username']",
                        "//h2[@data-e2e='browse-username']",
                        "//span[contains(@class, 'username')]",
                        "//h1//span"
                    ]
                    for sel in author_selectors:
                        try:
                            elem = self.driver.find_element(By.XPATH, sel)
                            video_data["author"] = elem.text.strip()
                            if video_data["author"]:
                                log.info(f"  → Found author: {video_data['author']}")
                                break
                        except Exception:
                            continue
                            
                    if not video_data["author"]:
                        log.warning(f"  → WARNING: Cloud not extract author from video. Selectors tried: {len(author_selectors)}")
                        # Fallback: try getting from URL if possible
                        try:
                            if "/@" in video_url:
                                match = re.search(r"@([^/?&]+)", video_url)
                                if match:
                                    video_data["author"] = match.group(1)
                                    log.info(f"  → Extracted author from URL: {video_data['author']}")
                        except:
                            pass
                    
                    # Extract description
                    desc_selectors = [
                        "//div[@data-e2e='browse-video-desc']",
                        "//div[contains(@class, 'video-meta-caption')]",
                        "//span[contains(@class, 'desc')]",
                        "//div[contains(@class, 'caption')]"
                    ]
                    for sel in desc_selectors:
                        try:
                            elem = self.driver.find_element(By.XPATH, sel)
                            desc = elem.text.strip()
                            if desc:
                                video_data["description"] = desc
                                video_data["hashtags"] = re.findall(r"#\w+", desc)
                                break
                        except NoSuchElementException:
                            continue

                    #Fallback: description from aria-label of search-common-link
                    if not video_data["description"]:
                        try:
                            a_tag = self.driver.find_element(By.XPATH, "//a[@data-e2e='search-common-link']")
                            aria_label = a_tag.get_attribute("aria-label")
                            match = re.search(r"Watch more videos from user (.+)", aria_label)
                            if match:
                                video_data["description"] = match.group(1).strip()
                                # print(f"Extracted description from aria-label: {video_data['description']}")  # Verbose
                        except NoSuchElementException:
                            pass

                    # Extract post date (relative time: "x minutes/hours/days ago") and calculate actual date
                    post_date_selectors = [
                        "//span[contains(@class, 'TUXText') and contains(text(), 'ago')]",
                        "//span[contains(text(), 'ago')]",
                        "//span[contains(text(), 'd ago') or contains(text(), 'h ago') or contains(text(), 'm ago')]",
                        "//*[contains(text(), 'ago')]"
                    ]
                    for sel in post_date_selectors:
                        try:
                            elem = self.driver.find_element(By.XPATH, sel)
                            post_date_text = elem.text.strip()
                            # Extract the relative time part (e.g., "6d ago", "2h ago", "30m ago")
                            if "ago" in post_date_text:
                                # Calculate actual post date from relative time
                                calculated_date = calculate_post_date(post_date_text)
                                if calculated_date:
                                    video_data["post_date"] = calculated_date
                                    break
                        except NoSuchElementException:
                            continue

                    # Likes
                    try:
                        like_btn = self.driver.find_element(By.XPATH, "//strong[@data-e2e='like-count']")
                        aria_label = like_btn.get_attribute("aria-label")
                        if aria_label:
                             likes_text = aria_label.split()[0]
                        else:
                             likes_text = like_btn.text
                        video_data["likes_count"] = parse_shorthand(likes_text)
                    except NoSuchElementException:
                        video_data["likes_count"] = ""

                    # Comments
                    try:
                        comm = self.driver.find_element(By.XPATH, "//strong[@data-e2e='comment-count']")
                        video_data["comments_count"] = parse_shorthand(comm.text)
                    except NoSuchElementException:
                        video_data["comments_count"] = ""

                    # Shared count
                    try:
                        saved = self.driver.find_element(By.XPATH, "//strong[@data-e2e='shared_count']")
                        video_data["shared_count"] = parse_shorthand(saved.text)
                    except NoSuchElementException:
                        video_data["shared_count"] = ""
                    
                    # Saved count - use direct element finding (not WebDriverWait)
                    saved_count_selectors = [
                        "//strong[@data-e2e='undefined-count']",
                        "//span[@data-e2e='undefined-icon']/following-sibling::strong",
                        "//strong[contains(@class, 'undefined-count')]",
                    ]
                    saved_count_found = False
                    for sel in saved_count_selectors:
                        try:
                            saved_elem = self.driver.find_element(By.XPATH, sel)
                            saved_text = saved_elem.text.strip()
                            if saved_text:
                                video_data["saved_count"] = parse_shorthand(saved_text)
                                saved_count_found = True
                                break
                        except (NoSuchElementException, Exception):
                            continue
                    
                    if not saved_count_found:
                        video_data["saved_count"] = ""

                    # Video URL
                    try:
                        source = self.driver.find_element(By.XPATH, "//video/source")
                        video_data["video_url"] = source.get_attribute("src")
                    except NoSuchElementException:
                        video_data["video_url"] = ""
                    
                    # --- NEW: Scrape Author Account Data ---
                    if video_data.get("author"):
                        try:
                            # print(f"  → Scraping account data for @{video_data['author']}...")  # Verbose
                            
                            # Navigate to profile in SAME tab to avoid driver crashes
                            author_name = video_data['author'].lstrip('@')
                            profile_url = f"https://www.tiktok.com/@{author_name}"
                            
                            # Use navigate with retry logic if available, otherwise standard get
                            if hasattr(self, '_navigate_with_retry'):
                                self._navigate_with_retry(profile_url)
                            else:
                                self.driver.get(profile_url)
                                
                            random_delay(2, 4)
                            
                            # Extract stats
                            account_stats = self._extract_profile_stats(video_data['author'])
                            video_data["author_stats"] = account_stats
                            
                            # print(f"  → Account scraping complete")  # Verbose
                            
                            # Navigate BACK to video page for comments extraction
                            # print(f"  → Returning to video page...")  # Verbose
                            self.driver.get(video_url)
                            random_delay(1, 2)
                            
                        except Exception as acc_err:
                            print(f"  → Failed to scrape account data: {acc_err}")
                            # Try to navigate back to video on error as well
                            try:
                                self.driver.get(video_url)
                                random_delay(1, 2)
                            except:
                                pass
                    
                    # Extract comments (top comments visible on page)
                    try:
                        # print(f"  → Extracting comments...")  # Verbose
                        comments = []
                        # TikTok comment selectors
                        comment_container_selectors = [
                            "//div[@data-e2e='comment-item']",
                            "//div[contains(@class, 'CommentItemContainer')]",
                            "//div[contains(@class, 'comment-item')]",
                        ]
                        
                        for container_sel in comment_container_selectors:
                            try:
                                comment_elements = self.driver.find_elements(By.XPATH, container_sel)
                                if comment_elements:
                                    for idx, elem in enumerate(comment_elements[:20]):  # Max 20 comments
                                        try:
                                            comment_data = {
                                                "username": "",
                                                "text": "",
                                                "likes": "",
                                                "timestamp": ""
                                            }
                                            
                                            # Username
                                            try:
                                                user_elem = elem.find_element(By.XPATH, ".//span[contains(@data-e2e, 'comment-username')] | .//a[contains(@href, '/@')]//span")
                                                comment_data["username"] = user_elem.text.strip()
                                            except:
                                                pass
                                            
                                            # Comment text
                                            try:
                                                text_elem = elem.find_element(By.XPATH, ".//span[contains(@data-e2e, 'comment-text')] | .//p | .//span[contains(@class, 'comment-text')]")
                                                comment_data["text"] = text_elem.text.strip()
                                            except:
                                                pass
                                            
                                            # Likes on comment
                                            try:
                                                likes_elem = elem.find_element(By.XPATH, ".//span[contains(@data-e2e, 'comment-like-count')] | .//span[contains(@class, 'like-count')]")
                                                comment_data["likes"] = likes_elem.text.strip()
                                            except:
                                                pass
                                            
                                            if comment_data["text"]:  # Only add if we got text
                                                comments.append(comment_data)
                                        except Exception:
                                            continue
                                    break  # Found comments, stop trying other selectors
                            except Exception:
                                continue
                        
                        video_data["comments"] = comments
                        # if comments:
                        #     print(f"  → Found {len(comments)} comments")  # Verbose
                    except Exception as e:
                        # print(f"  → Comment extraction failed: {e}")  # Verbose - keep as log.debug if needed
                        video_data["comments"] = []
                    
                    success = True

                except Exception as e:
                    print(f"Error during standard extraction: {e}")
                
                # Fallback JSON parsing - always try to get missing stats
                try:
                    page_source = self.driver.page_source
                    
                    # Extract author if missing
                    if not video_data["author"]:
                        m = re.search(r'"uniqueId":"([^"]+)"', page_source)
                        if m:
                            video_data["author"] = m.group(1)
                    
                    # Extract description if missing
                    if not video_data["description"]:
                        m = re.search(r'"desc":"([^"]+)"', page_source)
                        if m:
                            desc = m.group(1)
                            video_data["description"] = desc
                            video_data["hashtags"] = re.findall(r"#\w+", desc)
                    
                    # Always try to extract stats from JSON (more reliable)
                    m = re.search(r'"stats":(\{[^}]+\})', page_source)
                    if m:
                        stats = json.loads(m.group(1))
                        if not video_data["likes_count"]:
                            video_data["likes_count"] = str(stats.get("diggCount", ""))
                        if not video_data["comments_count"]:
                            video_data["comments_count"] = str(stats.get("commentCount", ""))
                        if not video_data["shared_count"]:
                            video_data["shared_count"] = str(stats.get("shareCount", ""))
                        # Always try to get saved_count from JSON if not found
                        if not video_data["saved_count"]:
                            saved_count = stats.get("collectCount", stats.get("savedCount", ""))
                            video_data["saved_count"] = str(saved_count) if saved_count else ""
                    
                    # Alternative: try to find savedCount in different JSON patterns
                    if not video_data["saved_count"]:
                        patterns = [
                            r'"collectCount":(\d+)',
                            r'"savedCount":(\d+)',
                            r'"bookmarkCount":(\d+)'
                        ]
                        for pattern in patterns:
                            m = re.search(pattern, page_source)
                            if m:
                                video_data["saved_count"] = m.group(1)
                                break
                    
                    # Extract post_date if missing (look for "ago" patterns in HTML)
                    if not video_data["post_date"]:
                        # Try to find relative time patterns in the page source
                        patterns = [
                            r'(\d+[dhm])\s+ago',
                            r'(\d+\s*(?:minute|hour|day)s?)\s+ago',
                            r'·\s*(\d+[dhm])\s+ago',
                            r'>\s*·\s*(\d+[dhm])\s+ago\s*<'
                        ]
                        for pattern in patterns:
                            m = re.search(pattern, page_source, re.IGNORECASE)
                            if m:
                                post_date_text = m.group(1).strip() + " ago"
                                calculated_date = calculate_post_date(post_date_text)
                                if calculated_date:
                                    video_data["post_date"] = calculated_date
                                    break
                                
                except Exception as e:
                    print(f"Error parsing fallback JSON: {e}")
                
                if video_data["author"] or video_data["description"]:
                    return video_data
                else:
                    print(f"No data extracted on attempt {attempt + 1}")
                    if attempt < retries:
                        random_delay(5, 8)
                        continue
            
            except Exception as e:
                print(f"Error on attempt {attempt + 1}: {e}")
                if attempt < retries:
                    random_delay(5, 8)
                    try:
                        self.driver.current_url
                    except:
                        print("Driver crashed; reinitializing...")
                        try:
                            self.driver.quit()
                        except:
                            pass
                        self.setup_driver()
                    continue
                
        print(f"Failed to scrape video after {retries + 1} attempts: {video_url}")
        return None


    
    def scrape_hashtag(self, hashtag, max_posts=None):
        """Scrape videos from a hashtag page (public access, no login required)."""
        import logging
        import sys
        log = logging.getLogger(__name__)
        # log.info(f"DEBUG: scrape_hashtag called with hashtag={hashtag}")  # Verbose
        sys.stdout.flush()
        
        if not hashtag.startswith("#"):
            hashtag = "#" + hashtag
            
        hashtag_url = f"https://www.tiktok.com/tag/{hashtag[1:]}"
        # log.info(f"DEBUG: About to print navigation message")  # Verbose
        print(f"Navigating to hashtag: {hashtag_url}", flush=True)
        
        # log.info(f"DEBUG: Checking use_cookies={self.use_cookies}, driver_type={self.driver_type}")  # Verbose
        # Cookie handling - only if use_cookies is enabled
        if self.use_cookies:
            # log.info("DEBUG: Loading cookies...")  # Verbose
            if not self.load_cookies():
                # log.info("DEBUG: Calling accept_cookies_and_setup...")  # Verbose
                self.accept_cookies_and_setup()
        else:
            # Guest mode - just accept cookie consent dialog
            # log.info("DEBUG: Guest mode - calling accept_cookies_and_setup...")  # Verbose
            self.accept_cookies_and_setup()
            # log.info("DEBUG: accept_cookies_and_setup completed")  # Verbose
        
        # log.info(f"DEBUG: Navigating to hashtag URL: {hashtag_url}")  # Verbose
        # Use retry logic for navigation
        if not self._navigate_with_retry(hashtag_url):
            log.error(f"Failed to navigate to hashtag {hashtag}")
            return False
            
        # log.info("DEBUG: Navigation completed, now running random_delay(3,5)...")  # Verbose
        random_delay(3, 5)
        # log.info("DEBUG: random_delay completed, taking screenshot...")  # Verbose
        
        # IMMEDIATELY take a screenshot for debugging (before any error detection)
        try:
            import os
            from datetime import datetime as dt_screenshot
            debug_screenshot_path = f"/app/screenshots/tiktok_initial_{self.driver_type}_{dt_screenshot.now().strftime('%Y%m%d_%H%M%S')}.png"
            os.makedirs("/app/screenshots", exist_ok=True)
            # log.info(f"DEBUG: About to call save_screenshot to {debug_screenshot_path}")  # Verbose
            self.driver.save_screenshot(debug_screenshot_path)
            # log.info(f"DEBUG: Initial screenshot saved to: {debug_screenshot_path}")  # Verbose
        except Exception as ss_err:
            pass  # Silently continue if screenshot fails
        
        # log.info("DEBUG: Now checking for error elements...")  # Verbose
        # Check if TikTok returned an error page and try clicking Refresh
        # Note: We check for VISIBLE error elements, not just page source text
        # (TikTok's JS includes 'something went wrong' strings even on successful pages)
        max_refresh_retries = 3
        for refresh_attempt in range(max_refresh_retries):
            error_detected = False
            
            # Try to find visible error elements instead of checking page source
            try:
                from selenium.webdriver.common.by import By
                # Check for actual error page elements
                error_selectors = [
                    "//div[contains(@class, 'error') and contains(text(), 'went wrong')]",
                    "//h1[contains(text(), 'Something went wrong')]",
                    "//p[contains(text(), 'Something went wrong')]",
                    "//button[contains(text(), 'Refresh')]//ancestor::div[contains(@class, 'error')]",
                ]
                for selector in error_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        if elements and len(elements) > 0:
                            # Check if element is actually visible
                            for el in elements:
                                if el.is_displayed():
                                    error_detected = True
                                    break
                        if error_detected:
                            break
                    except:
                        continue
            except Exception as e:
                log.error(f"Error checking for error elements: {e}")
            
            # Fallback check: if we couldn't find videos, assume there's an issue
            if not error_detected:
                try:
                    video_elements = self.driver.find_elements(By.XPATH, "//div[@data-e2e='challenge-item']//a")
                    if len(video_elements) > 0:
                        # log.info(f"DEBUG: Found {len(video_elements)} video elements - page loaded successfully!")  # Verbose
                        error_detected = False
                        break  # Exit the retry loop - page is working
                    else:
                        # No videos found - might be an issue, but don't trigger fallback yet
                        pass
                except Exception as e:
                    log.error(f"Error checking for videos: {e}")
            
            if error_detected:
                log.warning(f"TikTok showing error page - attempting refresh ({refresh_attempt + 1}/{max_refresh_retries})")
                
                # Take screenshot for debugging
                try:
                    # Removed redundant imports that cause UnboundLocalError
                    screenshot_path = f"/app/screenshots/tiktok_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    os.makedirs("/app/screenshots", exist_ok=True)
                    self.driver.save_screenshot(screenshot_path)
                    # print(f"Screenshot saved to: {screenshot_path}")  # Verbose
                except Exception as ss_err:
                    pass  # Silently continue
                
                if refresh_attempt < max_refresh_retries - 1:
                    # Special handling for SeleniumBase - try built-in captcha/verify tools
                    if self.driver_type == 'seleniumbase' and hasattr(self._raw_driver, 'sb'):
                        try:
                            # If we have access to the raw sb object
                            # print("Attempting SeleniumBase verification/captcha solver...")  # Verbose
                            sb = self._raw_driver.sb
                            
                            # Try general verification
                            if hasattr(sb, 'verify_success'):
                                sb.verify_success() 
                                
                            # Try captcha solving (works on some challenges)
                            # Note: TikTok 'Something went wrong' isn't always a captcha, but this might help
                            # if it's a hidden verify page
                            # sb.uc_gui_click_captcha() # Only if captcha is visible
                            
                            random_delay(2, 4)
                        except Exception as sb_err:
                            pass  # Silently continue

                    try:
                        from selenium.webdriver.common.by import By
                        refresh_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Refresh')]")
                        refresh_btn.click()
                        # print("Clicked Refresh button, waiting...")  # Verbose
                        random_delay(5, 8)  # Wait longer after refresh
                    except Exception as click_err:
                        # print(f"Could not click Refresh: {click_err}")  # Verbose

                        # Try page refresh instead
                        self.driver.get(hashtag_url)
                        random_delay(5, 8)
                else:
                    # print("Refresh failed. triggering fallback to Stealthy Playwright driver...")  # Verbose
                    # Switch to fallback driver (Playwright with stealth plugin)
                    try:
                        self._raw_driver, self.driver_type = switch_to_fallback(
                            self._raw_driver, 
                            headless=os.getenv("HEADLESS", "true").lower() not in ("false", "0", "no"),
                            proxy=self.proxy
                        )
                        
                        # Update driver reference
                        if self.driver_type == 'seleniumbase':
                            self.driver = self._raw_driver.driver
                        else:
                            self.driver = self._raw_driver
                            
                        # print(f"Switched to driver: {self.driver_type}")  # Verbose
                        
                        # Retry navigation with new driver
                        self.driver.get(hashtag_url)
                        random_delay(3, 5)
                        
                        # Check one last time
                        page_source = self.driver.page_source.lower() if hasattr(self.driver, 'page_source') else ""
                        if "something went wrong" in page_source:
                            raise Exception("TikTok returned 'Something went wrong' even with Stealthy Playwright driver")
                            
                    except Exception as fallback_err:
                        raise Exception(f"Failed to switch/use fallback driver: {fallback_err}")
            else:
                break  # Page loaded successfully



        
        # User requested specific check for post count
        try:
            # log.info("DEBUG: Attempting to extract post count using user XPath...")  # Verbose
            post_count_xpath = "/html/body/div[1]/div[2]/div[2]/div/div[1]/div[1]/div[2]/h2"
            
            # Wait briefly for the element
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            try:
                post_count_el = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, post_count_xpath))
                )
                if post_count_el:
                    post_count_text = post_count_el.text
                    # log.info(f"DEBUG: FOUND POST COUNT: {post_count_text}")  # Verbose
                    # print(f"FOUND POST COUNT: {post_count_text}")  # Verbose
                    pass
                else:
                    pass  # log.warning("DEBUG: Post count element found but null")
            except Exception as wait_err:
                pass  # log.warning(f"DEBUG: specific post count element not found: {wait_err}")
                
        except Exception as e:
            log.error(f"Error extracting post count: {e}")
            
        posts_data = []
        video_links = set()
        
        posts_data = []
        video_links = set()
        
        log.info(f"Finding videos for hashtag {hashtag}...")

        
        # Similar scrolling logic as profile scraping
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
        except Exception as e:
            log.error(f"Failed to get initial scroll height: {e}")
            last_height = 0
            
        scroll_attempts = 0
        max_scroll_attempts = 15
        
        while scroll_attempts < max_scroll_attempts:
            try:
                # Find video elements in hashtag page
                video_elements = self.driver.find_elements(By.XPATH, "//div[@data-e2e='challenge-item']//a")
                
                for el in video_elements:
                    href = el.get_attribute("href")
                    if href and "/video/" in href:
                        video_links.add(href)
                        
                print(f"Found {len(video_links)} videos so far...")
                
                if max_posts and len(video_links) >= max_posts:
                    break
                    
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                random_delay(2, 4)
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    scroll_attempts += 1
                    if scroll_attempts >= 3:
                        break
                else:
                    last_height = new_height
                    scroll_attempts = 0
                    
            except Exception as e:
                print(f"Error while scrolling: {e}")
                scroll_attempts += 1
        
        video_links = list(video_links)
        if max_posts:
            video_links = video_links[:max_posts]
        print(f"Found {len(video_links)} videos in total.")
        
        for idx, video_url in enumerate(video_links, start=1):
            try:
                print(f"Processing video {idx}/{len(video_links)}: {video_url}")
                data = self.scrape_video(video_url)
                if data:
                    posts_data.append(data)
                random_delay(2, 4)
            except Exception as e:
                print(f"Error processing {video_url}: {e}")
        
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        # Ensure output directory exists (using same logic as scrape_profile)
        output_dir = os.path.join(os.path.dirname(__file__), "scrape_result")
        os.makedirs(output_dir, exist_ok=True)
        json_filename = os.path.join(output_dir, f"{hashtag[1:]}_tiktoks_{timestamp}.json")
        
        with open(json_filename, "w", encoding="utf-8") as jf:
            json.dump(posts_data, jf, ensure_ascii=False, indent=4)
        print(f"Saved all videos to {json_filename}")
        
        return posts_data
    
    def scrape_explore(self, max_posts=None):
        """Scrape videos from TikTok explore page (public access, no login required)."""
        explore_url = "https://www.tiktok.com/explore?lang=en"
        print(f"Navigating to explore page: {explore_url}")
        
        # Cookie handling - only if use_cookies is enabled
        if self.use_cookies:
            if not self.load_cookies():
                self.accept_cookies_and_setup()
        else:
            # Guest mode - just accept cookie consent dialog
            self.accept_cookies_and_setup()
            
        self.driver.get(explore_url)
        random_delay(3, 5)
        
        posts_data = []
        video_links = set()
        
        print("Finding trending videos on explore page...")
        
        # Scroll to load more videos
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scroll_attempts = 20
        
        while scroll_attempts < max_scroll_attempts:
            try:
                # Find video elements on explore page - multiple selectors to try
                video_elements = []
                
                # Try different selectors for explore page videos
                selectors = [
                    "//div[contains(@class, 'video-feed-item')]//a[contains(@href, '/video/')]",
                    "//div[@data-e2e='explore-item']//a",
                    "//a[contains(@href, '/video/')]",
                    "//div[contains(@class, 'explore')]//a[contains(@href, '/@')]"
                ]
                
                for selector in selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        video_elements.extend(elements)
                    except:
                        continue
                
                # Remove duplicates and filter valid video links
                for el in video_elements:
                    try:
                        href = el.get_attribute("href")
                        if href and ("/video/" in href or "/@" in href):
                            # If it's a profile link, we might need to extract the video ID differently
                            if "/video/" in href:
                                video_links.add(href)
                            elif "/@" in href and "/video/" not in href:
                                # This might be a profile link, try to click and get actual video URL
                                continue
                    except:
                        continue
                        
                print(f"Found {len(video_links)} videos so far...")
                
                if max_posts and len(video_links) >= max_posts:
                    break
                    
                # Scroll down to load more content
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                random_delay(2, 4)
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    scroll_attempts += 1
                    # Try clicking on "Load more" or similar buttons
                    try:
                        load_more_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Load') or contains(text(), 'More')]")
                        load_more_btn.click()
                        random_delay(2, 3)
                        scroll_attempts = 0  # Reset if we found a load more button
                    except NoSuchElementException:
                        pass
                    
                    if scroll_attempts >= 3:  # If no new content after 3 attempts
                        break
                else:
                    last_height = new_height
                    scroll_attempts = 0
                    
            except Exception as e:
                print(f"Error while scrolling explore page: {e}")
                scroll_attempts += 1
        
        video_links = list(video_links)
        if max_posts:
            video_links = video_links[:max_posts]
        print(f"Found {len(video_links)} videos in total.")
        
        # If we didn't find many videos, try alternative approach
        if len(video_links) < 5:
            print("Trying alternative method to find videos...")
            try:
                # Try to find videos by looking for video elements directly
                video_tags = self.driver.find_elements(By.TAG_NAME, "video")
                for video_tag in video_tags:
                    try:
                        # Try to find the parent link
                        parent_link = video_tag.find_element(By.XPATH, "./ancestor::a[contains(@href, '/video/')]")
                        href = parent_link.get_attribute("href")
                        if href:
                            video_links.add(href)
                    except:
                        continue
                        
                print(f"Alternative method found {len(video_links)} total videos")
            except Exception as e:
                print(f"Alternative method failed: {e}")
        
        for idx, video_url in enumerate(video_links, start=1):
            try:
                print(f"Processing video {idx}/{len(video_links)}: {video_url}")
                data = self.scrape_video(video_url)
                if data:
                    posts_data.append(data)
                random_delay(2, 4)  # Longer delays between videos
            except Exception as e:
                print(f"Error processing {video_url}: {e}")
                
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"socialmedia/scrape_result/tiktok_explore_{timestamp}.json"
        with open(json_filename, "w", encoding="utf-8") as jf:
            json.dump(posts_data, jf, ensure_ascii=False, indent=4)
        print(f"Saved all explore videos to {json_filename}")
        
        return posts_data
    
    def close(self):
        """Close the scraper and clean up resources."""
        if self._raw_driver:
            try:
                self._raw_driver.quit()
            except Exception as e:
                print(f"Error closing driver: {e}")
            finally:
                self._raw_driver = None
                self.driver = None


if __name__ == "__main__":
    # Prompt for account name before initializing browser
    account_name = input("Enter TikTok account name to scrape (without @): ").strip()
    
    if not account_name:
        print("Error: Account name cannot be empty.")
        exit(1)
    
    # Remove @ if user included it
    account_name = account_name.lstrip("@")
    
    # Prompt for max posts (optional)
    max_posts_input = input("Enter maximum number of posts to scrape (press Enter for all): ").strip()
    max_posts = None
    if max_posts_input:
        try:
            max_posts = int(max_posts_input)
            if max_posts <= 0:
                print("Invalid number, scraping all posts...")
                max_posts = None
        except ValueError:
            print("Invalid number, scraping all posts...")
            max_posts = None
    
    # Format URL with lang parameter
    profile_url = f"https://www.tiktok.com/@{account_name}?lang=en"
    
    print(f"\nInitializing browser (Guest mode - no login required)...")
    print(f"Scraping profile: {profile_url}")
    if max_posts:
        print(f"Maximum posts: {max_posts}")
    else:
        print("Scraping all available posts...")
    
    # Create scraper with guest mode (headless mode with improved anti-detection)
    scraper = TikTokScraper(use_cookies=False, headless=True)
    
    try:
        profile_data = scraper.scrape_profile(profile_url, max_posts)
        
        print(f"\nScraping completed! Found {len(profile_data)} posts.")
        
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    except Exception as e:
        print(f"\nError occurred: {e}")
    finally:
        scraper.close()
        print("Browser closed.")