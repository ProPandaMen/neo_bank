import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from database.models.task import Task

import streamlit as st
import threading
import importlib

background_tasks = []

def run_script(module_name, task_id):
    try:
        module = importlib.import_module(module_name)
        module.start(task_id)
    except Exception as e:
        print(f"Ошибка в задаче: {e}")

st.title("🚀 Запуск скриптов")

tasks = Task.all()
if not tasks:
    st.info("Пока нет задач.")
    st.stop()

task_ids = [t.id for t in tasks]
selected_id = st.selectbox("Выберите ID задачи", task_ids)

script = st.selectbox(
    "Выберите скрипт",
    [
        ("mts_manager.1_step", "Шаг 1"),
        ("mts_manager.2_step", "Шаг 2")
        ("mts_manager.3_step", "Шаг 3")
    ],
    format_func=lambda x: x[1]
)

if st.button("▶️ Запустить в фоне"):
    t = threading.Thread(target=run_script, args=(script[0], selected_id))
    t.start()
    background_tasks.append(t)
    st.success(f"Скрипт {script[0]} для задачи #{selected_id} запущен в фоне")
