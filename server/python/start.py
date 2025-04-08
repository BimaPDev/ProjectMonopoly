import subprocess
import time
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
WORKER_APP = "worker.celery_app"  # Assuming celery_app.py is inside worker/

def start_redis():
    print("🚀 Starting Redis server...")
    try:
        subprocess.Popen(["redis-server"])
        time.sleep(2)
    except FileNotFoundError:
        print("❌ Redis not found. Make sure it's installed and in your PATH.")
        sys.exit(1)

def start_celery_worker():
    print("📦 Starting Celery worker...")
    return subprocess.Popen([
        "celery",
        "-A", WORKER_APP,
        "worker",
        "--loglevel=info"
    ], cwd=PROJECT_ROOT)

def start_dispatcher():
    print("🔁 Starting auto-dispatcher loop...")
    return subprocess.Popen([
        sys.executable,
        "-m", "worker.auto_dispatch"
    ], cwd=PROJECT_ROOT)

if __name__ == "__main__":
    os.chdir(PROJECT_ROOT)

    start_redis()
    celery_proc = start_celery_worker()
    dispatcher_proc = start_dispatcher()

    print("✅ All systems running. Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        dispatcher_proc.terminate()
        celery_proc.terminate()
        sys.exit(0)
