import os
# PostgreSQL database config
DB_CONFIG = {
    'dbname': 'project_monopoly',
    'user': 'root',
    'password': 'secret',
    'host': 'localhost',  # or your actual hostname
    'port': 5432,
    'sslmode': 'disable'
}

# RabbitMQ config for Celery
RABBITMQ_BROKER_URL = "amqp://guest:guest@rabbitmq:5672//"


# THIS: goes up TWO levels from /worker/config.py → /python → /server
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

