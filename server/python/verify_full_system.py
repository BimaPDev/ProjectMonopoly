
import os
import psycopg
import logging
import uuid
from datetime import datetime, timedelta
from worker.context_aggregator import aggregate_context
from socialmedia.drivers.proxy_manager import proxy_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger("verify_system")

DATABASE_URL = os.environ.get("DATABASE_URL")

def test_proxy_manager():
    log.info("Testing Proxy Manager...")
    try:
        proxy_manager.validate_all_proxies()
        count = len(proxy_manager.proxies)
        log.info(f"   Proxy Fetch Successful. Count: {count}")
        
        proxy = proxy_manager.get_working_proxy()
        if proxy:
            log.info(f"   Got working proxy: {proxy}")
        else:
            log.warning("   No working proxy available (expected if all blocked/down)")
            
    except Exception as e:
        log.error(f"   Proxy Manager Failed: {e}")

def verify_niche_brain():
    log.info("\n🧠 Verifying Global Niche Brain (Cross-Group Sharing)...")
    
    conn = psycopg.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Generate unique identifiers to avoid conflicts
    run_id = str(uuid.uuid4())[:8]
    test_genre = f"TestGenre_{run_id}"
    email_a = f"verify_a_{run_id}@test.com"
    email_b = f"verify_b_{run_id}@test.com"
    comp_name = f"TestComp_{run_id}"
    handle = f"test_handle_{run_id}"
    
    user_a_id = None
    user_b_id = None
    
    try:
        # 1. Setup Test Data
        log.info(f"   → Creating temp users (run_id: {run_id})...")
        cur.execute("""
            INSERT INTO users (email, username, password_hash, created_at)
            VALUES 
            (%s, %s, 'hash', NOW()),
            (%s, %s, 'hash', NOW())
            RETURNING id
        """, (email_a, email_a, email_b, email_b))
        user_ids = cur.fetchall()
        user_a_id = user_ids[0][0]
        user_b_id = user_ids[1][0]
        
        # Create Groups
        try:
             cur.execute("INSERT INTO groups (user_id, name) VALUES (%s, %s) RETURNING id", (user_a_id, f"GroupA_{run_id}"))
             group_a_id = cur.fetchone()[0]
             cur.execute("INSERT INTO groups (user_id, name) VALUES (%s, %s) RETURNING id", (user_b_id, f"GroupB_{run_id}"))
             group_b_id = cur.fetchone()[0]
        except Exception:
             # Fallback
             conn.rollback()
             group_a_id = 9991
             group_b_id = 9992
             log.warning("   ⚠️ Could not insert into groups table, utilizing raw IDs")

        log.info(f"   → Creating Game Contexts with shared genre '{test_genre}'...")
        cur.execute("""
            INSERT INTO game_contexts (user_id, group_id, game_title, primary_genre, created_at)
            VALUES 
            (%s, %s, 'Game A', %s, NOW()),
            (%s, %s, 'Game B', %s, NOW())
        """, (user_a_id, group_a_id, test_genre, user_b_id, group_b_id, test_genre))
        
        # Insert a Competitor for Group A
        cur.execute("""
            INSERT INTO competitors (display_name)
            VALUES (%s)
            RETURNING id
        """, (comp_name,))
        comp_id = cur.fetchone()[0]
        
        cur.execute("""
            INSERT INTO user_competitors (user_id, group_id, competitor_id)
            VALUES (%s, %s, %s)
        """, (user_a_id, group_a_id, comp_id))

        # Create Profile
        cur.execute("""
            INSERT INTO competitor_profiles (competitor_id, platform, handle, profile_url, last_checked)
            VALUES (%s, 'instagram', %s, %s, NOW())
            RETURNING id
        """, (comp_id, handle, f"http://instagram.com/{handle}"))
        
        # 2. Insert Viral Outlier (Found by Group A)
        log.info("   → Inserting viral outlier for Group A...")
        cur.execute("""
            INSERT INTO viral_outliers 
            (source_table, source_id, multiplier, median_engagement, actual_engagement, 
             available_count, support_count, hook, platform, username, expires_at)
            VALUES 
            ('competitor_posts', 99999, 100, 1000, 100000, 3, 3, 
             'Use this viral hook structure for maximum engagement', 'instagram', %s, 
             NOW() + INTERVAL '7 days')
        """, (handle,))
        
        conn.commit()
        
        # 3. Test: Can Group B see this outlier?
        log.info("   → Fetching context for User B (who tracks NOTHING)...")
        
        ctx = aggregate_context(user_id=user_b_id, group_id=group_b_id, platform="instagram")
        
        found = False
        for hook in ctx.viral_hooks:
            if hook['username'] == handle:
                found = True
                log.info(f"   ✅ SUCCESS! Found shared viral hook: {hook['hook'][:50]}...")
                log.info(f"      Multiplier: {hook['multiplier']}x (from {hook['username']})")
                break
        
        if not found:
            log.error("   ❌ FAILED: User B did not see the shared viral hook.")
            
    except Exception as e:
        log.exception(f"   ❌ Niche Brain Verification Failed: {e}")
        conn.rollback()
    
    finally:
        # Cleanup (Optional since we use UUIDs, but good practice)
        log.info("   → cleaning up...")
        if user_a_id and user_b_id:
            try:
                # Basic cleanup effort
                cur.execute("DELETE FROM users WHERE id IN (%s, %s)", (user_a_id, user_b_id))
                cur.execute("DELETE FROM game_contexts WHERE primary_genre = %s", (test_genre,))
                cur.execute("DELETE FROM viral_outliers WHERE username = %s", (handle,))
                cur.execute("DELETE FROM competitor_profiles WHERE handle = %s", (handle,))
                cur.execute("DELETE FROM competitors WHERE display_name = %s", (comp_name,))
                conn.commit()
            except Exception as e:
                log.warning(f"   ⚠️ Cleanup failed (non-critical due to UUIDs): {e}")
        conn.close()

if __name__ == "__main__":
    # Setup file logging to capture full output
    fh = logging.FileHandler('verify_niche.log', mode='w')
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    fh.setFormatter(formatter)
    log.addHandler(fh)
    # Also log to console
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    log.addHandler(ch)
    
    print("="*60)
    test_proxy_manager() 
    # verify_niche_brain() # Skip niche brain to focus on proxy
    print("="*60)
