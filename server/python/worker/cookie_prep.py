from .celery_app import app
import os
import json
import time
import logging
import psycopg
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# DATABASE_URL like: postgresql://root:secret@db:5432/project_monopoly?sslmode=disable
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://root:secret@db:5432/project_monopoly?sslmode=disable")

log = logging.getLogger(__name__)

# ---------- Cookie Preparation Task ----------
@app.task(name="worker.tasks.prepare_cookies", queue="celery")
def prepare_cookies(group_item_id: int, platform: str, email: str, password: str):
    """
    Login to platform and extract sessionid cookie, storing it in group_items.data
    """
    log.info("Starting cookie preparation for group_item_id=%s platform=%s", group_item_id, platform)
    
    try:
        # Set up Chrome options
        chrome_options = Options()
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
        
        sessionid = None
        
        try:
            if platform.lower() == "instagram":
                # Navigate to login page
                driver.get("https://www.instagram.com/accounts/login/")
                time.sleep(5)
                
                # Accept cookies dialog if present
                cookie_xpaths = [
                    "//button[contains(text(), 'Accept')]",
                    "//button[contains(text(), 'Allow')]",
                    "//button[contains(text(), 'Only allow essential')]",
                    "//button[contains(text(), 'Accept All')]",
                ]
                for xp in cookie_xpaths:
                    try:
                        btn = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, xp))
                        )
                        btn.click()
                        time.sleep(0.5)
                        break
                    except TimeoutException:
                        continue
                
                # Fill credentials
                username_input = WebDriverWait(driver, 20).until(
                    EC.visibility_of_element_located((By.NAME, "username"))
                )
                password_input = driver.find_element(By.NAME, "password")
                
                username_input.clear()
                username_input.send_keys(email)
                password_input.clear()
                password_input.send_keys(password)
                time.sleep(1)
                password_input.send_keys(Keys.RETURN)
                
                # Wait for login to complete
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, "//nav//a[contains(@href, '/explore')]"))
                )
                log.info("Login successful for Instagram")
                
                # Extract sessionid from cookies
                cookies = driver.get_cookies()
                for cookie in cookies:
                    if cookie.get("name") == "sessionid":
                        sessionid = cookie.get("value")
                        break
                
            elif platform.lower() == "tiktok":
                # TikTok login logic would go here
                driver.get("https://www.tiktok.com/login")
                time.sleep(5)
                # TODO: Implement TikTok login
                # Extract sessionid from cookies
                cookies = driver.get_cookies()
                for cookie in cookies:
                    if cookie.get("name") == "sessionid":
                        sessionid = cookie.get("value")
                        break
            else:
                raise ValueError(f"Unsupported platform: {platform}")
            
            if not sessionid:
                raise Exception("sessionid cookie not found after login")
            
            # Update group_items.data with sessionid and set cookie_created_at
            with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
                with conn.cursor() as cur:
                    # Get current data
                    cur.execute(
                        "SELECT data FROM group_items WHERE id = %s",
                        (group_item_id,)
                    )
                    row = cur.fetchone()
                    if not row:
                        raise Exception(f"group_item {group_item_id} not found")
                    
                    current_data = row[0] if row[0] else {}
                    
                    # Update data with sessionid (preserve email/password)
                    current_data["sessionid"] = sessionid
                    
                    # Update database
                    cur.execute(
                        """
                        UPDATE group_items 
                        SET data = %s::jsonb, 
                            cookie_created_at = NOW(),
                            updated_at = NOW()
                        WHERE id = %s
                        """,
                        (json.dumps(current_data), group_item_id)
                    )
            
            log.info("Cookie preparation completed successfully for group_item_id=%s", group_item_id)
            return {"status": "success", "group_item_id": group_item_id, "platform": platform}
            
        finally:
            driver.quit()
            
    except Exception as e:
        log.exception("Cookie preparation failed for group_item_id=%s: %s", group_item_id, e)
        return {"status": "failed", "group_item_id": group_item_id, "error": str(e)}

