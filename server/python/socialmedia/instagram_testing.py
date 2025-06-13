import os
import time
import json
import re
import uuid

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

# ──────────────── 1. CONFIGURATION ─────────────────────
INSTAGRAM_USERNAME = "davidisdatboi"
INSTAGRAM_PASSWORD = "Fiyin@2004"

AUTH_PATH = "auth.json"
PAGE_LOAD_WAIT = 3  # seconds to wait after each driver.get()

# ──────────────── 2. DRIVER SETUP ──────────────────────
def create_driver(headless: bool = True) -> webdriver.Chrome:
    chrome_opts = Options()
    if headless:
        chrome_opts.add_argument("--headless")
        chrome_opts.add_argument("--disable-gpu")
    chrome_opts.add_argument("--window-size=1200,800")
    chrome_opts.add_argument("--no-sandbox")
    chrome_opts.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_opts)
    driver.maximize_window()
    return driver


# ──────────────── 3. LOGIN / COOKIE MANAGEMENT ──────────────
def save_cookies(driver: webdriver.Chrome, path: str = AUTH_PATH):
    cookie_data = driver.get_cookies()
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"cookies": cookie_data, "origins": []}, f, indent=2)


def load_cookies_and_local_storage(driver: webdriver.Chrome, path: str = AUTH_PATH) -> bool:
    if not os.path.exists(path):
        return False

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    driver.get("https://www.instagram.com")
    time.sleep(2)

    for cookie in data.get("cookies", []):
        selenium_cookie = {
            "name": cookie["name"],
            "value": cookie["value"],
            "domain": cookie["domain"],
            "path": cookie.get("path", "/"),
            "secure": cookie.get("secure", False),
            "httpOnly": cookie.get("httpOnly", False),
        }
        if cookie.get("expiry", None) and isinstance(cookie["expiry"], (int, float)) and cookie["expiry"] > 0:
            selenium_cookie["expiry"] = int(cookie["expiry"])
        try:
            selenium_cookie["sameSite"] = cookie.get("sameSite", "Lax")
        except:
            pass

        try:
            driver.add_cookie(selenium_cookie)
        except:
            pass

    for origin_block in data.get("origins", []):
        origin_url = origin_block.get("origin", "")
        if "instagram.com" not in origin_url:
            continue

        driver.get(origin_url)
        time.sleep(1)

        for item in origin_block.get("localStorage", []):
            key = item.get("name")
            val = item.get("value", "")
            script = f"window.localStorage.setItem({json.dumps(key)}, {json.dumps(val)});"
            try:
                driver.execute_script(script)
            except:
                pass

    return True


def instagram_login(driver: webdriver.Chrome):
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(PAGE_LOAD_WAIT)

    try:
        username_input = driver.find_element(By.NAME, "username")
        password_input = driver.find_element(By.NAME, "password")
    except:
        return

    if INSTAGRAM_USERNAME == "" or INSTAGRAM_PASSWORD == "":
        print("🔐  Please log into Instagram manually in the opened browser window.")
        print("    Once you are logged in, press [Enter] in this terminal to continue.")
        input()
    else:
        username_input.clear()
        username_input.send_keys(INSTAGRAM_USERNAME)
        password_input.clear()
        password_input.send_keys(INSTAGRAM_PASSWORD)
        password_input.send_keys(Keys.ENTER)
        time.sleep(PAGE_LOAD_WAIT * 2)

    time.sleep(PAGE_LOAD_WAIT)
    save_cookies(driver, AUTH_PATH)
    print("✅  Logged in and saved cookies to auth.json.")


# ──────────────── 4. UTIL: PARSE NUMBERS (“1.2K” → 1200, etc.) ──────────────
def parse_number(value: str) -> int:
    value = value.upper().replace(",", "").strip()
    if value.endswith("K"):
        return int(float(value[:-1]) * 1_000)
    if value.endswith("M"):
        return int(float(value[:-1]) * 1_000_000)
    if value.endswith("B"):
        return int(float(value[:-1]) * 1_000_000_000)
    try:
        return int(float(value))
    except:
        return 0


# ──────────────── 5. FETCH LATEST POSTS VIA “?__a=1” JSON ENDPOINT ──────────────
def get_latest_post_urls_selenium(
    driver: webdriver.Chrome, username: str, count: int = 5
) -> list[str]:
    if not load_cookies_and_local_storage(driver):
        instagram_login(driver)

    # ────── Change is here: use the JSON endpoint, not the HTML profile ──────
    api_url = f"https://www.instagram.com/{username}/?__a=1&__d=dis"
    driver.get(api_url)
    time.sleep(PAGE_LOAD_WAIT)

    raw = driver.find_element(By.TAG_NAME, "body").text
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print("⚠️  Failed to decode JSON from Instagram. Maybe Instagram blocked you?")
        return []

    try:
        edges = data["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"]
    except KeyError:
        print("⚠️  JSON didn’t contain the expected structure. Perhaps private or invalid username.")
        return []

    post_urls = []
    for edge in edges[:count]:
        shortcode = edge["node"]["shortcode"]
        post_urls.append(f"https://www.instagram.com/p/{shortcode}/")

    return post_urls


# ──────────────── 6. SCRAPE A SINGLE POST VIA SELENIUM + BS4 ──────────────
def scrape_post_with_selenium(driver: webdriver.Chrome, post_url: str):
    driver.get(post_url)
    time.sleep(PAGE_LOAD_WAIT)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    result = {}

    og_desc = soup.find("meta", property="og:description")
    caption_text = None

    if og_desc:
        desc = og_desc.get("content", "")
        match = re.search(
            r"([\d.,]+[KMB]?)\s+likes,\s+([\d.,]+)\s+.*\s+–\s+([@\w\d._]+)\s+on.*?:\s+\"(.*?)\"(?:\.|\”)?$",
            desc.strip(),
            re.DOTALL,
        )
        if match:
            result["likes"] = parse_number(match.group(1))
            result["comments"] = int(match.group(2).replace(",", ""))
            result["username"] = match.group(3).strip()
            caption_text = match.group(4).replace("\n", " ").strip()
        else:
            result["likes"] = None
            result["comments"] = None
            result["username"] = None
    else:
        result["likes"] = None
        result["comments"] = None
        result["username"] = None

    if caption_text is None:
        caption_block = soup.find("div", {"role": "button"})
        if caption_block:
            raw_cap = caption_block.get_text(separator=" ", strip=True)
            result["caption_raw"] = raw_cap
            result["caption"] = raw_cap
        else:
            result["caption_raw"] = None
            result["caption"] = None
    else:
        result["caption_raw"] = None
        result["caption"] = caption_text

    comments_list = []
    for comment_li in soup.select("ul li"):
        comment_span = comment_li.find("span")
        if comment_span and comment_span.text:
            username_tag = comment_li.find("h3")
            commenter = username_tag.get_text(strip=True) if username_tag else None

            raw = comment_span.get_text(separator=" ", strip=True)
            comment_text = re.sub(r"^@[^\s]+\s*", "", raw).strip()
            if commenter or comment_text:
                comments_list.append(
                    {
                        "commenter": commenter,
                        "comment": (commenter + " " + comment_text) if commenter else comment_text,
                    }
                )

    result["comments_detail"] = comments_list

    if result.get("username"):
        poster = result["username"].lstrip("@")
        profile_url = f"https://www.instagram.com/{poster}/?__a=1&__d=dis"
        driver.get(profile_url)
        time.sleep(PAGE_LOAD_WAIT)

        raw2 = driver.find_element(By.TAG_NAME, "body").text
        try:
            prof_data = json.loads(raw2)
            followers = prof_data["graphql"]["user"]["edge_followed_by"]["count"]
            following = prof_data["graphql"]["user"]["edge_follow"]["count"]
            posts = prof_data["graphql"]["user"]["edge_owner_to_timeline_media"]["count"]
            result["profile"] = {
                "followers": followers,
                "following": following,
                "posts": posts,
            }
        except Exception:
            html2 = driver.page_source
            soup2 = BeautifulSoup(html2, "html.parser")
            meta2 = soup2.find("meta", property="og:description")
            if meta2:
                desc2 = meta2.get("content", "")
                parts = [p.strip() for p in desc2.split("–")[0].split(",")]
                clean_count = lambda s: parse_number(re.sub(r"[^\dKM\.]", "", s))
                try:
                    result["profile"] = {
                        "followers": clean_count(parts[0]),
                        "following": clean_count(parts[1]),
                        "posts": clean_count(parts[2]),
                    }
                except Exception:
                    result["profile"] = None
            else:
                result["profile"] = None
    else:
        result["profile"] = None

    final = {
        "likes": result.get("likes"),
        "comments": result.get("comments"),
        "username": result.get("username"),
        "caption": result.get("caption"),
        "comments_detail": result.get("comments_detail"),
        "profile": result.get("profile"),
    }

    os.makedirs("scrape_result", exist_ok=True)
    filename = f"{uuid.uuid4().hex}.json"
    path = os.path.join("scrape_result", filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(final, f, indent=2, ensure_ascii=False)

    print(f"✅  Saved: {path}")


# ──────────────── 7. SCRAPE LATEST N POSTS ─────────────────────
def scrape_latest_from_account_selenium(
    username: str, count: int = 5, headless: bool = True
):
    driver = create_driver(headless=headless)

    if not load_cookies_and_local_storage(driver):
        instagram_login(driver)

    urls = get_latest_post_urls_selenium(driver, username, count)
    if not urls:
        print(f"⚠️  No posts found for {username}. Perhaps the account is private?")
        driver.quit()
        return

    print(f"🔎  Found {len(urls)} posts. Scraping each…")
    for idx, post_url in enumerate(urls, start=1):
        print(f"  ▶️  [{idx}/{len(urls)}] {post_url}")
        try:
            scrape_post_with_selenium(driver, post_url)
        except Exception as e:
            print(f"    ⚠️  Error scraping {post_url}: {e}")

    driver.quit()
    print("🏁  Done.")


# ──────────────── 8. ENTRY POINT ─────────────────────
if __name__ == "__main__":
    scrape_latest_from_account_selenium("chelseafc", count=5, headless=False)
