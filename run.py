from database.base import init_db

import os
import sys
import time
import atexit
import signal
import subprocess


procs = []

def spawn(cmd):
    p = subprocess.Popen(cmd, start_new_session=True)
    procs.append(p)
    return p

def stop_all():
    for p in procs[::-1]:
        try:
            if p.poll() is None:
                os.killpg(p.pid, signal.SIGTERM)
        except Exception:
            pass


def main():
    print("🔨 Инициализация БД...")
    init_db()
    print("🚀 Старт сервисов...")
    spawn([sys.executable, "-m", "streamlit", "run", "dashboard/app.py", "--server.port=8501"])
    spawn([sys.executable, "-m", "celery", "-A", "scheduler.app:celery_app", "worker", "-Q", "executor", "-n", "executor@%h", "-c", "1", "--prefetch-multiplier=1"])
    spawn([sys.executable, "-m", "celery", "-A", "scheduler.app:celery_app", "worker", "-Q", "scheduler", "-n", "scheduler@%h", "-c", "1"])
    spawn([sys.executable, "-m", "celery", "-A", "scheduler.app:celery_app", "beat"])
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