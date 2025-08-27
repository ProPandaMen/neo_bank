from database.models.task import Task, TaskLogs, StepStatus
from scheduler.celery_app import celery_app

import streamlit as st
import pandas as pd
import datetime

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
    tasks = Task.all()
    if not tasks:
        st.info("Пока нет данных")
        return
    data = []
    for t in tasks:
        pct = 0 if (t.steps_total or 0) == 0 else int(round((min(t.step_index + 1, t.steps_total) / max(t.steps_total, 1)) * 100))
        data.append({
            "ID": t.id,
            "Создано": t.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "Шаг": f"{t.step_index + 1}/{t.steps_total}",
            "Прогресс": f"{pct}%",
            "Статус": status_map.get(t.step_status, ""),
            "Подробнее": f"[Открыть](?task_id={t.id})",
        })
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_task_details(task_id: int):
    cols = st.columns(2)
    if cols[0].button("← Все задачи"):
        st.query_params.pop("task_id", None)
        st.rerun()
    act_cols = st.columns(2)
    if act_cols[0].button("🧹 Очистить логи"):
        TaskLogs.delete_where(where=[TaskLogs.task_id == task_id])
        TaskLogs.create(task_id=task_id, description="logs clear")
        st.success("Логи очищены")
        st.rerun()
    if act_cols[1].button("🔁 Перезапустить задачу"):
        tt = Task.get(id=task_id)
        if tt:
            tt.step_index = 0
            tt.step_attempts = 0
            tt.next_attempt_at = None
            tt.last_error = None
            tt.locked_by = None
            tt.locked_until = None
            tt.step_started_at = None
            tt.step_status = StepStatus.WAITING
            tt.save()
            TaskLogs.create(task_id=tt.id, description="Restart task")
            try:
                celery_app.send_task("scheduler.task_execute", args=[tt.id], queue="executor")
                st.success(f"Задача #{tt.id} перезапущена")
            except Exception as e:
                TaskLogs.create(task_id=tt.id, description=f"restart error: {e}")
                st.error(f"Ошибка перезапуска: {e}")
            st.rerun()
        else:
            st.error("Задача не найдена")
    st.subheader(f"🧾 Логи задачи #{task_id}")
    logs = TaskLogs.filter_ex(
        where=[TaskLogs.task_id == task_id],
        order_by=TaskLogs.created_at.desc(),
        limit=2000,
        offset=0,
    )
    ldf = pd.DataFrame([{"Время": x.created_at, "Сообщение": x.description} for x in logs])
    if ldf.empty:
        st.info("Логи отсутствуют")
    else:
        st.dataframe(ldf, use_container_width=True, hide_index=True, height=600)

def main():
    task_id = get_selected_task_id()
    render_title(task_id)
    if task_id:
        render_task_details(task_id)
    else:
        render_tasks_table()

main()
