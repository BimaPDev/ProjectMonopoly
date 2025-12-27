import os

# PostgreSQL database config - uses env vars for Docker compatibility
# In docker-compose, DB_HOST should be 'db' (the service name)
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'project_monopoly'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'secret'),
    'host': os.getenv('DB_HOST', 'db'),  # Default to 'db' for docker-compose
    'port': int(os.getenv('DB_PORT', '5432')),
    'sslmode': os.getenv('DB_SSLMODE', 'disable')
}

# RabbitMQ config for Celery - uses env var for flexibility
RABBITMQ_BROKER_URL = os.getenv(
    'CELERY_BROKER_URL',
    'amqp://guest:guest@rabbitmq:5672//'
)

# THIS: goes up TWO levels from /worker/config.py -> /python -> /server
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

UPLOADS_DIR = os.getenv('UPLOADS_DIR', os.path.join(BASE_DIR, "uploads"))

