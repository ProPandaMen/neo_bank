import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from database.manager.task import TaskManager

import streamlit as st
import pandas as pd


st.set_page_config(page_title="Дашборд задач", layout="wide")

tabs = st.tabs(["📋 Все задачи"])

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
