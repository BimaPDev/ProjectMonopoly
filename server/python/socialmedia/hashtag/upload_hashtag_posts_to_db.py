#!/usr/bin/env python3
# Script to upload scraped Instagram and TikTok hashtag posts to PostgreSQL database
import json
import psycopg2
import psycopg2.extras
from datetime import datetime
import re
import os
import sys
import hashlib

# Set default DATABASE_URL if not already set
if not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "postgresql://root:secret@localhost:5434/project_monopoly?sslmode=disable"

def extract_post_id(url, platform='instagram'):
    # Extract post ID from URL based on platform
    if platform == 'instagram':
        match = re.search(r'/(?:p|reel)/([^/]+)/', url)
        return match.group(1) if match else None
    elif platform == 'tiktok':
        # TikTok URL format: https://www.tiktok.com/@user/video/1234567890123456789
        match = re.search(r'/video/(\d+)', url)
        return match.group(1) if match else None
    return None

def normalize_caption(caption):
    if not caption:
        return ""
    
    # Remove extra whitespace and normalize
    normalized = re.sub(r'\s+', ' ', caption.strip().lower())
    
    # Remove common Instagram/TikTok variations
    normalized = re.sub(r'[^\w\s#@]', '', normalized)  # Keep only alphanumeric, spaces, #, @
    
    return normalized

def generate_caption_hash(caption):
    normalized = normalize_caption(caption)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

def parse_engagement(likes_str, comments_str):
    # Parse engagement data from string values
    try:
        # Remove commas, 'K', 'M' and convert to integers
        likes = parse_count(likes_str)
        comments = parse_count(comments_str)
        return {
            "likes": likes,
            "comments": comments,
            "total_engagement": likes + comments
        }
    except (ValueError, AttributeError):
        return {
            "likes": 0,
            "comments": 0,
            "total_engagement": 0
        }

def parse_count(count_str):
    """Parse count string with K/M suffixes"""
    if not count_str:
        return 0
    
    s = str(count_str).strip().upper().replace(',', '')
    try:
        if s.endswith('K'):
            return int(float(s[:-1]) * 1000)
        elif s.endswith('M'):
            return int(float(s[:-1]) * 1000000)
        elif s.endswith('B'):
            return int(float(s[:-1]) * 1000000000)
        else:
            return int(float(s))
    except ValueError:
        return 0

def parse_posted_at(post_date_str):
    # Parse post date from ISO string
    if not post_date_str:
        return None
    try:
        return datetime.fromisoformat(post_date_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        # Try simple date format YYYY-MM-DD HH:MM:SS
        try:
            return datetime.strptime(post_date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None

def get_database_connection():
    default_url = "postgresql://root:secret@localhost:5434/project_monopoly?sslmode=disable"
    database_url = os.getenv("DATABASE_URL", default_url)
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        print(f"Tried connecting to: {database_url}")
        print("\nTip: Set DATABASE_URL environment variable if using a different database")
        sys.exit(1)

def detect_platform(json_file_path, posts_list):
    """Detect platform from filename or content"""
    filename = os.path.basename(json_file_path).lower()
    
    if 'tiktok' in filename:
        return 'tiktok'
    if 'instagram' in filename:
        return 'instagram'
        
    # Check first post URL structure
    if posts_list:
        first_url = posts_list[0].get('url', '')
        if 'tiktok.com' in first_url:
            return 'tiktok'
        if 'instagram.com' in first_url:
            return 'instagram'
            
    # Default to instagram for backward compatibility
    return 'instagram'

def upload_hashtag_posts_to_db(json_file_path):
    # Load the JSON data
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            posts_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File {json_file_path} not found")
        return False
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return False
    
    if isinstance(posts_data, list):
        posts_list = posts_data
        hashtag_info = {}
    elif isinstance(posts_data, dict):
        posts_list = posts_data.get('posts', [])
        hashtag_info = posts_data.get('hashtag_info', {})
    else:
        print("Error: JSON content is neither list nor dict")
        return False

    if not posts_list:
        print("No posts data found in file")
        return False

    # Get hashtag from hashtag_info or from first post
    hashtag = hashtag_info.get('hashtag', '')
    if not hashtag and posts_list:
        # Try to get from first post's source_hashtag field
        hashtag = posts_list[0].get('source_hashtag', '')
    
    if not hashtag:
        # Try to extract from filename
        filename = os.path.basename(json_file_path)
        match = re.match(r"^([^_]+)_hashtag_posts_\d{8}_\d{6}\.json$", filename)
        if match:
            hashtag = match.group(1)
            
        # Try TikTok filename pattern: {hashtag}_tiktoks_{timestamp}.json
        match = re.search(r"([^_]+)_tiktoks_\d+_\d+\.json$", filename)
        if match:
            hashtag = match.group(1)
    
    if not hashtag:
        print("Error: Could not determine hashtag from file")
        return False
    
    # Detect platform
    platform = detect_platform(json_file_path, posts_list)
    
    print(f"Uploading posts for hashtag: #{hashtag} (Platform: {platform})")

    # Get database connection
    conn = get_database_connection()
    
    try:
        # Process each post
        uploaded_count = 0
        skipped_count = 0
        
        with conn.cursor() as cur:
            for post in posts_list:
                try:
                    # Extract post ID based on platform
                    post_id = extract_post_id(post['url'], platform)
                    if not post_id:
                        # Fallback: use hash of URL if ID extraction fails
                        post_id = hashlib.md5(post['url'].encode()).hexdigest()
                        print(f"Warning: Could not extract post ID, using hash: {post_id}")
                    
                    # Map fields based on platform
                    if platform == 'tiktok':
                        caption = post.get('description', '')
                        likes_val = parse_count(post.get('likes_count', 0))
                        comments_val = parse_count(post.get('comments_count', 0))
                        
                        # TikTok doesn't typically give us array of hashtags in the json directly usually
                        # unless our scraper extracts them.
                        hashtags_list = post.get('hashtags', [])
                        
                        # Video URL
                        media_url = post.get('video_url', '') or post.get('url', '')
                        media_data = {
                            "urls": [media_url],
                            "type": "video"
                        }
                    else:
                        # Instagram
                        caption = post.get('caption', '')
                        likes_val = int(str(post.get('likes', '0')).replace(',', '')) if post.get('likes') else 0
                        comments_val = int(str(post.get('comments_count', '0')).replace(',', '')) if post.get('comments_count') else 0
                        hashtags_list = post.get('hashtags', [])
                        media_data = {
                            "urls": post.get('media_urls', []),
                            "type": "image" if post.get('media_urls') else "unknown"
                        }
                    
                    # Parse posted date
                    posted_at = parse_posted_at(post.get('post_date'))
                    
                    # Generate caption hash for deduplication
                    caption_hash = generate_caption_hash(caption)
                    
                    # Get username
                    username = post.get('username', '')
                    if not username:
                        username = post.get('author', '')  # TikTok uses 'author' field
                        
                    if not username:
                        # Try to extract from URL
                        url = post.get('url', '')
                        if url:
                            if platform == 'instagram':
                                match = re.search(r'instagram\.com/([^/]+)', url)
                                if match:
                                    username = match.group(1)
                            elif platform == 'tiktok':
                                match = re.search(r'tiktok\.com/@([^/]+)', url)
                                if match:
                                    username = match.group(1)
                    
                    # Use source_hashtag from post if available, otherwise use the main hashtag
                    post_hashtag = post.get('source_hashtag', hashtag)
                    
                    # Insert or update post
                    cur.execute("""
                        INSERT INTO hashtag_posts (
                            hashtag, platform, post_id, username, content, media,
                            posted_at, likes, comments_count, hashtags, scraped_at, caption_hash
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (platform, post_id) DO UPDATE SET
                            hashtag = EXCLUDED.hashtag,
                            username = EXCLUDED.username,
                            content = EXCLUDED.content,
                            media = EXCLUDED.media,
                            posted_at = EXCLUDED.posted_at,
                            likes = EXCLUDED.likes,
                            comments_count = EXCLUDED.comments_count,
                            hashtags = EXCLUDED.hashtags,
                            scraped_at = EXCLUDED.scraped_at
                    """, (
                        post_hashtag,
                        platform,
                        post_id,
                        username,
                        caption,
                        json.dumps(media_data),
                        posted_at,
                        likes_val,
                        comments_val,
                        hashtags_list,
                        datetime.now(),
                        caption_hash
                    ))
                    
                    uploaded_count += 1
                    
                except Exception as e:
                    print(f"Error processing post {post.get('url', 'unknown')}: {e}")
                    conn.rollback()  # Rollback the failed transaction so we can continue
                    skipped_count += 1
                    continue

        # Finalize database changes
        conn.commit()
        print(f"Successfully uploaded {uploaded_count} posts for #{hashtag} to database")
        if skipped_count > 0:
            print(f"Skipped {skipped_count} posts due to errors")
        return True
        
    except Exception as e:
        print(f"Error during upload: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    # Main function
    if len(sys.argv) != 2:
        print("Usage: python upload_hashtag_posts_to_db.py <json_file_path>")
        sys.exit(1)
    
    json_file_path = sys.argv[1]
    
    if not os.path.exists(json_file_path):
        print(f"Error: File {json_file_path} does not exist")
        sys.exit(1)
    
    print(f"Uploading hashtag posts from {json_file_path} to database...")
    success = upload_hashtag_posts_to_db(json_file_path)
    
    if success:
        print("Upload completed successfully!")
    else:
        print("Upload failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()

