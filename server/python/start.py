import subprocess
import time
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
WORKER_APP = "worker.celery_app"

# Number of concurrent workers (scale this based on your CPU)
CONCURRENCY = 4

def start_redis():
    print("🚀 Starting Redis server...")
    try:
        subprocess.Popen(["redis-server"])
        time.sleep(2)
    except FileNotFoundError:
        print("❌ Redis not found. Make sure it's installed and in your PATH.")
        sys.exit(1)

def start_celery_worker(name, concurrency=CONCURRENCY):
    print(f"📦 Starting Celery worker: {name} (concurrency={concurrency})")
    return subprocess.Popen([
        "celery",
        "-A", WORKER_APP,
        "worker",
        "-n", name,
        "--loglevel=info",
        f"--concurrency={concurrency}"
    ], cwd=PROJECT_ROOT)

def start_dispatcher():
    print("🔁 Starting auto-dispatcher loop...")
    return subprocess.Popen([
        sys.executable,
        "-m", "worker.auto_dispatch"
    ], cwd=PROJECT_ROOT)

def start_flower():
    print("🌸 Starting Flower (monitoring dashboard)...")
    return subprocess.Popen([
        "celery",
        "-A", WORKER_APP,
        "flower",
        "--port=5555"
    ], cwd=PROJECT_ROOT)

if __name__ == "__main__":
    os.chdir(PROJECT_ROOT)

    start_redis()
    worker1 = start_celery_worker("worker1@%h")
    worker2 = start_celery_worker("worker2@%h")
    dispatcher_proc = start_dispatcher()
    flower_proc = start_flower()

    print("\n✅ All systems running. Visit Flower at http://localhost:5555")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        for proc in [worker1, worker2, dispatcher_proc, flower_proc]:
            proc.terminate()
        sys.exit(0)
