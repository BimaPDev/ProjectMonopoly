#!/usr/bin/env python3
# Script to upload scraped Instagram data to PostgreSQL database
import json
import psycopg2
import psycopg2.extras
from datetime import datetime
import re
import os
import sys
from urllib.parse import urlparse

def extract_post_id(url):
    # Extract post ID from instagram URL
    match = re.search(r'/p/([^/]+)/', url)
    return match.group(1) if match else None

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
        # Parse ISO format: 2025-09-15T17:35:15.000Z
        return datetime.fromisoformat(post_date_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None

def get_database_connection():
    # Get database connection
    # Database connection parameters
    # Update these to match your database configuration
    conn_params = {
        'host': 'localhost',
        'port': 5432,
        'database': 'project_monopoly',
        'user': 'root',
        'password': 'secret'
    }
    
    try:
        conn = psycopg2.connect(**conn_params)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def create_or_get_competitor(conn, platform, username, profile_url):
    # Check if competitor exists, else create new one
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id FROM competitors 
            WHERE platform = %s AND username = %s
        """, (platform, username))
        
        result = cur.fetchone()
        if result:
            return result[0]
        
        # Create new competitor if not exists
        cur.execute("""
            INSERT INTO competitors (platform, username, profile_url, last_checked)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (platform, username) DO UPDATE SET
                profile_url = EXCLUDED.profile_url,
                last_checked = EXCLUDED.last_checked
            RETURNING id
        """, (platform, username, profile_url))
        
        return cur.fetchone()[0]

def upload_posts_to_db(json_file_path):
    # Upload posts from JSON file to database
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
    
    if not posts_data:
        print("No posts data found in file")
        return False
    
    # Get database connection
    conn = get_database_connection()
    
    try:
        # Determine competitor info from the first post
        first_post = posts_data[0]
        url = first_post['url']
        
        # Extract username from URL
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')
        username = path_parts[0] if path_parts else 'unknown'
        
        # Create or get competitor
        competitor_id = create_or_get_competitor(
            conn,'instagram', 
            username,f"https://www.instagram.com/{username}/"
        )
        print(f"Using competitor ID: {competitor_id} for @{username}")
        
        # Process each post
        uploaded_count = 0
        with conn.cursor() as cur:
            for post in posts_data:
                try:
                    # Extract post ID from URL
                    post_id = extract_post_id(post['url'])
                    if not post_id:
                        print(f"Warning: Could not extract post ID from URL: {post['url']}")
                        continue
                    
                    # Parse engagement data
                    engagement = parse_engagement(post.get('likes', '0'), post.get('comments_count', '0'))
                    
                    # Parse posted date
                    posted_at = parse_posted_at(post.get('post_date'))
                    
                    # Prepare media data
                    media_data = {
                        "urls": post.get('media_urls', []),
                        "type": "image" if post.get('media_urls') else "unknown"
                    }
                    
                    # Insert or update post
                    cur.execute("""
                        INSERT INTO competitor_posts (
                            competitor_id, platform, post_id, content, media,
                            posted_at, engagement, hashtags, scraped_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (platform, post_id) DO UPDATE SET
                            content = EXCLUDED.content,
                            media = EXCLUDED.media,
                            posted_at = EXCLUDED.posted_at,
                            engagement = EXCLUDED.engagement,
                            hashtags = EXCLUDED.hashtags,
                            scraped_at = EXCLUDED.scraped_at
                    """, (
                        competitor_id,'instagram',
                        post_id,post.get('caption', ''),
                        json.dumps(media_data),posted_at,
                        json.dumps(engagement),post.get('hashtags', []),
                        datetime.now()
                    ))
                    uploaded_count += 1
                    print(f"Uploaded post: {post_id}")
                    
                except Exception as e:
                    print(f"Error processing post {post.get('url', 'unknown')}: {e}")
                    continue

        # Finalize database changes
        conn.commit()
        print(f"Successfully uploaded {uploaded_count} posts to database")
        return True
        
    except Exception as e:
        print(f"Error during upload: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def main():
    # Main function
    if len(sys.argv) != 2:
        print("Usage: python upload_to_db.py <json_file_path>")
        sys.exit(1)
    
    json_file_path = sys.argv[1]
    
    if not os.path.exists(json_file_path):
        print(f"Error: File {json_file_path} does not exist")
        sys.exit(1)
    
    print(f"Uploading posts from {json_file_path} to database...")
    success = upload_posts_to_db(json_file_path)
    
    if success:
        print("Upload completed successfully!")
    else:
        print("Upload failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()