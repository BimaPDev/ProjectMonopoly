#!/usr/bin/env python3
"""
Test script for cookie preparation functionality.
This script can be used in two ways:
1. Manual test: Creates a test group_item and manually triggers the task
2. Auto test: Creates a test group_item and waits for dispatcher to pick it up
"""

import os
import sys
import psycopg
import json
import time

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://root:secret@localhost:5432/project_monopoly?sslmode=disable")

def create_test_group_item(email: str, password: str, platform: str = "instagram"):
    """Create a test group_item with email/password but no cookie_created_at"""
    print(f"Creating test group_item for platform: {platform}")
    
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            # First, get or create a test user
            cur.execute("SELECT id FROM users LIMIT 1")
            user_row = cur.fetchone()
            if not user_row:
                print("No users found. Creating test user...")
                cur.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                    ("test_user", "test@example.com", "test_hash")
                )
                user_id = cur.fetchone()[0]
            else:
                user_id = user_row[0]
            
            # Get or create a test group
            cur.execute("SELECT id FROM groups WHERE user_id = %s LIMIT 1", (user_id,))
            group_row = cur.fetchone()
            if not group_row:
                print("Creating test group...")
                cur.execute(
                    "INSERT INTO groups (user_id, name, description) VALUES (%s, %s, %s) RETURNING id",
                    (user_id, "Test Group", "Test group for cookie prep")
                )
                group_id = cur.fetchone()[0]
            else:
                group_id = group_row[0]
            
            # Check if group_item already exists for this platform
            cur.execute(
                "SELECT id FROM group_items WHERE group_id = %s AND platform = %s",
                (group_id, platform)
            )
            existing = cur.fetchone()
            
            if existing:
                # Update existing group_item to reset cookie_created_at
                group_item_id = existing[0]
                # Check if cookie_created_at column exists
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='group_items' AND column_name='cookie_created_at'
                """)
                has_column = cur.fetchone() is not None
                
                if has_column:
                    cur.execute(
                        """
                        UPDATE group_items 
                        SET data = %s::jsonb, 
                            cookie_created_at = NULL,
                            updated_at = NOW()
                        WHERE id = %s
                        """,
                        (json.dumps({"email": email, "password": password}), group_item_id)
                    )
                else:
                    cur.execute(
                        """
                        UPDATE group_items 
                        SET data = %s::jsonb, 
                            updated_at = NOW()
                        WHERE id = %s
                        """,
                        (json.dumps({"email": email, "password": password}), group_item_id)
                    )
                print(f"Updated existing group_item (id={group_item_id}) - reset cookie_created_at")
            else:
                # Check if cookie_created_at column exists
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='group_items' AND column_name='cookie_created_at'
                """)
                has_column = cur.fetchone() is not None
                
                # Create new group_item
                if has_column:
                    cur.execute(
                        """
                        INSERT INTO group_items (group_id, platform, data, cookie_created_at)
                        VALUES (%s, %s, %s::jsonb, NULL)
                        RETURNING id
                        """,
                        (group_id, platform, json.dumps({"email": email, "password": password}))
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO group_items (group_id, platform, data)
                        VALUES (%s, %s, %s::jsonb)
                        RETURNING id
                        """,
                        (group_id, platform, json.dumps({"email": email, "password": password}))
                    )
                group_item_id = cur.fetchone()[0]
                print(f"Created new group_item (id={group_item_id})")
            
            return group_item_id, group_id, platform

def check_cookie_status(group_item_id: int):
    """Check if cookie was prepared successfully"""
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            # Check if cookie_created_at column exists
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='group_items' AND column_name='cookie_created_at'
            """)
            has_column = cur.fetchone() is not None
            
            if has_column:
                cur.execute(
                    "SELECT data, cookie_created_at FROM group_items WHERE id = %s",
                    (group_item_id,)
                )
            else:
                cur.execute(
                    "SELECT data FROM group_items WHERE id = %s",
                    (group_item_id,)
                )
            
            row = cur.fetchone()
            if row:
                if has_column:
                    data, cookie_created_at = row
                else:
                    data = row[0]
                    cookie_created_at = None
                
                has_sessionid = data and "sessionid" in data if data else False
                return {
                    "has_sessionid": has_sessionid,
                    "cookie_created_at": cookie_created_at,
                    "data": data
                }
            return None

def manual_test(email: str, password: str, platform: str = "instagram"):
    """Manually trigger the cookie preparation task"""
    print("\n=== Manual Test Mode ===")
    print("This will directly call the prepare_cookies function")
    
    group_item_id, group_id, platform = create_test_group_item(email, password, platform)
    
    print(f"\nCalling prepare_cookies task directly...")
    # Import the function directly without celery initialization
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Import the actual function code without celery decorator
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
    
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://root:secret@localhost:5432/project_monopoly?sslmode=disable")
    log = logging.getLogger(__name__)
    
    # Copy the function logic directly (without celery decorator)
    def prepare_cookies_direct(group_item_id: int, platform: str, email: str, password: str):
        """Login to platform and extract sessionid cookie, storing it in group_items.data"""
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
                        
                        # Check if cookie_created_at column exists before updating
                        cur.execute("""
                            SELECT column_name 
                            FROM information_schema.columns 
                            WHERE table_name='group_items' AND column_name='cookie_created_at'
                        """)
                        has_column = cur.fetchone() is not None
                        
                        if has_column:
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
                        else:
                            cur.execute(
                                """
                                UPDATE group_items 
                                SET data = %s::jsonb, 
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
    
    result = prepare_cookies_direct(group_item_id, platform, email, password)
    
    print(f"\nTask result: {result}")
    
    # Check status
    status = check_cookie_status(group_item_id)
    if status:
        if status["has_sessionid"]:
            print(f"\nSUCCESS! Cookie prepared:")
            print(f"   - cookie_created_at: {status['cookie_created_at']}")
            print(f"   - sessionid present: Yes")
            print(f"   - sessionid value: {status['data'].get('sessionid', 'N/A')[:50]}...")
        else:
            print(f"\nFAILED: No sessionid found in data")
            print(f"   - cookie_created_at: {status['cookie_created_at']}")
    else:
        print(f"\nERROR: Could not find group_item {group_item_id}")

def auto_test(email: str, password: str, platform: str = "instagram", wait_time: int = 60):
    """Create test group_item and wait for dispatcher to pick it up"""
    print("\n=== Auto Test Mode ===")
    print("This will create a test group_item and wait for the dispatcher to process it")
    print("Make sure the dispatcher is running!")
    
    group_item_id, group_id, platform = create_test_group_item(email, password, platform)
    
    print(f"\nCreated group_item (id={group_item_id})")
    print(f"Waiting up to {wait_time} seconds for dispatcher to process...")
    print("(The dispatcher checks every ~1 second)")
    
    start_time = time.time()
    while time.time() - start_time < wait_time:
        status = check_cookie_status(group_item_id)
        if status and status["cookie_created_at"]:
            print(f"\nSUCCESS! Cookie was prepared by dispatcher:")
            print(f"   - cookie_created_at: {status['cookie_created_at']}")
            print(f"   - sessionid present: {status['has_sessionid']}")
            if status["has_sessionid"]:
                print(f"   - sessionid value: {status['data'].get('sessionid', 'N/A')[:50]}...")
            return
        
        time.sleep(2)
        elapsed = int(time.time() - start_time)
        if elapsed % 10 == 0:
            print(f"   Still waiting... ({elapsed}s elapsed)")
    
    print(f"\nTimeout after {wait_time} seconds")
    status = check_cookie_status(group_item_id)
    if status:
        print(f"   - cookie_created_at: {status['cookie_created_at']}")
        print(f"   - sessionid present: {status['has_sessionid']}")
    else:
        print(f"   - Could not find group_item")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test cookie preparation functionality")
    parser.add_argument("--email", required=True, help="Email/username for login")
    parser.add_argument("--password", required=True, help="Password for login")
    parser.add_argument("--platform", default="instagram", choices=["instagram", "tiktok"], 
                       help="Platform to test (default: instagram)")
    parser.add_argument("--mode", default="manual", choices=["manual", "auto"],
                       help="Test mode: 'manual' calls task directly, 'auto' waits for dispatcher")
    parser.add_argument("--wait", type=int, default=60,
                       help="Wait time in seconds for auto mode (default: 60)")
    
    args = parser.parse_args()
    
    if args.mode == "manual":
        manual_test(args.email, args.password, args.platform)
    else:
        auto_test(args.email, args.password, args.platform, args.wait)

