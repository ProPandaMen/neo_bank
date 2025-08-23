import sys, os, datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd
from sqlalchemy import and_
from database.models.task import Task, TaskLogs, StepStatus

st.set_page_config(page_title="Задачи", layout="wide")
st.title("📋 Задачи")

def mask_card(v):
    if not v:
        return ""
    v = v.replace(" ", "")
    return ("*" * (len(v) - 4)) + v[-4:]

status_map = {StepStatus.WAITING: "🟡 Ожидание", StepStatus.RUNNING: "🟠 В работе", StepStatus.ERROR: "🔴 Ошибка", StepStatus.SUCCESS: "🟢 Успешно"}

with st.sidebar:
    st.subheader("Фильтры")
    statuses = st.multiselect("Статус", options=list(StepStatus), format_func=lambda x: x.value)
    id_or_card = st.text_input("ID или часть номера карты")
    dr = st.date_input("Дата создания", value=None)
    page_size = st.selectbox("Размер страницы", [10, 20, 50, 100], index=1)
    page = st.number_input("Страница", min_value=1, value=1, step=1)
    refresh = st.button("Обновить")

where = []
if statuses:
    where.append(Task.step_status.in_(statuses))
if id_or_card:
    s = id_or_card.strip()
    if s.isdigit():
        where.append(Task.id == int(s))
    else:
        where.append(Task.card_number.like(f"%{s}%"))
if dr:
    if isinstance(dr, list) and len(dr) == 2:
        start = datetime.datetime.combine(dr[0], datetime.time.min)
        end = datetime.datetime.combine(dr[1], datetime.time.max)
        where.append(and_(Task.created_at >= start, Task.created_at <= end))
    elif hasattr(dr, "year"):
        start = datetime.datetime.combine(dr, datetime.time.min)
        end = datetime.datetime.combine(dr, datetime.time.max)
        where.append(and_(Task.created_at >= start, Task.created_at <= end))

offset = (page - 1) * page_size
rows = Task.filter_ex(where=where, order_by=Task.created_at.desc(), limit=page_size + 1, offset=offset)
has_next = len(rows) > page_size
rows = rows[:page_size]

if not rows:
    st.info("Пока нет данных")
else:
    data = []
    for t in rows:
        pct = 0 if (t.steps_total or 0) == 0 else int(round((min(t.step_index + 1, t.steps_total) / max(t.steps_total, 1)) * 100))
        data.append({
            "ID": t.id,
            "Создано": t.created_at,
            "Шаг": f"{t.step_index + 1}/{t.steps_total}",
            "Прогресс": pct,
            "Статус": status_map.get(t.step_status, str(t.step_status.value if hasattr(t.step_status, 'value') else t.step_status)),
            "Карта": mask_card(t.card_number or ""),
        })
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    for t in rows:
        cols = st.columns([1, 5, 4, 2, 2, 2])
        cols[0].markdown(f"**#{t.id}**")
        cols[1].markdown(t.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        cols[2].progress(0 if (t.steps_total or 0) == 0 else (min(t.step_index + 1, t.steps_total) / max(t.steps_total, 1)))
        cols[3].markdown(status_map.get(t.step_status, ""))
        cols[4].markdown(mask_card(t.card_number or ""))
        if cols[5].button("Логи", key=f"logs_{t.id}"):
            st.query_params["task_id"] = str(t.id)
            st.rerun()

    nav = st.columns(3)
    if nav[0].button("← Назад", disabled=(page == 1)):
        st.query_params["page"] = str(max(1, page - 1))
        st.rerun()
    nav[1].markdown(f"Стр. **{page}**")
    if nav[2].button("Вперёд →", disabled=not has_next):
        st.query_params["page"] = str(page + 1)
        st.rerun()

st.divider()
st.caption("Нажмите «Логи» у нужной строки, затем откройте страницу логов.")
