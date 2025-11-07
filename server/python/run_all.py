#!/usr/bin/env python3
import os, sys, time, socket, shutil, subprocess, signal

REPO_ROOT   = os.path.dirname(os.path.abspath(__file__))
BROKER_URL  = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
BACKEND_URL = os.getenv("CELERY_RESULT_BACKEND", BROKER_URL)
DATABASE_URL= os.getenv("DATABASE_URL", "postgresql://root:secret@localhost:5432/project_monopoly?sslmode=disable")
DOCS_DIR    = os.getenv("DOCS_DIR", os.path.join(REPO_ROOT, "data", "docs"))
CONCURRENCY = os.getenv("CELERY_CONCURRENCY", "4")
START_FLOWER= os.getenv("START_FLOWER", "1").lower() in ("1","true","yes","on")
FLOWER_PORT = os.getenv("FLOWER_PORT", "5555")

CELERY_APP  = "worker.celery_app"
DISPATCH_MOD= "worker.auto_dispatch"
BEAT_MOD    = "worker.weekly_scheduler"

def check_celery_available():
    """Check if celery is installed and available."""
    try:
        import importlib
        importlib.import_module("celery")
        return True
    except ImportError:
        return False

def wait_port(host, port, timeout=10):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with socket.create_connection((host, port), timeout=1): return True
        except OSError: time.sleep(0.2)
    return False

# Start redis if needed for broker/backend
def start_redis():
    if BROKER_URL.startswith("redis://") and not wait_port("127.0.0.1", 6379, 0.5):
        if shutil.which("redis-server") is None:
            print("redis-server not found"); sys.exit(1)
        print("🚀 starting redis")
        p = subprocess.Popen(["redis-server","--save","","--appendonly","no"])
        if not wait_port("127.0.0.1", 6379, 10):
            print("redis failed to bind 6379"); p.terminate(); sys.exit(1)
        return p
    print("ℹ️ redis available")
    return None

# Start celery worker for tasks
def start_celery_worker(env):
    if not check_celery_available():
        print("celery not installed; skipping celery worker")
        return None
    print(f"📦 starting celery x{CONCURRENCY}")
    return subprocess.Popen(
        [sys.executable,"-m","celery","-A",CELERY_APP,"worker","-Q","celery","-l","info","--concurrency",str(CONCURRENCY)],
        cwd=REPO_ROOT, env=env
    )

# Start dispatcher for new jobs
def start_dispatcher(env):
    if not check_celery_available():
        print("celery not installed; skipping dispatcher")
        return None
    print("🔁 starting dispatcher")
    return subprocess.Popen([sys.executable,"-m",DISPATCH_MOD], cwd=REPO_ROOT, env=env)

# Start flower for monitoring
def start_flower(env):
    if not START_FLOWER: return None
    if not check_celery_available():
        print("celery not installed; skipping flower")
        return None
    print(f"🌸 starting flower :{FLOWER_PORT}")
    return subprocess.Popen([sys.executable,"-m","celery","-A",CELERY_APP,"flower",f"--port={FLOWER_PORT}"], cwd=REPO_ROOT, env=env)

# Start beat scheduler for periodic tasks
def start_beat_scheduler(env):
    if not check_celery_available():
        print("celery not installed; skipping beat scheduler")
        return None
    print("starting beat scheduler")
    return subprocess.Popen([sys.executable,"-m","celery","-A",CELERY_APP,"beat","-l","info"], cwd=REPO_ROOT, env=env)

# Start weekly scraper on idle (runs immediately, then periodically)
def start_weekly_scraper_idle(env):
    print("starting weekly scraper (idle mode)")
    scraper_script = os.path.join(REPO_ROOT, "worker", "weekly_scraper_idle.py")
    return subprocess.Popen([sys.executable, scraper_script], cwd=REPO_ROOT, env=env)

# Terminate a subprocess if running
def kill(proc):
    if not proc: return
    try: proc.terminate()
    except Exception: pass

if __name__ == "__main__":
    os.chdir(REPO_ROOT)
    os.makedirs(DOCS_DIR, exist_ok=True)

    env = os.environ.copy()
    env.setdefault("CELERY_BROKER_URL", BROKER_URL)
    env.setdefault("CELERY_RESULT_BACKEND", BACKEND_URL)
    env.setdefault("DATABASE_URL", DATABASE_URL)
    env.setdefault("DOCS_DIR", DOCS_DIR)

    # init handles to avoid NameError
    redis_proc = worker = dispatcher = flower = beat = weekly_scraper = None

    try:
        redis_proc = start_redis()
        worker = start_celery_worker(env)
        dispatcher = start_dispatcher(env)
        beat = start_beat_scheduler(env)
        weekly_scraper = start_weekly_scraper_idle(env)
        flower = start_flower(env)

        print(f"\n✅ running. broker: {BROKER_URL}  docs: {DOCS_DIR}")
        if flower: print(f"   flower: http://localhost:{FLOWER_PORT}")
        print("Ctrl+C to stop.\n")

        while True:
            if worker and worker.poll() is not None:
                print("celery worker exited; restarting...")
                worker = start_celery_worker(env)
            if dispatcher and dispatcher.poll() is not None:
                print("dispatcher exited; restarting...")
                dispatcher = start_dispatcher(env)
            if beat and beat.poll() is not None:
                print("beat scheduler exited; restarting...")
                beat = start_beat_scheduler(env)
            if weekly_scraper and weekly_scraper.poll() is not None:
                print("weekly scraper exited; restarting...")
                weekly_scraper = start_weekly_scraper_idle(env)
            if flower and flower.poll() is not None:
                print("flower exited; continuing"); flower = None
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        for p in [flower, weekly_scraper, beat, dispatcher, worker, redis_proc]:
            kill(p)
