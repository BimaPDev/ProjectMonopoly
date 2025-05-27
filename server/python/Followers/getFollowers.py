import time
import json
import random
import concurrent.futures
import sys
import datetime
import re

import requests
from bs4 import BeautifulSoup

import psycopg2
from psycopg2.extras import RealDictCursor

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# ── DATABASE SETUP ────────────────────────────────────────────────────────────

def connectDB():
    try:
        conn = psycopg2.connect(
            user="root",
            password="secret",
            host="localhost",
            port=5432,
            database="project_monopoly"
        )
        conn.autocommit = True
        return conn
    except psycopg2.Error as e:
        print(f"DB connection error: {e}")
        sys.exit(1)

INSERT_FOLLOWER_SQL = """
INSERT INTO daily_followers (
  record_date,
  follower_count
) VALUES (
  %s,
  %s
)
RETURNING id;
"""

def insert_follower_count(record_date, followers):
    """
    record_date: date (datetime.date)
    followers:    int
    returns:      new row id
    """
    conn = connectDB()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(INSERT_FOLLOWER_SQL, (record_date, followers))
                return cur.fetchone()["id"]
    finally:
        conn.close()

# ── UTILITIES ─────────────────────────────────────────────────────────────────

def parse_number(text: str) -> int:
    """Normalize strings like '1.2M', '34.5K', '1,234' into an integer."""
    text = text.replace(",", "").strip()
    if text.lower().endswith("k"):
        return int(float(text[:-1]) * 1_000)
    if text.lower().endswith("m"):
        return int(float(text[:-1]) * 1_000_000)
    m = re.search(r"\d+", text)
    return int(m.group(0)) if m else 0

def wait_for_element(driver, xpath, timeout=5):
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return el.text
    except TimeoutException:
        return None

def set_up_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(10)
    return driver

# ── SCRAPERS ──────────────────────────────────────────────────────────────────

def get_instagram_followers(username: str) -> int:
    """Fast scrape via Instagram's og:description meta tag."""
    url = f"https://www.instagram.com/{username}/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        meta = soup.find("meta", property="og:description")
        if not meta or not meta.get("content"):
            print("IG: og:description meta not found")
            return 0
        content = meta["content"]
        # e.g. "1,234 Followers, 56 Following, 78 Posts – See Instagram photos"
        m = re.search(r"([\d,\.]+)\s+Followers", content)
        return parse_number(m.group(1)) if m else 0
    except Exception as e:
        print(f"Error scraping Instagram followers: {e}")
        return 0

def get_linkedin_followers(company_name: str) -> int:
    """Fast scrape via LinkedIn's og:description meta tag."""
    url = f"https://www.linkedin.com/company/{company_name}/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    driver = set_up_driver()
    try:
        driver.get(url)
        xpath = "//div[2]/div[2]/div/div[1]/div[2]/div/div/div[2]/div[2]"
        txt = wait_for_element(driver, xpath, 3)
        txt = txt.replace("Followers", "").strip() if txt else ""
        return parse_number(txt) if txt else 0
    except Exception as e:
        print(f"Error scraping LinkedIn followers: {e}")
        return 0

def get_facebook_followers(page_name: str) -> int:
    driver = set_up_driver()
    try:
        driver.get(f"https://www.facebook.com/{page_name}")
        xpath = "//div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div/div[1]/div[2]/div/div/div/div[3]/div/div/div[2]/span/a[2]"
        txt = wait_for_element(driver, xpath, 3)
        txt = txt.replace("followers", "").strip() if txt else ""
        return parse_number(txt) if txt else 0
    except Exception as e:
        print(f"Error scraping Facebook followers: {e}")
        return 0
    finally:
        driver.quit()

def get_twitch_followers(username: str) -> int:
    driver = set_up_driver()
    try:
        driver.get(f"https://twitch.tv/{username}/about")
        xpath = "//div[3]/div/div/div/div[1]/div[2]/div/div/div[2]/div/div[1]/div/div/div/span/div/div/span"
        txt = wait_for_element(driver, xpath, 3)
        return parse_number(txt) if txt else 0
    except Exception as e:
        print(f"Error scraping Twitch followers: {e}")
        return 0
    finally:
        driver.quit()

def get_youtube_followers(channel_id: str) -> int:
    driver = set_up_driver()
    try:
        driver.get(f"https://www.youtube.com/c/{channel_id}")
        xpath = "//yt-page-header-renderer//yt-content-metadata-view-model//span[1]"
        txt = wait_for_element(driver, xpath, 3)
        return parse_number(txt) if txt else 0
    except Exception as e:
        print(f"Error scraping YouTube subscribers: {e}")
        return 0
    finally:
        driver.quit()

# ── MAIN AGGREGATOR ────────────────────────────────────────────────────────────

def totalFollowers():
    tasks = {
        "instagram": (get_instagram_followers, "dogwood_gaming"),
        "twitch":    (get_twitch_followers, "dogwoodgaming"),
        "youtube":   (get_youtube_followers, "DogwoodGaming"),
        "facebook":  (get_facebook_followers, "DogwoodGaming"),
        "linkedin":  (get_linkedin_followers, "dogwood-gaming"),
    }

    followers = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(fn, arg): plat for plat, (fn, arg) in tasks.items()}
        for fut in concurrent.futures.as_completed(futures, timeout=15):
            plat = futures[fut]
            try:
                followers[plat] = fut.result(timeout=5)
            except Exception as e:
                print(f"Error getting {plat} followers: {e}")
                followers[plat] = 0

    total = sum(followers.values())
    today = datetime.datetime.now().date()
    new_id = insert_follower_count(today, total)
    print(f"Inserted record id {new_id} for {today}: {total} followers")

    return json.dumps({
        "total_followers": total,
        "breakdown": followers
    })

if __name__ == "__main__":
    start = time.time()
    result = totalFollowers()
    print(result)
    elapsed = time.time() - start
    print(f"Execution time: {datetime.timedelta(seconds=int(elapsed))}")
    sys.exit(0)
