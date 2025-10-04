from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import time
import json
import os
import pickle
import re
from datetime import datetime
import random


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

# Random delay function to avoid detection
def random_delay(min_seconds=1, max_seconds=3):
    time.sleep(random.uniform(min_seconds, max_seconds))


class TikTokScraper:
    def __init__(self, cookies_path="cookies/tiktok_cookies.pkl"):
        self.cookies_path = cookies_path
        self.driver = None
        self.setup_driver()
        
    def setup_driver(self):
        chrome_options = Options()
        chrome_options.headless = False  # TikTok is harder to scrape headless
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Speed up loading
        #chrome_options.add_argument("--disable-javascript")  # Disable JS to avoid detection
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Add user agent for macOS
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Add memory and stability options
        chrome_options.add_argument("--max_old_space_size=4096")
        chrome_options.add_argument("--memory-pressure-off")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.set_window_size(1920, 1080)
            # Set timeouts
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
        except Exception as e:
            print(f"Error setting up driver: {e}")
            raise
        
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
        """Handle initial TikTok page setup"""
        self.driver.get("https://www.tiktok.com")
        time.sleep(3)
        
        # Try to accept cookies if dialog appears
        try:
            accept_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Agree')]"))
            )
            accept_button.click()
            print("Accepted cookies")
            time.sleep(2)
        except TimeoutException:
            print("No cookie dialog found")
            
        # Close any popup dialogs
        try:
            close_button = self.driver.find_element(By.XPATH, "//button[@aria-label='Close']")
            close_button.click()
            time.sleep(1)
        except NoSuchElementException:
            pass
        self.save_cookies()
        return True
    
    def scrape_profile(self, profile_url, max_posts=None):
        """Scrape TikTok profile posts"""
        if not profile_url.startswith("https://www.tiktok.com/"):
            profile_url = profile_url.lstrip("@")
            profile_url = f"https://www.tiktok.com/@{profile_url.strip('/')}"
            
        print(f"Navigating to profile: {profile_url}")
        
        # Load cookies first
        if not self.load_cookies():
            self.accept_cookies_and_setup()
            
        self.driver.get(profile_url)
        random_delay(3, 5)
        
        try:
            profile_name = re.search(r"tiktok\.com/@([^/?]+)", profile_url).group(1)
        except:
            profile_name = "tiktok_profile"
            
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
                
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"socialmedia/scrape_result/{profile_name}_tiktoks_{timestamp}.json"
        with open(json_filename, "w", encoding="utf-8") as jf:
            json.dump(posts_data, jf, ensure_ascii=False, indent=4)
        print(f"Saved all videos to {json_filename}")
        return posts_data
    
    def scrape_video(self, video_url, retries=2):
        """
        Scrape one TikTok video with retry logic and better error handling
        """
        for attempt in range(retries + 1):
            try:
                print(f"Attempting to scrape video (attempt {attempt + 1}/{retries + 1}): {video_url}")
                
                try:
                    self.driver.get(video_url)
                except Exception as e:
                    print(f"Error navigating to video: {e}")
                    if attempt < retries:
                        random_delay(3, 5)
                        continue
                    return None
                
                random_delay(3, 5)
                
                try:
                    WebDriverWait(self.driver, 15).until(
                        lambda d: d.execute_script("return document.readyState") == "complete"
                    )
                except TimeoutException:
                    print("Page didn't load completely, continuing anyway...")
                
                video_data = {
                    "url": video_url,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "post_date": "",
                    "description": "",
                    "hashtags": [],
                    "likes_count": "",
                    "comments_count": "",
                    "shared_count": "",
                    "author": "",
                }
                
                success = False
                
                try:
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
                        except NoSuchElementException:
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
                    
                    # Saved count
                    try:
                        saved = self.driver.find_element(By.XPATH, "//strong[@data-e2e='undefined-count']")
                        video_data["saved_count"] = parse_shorthand(saved.text)
                    except NoSuchElementException:
                        video_data["saved_count"] = ""

                    # Video URL
                    try:
                        source = self.driver.find_element(By.XPATH, "//video/source")
                        video_data["video_url"] = source.get_attribute("src")
                    except NoSuchElementException:
                        video_data["video_url"] = ""
                    
                    success = True

                except Exception as e:
                    print(f"Error during standard extraction: {e}")
                
                # Fallback JSON parsing
                if not success or not any([video_data["author"], video_data["description"]]):
                    try:
                        page_source = self.driver.page_source
                        if not video_data["author"]:
                            m = re.search(r'"uniqueId":"([^"]+)"', page_source)
                            if m:
                                video_data["author"] = m.group(1)
                        if not video_data["description"]:
                            m = re.search(r'"desc":"([^"]+)"', page_source)
                            if m:
                                desc = m.group(1)
                                video_data["description"] = desc
                                video_data["hashtags"] = re.findall(r"#\w+", desc)
                        m = re.search(r'"stats":(\{[^}]+\})', page_source)
                        if m:
                            stats = json.loads(m.group(1))
                            video_data["likes_count"] = str(stats.get("diggCount", ""))
                            video_data["comments_count"] = str(stats.get("commentCount", ""))
                            video_data["shared_count"] = str(stats.get("shareCount", ""))
                            video_data["saved_count"] = str(stats.get("savedCount","")) 
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
        """Scrape videos from a hashtag page"""
        if not hashtag.startswith("#"):
            hashtag = "#" + hashtag
            
        hashtag_url = f"https://www.tiktok.com/tag/{hashtag[1:]}"
        print(f"Navigating to hashtag: {hashtag_url}")
        
        # Load cookies first
        if not self.load_cookies():
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
        """Scrape videos from TikTok explore page"""
        explore_url = "hhttps://www.tiktok.com/explore?lang=en"
        print(f"Navigating to explore page: {explore_url}")
        
        # Load cookies first
        if not self.load_cookies():
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
        if self.driver:
            self.driver.quit()


if __name__ == "__main__":
    scraper = TikTokScraper()
    
    try:
        # Example usage - scrape explore page
        print("Scraping explore page...")
        explore_data = scraper.scrape_explore(max_posts=5)
        
        # Example usage - scrape a profile
        # profile = "charlidamelio"  # or use full URL: "https://www.tiktok.com/@charlidamelio"
        # max_posts = 5
        # print("Scraping profile...")
        # profile_data = scraper.scrape_profile(profile, max_posts)
        
        # Example usage - scrape a hashtag
        # hashtag = "fyp"  # or use "#fyp"
        # print("Scraping hashtag...")
        # hashtag_data = scraper.scrape_hashtag(hashtag, max_posts=3)
        
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    finally:
        scraper.close()
        print("Browser closed.")