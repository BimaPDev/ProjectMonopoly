# Reddit Listener Pipeline

A Python-based service for ingesting, filtering, and chunking Reddit content for the "Insider" feature.

## Features
- **Monitors** subreddits and keyword queries.
- **Filters** content based on quality score (upvotes, comments, recency).
- **Chunks** text (posts & comments) for RAG with prompt injection guards.
- **Extracts** structured "Strategy Cards" (marketing tactics) via LLM.
- **Detects** volume spikes ("Ears to the Ground") and alerts.

## Setup

1. **Install Dependencies**:
   ```bash
   cd server/python
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   Add these to your `.env`:
   ```env
   # Database (Required)
   DATABASE_URL="postgresql://user:pass@localhost:5432/db_name"
   
   # Optional Overrides
   # MIN_QUALITY_SCORE=0.3
   # MIN_SCORE=5
   # SPIKE_FACTOR_THRESHOLD=2.0  # Alert if volume doubles
   # LLM_ENABLED=true
   ```

> **Note**: No Reddit account needed! This uses Reddit's public `.json` endpoints.

## Usage (CLI)

The CLI tool allows you to manage sources and run the ingestion loop manually.

```bash
# Run from server/python directory
python -m reddit_listener.cli --help

# 1. Add a source (e.g., subreddit r/marketing)
python -m reddit_listener.cli add-subreddit marketing --user-id 1

# 2. Add a keyword source (e.g., "SaaS growth" in r/SaaS)
python -m reddit_listener.cli add-query "SaaS growth" --subreddit SaaS --user-id 1

# 3. Run one intake cycle (fetch, score, store, chunk)
python -m reddit_listener.cli run-once

# 4. Run loop (every 15 mins)
python -m reddit_listener.cli run --interval-min 15

# 5. Backfill historical data (e.g., last 72 hours)
#    Note: This bypasses the "last seen" check and fetches deeper.
python -m reddit_listener.cli backfill --source-id 1 --hours 72
```

## Architecture

- **`reddit_api.py`**: PRAW wrapper with rate limit handling (exponential backoff).
- **`scheduler.py`**: Main loop. Fetches new items, triggers normalization, scoring, and storage.
- **`store.py`**: Database operations. Prunes huge JSON payloads before storage.
- **`chunker.py`**: Splits text into RAG-ready chunks with metadata.
- **`quality.py`**: Scoring logic to ignore low-effort posts.
- **`extractor.py`**: Extracts Strategy Cards (placeholder/LLM integration).

## Verification Steps

1. **Apply Migrations**:
   Run the SQL migrations to create the necessary tables.
   ```bash
   migrate -path server/internal/db/migration -database "$DATABASE_URL" up
   ```

2. **Generate SQLC**:
   Generate the Go boilerplate for the new queries.
   ```bash
   sqlc generate
   ```

3. **Test Ingestion**:
   - Add a source via CLI.
   - Run `run-once`.
   - Check database: `SELECT count(*) FROM reddit_items;`

4. **Test API**:
   - GET `/api/reddit/items?limit=10` (Authenticated)
   - Ensure it returns items only for the logged-in user.
