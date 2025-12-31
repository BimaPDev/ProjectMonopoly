#!/usr/bin/env python3
# Script to upload scraped Instagram hashtag posts to PostgreSQL database
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
    os.environ["DATABASE_URL"] = "postgresql://root:secret@localhost:5432/project_monopoly?sslmode=disable"

def extract_post_id(url):
    # Extract post ID from instagram URL
    match = re.search(r'/(?:p|reel)/([^/]+)/', url)
    return match.group(1) if match else None

def normalize_caption(caption):
    if not caption:
        return ""
    
    # Remove extra whitespace and normalize
    normalized = re.sub(r'\s+', ' ', caption.strip().lower())
    
    # Remove common Instagram variations
    normalized = re.sub(r'[^\w\s#@]', '', normalized)  # Keep only alphanumeric, spaces, #, @
    
    return normalized

def generate_caption_hash(caption):
    normalized = normalize_caption(caption)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

def parse_engagement(likes_str, comments_str):
    # Parse engagement data from string values
    try:
        # Remove commas and convert to integers
        likes = int(likes_str.replace(',', '')) if likes_str else 0
        comments = int(comments_str.replace(',', '')) if comments_str else 0
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

def parse_posted_at(post_date_str):
    # Parse post date from ISO string
    try:
        return datetime.fromisoformat(post_date_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None

def get_database_connection():
    default_url = "postgresql://root:secret@localhost:5432/project_monopoly?sslmode=disable"
    database_url = os.getenv("DATABASE_URL", default_url)
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        print(f"Tried connecting to: {database_url}")
        print("\nTip: Set DATABASE_URL environment variable if using a different database")
        sys.exit(1)

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
    
    if not hashtag:
        print("Error: Could not determine hashtag from file")
        return False
    
    print(f"Uploading posts for hashtag: #{hashtag}")

    # Get database connection
    conn = get_database_connection()
    
    try:
        # Process each post
        uploaded_count = 0
        skipped_count = 0
        
        with conn.cursor() as cur:
            for post in posts_list:
                try:
                    # Extract post ID from URL
                    post_id = extract_post_id(post['url'])
                    if not post_id:
                        print(f"Warning: Could not extract post ID from URL: {post['url']}")
                        skipped_count += 1
                        continue
                    
                    # Parse likes and comments_count
                    likes_str = post.get('likes', '0')
                    comments_str = post.get('comments_count', '0')
                    try:
                        likes = int(str(likes_str).replace(',', '')) if likes_str else 0
                        comments_count = int(str(comments_str).replace(',', '')) if comments_str else 0
                    except (ValueError, AttributeError):
                        likes = 0
                        comments_count = 0
                    
                    # Parse posted date
                    posted_at = parse_posted_at(post.get('post_date'))
                    
                    # Prepare media data
                    media_data = {
                        "urls": post.get('media_urls', []),
                        "type": "image" if post.get('media_urls') else "unknown"
                    }
                    
                    # Generate caption hash for deduplication
                    caption = post.get('caption', '')
                    caption_hash = generate_caption_hash(caption)
                    
                    # Get username from post URL or post data
                    username = post.get('username', '')
                    if not username:
                        # Try to extract from URL
                        url = post.get('url', '')
                        if url:
                            import re
                            match = re.search(r'instagram\.com/([^/]+)', url)
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
                        'instagram',
                        post_id,
                        username,
                        caption,
                        json.dumps(media_data),
                        posted_at,
                        likes,
                        comments_count,
                        post.get('hashtags', []),
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

