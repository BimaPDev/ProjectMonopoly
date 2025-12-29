#!/usr/bin/env python3
"""
Run All Services
================

Main entry point for the ProjectMonopoly Python worker container.
Starts and manages all background services.

Author: ProjectMonopoly Team
Last Updated: 2025-12-27
"""

import os
import sys
import time
import socket
import subprocess
from dotenv import load_dotenv

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(REPO_ROOT, "..", ".env"))

BROKER_URL = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@rabbitmq:5672//")
BACKEND_URL = os.getenv("CELERY_RESULT_BACKEND", "rpc://")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://root:secret@postgres:5432/project_monopoly?sslmode=disable"
)
DOCS_DIR = os.getenv("DOCS_DIR", "/data/docs")
CONCURRENCY = os.getenv("CELERY_CONCURRENCY", "4")
START_FLOWER = os.getenv("START_FLOWER", "0").lower() in ("1", "true", "yes", "on")
FLOWER_PORT = os.getenv("FLOWER_PORT", "5555")

# absolute module paths so running as a script works
CELERY_APP = "worker.celery_app"
DISPATCH_MOD = "worker.auto_dispatch"

def wait_port(host, port, timeout=10):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.2)
    return False

def wait_for_deps():
    if not wait_port("rabbitmq", 5672, 30):
        raise RuntimeError("rabbitmq not reachable")
    if not wait_port("postgres", 5432, 30):
        raise RuntimeError("postgres not reachable")

def start_celery_worker(env):
    print(f"starting celery worker x{CONCURRENCY}")
    return subprocess.Popen(
        [
            sys.executable, "-m", "celery",
            "-A", CELERY_APP, "worker",
            "-Q", "celery",
            "-l", "info",
            "--concurrency", str(CONCURRENCY),
        ],
        cwd=REPO_ROOT, env=env
    )

def start_dispatcher(env):
    print("starting dispatcher")
    return subprocess.Popen(
        [sys.executable, "-m", DISPATCH_MOD],
        cwd=REPO_ROOT, env=env
    )

def start_beat(env):
    print("starting beat")
    return subprocess.Popen(
        [
            sys.executable, "-m", "celery",
            "-A", CELERY_APP, "beat",
            "-l", "info",
            "--schedule", "/tmp/celerybeat-schedule.db",
        ],
        cwd=REPO_ROOT, env=env
    )

def start_flower(env):
    if not START_FLOWER:
        return None
    print(f"starting flower :{FLOWER_PORT}")
    return subprocess.Popen(
        [
            sys.executable, "-m", "celery",
            "-A", CELERY_APP, "flower",
            f"--port={FLOWER_PORT}",
        ],
        cwd=REPO_ROOT, env=env
    )

def kill(proc):
    if not proc:
        return
    try:
        proc.terminate()
    except Exception:
        pass

if __name__ == "__main__":
    os.chdir(REPO_ROOT)
    os.makedirs(DOCS_DIR, exist_ok=True)

    env = os.environ.copy()
    env["CELERY_BROKER_URL"] = BROKER_URL
    env["CELERY_RESULT_BACKEND"] = BACKEND_URL
    env["DATABASE_URL"] = DATABASE_URL
    env["DOCS_DIR"] = DOCS_DIR
    env["C_FORCE_ROOT"] = "1" # Allow Celery to run as root

    procs = []
    try:
        wait_for_deps()

        worker = start_celery_worker(env); procs.append(worker)
        dispatcher = start_dispatcher(env); procs.append(dispatcher)
        beat = start_beat(env); procs.append(beat)
        flower = start_flower(env)
        if flower:
            procs.append(flower)

        print(f"running. broker={BROKER_URL} docs={DOCS_DIR}")

        while True:
            for p in procs:
                if p.poll() is not None:
                    raise RuntimeError("a subprocess exited")
            time.sleep(1)

    except KeyboardInterrupt:
        pass
    finally:
        for p in reversed(procs):
            kill(p)
