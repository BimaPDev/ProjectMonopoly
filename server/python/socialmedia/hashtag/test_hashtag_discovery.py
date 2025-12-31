#!/usr/bin/env python3
"""
Test script for Hashtag Discovery functionality.
Run this to test the hashtag discovery system without Celery.
"""
import os
import sys

# Set default DATABASE_URL if not already set
if not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "postgresql://root:secret@localhost:5432/project_monopoly?sslmode=disable"

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from socialmedia.hashtag.hashtag_discovery import HashtagDiscovery

def test_hashtag_discovery_interactive():
    """
    Interactive test for hashtag discovery.
    """
    print("=" * 60)
    print("Hashtag Discovery Test")
    print("=" * 60)
    
    # Get user preferences
    print("\nTest Options:")
    print("1. Single iteration (scrape new hashtags once)")
    print("2. Recursive discovery (scrape hashtags, then find new ones from those posts)")
    
    choice = input("\nEnter choice (1 or 2, default: 1): ").strip() or "1"
    
    if choice == "2":
        recursive = True
        max_iterations = input("Max iterations (default: 2): ").strip()
        max_iterations = int(max_iterations) if max_iterations else 2
        max_hashtags = input("Max hashtags per iteration (default: 5): ").strip()
        max_hashtags = int(max_hashtags) if max_hashtags else 5
    else:
        recursive = False
        max_iterations = None
        max_hashtags = input("Max hashtags to scrape (default: 5): ").strip()
        max_hashtags = int(max_hashtags) if max_hashtags else 5
    
    max_posts = input("Max posts per hashtag (default: 10): ").strip()
    max_posts = int(max_posts) if max_posts else 10
    
    user_id = input("User ID (optional, press Enter to skip): ").strip()
    user_id = int(user_id) if user_id else None
    
    group_id = input("Group ID (optional, press Enter to skip): ").strip()
    group_id = int(group_id) if group_id else None
    
    print("\n" + "=" * 60)
    print("Starting test...")
    print("=" * 60)
    
    # For local testing, use non-headless mode to avoid browser window closing issues
    # Set HEADLESS=false to use visible browser (better for debugging)
    import os
    if not os.getenv("HEADLESS"):
        os.environ["HEADLESS"] = "false"
        print("Note: Using non-headless mode for local testing (visible browser)")
    
    # Create discovery instance
    discovery = HashtagDiscovery(
        user_id=user_id,
        group_id=group_id,
        max_posts_per_hashtag=max_posts
    )
    
    # Run discovery
    if recursive:
        print(f"\nRunning recursive discovery:")
        print(f"  - Max iterations: {max_iterations}")
        print(f"  - Max hashtags per iteration: {max_hashtags}")
        print(f"  - Max posts per hashtag: {max_posts}")
        results = discovery.discover_and_scrape_recursive(
            max_iterations=max_iterations,
            max_hashtags_per_iteration=max_hashtags
        )
        
        print("\n" + "=" * 60)
        print("Test Results:")
        print("=" * 60)
        print(f"Status: {results.get('status', 'unknown')}")
        print(f"Iterations completed: {results.get('iterations', 0)}")
        print(f"Total hashtags scraped: {results.get('total_hashtags_scraped', 0)}")
        print(f"Total hashtags failed: {results.get('total_hashtags_failed', 0)}")
        print(f"Total posts scraped: {results.get('total_posts_scraped', 0)}")
        
        if results.get('iteration_details'):
            print("\nPer-iteration breakdown:")
            for iter_detail in results['iteration_details']:
                print(f"\n  Iteration {iter_detail['iteration']}:")
                print(f"    - Hashtags scraped: {iter_detail['hashtags_scraped']}")
                print(f"    - Posts scraped: {iter_detail['posts_scraped']}")
                if iter_detail.get('details'):
                    print(f"    - Details:")
                    for detail in iter_detail['details'][:3]:  # Show first 3
                        print(f"      • #{detail.get('hashtag', 'unknown')}: {detail.get('status', 'unknown')} ({detail.get('posts', 0)} posts)")
    else:
        print(f"\nRunning single iteration discovery:")
        print(f"  - Max hashtags: {max_hashtags}")
        print(f"  - Max posts per hashtag: {max_posts}")
        results = discovery.scrape_new_hashtags(max_hashtags=max_hashtags)
        
        print("\n" + "=" * 60)
        print("Test Results:")
        print("=" * 60)
        print(f"Status: {results.get('status', 'unknown')}")
        print(f"Hashtags scraped: {results.get('hashtags_scraped', 0)}")
        print(f"Hashtags failed: {results.get('hashtags_failed', 0)}")
        print(f"Total posts scraped: {results.get('total_posts_scraped', 0)}")
        
        if results.get('details'):
            print("\nHashtag details:")
            for detail in results['details']:
                print(f"  • #{detail.get('hashtag', 'unknown')}: {detail.get('status', 'unknown')} ({detail.get('posts', 0)} posts)")
    
    print("\n" + "=" * 60)
    if results.get('status') == 'success':
        print("Test completed successfully!")
    else:
        print(f"Test failed: {results.get('error', 'Unknown error')}")
    print("=" * 60)
    
    return results

def test_hashtag_extraction_only():
    """
    Test just the hashtag extraction logic without scraping.
    Useful for debugging and understanding what hashtags would be discovered.
    """
    print("=" * 60)
    print("Hashtag Extraction Test (No Scraping)")
    print("=" * 60)
    
    user_id = input("User ID (optional, press Enter to skip): ").strip()
    user_id = int(user_id) if user_id else None
    
    group_id = input("Group ID (optional, press Enter to skip): ").strip()
    group_id = int(group_id) if group_id else None
    
    discovery = HashtagDiscovery(user_id=user_id, group_id=group_id)
    
    print("\n1. Extracting hashtags from competitor posts...")
    competitor_hashtags = discovery.get_competitor_hashtags(limit=50)
    print(f"   Found {len(competitor_hashtags)} unique hashtags")
    if competitor_hashtags:
        print("   Top 10:")
        for ht in competitor_hashtags[:10]:
            print(f"     • #{ht['hashtag']} (frequency: {ht['frequency']})")
    
    print("\n2. Extracting hashtags from hashtag_posts...")
    hashtag_posts_hashtags = discovery.get_hashtag_posts_hashtags(limit=50)
    print(f"   Found {len(hashtag_posts_hashtags)} unique hashtags")
    if hashtag_posts_hashtags:
        print("   Top 10:")
        for ht in hashtag_posts_hashtags[:10]:
            print(f"     • #{ht['hashtag']} (frequency: {ht['frequency']})")
    
    print("\n3. Checking which hashtags have been scraped...")
    scraped_hashtags = discovery.get_scraped_hashtags()
    print(f"   Found {len(scraped_hashtags)} already scraped hashtags")
    
    print("\n4. Finding unscraped hashtags...")
    unscraped = discovery.get_unscraped_hashtags(limit=20, include_hashtag_posts=True)
    print(f"   Found {len(unscraped)} unscraped hashtags")
    if unscraped:
        print("   Top unscraped hashtags:")
        for ht in unscraped[:10]:
            print(f"     • #{ht['hashtag']} (frequency: {ht['frequency']})")
    else:
        print("   No unscraped hashtags found!")
    
    print("\n" + "=" * 60)
    print("Extraction test complete!")
    print("=" * 60)

def main():
    """
    Main function with command-line options.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Test hashtag discovery functionality")
    parser.add_argument(
        "--mode",
        choices=["interactive", "extraction-only"],
        default="interactive",
        help="Test mode: 'interactive' for full test, 'extraction-only' to just test hashtag extraction"
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Enable recursive discovery (only used in non-interactive mode)"
    )
    parser.add_argument(
        "--max-hashtags",
        type=int,
        default=5,
        help="Maximum hashtags to scrape (default: 5)"
    )
    parser.add_argument(
        "--max-posts",
        type=int,
        default=10,
        help="Maximum posts per hashtag (default: 10)"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=2,
        help="Maximum iterations for recursive discovery (default: 2)"
    )
    parser.add_argument(
        "--user-id",
        type=int,
        default=None,
        help="User ID to filter competitors"
    )
    parser.add_argument(
        "--group-id",
        type=int,
        default=None,
        help="Group ID to filter competitors"
    )
    
    args = parser.parse_args()
    
    if args.mode == "extraction-only":
        test_hashtag_extraction_only()
    elif args.mode == "interactive":
        if len(sys.argv) == 1:
            # No arguments provided, run interactive mode
            test_hashtag_discovery_interactive()
        else:
            # Arguments provided, run non-interactive
            discovery = HashtagDiscovery(
                user_id=args.user_id,
                group_id=args.group_id,
                max_posts_per_hashtag=args.max_posts
            )
            
            if args.recursive:
                print(f"Running recursive discovery (max_iterations={args.max_iterations}, max_hashtags={args.max_hashtags})...")
                results = discovery.discover_and_scrape_recursive(
                    max_iterations=args.max_iterations,
                    max_hashtags_per_iteration=args.max_hashtags
                )
            else:
                print(f"Running single iteration discovery (max_hashtags={args.max_hashtags})...")
                results = discovery.scrape_new_hashtags(max_hashtags=args.max_hashtags)
            
            print(f"\nResults: {results}")

if __name__ == "__main__":
    main()

