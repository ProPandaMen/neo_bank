import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from scheduler.app import celery
from celery.result import AsyncResult

import streamlit as st


st.set_page_config(page_title="Мониторинг задач", layout="wide")
st.title("📊 Все запущенные процессы")

i = celery.control.inspect()

active_tasks = i.active() or {}
reserved_tasks = i.reserved() or {}
scheduled_tasks = i.scheduled() or {}

rows = []

def append_tasks(state_name, task_list):
    for worker, tasks in (task_list or {}).items():
        for t in tasks:
            task_id = t.get("id") or t.get("request", {}).get("id")
            name = t.get("name") or t.get("request", {}).get("name")
            args = t.get("args") or t.get("request", {}).get("args")
            kwargs = t.get("kwargs") or t.get("request", {}).get("kwargs")
            rows.append({
                "Worker": worker,
                "Task ID": task_id,
                "Name": name,
                "Args": args,
                "Kwargs": kwargs,
                "State": state_name
            })

append_tasks("Active", active_tasks)
append_tasks("Reserved", reserved_tasks)
append_tasks("Scheduled", scheduled_tasks)

st.subheader("Текущие задачи")
st.dataframe(rows, use_container_width=True)

st.subheader("Проверить результат задачи")
task_id = st.text_input("Task ID")
if task_id:
    res = AsyncResult(task_id, app=celery)
    st.write({
        "ID": task_id,
        "Status": res.status,
        "Result": res.result
    })
