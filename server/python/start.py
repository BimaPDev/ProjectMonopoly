import subprocess, time, os, sys, shutil, socket

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
WORKER_APP = "worker.celery_app"
CONCURRENCY = int(os.getenv("CELERY_CONCURRENCY", "4"))

def wait_port(host, port, timeout=10):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with socket.create_connection((host, port), timeout=1): return True
        except OSError:
            time.sleep(0.2)
    return False

def start_redis():
    if shutil.which("redis-server") is None:
        print("❌ redis-server not found")
        sys.exit(1)
    print("🚀 Starting Redis...")
    p = subprocess.Popen(["redis-server", "--save", "", "--appendonly", "no"])
    if not wait_port("127.0.0.1", 6379, 10):
        print("❌ Redis failed to bind 6379")
        sys.exit(1)
    return p

def start_celery_worker(name):
    print(f"📦 Celery {name} x{CONCURRENCY}")
    env = os.environ.copy()
    env.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/0")
    env.setdefault("CELERY_RESULT_BACKEND", env["CELERY_BROKER_URL"])
    return subprocess.Popen(
        ["celery", "-A", WORKER_APP, "worker", "-n", name, "-Q", "celery", "-l", "info",
         "--concurrency", str(CONCURRENCY)],
        cwd=PROJECT_ROOT, env=env
    )

def start_dispatcher():
    print("🔁 Dispatcher")
    return subprocess.Popen([sys.executable, "-m", "worker.auto_dispatch"], cwd=PROJECT_ROOT, env=os.environ.copy())

def start_flower():
    print("🌸 Flower http://localhost:5555")
    env = os.environ.copy()
    env.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/0")
    return subprocess.Popen(["celery", "-A", WORKER_APP, "flower", "--port", "5555"], cwd=PROJECT_ROOT, env=env)

if __name__ == "__main__":
    os.chdir(PROJECT_ROOT)
    r = start_redis()
    w1 = start_celery_worker("worker1@%h")
    w2 = start_celery_worker("worker2@%h")
    disp = start_dispatcher()
    flow = start_flower()
    print("\n✅ Running. Flower at http://localhost:5555\n")
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Stopping...")
        for p in [w1, w2, disp, flow, r]:
            try: p.terminate()
            except Exception: pass
        sys.exit(0)
