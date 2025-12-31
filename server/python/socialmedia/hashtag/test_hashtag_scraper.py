#!/usr/bin/env python3
"""
Test script for Instagram hashtag scraping functionality.
Run this to test the hashtag scraper without Celery.
"""
import os
import sys

if not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "postgresql://root:secret@localhost:5432/project_monopoly?sslmode=disable"

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from socialmedia.instagram.scraper.profile_scraper import InstagramScraper

def test_hashtag_scraper(hashtag="gaming", max_posts=5, max_retries=3):
    # Get credentials from environment or use defaults
    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")
    print(f"Testing Instagram Hashtag Scraper for hashtag: #{hashtag} with max {max_posts} posts")

    scraper = None
    # Retry logic for browser window closing issues
    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1:
                print(f"\nRetry attempt {attempt}/{max_retries}...")
                import time
                time.sleep(3)  # Wait a bit before retrying
                # Clean up previous scraper if it exists
                if scraper:
                    try:
                        scraper.close()
                    except:
                        pass
            
            # Initialize scraper - use non-headless mode for local testing
            # This helps avoid window closing issues on macOS
            scraper = InstagramScraper(username, password, headless=False)
            
            # Login
            print("Logging in to Instagram...")
            if not scraper.login():
                print("Failed to login to Instagram")
                if scraper:
                    scraper.close()
                if attempt < max_retries:
                    continue  # Retry
                return False
            print("Login successful")
            break  # Success, exit retry loop
            
        except Exception as e:
            error_msg = str(e)
            if "no such window" in error_msg.lower() or "target window already closed" in error_msg.lower():
                print(f"Browser window closed unexpectedly (attempt {attempt}/{max_retries})")
                if scraper:
                    try:
                        scraper.close()
                    except:
                        pass
                if attempt < max_retries:
                    print("   Retrying...")
                    continue
                else:
                    return False
            else:
                # Different error, don't retry
                print(f"Error: {e}")
                if scraper:
                    try:
                        scraper.close()
                    except:
                        pass
                return False
    
    if not scraper:
        print("Failed to initialize scraper after multiple attempts")
        return False
    
    # Test hashtag scraping
    print(f"Scraping hashtag: #{hashtag} (max {max_posts} posts)...")
    
    try:
        # Disable auto-upload for testing
        original_upload_setting = os.getenv("UPLOAD_AFTER_SCRAPE", "1")
        os.environ["UPLOAD_AFTER_SCRAPE"] = "0"
        
        posts_data = scraper.scrape_hashtag(hashtag, max_posts=max_posts)
        
        # Restore original setting
        os.environ["UPLOAD_AFTER_SCRAPE"] = original_upload_setting
        
        print(f"\nSuccessfully scraped {len(posts_data)} posts")    
        return True
        
    except Exception as e:
        print(f"\nError during scraping: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        scraper.close()

def test_upload_script():
    # Find the most recent hashtag JSON file
    import glob
    scrape_result_dir = os.path.join(
        os.path.dirname(__file__),
        "scrape_result"
    )
    
    json_files = glob.glob(os.path.join(scrape_result_dir, "*_hashtag_posts_*.json"))
    
    if not json_files:
        print("No hashtag JSON files found. Run scraper first.")
        return False
    
    # Get the most recent file
    latest_file = max(json_files, key=os.path.getctime)
    print(f"\nUsing file: {latest_file}")
    
    # Import and run upload
    from socialmedia.hashtag.upload_hashtag_posts_to_db import upload_hashtag_posts_to_db
    
    try:
        success = upload_hashtag_posts_to_db(latest_file)
        if success:
            print("Upload successful!")
        else:
            print("Upload failed")
        return success
    except Exception as e:
        print(f"Error during upload: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Instagram hashtag scraper")
    parser.add_argument(
        "--hashtag",
        type=str,
        default=None,
        help="Hashtag to scrape (will prompt if not provided)"
    )
    parser.add_argument(
        "--max-posts",
        type=int,
        default=None,
        help="Maximum number of posts to scrape (will prompt if not provided)"
    )
    parser.add_argument(
        "--test-upload",
        action="store_true",
        help="Also test the upload script (default: enabled)"
    )
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Skip upload testing"
    )
    parser.add_argument(
        "--no-scrape",
        action="store_true",
        help="Skip scraping, only test upload"
    )
    
    args = parser.parse_args()
    
    # Interactive prompts if not provided via command line
    if not args.no_scrape:
        if not args.hashtag:
            print("Instagram Hashtag Scraper")
            args.hashtag = input("\nEnter hashtag to scrape (without #): ").strip().lstrip('#')
            if not args.hashtag:
                print("Hashtag cannot be empty!")
                sys.exit(1)
        
        if args.max_posts is None:
            max_posts_input = input(f"Enter number of posts to scrape (default: 5): ").strip()
            if max_posts_input:
                try:
                    args.max_posts = int(max_posts_input)
                except ValueError:
                    print("Invalid number, using default: 5")
                    args.max_posts = 5
            else:
                args.max_posts = 5
        
        print(f"\nConfiguration:")
        print(f"   Hashtag: #{args.hashtag}")
        print(f"   Max posts: {args.max_posts}")
        print(f"   Upload to DB: {'Yes' if not args.no_upload else 'No'}\n")
    
    # Default behavior: scrape and upload
    if not args.no_scrape:
        # Test scraper with provided/default arguments
        success = test_hashtag_scraper(hashtag=args.hashtag, max_posts=args.max_posts)
        if not success:
            sys.exit(1)
    
    # Test upload by default (unless --no-upload is specified)
    if not args.no_upload:
        # Test upload
        success = test_upload_script()
        if not success:
            sys.exit(1)
    
    print("All tests completed!")

