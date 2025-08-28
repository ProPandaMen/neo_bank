from database.models.task import Task, TaskLogs, StepStatus
from utils.task_logging import log_dashboard

from config import SCREENSHOT_DIR
from pathlib import Path
from datetime import datetime
from PIL import Image

import streamlit as st
import pandas as pd
import math
import json
import time


UPDATE_INTERVAL = 5


def table_block(task_id: int):
    task = Task.get(id=task_id)
    if not task:
        return

    data = {
        "ID": task.id,
        "Время создания": task.created_at,
        "Текущий шаг": task.step_index,
        "Всего шагов": task.steps_total,
        "Статус": task.step_status,
        "Заблокировано кем": task.locked_by,
        "Заблокировано до": task.locked_until,
        "Начато в": task.step_started_at,
        "Попытки": task.step_attempts,
        "Следующая попытка": task.next_attempt_at,
        "Последняя ошибка": task.last_error,
    }

    df = pd.DataFrame(list(data.items()), columns=["Параметр", "Значение"])
    df["Значение"] = df["Значение"].apply(lambda x: "" if x is None else str(x))

    st.subheader("📋 Параметры задачи")
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


def logs_block(task_id: int):
    task = Task.get(id=task_id)
    if not task:
        return
    
    st.subheader(f"🧾 Логи задачи")

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


def screenshot_block(task_id: int):
    task = Task.get(id=task_id)
    if not task:
        return
    
    st.subheader(f"🖼 Скриншоты задачи")
    
    root = Path(SCREENSHOT_DIR) / str(task_id)
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    files = [p for p in root.glob("*") if p.suffix.lower() in exts]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    if not files:
        st.info("Скриншотов пока нет")
        return

    col_ctrl = st.columns([1,1,2,2])
    with col_ctrl[0]:
        per_page = st.selectbox("На странице", [8, 12, 24, 48], index=1)
    with col_ctrl[1]:
        grid_cols = st.selectbox("В ряд", [2, 3, 4], index=2)
    total = len(files)
    pages = max(1, math.ceil(total / per_page))
    with col_ctrl[2]:
        st.write(f"Найдено: {total}")
    with col_ctrl[3]:
        page = st.number_input("Страница", min_value=1, max_value=pages, value=1)

    start = (page - 1) * per_page
    chunk = files[start:start + per_page]

    cols = st.columns(grid_cols)
    for i, p in enumerate(chunk):
        with cols[i % grid_cols]:
            ts = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            st.caption(f"{p.name} · {ts}")
            img = Image.open(p)
            st.image(img, use_container_width=True)
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("Скачать", data=p.read_bytes(), file_name=p.name, mime="image/png")
            with c2:
                if st.button("Открыть", key=f"open_{p.name}"):
                    st.session_state["shot_preview"] = str(p)

    if "shot_preview" in st.session_state:
        p = Path(st.session_state["shot_preview"])
        if p.exists():
            st.markdown("---")
            st.subheader(f"Предпросмотр: {p.name}")
            st.image(Image.open(p), use_container_width=True)


def render_task_details(task_id: int):
    cols = st.columns(2)
    if cols[0].button("← Все задачи"):
        st.query_params.pop("task_id", None)
        st.rerun()

    table_block(task_id)
    button_block(task_id)
    logs_block(task_id)
    screenshot_block(task_id)
