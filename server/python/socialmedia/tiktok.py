import os
import time
import sys
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ── Hard-coded TikTok sessionid ───────────────────────────
SESSION_ID = "948c6a12dae7b47545f767d121075d41"


def upload_tiktok_video(session_id, video_path, caption, headless=False):
    """
    Automates the process of uploading and publishing a video on TikTok using Selenium.

    :param session_id: TikTok session ID to authenticate the user.
    :param video_path: Absolute path to the video file.
    :param caption: Caption text for the video.
    :param headless: Boolean flag to run Chrome in headless mode.
    """
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        """
    })
    
    try:
        driver.get("https://www.tiktok.com/")
        time.sleep(3)
        
        driver.add_cookie({
            "name": "sessionid",
            "value": session_id,
            "domain": ".tiktok.com",
            "path": "/",
            "secure": True,
            "httpOnly": True
        })
        driver.refresh()
        time.sleep(5)

        if "login" in driver.current_url.lower():
            raise Exception("Session cookie failed to log in. Check your SESSION_ID.")
        
        driver.get("https://www.tiktok.com/upload?lang=en")
        time.sleep(5)
        
        file_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
        )
        file_input.send_keys(video_path)
        
        WebDriverWait(driver, 60).until(
            EC.text_to_be_present_in_element(
                (By.XPATH, "//*[contains(text(),'Uploaded')]"), 
                "Uploaded"
            )
        )
        
        caption_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true']"))
        )
        caption_input.click()
        caption_input.send_keys(caption)
        
        post_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@data-e2e='post_video_button']"))
        )
        post_button.click()
        time.sleep(5)
    
    except Exception as e:
        raise Exception(f"An error occurred: {e}")
    
    finally:
        driver.quit()


def main():
    parser = argparse.ArgumentParser(
        description="Upload and publish a video on TikTok using Selenium."
    )
    parser.add_argument(
        '--video', required=True,
        help='Absolute path to the video file to upload'
    )
    parser.add_argument(
        '--caption', required=True,
        help='Caption for the video'
    )
    parser.add_argument(
        '--headless', action='store_true',
        help='Run Chrome in headless mode'
    )
    
    args = parser.parse_args()
    
    if not os.path.isfile(args.video):
        print(f"Error: Video file '{args.video}' does not exist.")
        sys.exit(1)
    
    video_path = os.path.abspath(args.video)
    
    # Use the hard-coded sessionid here
    upload_tiktok_video(SESSION_ID, video_path, args.caption, args.headless)


if __name__ == "__main__":
    main()
