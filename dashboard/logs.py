import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from database.models.task import Task, TaskLogs

import streamlit as st
import pandas as pd

st.title("📝 Логи")

task_id = st.query_params.get("task_id")

if not task_id:
    task_ids = [t.id for t in Task.all()]

    selected_id = st.selectbox(
        "Выбер ID задачи",
        task_ids,
    )

    if st.button("Подтвердить"):
        st.query_params["task_id"] = str(selected_id)
        st.rerun()
else:    
    if st.button("⬅️ Назад"):
        if "task_id" in st.query_params:
            del st.query_params["task_id"]
        st.rerun()

    task_logs = TaskLogs.filter(task_id=task_id)
    if not task_logs:
        st.info("Пока нет логов.")
    else:
        rows = []
        for t in task_logs:
            rows.append({
                "Дата создания": t.created_at.strftime("%Y-%m-%d %H:%M:%S") if t.created_at else "-",
                "Описание": t.description or "-",
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, hide_index=True, use_container_width=True)
