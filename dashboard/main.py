import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from mts_manager.main import MTSTask

import streamlit as st
import threading
import time


TASKS = {}

def start_new_task(task_id):
    task = MTSTask(task_id)
    TASKS[task_id] = task
    thread = threading.Thread(target=task.run)
    thread.start()



st.title("Монитор задач")


if st.button("Запустить новую задачу"):
    new_id = f"task-{int(time.time())}"
    start_new_task(new_id)
    st.success(f"Задача {new_id} запущена!")

st.write("## Статусы задач:")

for task_id, task in TASKS.items():
    st.write(f"**{task_id}**: {task.stage.value} (успешно: {task.success})")

