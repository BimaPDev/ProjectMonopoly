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
import random
import logging

# Import the driver factory for SeleniumBase + Playwright fallback
from .drivers import get_driver, switch_to_fallback, BotDetectedError

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
    def __init__(self, cookies_path="cookies/tiktok_cookies.pkl", use_cookies=False, headless=True):
        """
        Initialize TikTok scraper.
        
        Args:
            cookies_path: Path to save/load cookies (only used if use_cookies=True)
            use_cookies: If True, use cookies for authenticated scraping. If False, scrape as guest.
            headless: Run browser in headless mode (recommended for server)
        """
        self.cookies_path = cookies_path
        self.use_cookies = use_cookies
        self.headless = headless
        self.driver = None
        self.driver_type = None  # 'seleniumbase' or 'playwright'
        self._raw_driver = None  # The underlying driver object
        self.setup_driver()
        
    def setup_driver(self):
        """Initialize scraper using SeleniumBase CDP mode with Playwright."""
        print("Setting up TikTok scraper driver (SeleniumBase CDP + Playwright)...")
        
        try:
            self._raw_driver, self.driver_type = get_driver(headless=self.headless)
            
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
            self._raw_driver, self.driver_type = switch_to_fallback(self._raw_driver, headless=self.headless)
            
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
        self.driver.get("https://www.tiktok.com")
        time.sleep(3)
        
        # Try to accept cookies if dialog appears (Playwright-compatible)
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
                        print("Accepted cookies dialog")
                        time.sleep(2)
                        break
                except Exception:
                    continue
        except Exception as e:
            print(f"No cookie dialog found: {e}")
            
        # Close any popup dialogs
        self._dismiss_popups()
        
        # Only save cookies if we're using cookie mode
        if self.use_cookies:
            self.save_cookies()
        return True
    
    def _dismiss_popups(self):
        """Dismiss any popup dialogs (login prompts, notifications, etc.)."""
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
            # TikTok profile stats are in elements with specific data-e2e attributes
            # Followers: data-e2e="followers-count"
            # Following: data-e2e="following-count"
            # Likes: data-e2e="likes-count"
            
            selectors = {
                "followers": "[data-e2e='followers-count']",
                "following": "[data-e2e='following-count']", 
                "likes": "[data-e2e='likes-count']"
            }
            
            for key, selector in selectors.items():
                try:
                    locator = self.driver.page.locator(selector)
                    if locator.count() > 0:
                        text = locator.first.text_content()
                        profile_info[key] = self._parse_count_text(text)
                        print(f"  → {key.capitalize()}: {profile_info[key]}")
                except Exception as e:
                    print(f"Could not extract {key}: {e}")
            
            print(f"Profile stats for @{username}: {profile_info['followers']} followers, {profile_info['following']} following, {profile_info['likes']} likes")
            
        except Exception as e:
            print(f"Error extracting profile stats: {e}")
        
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
                    print(f"  → Navigating to video...")
                    # Use 20 second timeout for video pages
                    self.driver.get(video_url, timeout=20000)
                    print(f"  → Navigation complete")
                except Exception as e:
                    print(f"Error navigating to video: {e}")
                    if attempt < retries:
                        random_delay(3, 5)
                        continue
                    return None
                
                # Wait for page to load (reduced delay since we now have proper timeout)
                print(f"  → Waiting for content...")
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
                    print(f"  → Extracting video data...")
                    
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
                                break
                        except Exception:
                            continue
                    
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
                                print(f"Extracted description from aria-label: {video_data['description']}")
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
                        likes_text = like_btn.get_attribute("aria-label").split()[0]
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
                    
                    # Extract comments (top comments visible on page)
                    try:
                        print(f"  → Extracting comments...")
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
                        if comments:
                            print(f"  → Found {len(comments)} comments")
                    except Exception as e:
                        print(f"  → Comment extraction failed: {e}")
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
        if not hashtag.startswith("#"):
            hashtag = "#" + hashtag
            
        hashtag_url = f"https://www.tiktok.com/tag/{hashtag[1:]}"
        print(f"Navigating to hashtag: {hashtag_url}")
        
        # Cookie handling - only if use_cookies is enabled
        if self.use_cookies:
            if not self.load_cookies():
                self.accept_cookies_and_setup()
        else:
            # Guest mode - just accept cookie consent dialog
            self.accept_cookies_and_setup()
            
        self.driver.get(hashtag_url)
        random_delay(3, 5)
        
        posts_data = []
        video_links = set()
        
        print(f"Finding videos for hashtag {hashtag}...")
        
        # Similar scrolling logic as profile scraping
        last_height = self.driver.execute_script("return document.body.scrollHeight")
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
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"socialmedia/scrape_result/{hashtag[1:]}_tiktoks_{timestamp}.json"
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