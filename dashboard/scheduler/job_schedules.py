import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from database.models.task import JobSchedule, ScheduleType, ConflictPolicy
from database.base import SessionLocal

import streamlit as st
import json

st.set_page_config(page_title="Schedule Editor", layout="wide")
st.title("🕒 Расписание задач")

schedules = JobSchedule.all()
if not schedules:
    schedule = JobSchedule.create(
        name="default_schedule",
        task_name="scheduler.execute_pipeline",
        schedule_type=ScheduleType.ONEOFF,
        args=[],
        kwargs={"pipeline": []},
    )
else:
    schedule = schedules[0]

if not schedule.kwargs:
    schedule.kwargs = {"pipeline": []}
if "pipeline" not in schedule.kwargs or not isinstance(schedule.kwargs["pipeline"], list):
    schedule.kwargs["pipeline"] = []

pipeline_scripts = list(schedule.kwargs.get("pipeline", []))

st.markdown("### 📜 Скрипты пайплайна")
new_script = st.text_input("Добавить путь к скрипту", key="new_script_input")
if st.button("➕ Добавить скрипт", key="add_script_btn") and new_script:
    pipeline_scripts.append({"script": new_script})
    schedule.kwargs = {**schedule.kwargs, "pipeline": pipeline_scripts}
    schedule.save()
    st.rerun()

if pipeline_scripts:
    for i, step in enumerate(pipeline_scripts):
        col1, col2 = st.columns([6,1])
        col1.text(step.get("script", ""))
        if col2.button("❌ Удалить", key=f"del_{i}"):
            pipeline_scripts.pop(i)
            schedule.kwargs = {**schedule.kwargs, "pipeline": pipeline_scripts}
            schedule.save()
            st.rerun()
else:
    st.info("Скриптов пока нет.")

st.markdown("### ⚙️ Основные параметры")
with st.form("edit_schedule"):
    name = st.text_input("Название расписания", value=schedule.name or "")
    task_name = st.text_input("Название Celery-задачи", value=schedule.task_name or "")
    queue = st.text_input("Очередь Celery", value=schedule.queue or "")

    schedule_type = st.selectbox("Тип расписания", [e for e in ScheduleType], index=[e for e in ScheduleType].index(schedule.schedule_type or ScheduleType.ONEOFF))
    cron_expr = st.text_input("CRON-выражение (если тип cron)", value=schedule.cron_expr or "")
    interval_seconds = st.number_input("Интервал (сек)", value=int(schedule.interval_seconds or 0), step=1, min_value=0)
    timezone = st.text_input("Таймзона (например, UTC, Europe/Moscow)", value=schedule.timezone or "UTC")

    enabled = st.checkbox("Включено", value=schedule.enabled if schedule.enabled is not None else True)
    max_instances = st.number_input("Макс. параллельных запусков", value=int(schedule.max_instances or 1), min_value=1, step=1)

    policy = st.selectbox("Политика занятости", [e for e in ConflictPolicy], index=[e for e in ConflictPolicy].index(schedule.policy or ConflictPolicy.SKIP))
    jitter_seconds = st.number_input("Jitter (сек.)", value=int(schedule.jitter_seconds or 0), min_value=0, step=1)

    retry_limit = st.number_input("Макс. число повторов", value=int(schedule.retry_limit or 0), min_value=0, step=1)
    backoff_initial = st.number_input("Начальный бэкофф (сек.)", value=int(schedule.backoff_initial or 30), min_value=0, step=1)
    backoff_max = st.number_input("Макс. бэкофф (сек.)", value=int(schedule.backoff_max or 3600), min_value=0, step=1)

    submitted = st.form_submit_button("💾 Сохранить")
    if submitted:
        schedule.name = name
        schedule.task_name = task_name
        schedule.queue = queue or None
        schedule.schedule_type = schedule_type
        schedule.cron_expr = cron_expr or None
        schedule.interval_seconds = int(interval_seconds) if interval_seconds else None
        schedule.timezone = timezone
        schedule.enabled = enabled
        schedule.max_instances = int(max_instances)
        schedule.policy = policy
        schedule.jitter_seconds = int(jitter_seconds)
        schedule.retry_limit = int(retry_limit)
        schedule.backoff_initial = int(backoff_initial)
        schedule.backoff_max = int(backoff_max)
        schedule.kwargs = {**schedule.kwargs, "pipeline": pipeline_scripts}
        schedule.save()
        st.success("Сохранено")
