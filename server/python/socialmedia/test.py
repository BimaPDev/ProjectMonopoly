from playwright.sync_api import sync_playwright
import json
import re
import uuid
import os
from bs4 import BeautifulSoup
from datetime import datetime

# Optional: Uncomment these if you're saving to Postgres
# import psycopg2
# from psycopg2.extras import execute_values

def parse_number(value: str) -> int:
    value = value.upper().replace(",", "").strip()
    if value.endswith("K"):
        return int(float(value[:-1]) * 1_000)
    if value.endswith("M"):
        return int(float(value[:-1]) * 1_000_000)
    if value.endswith("B"):
        return int(float(value[:-1]) * 1_000_000_000)
    return int(float(value))

def scrape_post_with_playwright(post_url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="auth.json")
        page = context.new_page()

        print(f"🔗 Opening: {post_url}")
        page.goto(post_url, timeout=15000)
        page.wait_for_timeout(3000)

        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        result = {}

        og_desc = soup.find("meta", property="og:description")
        caption_text = None
        if og_desc:
            desc = og_desc["content"]
            print("📄 OG Description:", desc)
            match = re.search(
                r"([\d.,]+[KMB]?)\s+likes,\s+([\d.,]+)\s+comments\s+-\s+([@\w\d._]+)\s+on.*?:\s+\"(.*?)\"(?:\.|\”)?$",
                desc.strip(), re.DOTALL
            )
            if match:
                result["likes"] = parse_number(match.group(1))
                result["comments"] = int(match.group(2).replace(",", ""))
                result["username"] = match.group(3).strip()
                caption_text = match.group(4).replace("\n", " ").strip()
                result["caption"] = caption_text
            else:
                print("⚠️ OG description format mismatch.")
                result["caption_raw"] = desc
                result["likes"] = None
                result["comments"] = None
                result["username"] = None
        else:
            print("⚠️ No og:description found.")
            result["caption_raw"] = None
            result["likes"] = None
            result["comments"] = None
            result["username"] = None

        result["hashtags"] = re.findall(r"#\w+", caption_text) if caption_text else []
        og_image = soup.find("meta", property="og:image")
        result["image_url"] = og_image["content"] if og_image else None
        time_tag = soup.find("time")
        timestamp = time_tag["datetime"] if time_tag and time_tag.has_attr("datetime") else None
        result["timestamp"] = timestamp

        if result.get("username"):
            try:
                profile_url = f"https://www.instagram.com/{result['username']}/"
                print(f"👤 Visiting profile: {profile_url}")
                page.goto(profile_url, timeout=15000)
                page.wait_for_timeout(3000)

                stats = page.locator('header section ul li')
                raw_posts = stats.nth(0).inner_text().split()[0]
                raw_followers = stats.nth(1).inner_text().split()[0]
                raw_following = stats.nth(2).inner_text().split()[0]

                def clean_count(text):
                    return parse_number(text.replace(",", "").replace(" ", ""))

                result["profile"] = {
                    "url": profile_url,
                    "followers": clean_count(raw_followers),
                    "following": clean_count(raw_following),
                    "posts": clean_count(raw_posts)
                }
            except Exception as e:
                print("⚠️ Could not scrape profile stats:", e)
                result["profile"] = None
        else:
            result["profile"] = None

        # Engagement Score
        try:
            followers = result["profile"]["followers"] if result.get("profile") else 1
            engagement = ((result.get("likes") or 0) + (result.get("comments") or 0)) / max(1, followers)
            result["engagement_score"] = round(engagement, 4)
        except Exception as e:
            print("⚠️ Error calculating engagement:", e)
            result["engagement_score"] = None

        # Timestamp parsing
        try:
            ts_obj = datetime.fromisoformat(result["timestamp"]) if result.get("timestamp") else None
            day_of_week = ts_obj.weekday() if ts_obj else None
            hour = ts_obj.hour if ts_obj else None
        except Exception as e:
            print("⚠️ Error parsing timestamp:", e)
            ts_obj = None
            day_of_week = None
            hour = None

        final_result = {
            "post_id": post_url.strip("/").split("/")[-1],
            "post_url": post_url,
            "username": result.get("username"),
            "caption": result.get("caption", result.get("caption_raw")),
            "hashtags": result.get("hashtags", []),
            "timestamp": result.get("timestamp"),
            "day_of_week": day_of_week,
            "hour": hour,
            "image_url": result.get("image_url"),

            "likes": result.get("likes"),
            "comments": result.get("comments"),
            "engagement_score": result.get("engagement_score"),

            "followers": result["profile"]["followers"] if result.get("profile") else None,
            "following": result["profile"]["following"] if result.get("profile") else None,
            "total_posts": result["profile"]["posts"] if result.get("profile") else None,
        }

        # OPTIONAL: Save to PostgreSQL
        # conn = psycopg2.connect(dbname="your_db", user="your_user", password="your_pass", host="localhost")
        # cursor = conn.cursor()
        # execute_values(cursor, """
        #     INSERT INTO instagram_post_performance (
        #         post_id, post_url, username, caption, hashtags, timestamp,
        #         day_of_week, hour, image_url, likes, comments, engagement_score,
        #         followers, following, total_posts
        #     ) VALUES %s ON CONFLICT (post_id) DO NOTHING
        # """, [(final_result['post_id'], final_result['post_url'], final_result['username'],
        #        final_result['caption'], final_result['hashtags'], final_result['timestamp'],
        #        final_result['day_of_week'], final_result['hour'], final_result['image_url'],
        #        final_result['likes'], final_result['comments'], final_result['engagement_score'],
        #        final_result['followers'], final_result['following'], final_result['total_posts'])])
        # conn.commit()
        # cursor.close()
        # conn.close()

        os.makedirs("scrape_result", exist_ok=True)
        filename = f"{final_result['post_id']}.json"
        filepath = os.path.join("scrape_result", filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(final_result, f, indent=2, ensure_ascii=False)

        print(f"✅ Extracted data saved to {filepath}")
        browser.close()

# Example usage
scrape_post_with_playwright("https://www.instagram.com/p/DKAKajGg8io/?hl=en")
