from database.models.task import Task, TaskLogs, StepStatus
from utils.task_logging import log_dashboard

from config import SCREENSHOT_DIR
from pathlib import Path
from datetime import datetime
from PIL import Image

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

    root = Path(SCREENSHOT_DIR) / str(task_id)
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    files = sorted([p for p in root.glob("*") if p.suffix.lower() in exts],
                   key=lambda p: p.stat().st_mtime,
                   reverse=True)

    st.subheader("🖼 Скриншоты задачи")
    if not files:
        st.info("Скриншотов пока нет")
        return

    key_idx = f"shot_idx_{task_id}"
    if key_idx not in st.session_state:
        st.session_state[key_idx] = 0

    n = len(files)
    i = st.session_state[key_idx] % n
    p = files[i]

    text1, text2, text3 = st.columns(3)
    with text1:
        # 1. Общее количество
        st.markdown(f"**Всего скриншотов: {n}**")
    with text2:
        # 2. Текущий номер
        st.markdown(f"**Скриншот №{i+1}**")
    with text3:
        # 3. Изображение
        ts = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        st.caption(f"Создан: {ts}")
        
    st.image(Image.open(p), use_container_width=True)

    # 4. Кнопки
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("←", use_container_width=True, key=f"prev_{task_id}"):
            st.session_state[key_idx] = (i - 1) % n
            st.rerun()
    with c2:
        if st.button("🔍 Увеличить", use_container_width=True, key=f"zoom_{task_id}"):
            @st.dialog(f"Просмотр: {p.name}", width="large")
            def _dlg():
                st.image(Image.open(p), use_container_width=True)
            _dlg()
    with c3:
        if st.button("→", use_container_width=True, key=f"next_{task_id}"):
            st.session_state[key_idx] = (i + 1) % n
            st.rerun()


def render_task_details(task_id: int):
    cols = st.columns(2)
    if cols[0].button("← Все задачи"):
        st.query_params.pop("task_id", None)
        st.rerun()

    table_block(task_id)
    button_block(task_id)
    logs_block(task_id)
    screenshot_block(task_id)
