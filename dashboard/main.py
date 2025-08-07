import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from database.manager.task import TaskManager

import streamlit as st
import pandas as pd


st.set_page_config(page_title="Дашборд задач", layout="wide")
st.header("📋 Все задачи")

manager = TaskManager()
tasks = manager.get_all_tasks()

if tasks:
    data = [
        {
            "ID": task.id,
            "Дата создания": task.created_at.strftime("%Y-%m-%d %H:%M:%S") if task.created_at else "-",
            "Статус": task.status.value if task.status else "-",
            "GoLogin Profile": task.gologin_profile_id or "-",
            "Телефон": task.phone_number or "-",
        }
        for task in tasks
    ]
    df = pd.DataFrame(data)
    st.dataframe(df, hide_index=True, use_container_width=True)
else:
    st.info("Пока нет ни одной задачи.")

manager.close()
