from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import re

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
        browser = p.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context(storage_state="auth.json")
        page = context.new_page()

        print(f"🔗 Opening: {post_url}")
        page.goto(post_url, timeout=60000)
        page.wait_for_timeout(3000)

        html = page.content()
        browser.close()

        soup = BeautifulSoup(html, "html.parser")
        result = {}

        # Extract Open Graph description
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
                print("⚠️ OG description format did not match expected pattern.")
                caption_text = desc
                result["caption_raw"] = desc
                result["likes"] = None
                result["comments"] = None
                result["username"] = None
        else:
            print("⚠️ No og:description tag found.")
            caption_text = ""
            result["caption_raw"] = None
            result["likes"] = None
            result["comments"] = None
            result["username"] = None

        # Extract hashtags
        if caption_text:
            hashtags = re.findall(r"#\w+", caption_text)
            result["hashtags"] = hashtags

        # Extract image URL
        og_image = soup.find("meta", property="og:image")
        result["image_url"] = og_image["content"] if og_image else None

        # Extract timestamp
        time_tag = soup.find("time")
        if time_tag and time_tag.has_attr("datetime"):
            result["timestamp"] = time_tag["datetime"]
        else:
            result["timestamp"] = None

        # Save HTML (for debugging, optional)
        with open("result.html", "w", encoding="utf-8") as f:
            f.write(html)

        # Save final result
        with open("result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print("✅ Extracted data saved to result.json")

# Run it
scrape_post_with_playwright("https://www.instagram.com/p/DJMUS7gqssB/")
