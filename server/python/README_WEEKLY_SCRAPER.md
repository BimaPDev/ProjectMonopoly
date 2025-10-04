# Weekly Instagram Scraper - Changes Made

##What Was Added

A weekly Instagram scraper with caption-based deduplication that automatically scrapes competitor posts and prevents duplicates.

##Files Created/Modified

### New Files:
- `socialmedia/weekly_scraper.py` - Main weekly scraper class
- `worker/weekly_scheduler.py` - Celery Beat configuration
- `test_caption_dedup.py` - Caption deduplication tests
- `test_full_dedup.py` - Full system tests
- `quick_test.py` - Quick testing script
- `manual_login.py` - Manual login for cookie saving
- `internal/db/migration/000002_add_caption_hash.up.sql` - Database migration
- `internal/db/migration/000002_add_caption_hash.down.sql` - Rollback migration

### Modified Files:
- `worker/tasks.py` - Added `weekly_instagram_scrape` task
- `worker/celery_app.py` - Added beat schedule (every Monday 1 AM)
- `run_all.py` - Added beat scheduler to startup
- `socialmedia/upload_to_db.py` - Added caption-based deduplication
- `socialmedia/__init__.py` - Fixed import issues

## 🔧 Key Features Added

1. **Weekly Scraping** - Runs every Monday at 1 AM EST
2. **Caption Deduplication** - Prevents duplicate posts using caption matching
3. **Cookie Authentication** - Uses saved Instagram cookies to bypass login
4. **Smart Updates** - Updates existing posts with fresh engagement data
5. **Database Integration** - Seamlessly works with existing PostgreSQL setup

## 🚀 How to Run

### 1. Set Environment Variables
```bash
export INSTAGRAM_USERNAME="your_instagram_username"
export INSTAGRAM_PASSWORD="your_instagram_password"
export DATABASE_URL="postgresql://root:secret@localhost:5432/project_monopoly?sslmode=disable"
```

### 2. Run Database Migration
```bash
# Apply the caption hash migration
cd /Users/davidfmajek/ProjectMonopoly
psql "postgresql://root:secret@localhost:5432/project_monopoly?sslmode=disable" -f server/internal/db/migration/000002_add_caption_hash.up.sql

# Remove old constraint that conflicts with caption-based deduplication
psql "postgresql://root:secret@localhost:5432/project_monopoly?sslmode=disable" -c "ALTER TABLE competitor_posts DROP CONSTRAINT IF EXISTS competitor_posts_platform_post_id_key;"
```

### 3. Add Instagram Competitors
```sql
INSERT INTO competitors (platform, username, profile_url) VALUES
('instagram', 'nike', 'https://www.instagram.com/nike/'),
('instagram', 'adidas', 'https://www.instagram.com/adidas/');
```

### 4. Start the System
```bash
cd /Users/davidfmajek/ProjectMonopoly/server/python
python3 run_all.py
```

**What `run_all.py` does:**
- 🚀 **Starts Redis** - Message broker for Celery
- 📦 **Starts Celery Worker** - Executes tasks (including weekly scraper)
- 🔁 **Starts Dispatcher** - Manages job queue
- ⏰ **Starts Beat Scheduler** - Triggers weekly scraper every 7 days
- 🌸 **Starts Flower** - Monitoring dashboard at http://localhost:5555

**Note**: 
- All cookie files (`.pkl`) are now stored in the `server/python/cookies` directory for better organization
- All scraped data files (`.json`) are saved to the `server/python/socialmedia/scrape_result/` directory

## Testing

### Test the Complete System
```bash
# Test weekly scraper 
python3 test_weekly_scraper.py

# Manual login (if needed)
python3 manual_login.py
```

**How `test_weekly_scraper.py` works:**
1. **Sets up test environment** - Configures Instagram credentials and database
2. **Creates scraper instance** - Initializes `WeeklyInstagramScraper`
3. **Tests with Nike profile** - Uses a real Instagram profile for testing
4. **First scrape** - Scrapes 3 posts and uploads to database
5. **Waits 5 seconds** - Brief pause between scrapes
6. **Second scrape** - Scrapes the same 3 posts again
7. **Shows deduplication** - Demonstrates caption-based deduplication in action

**Expected Test Output:**
- First scrape: `New post: [post_id]` messages
- Second scrape: `🔄 Updated post: [post_id] (caption match)` messages
- This proves deduplication is working correctly!

### **Test File Details:**

**`test_weekly_scraper.py` Configuration:**
```python
# Sets up test environment
os.environ["INSTAGRAM_USERNAME"] = "dogw.ood6"
os.environ["INSTAGRAM_PASSWORD"] = "qwert1233@"
os.environ["DATABASE_URL"] = "postgresql://root:secret@localhost:5432/project_monopoly?sslmode=disable"
os.environ["WEEKLY_MAX_POSTS"] = "5"  # Limit to 5 posts for testing
```

**Test Process:**
1. **Environment Setup** - Configures Instagram credentials and database connection
2. **Scraper Initialization** - Creates `WeeklyInstagramScraper` instance
3. **Profile Selection** - Uses Nike Instagram profile for testing
4. **First Scrape** - Scrapes 3 posts and uploads to database
5. **Wait Period** - 5-second pause to simulate time difference
6. **Second Scrape** - Scrapes the same 3 posts again
7. **Deduplication Test** - Shows how caption-based deduplication works
8. **Cleanup** - Properly closes browser and cleans up resources

**What the Test Proves:**
- ✅ Instagram login works with saved cookies
- ✅ Database connection and uploads work
- ✅ Caption-based deduplication prevents duplicates
- ✅ Fresh engagement data is captured on updates
- ✅ System handles real Instagram scraping


### Verify Results
```bash
# Check latest scraped posts
psql "postgresql://root:secret@localhost:5432/project_monopoly?sslmode=disable" -c "SELECT post_id, LEFT(content, 30) as caption, scraped_at FROM competitor_posts WHERE platform = 'instagram' ORDER BY scraped_at DESC LIMIT 5;"

# Check scraped data files located in socialmedia -> scrape_result
ls -la socialmedia/scrape_result/

# Verify no duplicate captions exist
psql "postgresql://root:secret@localhost:5432/project_monopoly?sslmode=disable" -c "SELECT competitor_id, caption_hash, COUNT(*) as count FROM competitor_posts GROUP BY competitor_id, caption_hash HAVING COUNT(*) > 1;"
```

## 🔄 How It Works

### **System Integration with `run_all.py`:**

```
run_all.py
├── 🚀 Redis Server (Message Broker)
├── 📦 Celery Worker (Task Executor) 
├── 🔁 Dispatcher (Job Queue)
├── ⏰ Beat Scheduler (Cron-like Scheduler) ← **WEEKLY SCRAPER HERE**
└── 🌸 Flower (Monitoring Dashboard)
```

### **Weekly Scraper Execution Flow:**

1. **Beat Scheduler** - Runs every 7 days (60*60*24*7 seconds)
2. **Task Queued** - `weekly_instagram_scrape` task added to Redis queue
3. **Worker Picks Up** - Celery worker executes the task
4. **Scraper Initializes** - `WeeklyInstagramScraper` starts up
5. **Finds Competitors** - Queries database for Instagram competitors needing scraping
6. **Uses Saved Cookies** - Logs into Instagram using saved cookies
7. **Scrapes Posts** - Gets up to 10 posts per competitor
8. **Deduplicates by Caption** - Prevents duplicate posts using caption matching
9. **Updates Database** - Updates existing posts or creates new ones
10. **Fresh Data** - Keeps engagement metrics (likes, comments) up-to-date

### **Task Configuration:**
- **Schedule**: Every 7 days (604,800 seconds)
- **Queue**: `celery` (default queue)
- **Priority**: 5 (lower than urgent tasks)
- **Retry**: Automatic on failure

## 📊 Database Changes

### New Fields Added:
- `caption_hash` - SHA256 hash of normalized captions
- `unique_competitor_caption` constraint - Prevents duplicate captions per competitor
- `idx_competitor_posts_caption_hash` index - Fast caption lookups

### Constraints Changed:
- **Removed**: `competitor_posts_platform_post_id_key` (old post_id based constraint)
- **Added**: `unique_competitor_caption` (new caption-based constraint)
<!-- Instagram post IDs are unique and never change for the same post (e.g., DOqyjekEeqo will always be the same ID). However, the old post ID constraint prevented us from updating engagement data. When we scraped the same post again to get fresh likes/comments, the database would reject it as a duplicate. With caption-based deduplication, we can now update existing posts with fresh engagement metrics while still preventing true duplicates. This allows us to keep engagement data current without creating duplicate entries, which is essential for tracking how posts perform over time. -->


### Deduplication Logic:
- **Same Caption** → Updates existing post with fresh engagement data
- **New Caption** → Creates new post entry
- **Caption Normalization** → Removes extra spaces, converts to lowercase, removes special chars

## 🎉 Result

The system now automatically scrapes Instagram competitors weekly, prevents duplicate posts, and maintains fresh engagement data in the database without any manual intervention!

## 🔧 Troubleshooting

### **Common Issues:**

**1. Flower Port Already in Use:**
```bash
# Kill existing processes
pkill -f "celery.*flower"
pkill -f "run_all.py"
# Then restart
python3 run_all.py
```

**2. Instagram Login Fails:**
```bash
# Use manual login to refresh cookies 
python3 manual_login.py
```

**3. Database Migration Issues:**
```bash
# Check if migration was applied
psql "postgresql://root:secret@localhost:5432/project_monopoly?sslmode=disable" -c "\d competitor_posts"
```

**4. Test File Errors:**
```bash
# Make sure you're in the right directory
cd /Users/davidfmajek/ProjectMonopoly/server/python
python3 test_weekly_scraper.py
```

**5. Beat Scheduler Not Running:**
- Check Flower dashboard: http://localhost:5555
- Look for "weekly-instagram-scrape" in scheduled tasks
- Verify Beat process is running in `run_all.py` output