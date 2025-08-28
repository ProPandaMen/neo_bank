from database.models.task import Task, TaskLogs, StepStatus
from scheduler.celery_app import celery_app
from utils.task_logging import log_dashboard

import streamlit as st
import pandas as pd
import json
import time


UPDATE_INTERVAL = 5


def table_block(task_id: int):
    task = Task.get(id=task_id)
    if not task:
        return

    data = {
        "ID": task.id,
        "Время создания": str(task.created_at),
        "Текущий шаг": task.step_index,
        "Всего шагов": task.steps_total,
        "Статус": str(task.step_status),
        "Заблокировано кем": task.locked_by,
        "Заблокировано до": str(task.locked_until),
        "Начато в": str(task.step_started_at),
        "Попытки": task.step_attempts,
        "Следующая попытка": str(task.next_attempt_at),
        "Последняя ошибка": task.last_error,
    }

    df = pd.DataFrame(list(data.items()), columns=["Параметр", "Значение"])
    st.subheader(f"📋 Параметры задачи #{task.id}")
    st.dataframe(df, use_container_width=True, hide_index=True)


def button_block(task_id: int):
    task = Task.get(id=task_id)
    if not task:
        return
    
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🧹 Очистить логи", use_container_width=True):
            TaskLogs.delete_where(where=[TaskLogs.task_id == task_id])
            log_dashboard(task_id, "логи", "Очищены через дашборд")
            st.success("Логи очищены")

            st.rerun()

    with col2:
        if st.button("🔁 Перезапустить шаг", use_container_width=True):
            task.step_status = StepStatus.WAITING
            task.locked_by = None
            task.locked_until = None
            task.save()

            st.rerun()

    with col3:
        if st.button("⚠️ Перезапустить задачу", use_container_width=True):                    
            log_dashboard(task_id, "перезапуск", "Инициирован через дашборд")
            task.step_index = 0
            task.step_attempts = 0
            task.next_attempt_at = None
            task.last_error = None
            task.locked_by = None
            task.locked_until = None
            task.step_started_at = None
            task.step_status = StepStatus.WAITING
            task.save()

            st.rerun()


def render_task_details(task_id: int):
    cols = st.columns(2)
    if cols[0].button("← Все задачи"):
        st.query_params.pop("task_id", None)
        st.rerun()

    table_block(task_id)
    button_block(task_id)

    st.subheader(f"🧾 Логи задачи #{task_id}")

    ctrl = st.columns([2, 1])
    auto = ctrl[0].toggle("Автообновление", value=False)

    logs = TaskLogs.filter_ex(
        where=[TaskLogs.task_id == task_id],
        order_by=TaskLogs.created_at.desc(),
        limit=2000,
        offset=0,
    )

    def _fmt_source(s: str) -> str:
        return {
            "celery": "Celery ⚙️", 
            "task": "Task 📄", 
            "dashboard": "Dashboard 🖥️"
        }.get(s or "", s or "")

    rows = []
    for x in logs:
        try:
            obj = json.loads(x.description or "")
            rows.append({
                "Время": x.created_at,
                "Источник": _fmt_source(obj.get("source", "")),
                "Этап": obj.get("stage", ""),
                "Сообщение": obj.get("message", ""),
            })
        except Exception:
            rows.append({
                "Время": x.created_at,
                "Источник": "",
                "Этап": "",
                "Сообщение": x.description,
            })

    df = pd.DataFrame(rows)
    if df.empty:
        st.info("Логи отсутствуют")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

    if auto:
        time.sleep(UPDATE_INTERVAL)
        st.rerun()
