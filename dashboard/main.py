import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from database.manager.task import TaskManager

import streamlit as st
import pandas as pd


st.set_page_config(page_title="Дашборд задач", layout="wide")

tabs = st.tabs(["📋 Все задачи", "⚙️ Управление задачами"])

with tabs[0]:
    st.header("Все задачи")

    manager = TaskManager()

    if st.button("➕ Создать новую задачу"):
        new_task = manager.create_task()
        st.success(f"Задача создана! ID: {new_task.id}")

    tasks = manager.get_all_tasks()

    if tasks:
        data = [
            {
                "ID": task.id,
                "Дата создания": task.created_at.strftime("%Y-%m-%d %H:%M:%S") if task.created_at else "-",
            }
            for task in tasks
        ]
        df = pd.DataFrame(data)
        st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        st.info("Пока нет ни одной задачи.")

    manager.close()


with tabs[1]:
    st.header("Управление задачей")

    task_id = st.number_input("Введите ID задачи для управления", min_value=1, step=1)

    manager = TaskManager()
    task = manager.get_all_tasks()[0]

    if st.button("🔍 Найти задачу по ID"):
        task = manager.get_task_by_id(task_id)
        if task:
            st.success(f"ID: {task.id}, создана: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            st.error("Задача с таким ID не найдена.")
    
    if task:
        st.markdown("---")
        st.subheader(f"Управление задачей №{task.id}")

        if st.button("▶️ Запустить задачу №1"):
            st.info("Здесь будет логика запуска задачи №1")
        if st.button("🔄 Перезапустить задачу №1"):
            st.info("Здесь будет логика перезапуска задачи №1")

    manager.close()
