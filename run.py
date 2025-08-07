from database.base import init_db

import subprocess
import threading


def run_streamlit():
    subprocess.run([
        "streamlit", "run", "dashboard/main.py",
        "--server.port=8501",
        "--server.address=0.0.0.0"
    ])


if __name__ == "__main__":
    print("🔨 Инициализация базы данных...")
    init_db()
    print("🚀 Запуск Streamlit...")
    thread = threading.Thread(target=run_streamlit)
    thread.start()
    thread.join()