
import os
import json
import logging
import psycopg
import hashlib
from datetime import datetime

# Configure logging
log = logging.getLogger(__name__)

# Database connection URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://root:secret@db:5432/project_monopoly?sslmode=disable")

def generate_competitor_report(competitor_data):
    """
    Generates a text report from competitor data.
    """
    username = competitor_data.get('username', 'Unknown')
    followers = competitor_data.get('followers', 0)
    posts_count = competitor_data.get('posts_count', 0)
    engagement_rate = competitor_data.get('engagement_rate', 0.0)
    posting_freq = competitor_data.get('posting_frequency', 0.0)
    last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = f"COMPETITOR ANALYSIS REPORT\n"
    report += f"Generated on: {last_updated}\n"
    report += f"Target Competitor: @{username}\n"
    report += f"Platform: Instagram\n\n"
    report += f"--- KEY METRICS ---\n"
    report += f"Followers: {followers:,}\n"
    report += f"Total Posts: {posts_count}\n"
    report += f"Engagement Rate: {engagement_rate:.2f}%\n"
    report += f"Posting Frequency: {posting_freq:.2f} posts/week\n\n"
    
    report += f"--- RECENT POST DETAILS ---\n"
    posts = competitor_data.get('posts', [])
    if posts:
        for i, post in enumerate(posts[:5], 1): # Top 5 recent posts
            caption = post.get('caption', 'No caption')
            likes = post.get('likes', '0')
            comments = post.get('comments_count', '0')
            post_date = post.get('post_date', 'Unknown date')
            
            report += f"Post #{i} ({post_date}):\n"
            report += f"  Likes: {likes}, Comments: {comments}\n"
            report += f"  Caption: {caption[:200]}...\n\n"
    else:
        report += "No recent post data available in this batch.\n"

    return report

def ingest_competitor_report(username, report_text, user_id, group_id=None):
    """
    Ingests the generated report into the workshop_documents table for RAG.
    """
    log.info(f"📄 Ingesting competitor report for @{username} into RAG...")
    
    filename = f"competitor_analysis_{username}_{datetime.now().strftime('%Y%m%d')}.txt"
    
    content_sha256 = hashlib.sha256(report_text.encode("utf-8")).hexdigest()
    group_id = group_id or 1
    
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            # 1. Insert into workshop_documents
            cur.execute("""
                INSERT INTO workshop_documents
                (user_id, group_id, filename, mime, size_bytes, sha256, storage_url, status, created_at, updated_at)
                VALUES (%s, %s, %s, 'text/plain', %s, %s, '', 'ready', NOW(), NOW())
                RETURNING id
            """, (user_id, group_id, filename, len(report_text), content_sha256))
            
            doc_id = cur.fetchone()[0]
            
            # 2. Insert chunks
            chunk_size = 3000
            chunks = [report_text[i:i+chunk_size] for i in range(0, len(report_text), chunk_size)]
            
            for index, chunk in enumerate(chunks):
                token_count = len(chunk.split())
                content_sha = hashlib.sha1(chunk.encode("utf-8", "ignore")).hexdigest()
                
                cur.execute("""
                    INSERT INTO workshop_chunks
                    (document_id, group_id, page, chunk_index, content, token_count, content_sha)
                    VALUES (%s, %s, 1, %s, %s, %s, %s)
                """, (doc_id, group_id, index, chunk, token_count, content_sha))
            
            conn.commit()
            log.info(f"✅ Report ingested successfully. Document ID: {doc_id}")
            return doc_id
