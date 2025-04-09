# PostgreSQL database config
DB_CONFIG = {
    'dbname': 'project_monopoly',
    'user': 'root',
    'password': 'secret',
    'host': 'localhost',  # or your actual hostname
    'port': 5432,
    'sslmode': 'disable'
}

# Redis config for Celery
REDIS_BROKER_URL = "redis://localhost:6379/0"
REDIS_BACKEND_URL = "redis://localhost:6379/1"
