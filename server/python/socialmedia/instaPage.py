from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
import os
import pickle
import re
from datetime import datetime


def parse_shorthand(value: str) -> str:
    # Convert notation (K, M, B) full numbers
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
    return val  # No suffix

def prefix_words_with_hash(caption: str) -> str:
    # Prefix every word in the caption with "#"
    tokens = caption.split()
    return " ".join(f"{tok}" for tok in tokens if tok.strip())

class InstagramScraper:
    def __init__(self, username=None, password=None, cookies_path="instagram_cookies.pkl"):
        self.username = username
        self.password = password
        self.cookies_path = cookies_path
        self.driver = None
        self.setup_driver()
        
    def setup_driver(self):
        chrome_options = Options()
        chrome_options.headless = False
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()
        
    def save_cookies(self):
        pickle.dump(self.driver.get_cookies(), open(self.cookies_path, "wb"))
        print("Cookies saved successfully!")
        
    def load_cookies(self):
        if os.path.exists(self.cookies_path):
            cookies = pickle.load(open(self.cookies_path, "rb"))
            self.driver.get("https://www.instagram.com")
            time.sleep(2)
            for cookie in cookies:
                try:
                    cookie.pop("sameSite", None)
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"Error adding cookie: {e}")
            print("Cookies loaded successfully!")
            self.driver.get("https://www.instagram.com")
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//nav//a[contains(@href, '/explore')]"))
                )
                return True
            except TimeoutException:
                return False
        return False
        
    def login(self):
        # First try to log in via saved cookies
        if self.load_cookies():
            print("Login successful using cookies!")
            return True
        
        # Otherwise, perform username/password login
        if not self.username or not self.password:
            print("No saved cookies and no credentials provided. Cannot login.")
            return False
            
        print("Logging in with username and password...")
        self.driver.get("https://www.instagram.com/accounts/login/")
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        
        # Accept cookies dialog if it appears
        try:
            cookie_button = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow')]"))
            )
            cookie_button.click()
            time.sleep(1)
        except TimeoutException:
            pass
                
        self.driver.find_element(By.NAME, "username").send_keys(self.username)
        self.driver.find_element(By.NAME, "password").send_keys(self.password)
        
        login_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
        )
        login_button.click()
        
        try:
            WebDriverWait(self.driver, 10).until(
                EC.url_contains("instagram.com")
            )
            print("Login successful!")
            self.save_cookies()
            return True
        except TimeoutException:
            print("Login failed. Try again.")
            return False
    
    def scrape_profile(self, profile_url, max_posts=None):
        if not profile_url.startswith("https://www.instagram.com/"):
            profile_url = profile_url.lstrip("@")
            profile_url = f"https://www.instagram.com/{profile_url.strip('/')}/"
            
        print(f"Navigating to profile: {profile_url}")
        self.driver.get(profile_url)
        time.sleep(3)
        
        try:
            profile_name = re.search(r"instagram\.com/([^/?]+)", profile_url).group(1)
        except:
            profile_name = "instagram_profile"
            
        posts_data = []
        post_links = set()
        
        print("Finding posts...")
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while True:
            try:
                post_elements = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '/p/')]"))
                )
                for el in post_elements:
                    href = el.get_attribute("href")
                    if href:
                        post_links.add(href)
                        
                print(f"Found {len(post_links)} posts so far...")
                
                if max_posts and len(post_links) >= max_posts:
                    break
                    
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    time.sleep(2)
                    new_height2 = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height2 == last_height:
                        break
                    else:
                        last_height = new_height2
                else:
                    last_height = new_height
            except Exception as e:
                print(f"Error while scrolling: {e}")
                break
                
        post_links = list(post_links)
        if max_posts:
            post_links = post_links[:max_posts]
        print(f"Found {len(post_links)} posts in total.")
        
        for idx, post_url in enumerate(post_links, start=1):
            try:
                print(f"Processing post {idx}/{len(post_links)}: {post_url}")
                data = self.scrape_post(post_url)
                if data:
                    posts_data.append(data)
                time.sleep(1)
            except Exception as e:
                print(f"Error processing {post_url}: {e}")
                
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"{profile_name}_posts_{timestamp}.json"
        with open(json_filename, "w", encoding="utf-8") as jf:
            json.dump(posts_data, jf, ensure_ascii=False, indent=4)
        print(f"Saved all posts to {json_filename}")
        
        return posts_data
    
    def scrape_post(self, post_url):
        """
        Scrape one Instagram post. Extract:
          - url
          - timestamp (when we scraped)
          - post_date (timestamp from the <time> tag)
          - caption (each word prefixed with "#")
          - hashtags (list of #words found in raw caption)
          - likes (full integer)
          - comments_count (full integer)
          - media_urls (only real images/videos)
        """
        self.driver.get(post_url)
        time.sleep(2)
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//article"))
            )
            
            post_data = {
                "url": post_url,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "post_date": "",
                "caption": "",
                "hashtags": [],
                "likes": "",
                "comments_count": "",
                "media_urls": []
            }
            
            # 1) Extract post_date from <time>
            try:
                time_elem = self.driver.find_element(By.XPATH, "//time[@datetime]")
                post_data["post_date"] = time_elem.get_attribute("datetime")
            except NoSuchElementException:
                pass
            
            # 2) Try to expand a long caption via the “more” button
            try:
                more_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'more')]")
                more_btn.click()
                time.sleep(0.5)
            except NoSuchElementException:
                pass
            
            # 3) Attempt to read the full caption from <div class="xt0psk2"> / <h1>
            raw_caption = ""
            try:
                caption_h1 = self.driver.find_element(By.XPATH, "//div[contains(@class,'xt0psk2')]/h1")
                raw_caption = caption_h1.text or ""
            except NoSuchElementException:
                raw_caption = ""
            
            # 4) If that fails, read from <div role="textbox">
            if not raw_caption:
                try:
                    caption_span = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, "//article//div[@role='textbox']//span"))
                    )
                    raw_caption = caption_span.text or ""
                except (TimeoutException, NoSuchElementException):
                    raw_caption = ""
            
            # 5) If still empty, fall back to the img[@alt] auto‐generated text
            if not raw_caption:
                try:
                    img_elem = self.driver.find_element(By.XPATH, "//article//img[@alt]")
                    raw_caption = img_elem.get_attribute("alt") or ""
                except NoSuchElementException:
                    raw_caption = ""
            
            # 6) Extract likes and comments_count from <meta name="description">
            try:
                meta_desc = self.driver.find_element(
                    By.XPATH, "//meta[@name='description']"
                ).get_attribute("content")
                
                # Likes shorthand
                m_likes = re.search(r"([\d,]+[KMB]?)\s+likes", meta_desc)
                if m_likes:
                    post_data["likes"] = parse_shorthand(m_likes.group(1))
                
                # Comments shorthand
                m_comments = re.search(r"([\d,]+[KMB]?)\s+comments", meta_desc)
                if m_comments:
                    post_data["comments_count"] = parse_shorthand(m_comments.group(1))
            except NoSuchElementException:
                pass
            
            # 7) If likes or comments_count still empty, use on-page fallback
            if not post_data["likes"]:
                try:
                    likes_elem = self.driver.find_element(
                        By.XPATH, "//section//div[contains(text(), ' likes')]"
                    )
                    post_data["likes"] = re.sub(r"\D", "", likes_elem.text)
                except NoSuchElementException:
                    post_data["likes"] = ""
            if not post_data["comments_count"]:
                try:
                    comm_btn = self.driver.find_element(
                        By.XPATH, "//button[@aria-label='Comment']"
                    )
                    txt = comm_btn.text  # e.g. "View all 23 comments"
                    m_c = re.search(r"(\d+)", txt)
                    post_data["comments_count"] = m_c.group(1) if m_c else "0"
                except NoSuchElementException:
                    post_data["comments_count"] = "0"
            
            # 8) Prefix each word in the final raw_caption with "#"
            post_data["caption"] = prefix_words_with_hash(raw_caption)
            
            # 9) Extract any actual hashtags from raw_caption
            post_data["hashtags"] = re.findall(r"#\w+", raw_caption)
            
            # 10) Gather media URLs (images & videos), excluding small thumbnails/profile icons
            imgs = self.driver.find_elements(By.XPATH, "//article//img")
            for img in imgs:
                src = img.get_attribute("src")
                if not src:
                    continue
                if "s150x150" in src or "profile_pic" in src:
                    continue
                if src not in post_data["media_urls"]:
                    post_data["media_urls"].append(src)
            
            vids = self.driver.find_elements(By.XPATH, "//article//video")
            for vid in vids:
                src = vid.get_attribute("src")
                if src and src not in post_data["media_urls"]:
                    post_data["media_urls"].append(src)
            
            return post_data
        
        except Exception as e:
            print(f"Error scraping post {post_url}: {e}")
            return None
    
    def close(self):
        if self.driver:
            self.driver.quit()



if __name__ == "__main__":
    # Hardcoded login credentials for automated login
    USERNAME = "dogw.ood6"
    PASSWORD = "qwert1233@"
    
    scraper = InstagramScraper(USERNAME, PASSWORD)
    if not scraper.login():
        print("Failed to log in.")
        scraper.close()
        exit(1)
    
    # Example usage:
    profile = "chelseafc"         
    max_posts = 5               
    
    scraper.scrape_profile(profile, max_posts)
    scraper.close()