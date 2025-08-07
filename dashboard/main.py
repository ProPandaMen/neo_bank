import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

import streamlit as st
import time


if "tasks" not in st.session_state:
    st.session_state["tasks"] = []
if "last_id" not in st.session_state:
    st.session_state["last_id"] = 0

TASK_STEPS = ["Подготовка", "Выполнение 1", "Выполнение 2", "Финал"]

def run_next_task():
    last_id = st.session_state["last_id"] + 1
    st.session_state["last_id"] = last_id
    task = {
        "id": last_id,
        "step": 0,
        "status": "running",
        "log": []
    }
    st.session_state["tasks"].append(task)

def advance_task(task):
    if task["step"] < len(TASK_STEPS) - 1:
        task["step"] += 1
        task["log"].append(f"{time.strftime('%X')}: Перешли к шагу '{TASK_STEPS[task['step']]}'")
        if task["step"] == len(TASK_STEPS) - 1:
            task["status"] = "done"
    else:
        task["status"] = "done"
        task["log"].append(f"{time.strftime('%X')}: Задача завершена!")

st.title("Мониторинг конвейера задач")

if (not st.session_state["tasks"]) or (st.session_state["tasks"][-1]["status"] == "done"):
    if st.button("Запустить новую задачу"):
        run_next_task()
else:
    st.info("Дождитесь завершения текущей задачи для запуска следующей.")

st.write("---")
st.write("### Список задач:")

for task in st.session_state["tasks"]:
    col1, col2, col3 = st.columns([1, 2, 2])
    col1.write(f"**Задача #{task['id']}**")
    col2.write(f"Статус: {task['status']}")
    col3.write(f"Шаг: {TASK_STEPS[task['step']]} ({task['step']+1} из {len(TASK_STEPS)})")

    if task["status"] != "done":
        if st.button(f"Перейти к следующему шагу задачи #{task['id']}", key=f"advance_{task['id']}"):
            advance_task(task)

    with st.expander(f"Лог задачи #{task['id']}"):
        if not task["log"]:
            st.write("Нет записей.")
        else:
            for entry in task["log"]:
                st.write(entry)

st.write("---")
done_count = sum(1 for t in st.session_state["tasks"] if t["status"] == "done")
st.success(f"Всего задач завершено: {done_count} из {len(st.session_state['tasks'])}")
