
import os
import psycopg
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("db_fix")

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://root:secret@localhost:5434/project_monopoly?sslmode=disable")

def fix_missing_tables():
    log.info("Checking for missing tables...")
    
    try:
        with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
            with conn.cursor() as cur:
                # Check if hashtag_posts exists
                cur.execute("SELECT to_regclass('public.hashtag_posts')")
                if cur.fetchone()[0] is None:
                    log.warning("⚠️ Table 'hashtag_posts' is MISSING. Creating it...")
                    
                    cur.execute("""
                        CREATE TABLE hashtag_posts (
                          id SERIAL PRIMARY KEY,
                          hashtag TEXT NOT NULL,
                          platform VARCHAR(50) NOT NULL,
                          post_id VARCHAR(100) NOT NULL,
                          username TEXT,
                          content TEXT,
                          media JSONB DEFAULT '{}'::jsonb,
                          posted_at TIMESTAMP,
                          likes BIGINT DEFAULT 0,
                          comments_count BIGINT DEFAULT 0,
                          hashtags TEXT[] DEFAULT '{}',
                          scraped_at TIMESTAMP DEFAULT NOW(),
                          caption_hash TEXT,
                          UNIQUE (platform, post_id)
                        );
                        
                        CREATE INDEX IF NOT EXISTS idx_hashtag_posts_hashtag ON hashtag_posts(hashtag);
                        CREATE INDEX IF NOT EXISTS idx_hashtag_posts_posted_at ON hashtag_posts(posted_at);
                        CREATE INDEX IF NOT EXISTS idx_hashtag_posts_platform ON hashtag_posts(platform);
                        CREATE INDEX IF NOT EXISTS idx_hashtag_posts_username ON hashtag_posts(username);
                    """)
                    log.info("✅ Table 'hashtag_posts' created successfully.")
                else:
                    log.info("✅ Table 'hashtag_posts' already exists.")
                    
    except Exception as e:
        log.error(f"❌ DB Fix Failed: {e}")

if __name__ == "__main__":
    fix_missing_tables()
