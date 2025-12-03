from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, WebDriverException
from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
import time
import json
import os
import pickle
import re
from datetime import datetime
import subprocess
import sys


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
    def __init__(self, username=None, password=None, cookies_path="cookies/instagram_cookies.pkl"):
        self.username = username
        self.password = password
        self.cookies_path = cookies_path
        self.driver = None
        self.setup_driver()
        
    def setup_driver(self):
        chrome_options = Options()
        
        # REQUIRED for Docker/headless environments
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Additional stability options
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--single-process")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()), 
                options=chrome_options
            )
        except Exception as e:
            print(f"WebDriver Manager failed: {e}")
            self.driver = webdriver.Chrome(options=chrome_options)
        
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
        # Accept cookies dialog if it appears (try several common texts)
        cookie_xpaths = [
            "//button[contains(text(), 'Accept')]",
            "//button[contains(text(), 'Allow')]",
            "//button[contains(text(), 'Only allow essential')]",
            "//button[contains(text(), 'Accept All')]",
        ]
        for xp in cookie_xpaths:
            try:
                btn = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, xp))
                )
                try:
                    btn.click()
                except Exception:
                    # fallback: execute click via JS
                    self.driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.5)
                break
            except TimeoutException:
                continue

        # Fill credentials and submit with Enter (more reliable than clicking)
        user_input = self.driver.find_element(By.NAME, "username")
        pass_input = self.driver.find_element(By.NAME, "password")
        user_input.clear()
        user_input.send_keys(self.username)
        pass_input.clear()
        pass_input.send_keys(self.password)
        pass_input.send_keys(Keys.RETURN)
        
        try:
            # Wait for a post-login element (nav/explore link) to appear
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//nav//a[contains(@href, '/explore')]") )
            )
            print("Login successful!")
            try:
                self.save_cookies()
            except Exception as e:
                print(f"Warning: failed to save cookies: {e}")
            return True
        except TimeoutException:
            # Detect common failure states
            cur = self.driver.current_url.lower()
            if "challenge" in cur:
                print("Login requires a challenge (captcha / verification). Manual intervention required.")
            elif "two_factor" in cur or "two-factor" in cur:
                print("Login requires two-factor authentication. Manual intervention required.")
            else:
                print("Login failed or timed out. Check credentials or page layout.")
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
        json_filename = f"socialmedia/scrape_result/{profile_name}_posts_{timestamp}.json"
        with open(json_filename, "w", encoding="utf-8") as jf:
            json.dump(posts_data, jf, ensure_ascii=False, indent=4)
        print(f"Saved all posts to {json_filename}\n")
        

        try:
            if os.getenv("UPLOAD_AFTER_SCRAPE", "1") in ("1", "true", "True"):
                group_id = os.getenv("UPLOAD_GROUP_ID", "1")
                # If DATABASE_URL is provided in env, pass it to the uploader process environment
                env = os.environ.copy()
                dburl = os.getenv("DATABASE_URL")
                if dburl:
                    env["DATABASE_URL"] = dburl

                uploader = os.path.join(os.path.dirname(__file__), "upload_to_db.py")
                if not os.path.exists(uploader):
                    print(f"Uploader script not found at {uploader}; skipping auto-upload")
                else:
                    print(f"Auto-upload enabled — running uploader for {json_filename}")
                    cmd = [sys.executable, uploader, json_filename]
                    # Run uploader and stream output
                    proc = subprocess.run(cmd, env=env)
                    if proc.returncode == 0:
                        print("Auto-upload completed successfully")
                    else:
                        print(f"Auto-upload failed with exit code {proc.returncode}")
        except Exception as e:
            print(f"Error during optional auto-upload: {e}")

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
        # First try the JSON endpoint for the post (more reliable)
        shortcode_m = re.search(r"/p/([^/]+)/", post_url)
        if shortcode_m:
            shortcode = shortcode_m.group(1)
            api_url = f"https://www.instagram.com/p/{shortcode}/?__a=1&__d=dis"
            try:
                self.driver.get(api_url)
                time.sleep(1.0)
                body_txt = self.driver.find_element(By.TAG_NAME, "body").text
                data = json.loads(body_txt)
                # navigate to shortcode_media
                node = None
                if isinstance(data, dict):
                    # some responses nest under graphql
                    node = data.get("graphql", {}).get("shortcode_media") or data.get("shortcode_media")
                if not node:
                    # older or alternate structure
                    try:
                        node = data
                    except Exception:
                        node = None

                if node and isinstance(node, dict):
                    post_data = {
                        "url": post_url,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "post_date": node.get("taken_at_timestamp") or node.get("timestamp") or "",
                        "caption": "",
                        "hashtags": [],
                        "likes": "",
                        "comments_count": "",
                        "media_urls": []
                    }

                    # caption
                    try:
                        edges = node.get("edge_media_to_caption", {}).get("edges", [])
                        if edges:
                            cap = edges[0].get("node", {}).get("text", "")
                            post_data["caption"] = cap
                            post_data["hashtags"] = re.findall(r"#([A-Za-z0-9_]+)", cap)
                    except Exception:
                        pass

                    # likes and comments
                    try:
                        likes = node.get("edge_media_preview_like", {}) or node.get("edge_media_preview_like")
                        if isinstance(likes, dict):
                            count = likes.get("count")
                            if count is not None:
                                post_data["likes"] = str(count)
                    except Exception:
                        pass
                    try:
                        comments = node.get("edge_media_to_parent_comment", {}) or node.get("edge_media_to_parent_comment")
                        if isinstance(comments, dict):
                            count = comments.get("count")
                            if count is not None:
                                post_data["comments_count"] = str(count)
                    except Exception:
                        pass

                    # media urls: single, sidecar, or video
                    try:
                        if node.get("__typename") == "GraphSidecar":
                            children = node.get("edge_sidecar_to_children", {}).get("edges", [])
                            for c in children:
                                n = c.get("node", {})
                                if n.get("is_video"):
                                    url = n.get("video_url") or n.get("display_url")
                                else:
                                    url = n.get("display_url")
                                if url and url not in post_data["media_urls"]:
                                    post_data["media_urls"].append(url)
                        else:
                            if node.get("is_video"):
                                url = node.get("video_url") or node.get("display_url")
                                if url:
                                    post_data["media_urls"].append(url)
                            else:
                                url = node.get("display_url")
                                if url:
                                    post_data["media_urls"].append(url)
                    except Exception:
                        pass

                    return post_data
            except Exception:
                # JSON endpoint failed - fall back to HTML parsing below
                pass

        # Prefer parsing the page HTML with BeautifulSoup to avoid many direct Selenium calls
        for attempt in range(2):
            try:
                self.driver.get(post_url)
                time.sleep(1.5)
                html = self.driver.page_source
                soup = BeautifulSoup(html, "html.parser")

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

                # post_date from <time datetime>
                time_tag = soup.find("time", attrs={"datetime": True})
                if time_tag:
                    post_data["post_date"] = time_tag.get("datetime", "")

                # caption: try meta property og:description first
                og_desc = soup.find("meta", property="og:description")
                raw_caption = ""
                if og_desc and og_desc.get("content"):
                    # sometimes og:description includes caption + stats
                    candidate = og_desc.get("content")
                    # Prefer any quoted text (many posts wrap caption in quotes)
                    try:
                        quotes = re.findall(r'"(.*?)"', candidate)
                        if quotes:
                            # choose the longest quoted segment (more likely full caption)
                            raw_caption = max(quotes, key=lambda s: len(s)).replace("\n", " ").strip()
                        else:
                            # fallback: look for dash (hyphen, en-dash, em-dash) then take text after the colon
                            # Look for pattern like "username on date: "caption text""
                            m = re.search(r"[-\u2013\u2014].*?:\s*\"(.+?)\"", candidate)
                            if m:
                                raw_caption = m.group(1).replace("\n", " ").strip()
                            else:
                                # Try without quotes - capture everything after colon until end or next pattern
                                m = re.search(r"[-\u2013\u2014].*?:\s*(.+?)(?:\s*\.\.\.|$)", candidate)
                                if m:
                                    raw_caption = m.group(1).replace("\n", " ").strip()
                                else:
                                    # as last resort, take the part after the last colon
                                    if ':' in candidate:
                                        raw_caption = candidate.split(':')[-1].strip().strip(' .\n')
                                    else:
                                        raw_caption = candidate.strip()
                    except Exception as e:
                        raw_caption = candidate.strip()

                # If caption still missing, try extracting from embedded JSON in scripts
                if not raw_caption:
                    # Search for <script type="application/ld+json"> which sometimes contains description
                    ld = soup.find("script", type="application/ld+json")
                    if ld and ld.string:
                        try:
                            ldj = json.loads(ld.string)
                            if isinstance(ldj, dict):
                                desc = ldj.get("caption") or ldj.get("description")
                                if desc:
                                    raw_caption = desc
                        except Exception:
                            pass

                if not raw_caption:
                    # Some Instagram pages include a JS object with 'shortcode_media' or 'edge_media_to_caption'
                    scripts = soup.find_all("script")
                    for s in scripts:
                        txt = s.string or s.get_text()
                        if not txt or len(txt) < 50:
                            continue
                        # quick heuristic: look for 'shortcode_media' or 'edge_media_to_caption'
                        if 'shortcode_media' in txt or 'edge_media_to_caption' in txt or 'graphql' in txt:
                            # try to find a JSON substring
                            m = re.search(r"(\{\s*\"shortcode_media\"[\s\S]*\})", txt)
                            if not m:
                                # fallback: look for window._sharedData = {...};
                                m2 = re.search(r"window\._sharedData\s*=\s*(\{[\s\S]*?\})\s*;", txt)
                                if m2:
                                    js = m2.group(1)
                                else:
                                    continue
                            else:
                                js = m.group(1)
                            try:
                                data = json.loads(js)
                                # dig for caption in known locations
                                def find_caption(d):
                                    if isinstance(d, dict):
                                        if 'edge_media_to_caption' in d:
                                            edges = d['edge_media_to_caption'].get('edges', [])
                                            if edges:
                                                return edges[0].get('node', {}).get('text', '')
                                        for k, v in d.items():
                                            if isinstance(v, (dict, list)):
                                                res = find_caption(v)
                                                if res:
                                                    return res
                                    elif isinstance(d, list):
                                        for it in d:
                                            res = find_caption(it)
                                            if res:
                                                return res
                                    return None
                                cap = find_caption(data)
                                if cap:
                                    raw_caption = cap
                                    break
                            except Exception:
                                continue
                    # Prefer the common caption container class used by Instagram
                    rb = soup.select_one("article div[class*='C4VMK'] span")
                    if rb and rb.get_text(strip=True):
                        raw_caption = rb.get_text(separator=" ", strip=True)

                if not raw_caption:
                    # Fallback: pick the longest non-empty <span> text within the article
                    spans = soup.select("article span")
                    best = ""
                    for s in spans:
                        txt = s.get_text(separator=" ", strip=True)
                        if not txt:
                            continue
                        # skip obvious UI strings
                        if re.search(r"view all \d+ comments|likes|comment", txt, re.IGNORECASE):
                            continue
                        if len(txt) > len(best):
                            best = txt
                    raw_caption = best

                if not raw_caption:
                    # fallback to image alt
                    img_alt = soup.select_one("article img[alt]")
                    if img_alt:
                        raw_caption = img_alt.get("alt", "")

                # Store the raw caption text and extract hashtags (Unicode-aware)
                post_data["caption"] = raw_caption
                # Use a Unicode-aware hashtag regex, allow letters, numbers, underscores and hyphens
                try:
                    post_data["hashtags"] = re.findall(r"(?u)#([\w\-]+)", raw_caption)
                except Exception:
                    post_data["hashtags"] = re.findall(r"#([A-Za-z0-9_]+)", raw_caption)

                # likes/comments from meta or text
                if og_desc and og_desc.get("content"):
                    desc = og_desc.get("content")
                    m_likes = re.search(r"([\d,]+[KMB]?)\s+likes", desc)
                    if m_likes:
                        post_data["likes"] = parse_shorthand(m_likes.group(1))
                    m_comments = re.search(r"([\d,]+[KMB]?)\s+comments", desc)
                    if m_comments:
                        post_data["comments_count"] = parse_shorthand(m_comments.group(1))

                # media urls
                imgs = soup.select("article img")
                for img in imgs:
                    src = img.get("src") or img.get("data-src")
                    if not src:
                        continue
                    if "s150x150" in src or "profile_pic" in src:
                        continue
                    if src not in post_data["media_urls"]:
                        post_data["media_urls"].append(src)

                vids = soup.select("article video")
                for v in vids:
                    # video src may be in <video src=> or source tags
                    src = v.get("src")
                    if not src:
                        src_tag = v.find("source")
                        src = src_tag.get("src") if src_tag else None
                    if src and src not in post_data["media_urls"]:
                        post_data["media_urls"].append(src)

                return post_data

            except (StaleElementReferenceException, WebDriverException) as e:
                # chromedriver sometimes throws low-level errors; retry once after small sleep
                if attempt == 0:
                    time.sleep(1)
                    continue
                print(f"Error scraping post {post_url}: {e}")
                return None
            except Exception as e:
                print(f"Error scraping post {post_url}: {e}")
                return None
    
    def close(self):
        if self.driver:
            self.driver.quit()



if __name__ == "__main__":
    USERNAME = "dogw.ood6"
    PASSWORD = "qwert1233@"
    
    scraper = InstagramScraper(USERNAME, PASSWORD)
    if not scraper.login():
        print("Failed to log in.")
        scraper.close()
        exit(1)
    
    # Example usage:
    profile = "umbclife"         
    max_posts = 5               
    
    scraper.scrape_profile(profile, max_posts)
    scraper.close()
