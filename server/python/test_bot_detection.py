#!/usr/bin/env python3
"""
Bot Detection Test Script with Captcha Solving
==============================================
Uses SeleniumBase's sb_cdp with solve_captcha() to bypass bot detection.
"""

import time
from playwright.sync_api import sync_playwright
from seleniumbase import sb_cdp


def test_captcha_solving(url: str = "https://www.bing.com/turing/captcha/challenge"):
    """
    Test captcha solving using SeleniumBase's built-in solver.
    
    Args:
        url: The URL to test
    """
    print("=" * 60)
    print("🤖 CAPTCHA SOLVING TEST")
    print("=" * 60)
    print(f"\nTarget URL: {url}")
    
    sb = None
    playwright_instance = None
    
    try:
        # Create SeleniumBase CDP Chrome instance
        print("\n📦 Initializing SeleniumBase CDP Chrome...")
        sb = sb_cdp.Chrome(locale="en")
        endpoint_url = sb.get_endpoint_url()
        print(f"✅ Chrome started at: {endpoint_url}")
        
        # Connect Playwright to the same browser
        print("🔌 Connecting Playwright...")
        playwright_instance = sync_playwright().start()
        browser = playwright_instance.chromium.connect_over_cdp(endpoint_url)
        context = browser.contexts[0]
        page = context.pages[0]
        print("✅ Playwright connected")
        
        # Navigate to the captcha page
        print(f"\n📍 Navigating to: {url}")
        page.goto(url)
        sb.sleep(3)
        
        # Check page before solving
        print(f"\n📄 Page Info (Before):")
        print(f"   URL: {page.url}")
        print(f"   Title: {page.title()}")
        
        # Attempt to solve captcha
        print("\n🔓 Attempting to solve captcha...")
        try:
            sb.solve_captcha()
            print("✅ solve_captcha() completed")
        except Exception as e:
            print(f"⚠️  solve_captcha() error: {e}")
        
        sb.sleep(3)
        
        # Check page after solving
        print(f"\n📄 Page Info (After):")
        print(f"   URL: {page.url}")
        print(f"   Title: {page.title()}")
        
        # Take screenshot
        screenshot_path = "/app/captcha_result.png"
        try:
            page.screenshot(path=screenshot_path)
            print(f"\n📸 Screenshot saved: {screenshot_path}")
        except Exception as e:
            print(f"⚠️  Screenshot failed: {e}")
        
        # Summary
        print("\n" + "=" * 60)
        if "captcha" in page.url.lower() or "challenge" in page.url.lower():
            print("⚠️  RESULT: Still on captcha page")
        else:
            print("✅ RESULT: Captcha bypassed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        try:
            if playwright_instance:
                playwright_instance.stop()
        except:
            pass
        try:
            if sb:
                # sb_cdp.Chrome doesn't have quit(), use different cleanup
                pass
        except:
            pass
        print("\n🧹 Cleaned up")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test captcha solving")
    parser.add_argument("--url", "-u", type=str, 
                       default="https://www.bing.com/turing/captcha/challenge",
                       help="URL to test")
    
    args = parser.parse_args()
    test_captcha_solving(args.url)
