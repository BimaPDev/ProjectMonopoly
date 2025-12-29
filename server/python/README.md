# Python Worker Services

Background task processing system for ProjectMonopoly using Celery with RabbitMQ.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Python Worker Container                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │  run_all.py  │───▶│    Worker    │    │     Beat     │    │  Flower    │ │
│  │  (launcher)  │    │  (executor)  │    │  (scheduler) │    │ (monitor)  │ │
│  └──────────────┘    └──────┬───────┘    └──────────────┘    └────────────┘ │
│         │                   │                                                │
│         ▼                   ▼                                                │
│  ┌──────────────┐    ┌──────────────┐                                        │
│  │  Dispatcher  │───▶│   RabbitMQ   │◀──────────────────────────────────────│
│  │ (job poller) │    │   (broker)   │                                        │
│  └──────┬───────┘    └──────────────┘                                        │
│         │                                                                    │
│         ▼                                                                    │
│  ┌──────────────┐                                                            │
│  │  PostgreSQL  │                                                            │
│  │  (job queue) │                                                            │
│  └──────────────┘                                                            │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Celery App (`worker/celery_app.py`)
Central Celery configuration with RabbitMQ broker settings.

**Key Features:**
- Connection retry and reconnection handling
- Task acknowledgment after completion (reliability)
- Queue prioritization (celery, high_priority, low_priority)
- Broker health verification utilities

### 2. Tasks (`worker/tasks.py`)
All asynchronous task definitions:

| Task | Description | Schedule |
|------|-------------|----------|
| `process_upload_job` | Upload media to Instagram/TikTok | On-demand |
| `process_document` | PDF ingestion for RAG system | On-demand |
| `weekly_instagram_scrape` | Scrape competitor Instagram data | Weekly (Monday 1 AM) |
| `scrape_followers` | Collect follower counts | Daily (3 AM) |
| `ai_web_scrape` | AI-powered web content scraping | On-demand |
| `scrape_hashtag_trends` | TikTok trending hashtags | Twice daily |

### 3. Auto Dispatcher (`worker/auto_dispatch.py`)
Polls PostgreSQL for pending jobs and dispatches to Celery.

**Job Types:**
- Upload jobs (`upload_jobs` table)
- Document ingest jobs (`document_ingest_jobs` table)
- Cookie preparation (`group_items` table)
- Competitor scraping (`competitor_profiles` table)

### 4. Cookie Prep (`worker/cookie_prep.py`)
Automated social media login and session extraction.

**Supported Platforms:**
- ✅ Instagram (fully implemented)
- ⚠️ TikTok (placeholder - needs implementation)

### 5. Configuration (`worker/config.py`)
Environment variable management with validation.

## Environment Variables

### Required
| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql://root:secret@postgres:5432/project_monopoly` |
| `CELERY_BROKER_URL` | RabbitMQ connection URL | `amqp://guest:guest@rabbitmq:5672//` |

### Optional
| Variable | Description | Default |
|----------|-------------|---------|
| `CELERY_CONCURRENCY` | Worker process count | `4` |
| `DISPATCH_SLEEP` | Dispatcher poll interval (seconds) | `1.0` |
| `WEEKLY_SCRAPE_INTERVAL` | Days between scrapes | `7` |
| `START_FLOWER` | Enable Flower monitoring | `false` |
| `FLOWER_PORT` | Flower web UI port | `5555` |
| `SELENIUM_HEADLESS` | Run browser headless | `true` |
| `TZ` | Timezone for scheduling | `UTC` |

## Usage

### Starting All Services
```bash
# In Docker
docker-compose up python

# Directly
cd server/python
python run_all.py
```

### Manual Task Execution
```python
from worker.tasks import weekly_instagram_scrape

# Dispatch async task
result = weekly_instagram_scrape.delay()
print(f"Task ID: {result.id}")
```

### Health Checks
```python
from worker import verify_broker_connection, check_database_health

# Check RabbitMQ
if verify_broker_connection():
    print("Broker OK")

# Check PostgreSQL
status = check_database_health()
print(f"DB healthy: {status['healthy']}, latency: {status['latency_ms']}ms")
```

## Edge Cases Handled

### Connection Failures
- **Database**: Automatic reconnection with exponential backoff
- **RabbitMQ**: Retry on startup, periodic reconnection attempts
- **Selenium**: Graceful cleanup on browser crashes

### Task Failures
- **Retries**: Configurable retry count and delay per task
- **Time limits**: Soft and hard limits prevent runaway tasks
- **Dead letter**: Failed tasks preserved for debugging

### Concurrency
- **Row locking**: `FOR UPDATE SKIP LOCKED` prevents duplicate dispatch
- **Idempotency**: Tasks designed to be safe for retry
- **Rate limiting**: Adaptive sleep when queues are empty

## Monitoring

### Flower Dashboard
Enable Flower for web-based monitoring:
```bash
START_FLOWER=1 python run_all.py
# Access at http://localhost:5555
```

### Logs
All components log to stdout with structured format:
```
2025-12-27 17:00:00 INFO worker.tasks: ✅ Upload complete: job_id=123 files=1
```

### Health Endpoints
```python
from worker import get_broker_status, get_config_summary

# Broker status
status = get_broker_status()
# {'connected': True, 'broker_url': 'rabbitmq:5672//', 'queues': [...]}

# Config summary (safe for logging)
config = get_config_summary()
# {'database': {...}, 'rabbitmq': {...}, 'worker': {...}}
```

## File Structure
```
server/python/
├── run_all.py              # Service launcher
├── Dockerfile              # Container build
├── requirements.txt        # Python dependencies
└── worker/
    ├── __init__.py         # Package exports
    ├── celery_app.py       # Celery configuration
    ├── tasks.py            # Task definitions
    ├── db.py               # Database utilities
    ├── config.py           # Configuration
    ├── auto_dispatch.py    # Job dispatcher
    ├── cookie_prep.py      # Cookie extraction
    └── weekly_scheduler.py # Periodic schedules
```

## Troubleshooting

### "Connection refused" to RabbitMQ
1. Verify RabbitMQ container is running: `docker-compose ps rabbitmq`
2. Check connection URL: `echo $CELERY_BROKER_URL`
3. Test connectivity: `nc -zv rabbitmq 5672`

### Tasks not executing
1. Check worker is running: `docker-compose logs python`
2. Verify tasks are registered: `celery -A worker.celery_app inspect registered`
3. Check queue messages: RabbitMQ management UI at http://localhost:15672

### Cookie preparation failing
1. Check Chrome is installed: `google-chrome --version`
2. Verify headless mode works: `SELENIUM_HEADLESS=true python -c "from worker.cookie_prep import create_stealth_driver; d=create_stealth_driver(); d.quit()"`
3. Check Instagram login page structure hasn't changed

---
Last Updated: 2025-12-27
