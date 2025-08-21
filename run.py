from database.base import init_db

import subprocess
import argparse
import atexit
import signal
import time
import sys
import os


procs = []
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

def spawn(cmd):
    p = subprocess.Popen(cmd, start_new_session=True, cwd=PROJECT_ROOT, env={**os.environ, "PYTHONPATH": PROJECT_ROOT + os.pathsep + os.environ.get("PYTHONPATH","")})
    procs.append(p)
    
    return p

def stop_all():
    for p in procs[::-1]:
        try:
            if p.poll() is None:
                os.killpg(p.pid, signal.SIGTERM)
        except Exception:
            pass

def run_dashboard():
    spawn([sys.executable, "-m", "streamlit", "run", "dashboard/app.py", "--server.port=8501"])

def run_celery():
    spawn([sys.executable, "-m", "celery", "-A", "scheduler.celery_app:celery_app", "worker", "-Q", "executor", "-n", "executor@%h", "-c", "1", "--prefetch-multiplier=1"])
    spawn([sys.executable, "-m", "celery", "-A", "scheduler.celery_app:celery_app", "worker", "-Q", "scheduler", "-n", "scheduler@%h", "-c", "1"])
    spawn([sys.executable, "-m", "celery", "-A", "scheduler.celery_app:celery_app", "beat"])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dashboard", action="store_true")
    parser.add_argument("--celery", action="store_true")
    args = parser.parse_args()

    selected_dashboard = args.dashboard or (not args.dashboard and not args.celery)
    selected_celery = args.celery or (not args.dashboard and not args.celery)

    print("🔨 Инициализация БД...")
    init_db()
    print("🚀 Старт сервисов...")
    if selected_dashboard:
        run_dashboard()
    if selected_celery:
        run_celery()
    try:
        while True:
            time.sleep(1)
            for p in procs:
                if p.poll() is not None:
                    raise SystemExit(1)
    except KeyboardInterrupt:
        pass
    finally:
        print("🛑 Остановка...")
        stop_all()

if __name__ == "__main__":
    atexit.register(stop_all)
    main()
