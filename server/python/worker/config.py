import os
from urllib.parse import urlparse

# PostgreSQL database config - parse DATABASE_URL if available (Docker), otherwise use defaults (local dev)
_db_url = os.environ.get('DATABASE_URL', '')
if _db_url:
    _parsed = urlparse(_db_url)
    DB_CONFIG = {
        'dbname': _parsed.path.lstrip('/'),
        'user': _parsed.username or 'root',
        'password': _parsed.password or 'secret',
        'host': _parsed.hostname or 'postgres',
        'port': _parsed.port or 5432,
    }
else:
    DB_CONFIG = {
        'dbname': 'project_monopoly',
        'user': 'root',
        'password': 'secret',
        'host': 'localhost',  # Local development
        'port': 5432,
    }

# RabbitMQ config for Celery
RABBITMQ_BROKER_URL = "amqp://guest:guest@rabbitmq:5672//"


# THIS: goes up TWO levels from /worker/config.py → /python → /server
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

