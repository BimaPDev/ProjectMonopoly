#!/usr/bin/env python3
# Script to upload scraped Instagram data to PostgreSQL database
import json
import psycopg2
import psycopg2.extras
from datetime import datetime
import re
import os
import sys
import hashlib
from urllib.parse import urlparse

def extract_post_id(url):
    # Extract post ID from instagram URL
    match = re.search(r'/(?:p|reel)/([^/]+)/', url)
    return match.group(1) if match else None

def normalize_caption(caption):
    """
    Normalize caption for consistent comparison.
    - Remove extra whitespace
    - Convert to lowercase
    - Remove special characters that might vary
    """
    if not caption:
        return ""
    
    # Remove extra whitespace and normalize
    normalized = re.sub(r'\s+', ' ', caption.strip().lower())
    
    # Remove common Instagram variations
    normalized = re.sub(r'[^\w\s#@]', '', normalized)  # Keep only alphanumeric, spaces, #, @
    
    return normalized

def generate_caption_hash(caption):
    """
    Generate a hash for the normalized caption.
    This will be used for deduplication.
    """
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
        # Parse ISO format: 2025-09-15T17:35:15.000Z
        return datetime.fromisoformat(post_date_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None

def get_database_connection():
    database_url = os.getenv("DATABASE_URL", "postgresql://root:secret@postgres:5432/project_monopoly")
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def create_or_get_competitor(conn, platform, username, profile_url):
    # Check if competitor exists, else create new one
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id FROM competitors 
            WHERE platform = %s AND LOWER(username) = LOWER(%s)
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
    
    # Handle both old (list) and new (dict) JSON formats
    if isinstance(posts_data, list):
        posts_list = posts_data
        profile_stats = {}
    elif isinstance(posts_data, dict):
        posts_list = posts_data.get('posts', [])
        profile_stats = posts_data.get('profile_info', {})
    else:
        print("Error: JSON content is neither list nor dict")
        return False

    if not posts_list:
        print("No posts data found in file")
        # Even if no posts, we might want to update stats? But logic below relies on posts for competitor ID
        # Let's try to get username from profile_stats if available
        if not profile_stats:
            return False

    # Get database connection
    conn = get_database_connection()
    
    try:
        # Determine username
        username = 'unknown'
        
        # Priority 1: From profile stats (most reliable)
        if profile_stats.get('username'):
            username = profile_stats['username']
            print(f"Using username from profile stats: {username}")
            
        # Priority 2: From filename
        elif username == 'unknown':
            filename = os.path.basename(json_file_path)
            match = re.match(r"^(.*)_posts_\d{8}_\d{6}\.json$", filename)
            if match:
                username = match.group(1)
                print(f"Extracted username from filename: {username}")
        
        # Priority 3: From first post URL (fallback)
        if username == 'unknown' and posts_list:
            first_post = posts_list[0]
            url = first_post.get('url', '')
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.strip('/').split('/')
            if path_parts:
                username = path_parts[0]
                print(f"Extracted username from post URL: {username}")
                
        # Create or get competitor
        competitor_id = create_or_get_competitor(
            conn,'instagram', 
            username,f"https://www.instagram.com/{username}/"
        )
        print(f"Using competitor ID: {competitor_id} for @{username}")
        
        # Update competitor stats directly if available
        if profile_stats:
            try:
                followers = int(str(profile_stats.get('followers', 0)).replace(',', ''))
                posts_count = int(str(profile_stats.get('posts_count', 0)).replace(',', ''))
                
                # --- Analytics Calculation ---
                engagement_rate = 0.0
                posting_freq = 0.0
                
                if posts_list and followers > 0:
                    total_likes = 0
                    total_comments = 0
                    valid_posts = 0
                    min_date = None
                    max_date = None
                    
                    for p in posts_list:
                        try:
                            l = int(str(p.get('likes', '0')).replace(',', '') or '0')
                            c = int(str(p.get('comments_count', '0')).replace(',', '') or '0')
                            total_likes += l
                            total_comments += c
                            valid_posts += 1
                            
                            # Date parsing for frequency
                            p_date_str = p.get('post_date')
                            if p_date_str:
                                # Handle various date formats if needed, or assume standard ISO from scraper
                                # standard format from scraper seems to be ISO or similar
                                try:
                                    dt = parse_posted_at(p_date_str)
                                    if dt:
                                        if min_date is None or dt < min_date: min_date = dt
                                        if max_date is None or dt > max_date: max_date = dt
                                except:
                                    pass
                        except:
                            pass
                            
                    if valid_posts > 0:
                        avg_interactions = (total_likes + total_comments) / valid_posts
                        engagement_rate = (avg_interactions / followers) * 100
                        
                    # Frequency (Posts per Week)
                    # If we have a date range
                    if valid_posts > 1 and min_date and max_date:
                        delta_days = (max_date - min_date).days
                        if delta_days > 0:
                            weeks = delta_days / 7.0
                            posting_freq = valid_posts / weeks
                        else:
                            # all posted same day?
                            posting_freq = valid_posts # treat as "per week" if highly active in 1 day? or just raw count
                    elif valid_posts == 1:
                        posting_freq = 1.0 # placeholder
                        
                # --- Growth Rate Calculation ---
                growth_rate = 0.0
                try:
                    with conn.cursor() as cur:
                        # Get a snapshot from roughly 7 days ago
                        cur.execute("""
                            SELECT followers 
                            FROM competitor_snapshots 
                            WHERE competitor_id = %s 
                            AND snapshot_date <= CURRENT_DATE - INTERVAL '1 day'
                            ORDER BY snapshot_date DESC 
                            LIMIT 1
                        """, (competitor_id,))
                        row = cur.fetchone()
                        
                        # If no 7-day old snapshot, try any previous snapshot
                        if not row:
                             cur.execute("""
                                SELECT followers 
                                FROM competitor_snapshots 
                                WHERE competitor_id = %s 
                                AND snapshot_date < CURRENT_DATE
                                ORDER BY snapshot_date ASC 
                                LIMIT 1
                            """, (competitor_id,))
                             row = cur.fetchone()

                        if row and row[0] and row[0] > 0:
                            prev_followers = float(row[0])
                            growth_rate = ((followers - prev_followers) / prev_followers) * 100
                except Exception as e:
                    print(f"Error calculating growth rate: {e}")

                print(f"Calculated Analytics: EngRate={engagement_rate:.2f}%, Freq={posting_freq:.2f}/week, Growth={growth_rate:.2f}%")

                with conn.cursor() as cur:
                    # Update Competitor
                    cur.execute("""
                        UPDATE competitors 
                        SET followers = %s, 
                            total_posts = %s,
                            engagement_rate = %s,
                            growth_rate = %s,
                            posting_frequency = %s,
                            last_checked = NOW()
                        WHERE id = %s
                    """, (followers, posts_count, engagement_rate, growth_rate, posting_freq, competitor_id))
                    
                    # Add Snapshot
                    cur.execute("""
                        INSERT INTO competitor_snapshots (competitor_id, followers, engagement_rate, snapshot_date)
                        VALUES (%s, %s, %s, CURRENT_DATE)
                        ON CONFLICT (competitor_id, snapshot_date) 
                        DO UPDATE SET 
                            followers = EXCLUDED.followers,
                            engagement_rate = EXCLUDED.engagement_rate
                    """, (competitor_id, followers, engagement_rate))
                    
                    conn.commit()
                print(f"Updated stats for @{username}: {followers} followers, {posts_count} posts, {engagement_rate:.2f}% ER")
                
                # --- RAG Ingestion ---
                try:
                    user_id = None
                    group_id = None
                    
                    with conn.cursor() as cur:
                        # Fetch first user associated with this competitor to assign the document to
                        cur.execute("""
                            SELECT user_id, group_id FROM user_competitors WHERE competitor_id = %s LIMIT 1
                        """, (competitor_id,))
                        drow = cur.fetchone()
                        if drow:
                            user_id, group_id = drow
                    
                    if user_id:
                         # Prepare full data dict for reporting
                         report_data = {
                             'username': username,
                             'followers': followers,
                             'posts_count': posts_count,
                             'engagement_rate': engagement_rate,
                             'posting_frequency': posting_freq,
                             'posts': posts_list
                         }
                         
                         try:
                             from socialmedia.rag_ingest import generate_competitor_report, ingest_competitor_report
                         except ImportError:
                             from rag_ingest import generate_competitor_report, ingest_competitor_report
                         
                         report_text = generate_competitor_report(report_data)
                         ingest_competitor_report(username, report_text, user_id, group_id)
                         print(f"RAG Report generated and ingested for owner user_id={user_id}")
                    else:
                        print("Skipping RAG ingest: No owner found for this competitor.")

                except Exception as rag_err:
                    print(f"⚠️ RAG Ingest failed (non-fatal): {rag_err}")


            except Exception as e:
                print(f"Error updating competitor stats: {e}")
                import traceback
                traceback.print_exc()

        # Process each post
        uploaded_count = 0
        with conn.cursor() as cur:
            for post in posts_list:
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
                    
                    # Generate caption hash for deduplication
                    caption = post.get('caption', '')
                    caption_hash = generate_caption_hash(caption)
                    
                    # Insert or update post using caption-based deduplication
                    cur.execute("""
                        INSERT INTO competitor_posts (
                            competitor_id, platform, post_id, content, media,
                            posted_at, engagement, hashtags, scraped_at, caption_hash
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (platform, post_id) DO UPDATE SET
                            competitor_id = EXCLUDED.competitor_id,
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
                        datetime.now(), caption_hash
                    ))
                    
                    if cur.statusmessage == "INSERT 0 1": 
                         # This check might depend on driver, usually we rely on ON CONFLICT
                         pass
                        
                    uploaded_count += 1
                    
                except Exception as e:
                    print(f"Error processing post {post.get('url', 'unknown')}: {e}")
                    conn.rollback() # Important: Rollback the failed transaction so we can continue
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
