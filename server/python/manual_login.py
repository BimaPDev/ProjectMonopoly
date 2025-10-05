#!/usr/bin/env python3
"""
Manual Instagram login script that allows you to login manually and save cookies.
"""

import os
import sys
import time

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def manual_login():
    print("🔐 Manual Instagram Login")
    print("=" * 40)
    print("This will open Instagram in a browser where you can login manually.")
    print("After successful login, cookies will be saved for future use.")
    print()
    
    try:
        from socialmedia.instaPage import InstagramScraper
        
        # Create scraper instance
        scraper = InstagramScraper(
            username="dogw.ood6",
            password="qwert1233@"
        )
        
        print("Opening Instagram...")
        scraper.driver.get("https://www.instagram.com/accounts/login/?hl=en")
        
        print("⏳ Please login manually in the browser window that opened.")
        print("   - Enter your username: dogw.ood6")
        print("   - Enter your password: qwert1233@")
        print("   - Complete any 2FA or verification if required")
        print("   - Wait for the main Instagram page to load")
        print()
        
        # Wait for manual login
        input("Press Enter after you have successfully logged in...")
        
        # Check if login was successful
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            # Wait for a post-login element
            WebDriverWait(scraper.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//nav//a[contains(@href, '/explore')]"))
            )
            
            print("✅ Login appears successful!")
            
            # Save cookies
            scraper.save_cookies()
            print("🍪 Cookies saved successfully!")
            
            # Test scraping
            print("🕷️ Testing profile scraping...")
            try:
                posts = scraper.scrape_profile("https://www.instagram.com/nike/", max_posts=2)
                print(f"✅ Successfully scraped {len(posts)} posts from Nike")
                
                if posts:
                    print("Sample post data:")
                    for i, post in enumerate(posts[:2]):
                        print(f"  Post {i+1}: {post.get('url', 'No URL')}")
                        print(f"    Caption: {post.get('caption', 'No caption')[:100]}...")
                        print(f"    Likes: {post.get('likes', 'No likes')}")
                        print()
                
            except Exception as e:
                print(f"❌ Profile scraping failed: {e}")
            
        except Exception as e:
            print(f"❌ Login verification failed: {e}")
            print("Make sure you're logged in and on the main Instagram page.")
        
        # Keep browser open for inspection
        print("⏳ Keeping browser open for 30 seconds for inspection...")
        time.sleep(30)
        
        # Clean up
        scraper.close()
        print("🧹 Browser closed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    manual_login()
