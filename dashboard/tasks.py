import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from database.models.task import Task
import streamlit as st
import pandas as pd


st.title("📋 Задачи")

col1, col2 = st.columns([1, 1])

with col1:
    if st.button("➕ Создать задачу"):
        task = Task.create()
        st.success(f"Задача #{task.id} создана")
        st.rerun()

with col2:
    if st.button("🔄 Обновить"):
        st.rerun()

tasks = Task.all()

if not tasks:
    st.info("Пока нет задач.")
else:
    rows = []
    for t in tasks:
        rows.append({
            "ID": t.id,
            "Дата создания": t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else "-",
            "Статус": t.status.value if t.status else "-",
            "GoLogin Profile": t.gologin_profile_id or "-",
            "Телефон": t.phone_number or "-",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True, use_container_width=True)
    