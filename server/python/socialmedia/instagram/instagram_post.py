import os
import time
import sys
import pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
"""
This script is used to upload a video to Instagram using Selenium.
"""

# Default cookies path - automatically searched
DEFAULT_COOKIES_PATHS = [
    "cookies/instagram_cookies.pkl",
    "socialmedia/cookies/instagram_cookies.pkl",
    os.path.join(os.path.dirname(__file__), "cookies", "instagram_cookies.pkl"),
]

def _find_cookies_file():
    for path in DEFAULT_COOKIES_PATHS:
        # Try relative to current directory
        if os.path.exists(path):
            return os.path.abspath(path)
        # Try relative to script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(script_dir, path.lstrip("/"))
        if os.path.exists(full_path):
            return full_path
    return None


def upload_instagram_media(media_path, caption, headless=False):
    # Handle both single file and multiple files
    if isinstance(media_path, str):
        file_paths = [media_path]
    else:
        file_paths = media_path
    
    # Validate all files exist
    for path in file_paths:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"File not found: {path}")
    # Find cookies automatically
    cookies_path = _find_cookies_file()
    if not cookies_path:
        raise FileNotFoundError("Instagram cookies file not found.")
    
    if len(file_paths) > 1:
        print(f"Uploading {len(file_paths)} files as multiple media posts...")
    
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
        time.sleep(2)
        
        # Load cookies
        cookies = pickle.load(open(cookies_path, "rb"))
        for cookie in cookies:
            try:
                cookie.pop("sameSite", None)
                driver.add_cookie(cookie)
            except Exception:
                pass
        
        driver.refresh()
        time.sleep(3)

        # Dismiss any pop-ups that appear (like "The messaging tab has a new look")
        try:
            ok_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, 
                    "//button[contains(text(), 'OK')] | "
                    "//div[@role='button' and contains(text(), 'OK')] | "
                    "//button[contains(text(), 'Got it')] | "
                    "//div[@role='button' and contains(text(), 'Got it')]"
                ))
            )
            ok_button.click()
            print("Dismissed pop-up")
            time.sleep(1)
        except TimeoutException:
            pass  # No pop-up appeared, continue

        # Verify authentication
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//nav//a[contains(@href, '/explore')]"))
            )
            print("Authenticated successfully")
        except TimeoutException:
            raise Exception("Authentication failed. Cookies may be expired.")
        
        # Click on the Create/Upload Button (+ icon)
        # The button is an SVG with aria-label="New post" inside divs
        # Structure: div > div > div.html-div > div[aria-selected="false"] > svg[aria-label="New post"]
        print("Clicking New post button...")
        
        # Try multiple selectors to find the button
        create_button = None
        selectors = [
            "//svg[@aria-label='New post']",
            "//svg[@aria-label='New post']/ancestor::div[contains(@class, 'html-div')]",
            "//div[@aria-selected='false']//svg[@aria-label='New post']",
            "//div[contains(@class, 'html-div')]//svg[@aria-label='New post']",
            "//a[contains(@href, '/create/')]",
            "//*[@title='New post']",
            "//*[@aria-label='New post']"
        ]
        
        for selector in selectors:
            try:
                create_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                print(f"Found button with selector: {selector}")
                break
            except TimeoutException:
                continue
        
        if not create_button:
            try:
                driver.save_screenshot("/tmp/instagram_before_create.png")
                # Try to find any SVG elements
                svgs = driver.find_elements(By.TAG_NAME, "svg")
                print(f"Found {len(svgs)} SVG elements on page")
                for i, svg in enumerate(svgs[:5]):
                    try:
                        aria_label = svg.get_attribute("aria-label")
                        if aria_label:
                            print(f"  SVG {i}: aria-label='{aria_label}'")
                    except:
                        pass
            except Exception as e:
                print(f"Debug error: {e}")
            raise Exception("Could not find New post button. Check screenshot at /tmp/instagram_before_create.png")
        
        # Click the button
        try:
            create_button.click()
        except Exception as e:
            # Try JavaScript click as fallback
            driver.execute_script("arguments[0].click();", create_button)
        
        print("Clicked New post button - waiting for modal...")
        time.sleep(3)
        
        # Wait for the modal to appear
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, 
                    "//div[contains(text(), 'Create new post')] | "
                    "//button[contains(text(), 'Select from computer')] | "
                    "//div[contains(text(), 'Drag photos and videos here')]"
                ))
            )
            print("Create new post modal opened")
        except TimeoutException:
            # Debug: Save screenshot
            try:
                driver.save_screenshot("/tmp/instagram_modal_not_found.png")
            except:
                pass
        
        # Click on "Select from computer" option
        select_from_computer = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Select from computer')]"))
        )
        select_from_computer.click()
        
        # Upload File(s) - supports single file or multiple files for carousel
        if len(file_paths) == 1:
            print(f"Uploading file: {os.path.basename(file_paths[0])}")
        else:
            print(f"Uploading {len(file_paths)} files for carousel:")
            for i, path in enumerate(file_paths, 1):
                print(f"  {i}. {os.path.basename(path)}")
        
        file_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
        )

        if len(file_paths) > 1:
            driver.execute_script("arguments[0].setAttribute('multiple', 'multiple');", file_input)
            all_paths = "\n".join(file_paths)
            file_input.send_keys(all_paths)
        else:
            file_input.send_keys(file_paths[0])
        
        print("File path(s) sent to input")
        time.sleep(2)
        
        try:
            cancel_button = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Cancel')]"))
            )
            cancel_button.click()
            print("Clicked Cancel in file picker")
            time.sleep(1)
        except TimeoutException:
            pass
        
        if len(file_paths) > 1:
            print(f"Waiting for {len(file_paths)} files to process...")
        else:
            print("Waiting for file to process...")
        time.sleep(8)
        
        # Handle "Video posts are now shared as reels" modal (appears for video uploads)
        print("Checking for video/reels modal...")
        try:
            # Look for the "OK" button in the reels modal
            # The modal has text "Video posts are now shared as reels" and an OK button
            reels_modal_ok = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH,
                    "//div[contains(text(), 'Video posts are now shared as reels')]/ancestor::div//button[contains(text(), 'OK')] | "
                    "//div[contains(text(), 'Video posts are now shared as reels')]/following::button[contains(text(), 'OK')] | "
                    "//button[contains(text(), 'OK') and contains(@class, 'x1i10hfl')] | "
                    "//div[@role='button' and contains(text(), 'OK')]"
                ))
            )
            driver.execute_script("arguments[0].click();", reels_modal_ok)
            print("Dismissed 'Video posts are now shared as reels' modal")
            time.sleep(2)
        except TimeoutException:
            print("No reels modal found (may not be a video or modal already dismissed)")
        
        # Dismiss any other overlays/modals that might appear (like multiple media preview modal)
        try:
            # Look for common overlay/modal dismiss buttons
            overlay_selectors = [
                "//div[contains(@class, '_a9-v')]//button[contains(text(), 'OK')]",
                "//div[contains(@class, '_a9-v')]//div[@role='button' and contains(text(), 'OK')]",
                "//button[@aria-label='Close']",
                "//div[@role='button' and @aria-label='Close']",
                "//button[contains(@class, 'x1i10hfl') and contains(text(), 'Cancel')]",
            ]
            for selector in overlay_selectors:
                try:
                    overlay_close = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    driver.execute_script("arguments[0].click();", overlay_close)
                    print("Dismissed overlay/modal")
                    time.sleep(1)
                    break
                except TimeoutException:
                    continue
        except Exception as e:
            print(f"Note: No additional overlay to dismiss")
        
        # Wait for upload to complete and click Next
        # Next button is a div with role="button" and text "Next"
        print("Looking for Next button...")
        next_button = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, 
                "//div[@role='button' and contains(text(), 'Next')] | "
                "//button[contains(text(), 'Next')]"
            ))
        )
        
        # Scroll element into view and try to click
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
        time.sleep(1)
        
        # Try regular click first, fallback to JavaScript click
        try:
            next_button.click()
            print("Clicked Next button")
        except Exception as e:
            print(f"Regular click failed, trying JavaScript click: {e}")
            driver.execute_script("arguments[0].click();", next_button)
            print("Clicked Next button (via JavaScript)")
        time.sleep(2)
        
        # Wait for filters page and click Next again
        print("Clicking Next button again...")
        next_button = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, 
                "//div[@role='button' and contains(text(), 'Next')] | "
                "//button[contains(text(), 'Next')]"
            ))
        )
        
        # Scroll element into view and try to click
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
        time.sleep(1)
        
        # Try regular click first, fallback to JavaScript click
        try:
            next_button.click()
            print("Clicked Next button again")
        except Exception as e:
            print(f"Regular click failed, trying JavaScript click: {e}")
            driver.execute_script("arguments[0].click();", next_button)
            print("Clicked Next button again (via JavaScript)")
        time.sleep(2)
        
        # Add Caption
        # Caption field is a div with aria-label="Write a caption..." and contenteditable="true"
        print("Adding caption...")
        caption_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, 
                "//div[@aria-label='Write a caption...' and @contenteditable='true'] | "
                "//div[@contenteditable='true' and contains(@aria-label, 'Write a caption')] | "
                "//div[@role='textbox' and contains(@aria-label, 'Write a caption')]"
            ))
        )
        caption_input.click()
        time.sleep(1)
        caption_input.clear()
        caption_input.send_keys(caption)
        print("Caption added")
        time.sleep(1)
        
        # Click the 'Share' Button
        # Share button is a div with role="button" and text "Share"
        print("Looking for Share button...")
        share_button = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, 
                "//div[@role='button' and contains(text(), 'Share')] | "
                "//button[contains(text(), 'Share')]"
            ))
        )
        
        # Scroll element into view and try to click
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", share_button)
        time.sleep(1)
         
        # Try regular click first, fallback to JavaScript click
        try:
            share_button.click()
            print("Clicked Share button")
        except Exception as e:
            print(f"Regular click failed, trying JavaScript click: {e}")
            driver.execute_script("arguments[0].click();", share_button)
            print("Clicked Share button (via JavaScript)")
        
        # Wait for confirmation that the post was shared
        try:
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Your post has been shared')]"))
            )
            print("Successfully posted video to Instagram!")
        except TimeoutException:
            print("Post posted successfully!")
        
        # Wait for 5 seconds after uploading
        time.sleep(5)
    
    except Exception as e:
        raise Exception(f"An error occurred: {e}")
    
    finally:
        driver.quit()


def main():
    # Interactive prompts for user input
    print("Instagram Upload Script")
    print("=" * 40)
    
    # Ask for file path(s) - support multiple files for carousel
    file_paths = []
    print("\nEnter file paths (press enter when done):")
    print("(Multiple files will be uploaded as a multiple media post)")
    
    while True:
        file_path = input(f"File {len(file_paths) + 1} path: ").strip()
        if not file_path:
            if len(file_paths) == 0:
                print("Error: At least one file is required. Please try again.")
                continue
            break
        # Handle quoted paths
        file_path = file_path.strip('"\'')
        
        # Convert to absolute path
        if not os.path.isabs(file_path):
            abs_path = os.path.abspath(file_path)
        else:
            abs_path = file_path
        
        if not os.path.isfile(abs_path):
            print(f"Error: File '{abs_path}' does not exist. Check the path and try again.")
            continue
        
        file_paths.append(abs_path)
        print(f"Added: {os.path.basename(abs_path)}")
    
    # Use single path or list based on number of files
    if len(file_paths) == 1:
        media_path = file_paths[0]
    else:
        media_path = file_paths
    
    # Ask for caption
    if len(file_paths) > 1:
        print(f"\nEnter the caption for your multiple media post ({len(file_paths)} files):")
    else:
        print("\nEnter the caption for your post:")
    caption = input("Caption: ").strip()
    if not caption:
        print("Warning: No caption provided. Post will be posted without a caption.")
        caption = ""
    
    # Ask for headless mode (optional)
    headless_input = input("\nRun in headless mode? (y/n, default: n): ").strip().lower()
    headless = headless_input in ['y', 'yes']
    
    print("\nStarting upload...")
    print("=" * 40)
    
    try:
        upload_instagram_media(media_path, caption, headless)
        print("\n" + "=" * 40)
        if len(file_paths) > 1:
            print(f"Multiple media post with {len(file_paths)} files posted successfully!")
        else:
            print("Upload completed successfully!")
    except Exception as e:
        print("\n" + "=" * 40)
        print(f"Upload failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()