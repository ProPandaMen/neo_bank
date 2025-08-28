from database.models.task import Task, StepStatus
from dashboard.tasks.component.render_task_details import render_task_details

import streamlit as st
import pandas as pd


st.set_page_config(page_title="Задачи", layout="wide")

status_map = {
    StepStatus.WAITING: "🟡 Ожидание",
    StepStatus.RUNNING: "🟠 В работе",
    StepStatus.ERROR: "🔴 Ошибка",
    StepStatus.SUCCESS: "🟢 Успешно"
}

def get_selected_task_id():
    v = st.query_params.get("task_id")

    return int(v) if v else None

def render_title(task_id: int | None):
    if task_id:
        st.title(f"📋 Задача #{task_id}")
    else:
        st.title("📋 Задачи")

def render_tasks_table():
    tasks_list = Task.all()

    if not tasks_list:
        st.info("Пока нет данных")
        return

    data = []
    for task in tasks_list:
        data.append({
            "ID": task.id,
            "Создано": task.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "Шаг": f"{task.step_index + 1}/{task.steps_total}",
            "Статус": status_map.get(task.step_status, ""),
            "Подробнее": f"/tasks_table?task_id={task.id}",
        })

    df = pd.DataFrame(data)

    st.data_editor(
        df,
        column_config={
            "Подробнее": st.column_config.LinkColumn(
                "Подробнее",
                display_text="Открыть"
            )
        },
        hide_index=True,
        use_container_width=True,
        disabled=True,
    )


def main():
    task_id = get_selected_task_id()
    render_title(task_id)

    if task_id:
        render_task_details(task_id)
    else:
        render_tasks_table()

main()
