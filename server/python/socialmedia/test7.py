from playwright.sync_api import sync_playwright
import json
import re
import uuid
import os
from bs4 import BeautifulSoup

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

        # Scroll comments area to ensure all metadata loads
        try:
            scroll_container = page.locator(
                'section main div div:nth-child(1) div div:nth-child(2) div div:nth-child(2)'
            )
            for _ in range(10):
                scroll_container.evaluate("node => node.scrollBy(0, 2000)")
                page.wait_for_timeout(1000)
        except Exception as e:
            print("⚠️ Scroll container not found:", e)

        html = page.content()
        browser.close()

        soup = BeautifulSoup(html, "html.parser")
        result = {}

        # Extract metadata from Open Graph
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

        # Hashtags
        result["hashtags"] = re.findall(r"#\w+", caption_text) if caption_text else []

        # Image URL
        og_image = soup.find("meta", property="og:image")
        result["image_url"] = og_image["content"] if og_image else None

        # Timestamp
        time_tag = soup.find("time")
        result["timestamp"] = time_tag["datetime"] if time_tag and time_tag.has_attr("datetime") else None

        # Final JSON output
        final_result = {
            "likes": result.get("likes"),
            "comments": result.get("comments"),
            "username": result.get("username"),
            "caption": result.get("caption", result.get("caption_raw")),
            "hashtags": result.get("hashtags", []),
            "timestamp": result.get("timestamp"),
            "image_url": result.get("image_url")
        }

        # Ensure scrape_result directory exists
        os.makedirs("scrape_result", exist_ok=True)

        # Generate unique filename
        filename = f"{uuid.uuid4().hex}.json"
        filepath = os.path.join("scrape_result", filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(final_result, f, indent=2, ensure_ascii=False)

        print(f"✅ Extracted data saved to {filepath}")

# Example usage
scrape_post_with_playwright("https://www.instagram.com/p/DBFIuUIqINW/")
