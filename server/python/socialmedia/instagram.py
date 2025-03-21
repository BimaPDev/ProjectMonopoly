import os
import time
import sys
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException


def upload_instagram_video(session_id, video_path, caption, headless=False):
    """
    Automates the process of uploading and publishing a video on Instagram using Selenium.

    :param session_id: Instagram session ID to authenticate the user.
    :param video_path: Absolute path to the video file.
    :param caption: Caption text for the video.
    :param headless: Boolean flag to run Chrome in headless mode.
    """
    # Set up Chrome options
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
        # Navigate to Instagram homepage
        driver.get("https://www.instagram.com/")
        time.sleep(3)
        
        # Add session cookie
        driver.add_cookie({
            "name": "sessionid",
            "value": session_id,
            "domain": ".instagram.com",
            "path": "/",
            "secure": True,
            "httpOnly": True
        })
        driver.refresh()
        time.sleep(5)  # Allow time for the session to load

        # Verify if the user is logged in
        if "login" in driver.current_url.lower() or "accounts/login" in driver.current_url.lower():
            raise Exception("Session cookie failed to log in. Check your session_id.")
        
        # Click on the Create/Upload Button (+ icon)
        create_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@role, 'button') and contains(@aria-label, 'Create')]"))
        )
        create_button.click()
        time.sleep(3)
        
        # Click on "Select from computer" option
        select_from_computer = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Select from computer')]"))
        )
        select_from_computer.click()
        
        # Upload Video File
        file_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
        )
        file_input.send_keys(video_path)
        
        # Wait for upload to complete and click Next
        next_button = WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Next')]"))
        )
        next_button.click()
        
        # Wait for filters page and click Next again
        next_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Next')]"))
        )
        next_button.click()
        
        # Add Caption
        caption_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@aria-label, 'Write a caption...')]"))
        )
        caption_input.click()
        caption_input.send_keys(caption)
        
        # Click the 'Share' Button
        share_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Share')]"))
        )
        share_button.click()
        
        # Wait for confirmation that the post was shared
        try:
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Your post has been shared')]"))
            )
            print("Successfully posted video to Instagram!")
        except TimeoutException:
            print("Post may have been uploaded, but confirmation message was not detected.")
        
        # Wait for 5 seconds after uploading
        time.sleep(5)
    
    except Exception as e:
        raise Exception(f"An error occurred: {e}")
    
    finally:
        driver.quit()


def main():
    parser = argparse.ArgumentParser(description="Upload and publish a video on Instagram using Selenium.")
    parser.add_argument('--sessionid', required=True, help='Instagram sessionid cookie value')
    parser.add_argument('--video', required=True, help='Absolute path to the video file to upload')
    parser.add_argument('--caption', required=True, help='Caption for the video')
    parser.add_argument('--headless', action='store_true', help='Run Chrome in headless mode')
    
    args = parser.parse_args()
    
    if not os.path.isfile(args.video):
        print(f"Error: Video file not found at {args.video}")
        sys.exit(1)
    
    video_path = os.path.abspath(args.video)
    
    try:
        upload_instagram_video(args.sessionid, video_path, args.caption, args.headless)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()