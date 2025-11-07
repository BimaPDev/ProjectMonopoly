#!/usr/bin/env python3
"""
Test the full weekly scraper with caption-based deduplication.
"""

import os
import sys
import json
import tempfile

# Set credentials
os.environ["INSTAGRAM_USERNAME"] = "dogw.ood6"
os.environ["INSTAGRAM_PASSWORD"] = "qwert1233@"
os.environ["DATABASE_URL"] = "postgresql://root:secret@localhost:5432/project_monopoly?sslmode=disable"
os.environ["WEEKLY_MAX_POSTS"] = "5"  # Limit to 5 posts for testing

# Add the parent directory (server/python) to the path so we can import socialmedia
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_dedup_with_real_scraping():
    print("Testing Full Deduplication with Real Scraping")
    print("=" * 60)
    
    try:
        from socialmedia.weekly_scraper import WeeklyInstagramScraper
        
        # Create scraper instance
        scraper = WeeklyInstagramScraper()
        
        print("Scraper instance created")
        
        # Test with a single competitor first
        print("Testing with Nike (should show new posts)")
        print("-" * 40)
        
        # Get competitors
        competitors = scraper.get_competitors_to_scrape()
        if not competitors:
            print("No competitors need scraping - adding a test competitor")
            # For testing, we'll manually test with Nike
            test_competitor = {
                'id': 'test-nike-id',
                'username': 'nike',
                'profile_url': 'https://www.instagram.com/nike/',
                'last_checked': None,
                'recent_post_count': 0
            }
        else:
            test_competitor = competitors[0]
            print(f"Using competitor: @{test_competitor['username']}")
        
        # Initialize scraper
        if not scraper.initialize_scraper():
            print("Error: Failed to initialize scraper")
            return
        
        print("Instagram scraper initialized")
        
        # Test scraping with deduplication
        print("Testing scraping with deduplication...")
        
        # First scrape - use the internal scraper
        print("\n--- FIRST SCRAPE ---")
        posts_data = scraper.scraper.scrape_profile(
            profile_url=test_competitor['profile_url'],
            max_posts=3  # Small number for testing
        )
        
        if posts_data:
            print(f"First scrape: {len(posts_data)} posts")
            
            # Wait a moment
            import time
            print("Waiting 5 seconds...")
            time.sleep(5)
            
            # Second scrape (should show updates)
            print("\n--- SECOND SCRAPE (should show updates) ---")
            posts_data_2 = scraper.scraper.scrape_profile(
                profile_url=test_competitor['profile_url'],
                max_posts=3
            )
            
            if posts_data_2:
                print(f"Second scrape: {len(posts_data_2)} posts")
                
                # Compare captions
                print("\n--- CAPTION COMPARISON ---")
                for i, post in enumerate(posts_data_2, 1):
                    caption = post.get('caption', '')[:50] + "..." if len(post.get('caption', '')) > 50 else post.get('caption', '')
                    print(f"  {i}. {post.get('url', 'No URL')} - '{caption}'")
                
                print("\nIf captions are the same, you should see 'Updated post' messages")
                print("If captions are different, you should see 'New post' messages")
            else:
                print("Second scrape failed")
        else:
            print("First scrape failed")
        
        # Clean up
        if hasattr(scraper, 'scraper') and hasattr(scraper.scraper, 'close'):
            scraper.scraper.close()
        print("\n Scraper closed")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("Full Deduplication Test")
    print("=" * 50)
    print()
    
    test_dedup_with_real_scraping()
    print("\n✅ Test completed!")

if __name__ == "__main__":
    main()
