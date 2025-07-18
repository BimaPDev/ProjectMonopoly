import os
import time
import sys
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementClickInterceptedException


SESSION_ID = ""

def upload_instagram_video(session_id, video_path, caption, headless=False):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            });
        """
    })
    
    try:
        # 1) Load Instagram and input session cookie
        driver.get("https://www.instagram.com/")
        time.sleep(3)
        driver.add_cookie({
            "name": "sessionid",
            "value": session_id,
            "domain": ".instagram.com",
            "path": "/",
            "secure": True,
            "httpOnly": True
        })
        driver.refresh()
        try:
            next_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Next']"))
            )
            next_btn.click()
            time.sleep(2)
        except TimeoutException:
            pass 
        time.sleep(5)

        # Verifies login status
        if "login" in driver.current_url.lower():
            raise Exception("Session cookie failed to log in")


        # Open Create Post dialog
        svg_elem = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'svg[aria-label="New post"]'))
        )
        driver.execute_script("arguments[0].parentElement.click();", svg_elem)
        #time.sleep(1)

        #Press “Select from computer”
        sel_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH,
                "//button[normalize-space() = 'Select from computer']"
            ))
        )
        sel_btn.click()

        #Send file into the hidden <input type="file">
        file_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH,
                "//input[@type='file' and @accept]"
            ))
        )
        file_input.send_keys(video_path)

        # **NEW**: if the “Video posts are now shared as reels” modal appears here, click OK
        try:
            ok_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH,
                    "//button[normalize-space()='OK']"
                ))
            )
            ok_btn.click()
            time.sleep(1)
        except TimeoutException:
            pass

        # 6) Click “Next” twice
        for _ in range(2):
            nxt = WebDriverWait(driver, 60).until(
                EC.element_to_be_clickable((By.XPATH,
                    "//*[(@role='button' or self::button) and normalize-space()='Next']"
                ))
            )
            nxt.click()
            time.sleep(1)

        # 7) Enter caption
        caption_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH,
                "//div[@role='textbox' and @contenteditable='true' and @aria-placeholder='Write a caption...']"
            ))
        )
        caption_input.click()
        caption_input.send_keys(caption)

        # 8) Share
        share_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH,
                "//*[(@role='button' or self::button) and normalize-space()='Share']"
            ))
        )
        try:
            WebDriverWait(driver, 5).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".x1qjc9v5.x9f619.x78zum5.xdt5ytf.x1iyjqo2.xl56j7k"))
            )
        except TimeoutException:
            pass  # Overlay didn't disappear, try clicking anyway

        for _ in range(3):
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", share_btn)
                time.sleep(0.5)  # Give the UI a moment to update
                share_btn.click()
                break
            except ElementClickInterceptedException:
                time.sleep(1)
        else:
            raise Exception("Share button could not be clicked after several attempts.")

        # 9) Confirm
        try:
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.XPATH,
                    "//h3[normalize-space()='Your reel has been shared.']"
                ))
            )
            time.sleep(4)
            print("✅ Successfully posted video!")
        except TimeoutException:
            raise Exception("Failed to confirm video post. The post may not have been successful.")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    finally:
        driver.quit()


def main():
    parser = argparse.ArgumentParser(
        description="Upload a video to Instagram using Selenium."
    )
    parser.add_argument(
        '--sessionid', default=SESSION_ID,
        help='Instagram sessionid cookie (or supply via this flag)'
    )
    parser.add_argument(
        '--video', required=True,
        help='Absolute path to the video file'
    )
    parser.add_argument(
        '--caption', required=True,
        help='Caption for the post'
    )
    parser.add_argument(
        '--headless', action='store_true',
        help='Run Chrome headlessly'
    )
    args = parser.parse_args()

    if not args.sessionid:
        print("Error:SESSION_ID is empty.")
        sys.exit(1)
    if not os.path.isfile(args.video):
        print(f"Error: video file not found: {args.video}")
        sys.exit(1)

    upload_instagram_video(
        args.sessionid,
        os.path.abspath(args.video),
        args.caption,
        headless=args.headless
    )

if __name__ == "__main__":
    main()
