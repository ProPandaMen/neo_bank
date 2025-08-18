import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from database.models.task import JobSchedule, ScheduleType, ConflictPolicy
from database.base import SessionLocal

import streamlit as st
import json

st.set_page_config(page_title="Schedule Editor", layout="wide")
st.title("🕒 Расписание задач")

schedules = JobSchedule.all()
schedule_options = [f"{s.id} — {s.name}" for s in schedules]
selected_option = st.selectbox("Выберите расписание или создайте новое", ["<new>"] + schedule_options)

if selected_option == "<new>":
    schedule = JobSchedule.create(
        name="new_schedule",
        task_name="scheduler.execute_pipeline",
        schedule_type=ScheduleType.ONEOFF,
        args=[],
        kwargs={},
    )
else:
    selected_id = int(selected_option.split(" — ")[0])
    schedule = JobSchedule.get(id=selected_id)

with st.form("edit_schedule"):
    name = st.text_input("Название расписания", value=schedule.name or "")
    task_name = st.text_input("Название Celery-задачи", value=schedule.task_name or "")
    queue = st.text_input("Очередь Celery", value=schedule.queue or "")

    args = st.text_area("Аргументы (args) — JSON", value=json.dumps(schedule.args or [], indent=2))
    kwargs = st.text_area("Параметры (kwargs) — JSON (в т.ч. pipeline)", value=json.dumps(schedule.kwargs or {}, indent=2))

    schedule_type = st.selectbox("Тип расписания", [e for e in ScheduleType], index=[e for e in ScheduleType].index(schedule.schedule_type or ScheduleType.ONEOFF))
    cron_expr = st.text_input("CRON-выражение (если тип cron)", value=schedule.cron_expr or "")
    interval_seconds = st.number_input("Интервал (сек) (если тип interval)", value=schedule.interval_seconds or 0)
    timezone = st.text_input("Таймзона (например, UTC, Europe/Moscow)", value=schedule.timezone or "UTC")

    enabled = st.checkbox("Включено", value=schedule.enabled if schedule.enabled is not None else True)
    max_instances = st.number_input("Макс. параллельных запусков", value=schedule.max_instances or 1, min_value=1)

    policy = st.selectbox("Политика занятости", [e for e in ConflictPolicy], index=[e for e in ConflictPolicy].index(schedule.policy or ConflictPolicy.SKIP))
    jitter_seconds = st.number_input("Jitter (сек.)", value=schedule.jitter_seconds or 0, min_value=0)

    retry_limit = st.number_input("Макс. число повторов", value=schedule.retry_limit or 0, min_value=0)
    backoff_initial = st.number_input("Начальный бэкофф (сек.)", value=schedule.backoff_initial or 30, min_value=0)
    backoff_max = st.number_input("Макс. бэкофф (сек.)", value=schedule.backoff_max or 3600, min_value=0)

    submitted = st.form_submit_button("Сохранить")
    if submitted:
        schedule.name = name
        schedule.task_name = task_name
        schedule.queue = queue or None

        try:
            schedule.args = json.loads(args)
            schedule.kwargs = json.loads(kwargs)
        except Exception as e:
            st.error(f"Ошибка парсинга JSON: {e}")
            st.stop()

        schedule.schedule_type = schedule_type
        schedule.cron_expr = cron_expr or None
        schedule.interval_seconds = interval_seconds or None
        schedule.timezone = timezone
        schedule.enabled = enabled
        schedule.max_instances = max_instances
        schedule.policy = policy
        schedule.jitter_seconds = jitter_seconds
        schedule.retry_limit = retry_limit
        schedule.backoff_initial = backoff_initial
        schedule.backoff_max = backoff_max

        schedule.save()
        st.success("Сохранено")
