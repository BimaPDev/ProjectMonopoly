#!/usr/bin/env python3
import os, sys, time, socket, shutil, subprocess, signal

REPO_ROOT   = os.path.dirname(os.path.abspath(__file__))
BROKER_URL  = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
BACKEND_URL = os.getenv("CELERY_RESULT_BACKEND", BROKER_URL)
DATABASE_URL= os.getenv("DATABASE_URL", "postgresql://root:secret@localhost:5432/project_monopoly?sslmode=disable")
DOCS_DIR    = os.getenv("DOCS_DIR", os.path.join(REPO_ROOT, "data", "docs"))
CONCURRENCY = os.getenv("CELERY_CONCURRENCY", "4")
START_FLOWER= os.getenv("START_FLOWER", "0").lower() in ("1","true","yes","on")
FLOWER_PORT = os.getenv("FLOWER_PORT", "5555")

CELERY_APP  = "worker.celery_app"
DISPATCH_MOD= "worker.auto_dispatch"

def wait_port(host, port, timeout=10):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with socket.create_connection((host, port), timeout=1): return True
        except OSError: time.sleep(0.2)
    return False

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

def start_celery_worker(env):
    print(f"📦 starting celery x{CONCURRENCY}")
    return subprocess.Popen(
        ["celery","-A",CELERY_APP,"worker","-Q","celery","-l","info","--concurrency",str(CONCURRENCY)],
        cwd=REPO_ROOT, env=env
    )

def start_dispatcher(env):
    print("🔁 starting dispatcher")
    return subprocess.Popen([sys.executable,"-m",DISPATCH_MOD], cwd=REPO_ROOT, env=env)

def start_flower(env):
    if not START_FLOWER: return None
    print(f"🌸 starting flower :{FLOWER_PORT}")
    return subprocess.Popen(["celery","-A",CELERY_APP,"flower",f"--port={FLOWER_PORT}"], cwd=REPO_ROOT, env=env)

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
    redis_proc = worker = dispatcher = flower = None

    try:
        redis_proc = start_redis()
        worker = start_celery_worker(env)
        dispatcher = start_dispatcher(env)
        flower = start_flower(env)

        print(f"\n✅ running. broker: {BROKER_URL}  docs: {DOCS_DIR}")
        if flower: print(f"   flower: http://localhost:{FLOWER_PORT}")
        print("Ctrl+C to stop.\n")

        while True:
            if worker and worker.poll() is not None:
                raise RuntimeError("celery worker exited")
            if dispatcher and dispatcher.poll() is not None:
                raise RuntimeError("dispatcher exited")
            if flower and flower.poll() is not None:
                print("flower exited; continuing"); flower = None
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        for p in [flower, dispatcher, worker, redis_proc]:
            kill(p)
