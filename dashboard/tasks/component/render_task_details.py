from database.models.task import Task, TaskLogs, StepStatus
from scheduler.celery_app import celery_app
from utils.task_logging import log_dashboard

import streamlit as st
import pandas as pd
import json
import time


UPDATE_INTERVAL = 5


def render_task_details(task_id: int):
    cols = st.columns(2)
    if cols[0].button("← Все задачи"):
        st.query_params.pop("task_id", None)
        st.rerun()

    act_cols = st.columns(2)
    if act_cols[0].button("🧹 Очистить логи"):
        TaskLogs.delete_where(where=[TaskLogs.task_id == task_id])
        log_dashboard(task_id, "логи", "Очищены через дашборд")
        st.success("Логи очищены")
        st.rerun()

    if act_cols[1].button("🔁 Перезапустить задачу"):
        tt = Task.get(id=task_id)
        if tt:
            log_dashboard(task_id, "перезапуск", "Инициирован через дашборд")
            tt.step_index = 0
            tt.step_attempts = 0
            tt.next_attempt_at = None
            tt.last_error = None
            tt.locked_by = None
            tt.locked_until = None
            tt.step_started_at = None
            tt.step_status = StepStatus.WAITING
            tt.save()
            
            try:
                celery_app.send_task("scheduler.task_execute", args=[tt.id], queue="executor")                
                log_dashboard(task_id, "перезапуск", "Отправлен в очередь executor")

                st.success(f"Задача #{tt.id} перезапущена")
            except Exception as e:
                log_dashboard(task_id, "перезапуск", f"Ошибка отправки: {e}")
                st.error(f"Ошибка перезапуска: {e}")
            st.rerun()
        else:
            st.error("Задача не найдена")

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
