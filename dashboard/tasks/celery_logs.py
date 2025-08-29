from pathlib import Path

import streamlit as st
import pandas as pd
import json


LOG_FILE = Path("logs/celery.log")

st.set_page_config(page_title="Логи фоновых задач", layout="wide")
st.title("Celery Logs")

auto = st.toggle("Автообновление", value=False)
lvl = st.multiselect("Уровни", ["DEBUG","INFO","WARNING","ERROR","CRITICAL"], default=["INFO","WARNING","ERROR","CRITICAL"])
task = st.text_input("Фильтр по task")
task_id = st.text_input("Фильтр по task_id")
limit = st.number_input("Сколько последних строк", min_value=100, max_value=100000, value=500, step=100)

def read_tail_lines(p, n):
    if not p.exists():
        return []
    with p.open("rb") as f:
        f.seek(0, 2)
        size = f.tell()
        block = 1024
        data = b""
        while size > 0 and data.count(b"\n") <= n:
            step = min(block, size)
            f.seek(size - step, 0)
            data = f.read(step) + data
            size -= step
        return data.splitlines()[-n:]

lines = read_tail_lines(LOG_FILE, limit)
rows = []
for b in lines:
    try:
        obj = json.loads(b.decode("utf-8"))
        rows.append(obj)
    except:
        pass

df = pd.DataFrame(rows)
if not df.empty:
    if lvl:
        df = df[df["level"].isin(lvl)]
    if task:
        df = df[df["task"].fillna("").str.contains(task, case=False, na=False)]
    if task_id:
        df = df[df["task_id"].fillna("").str.contains(task_id, case=False, na=False)]
    if "ts" in df.columns:
        df = df.sort_values("ts", ascending=False)
    st.dataframe(df, use_container_width=True, height=600)
else:
    st.info("Логи пусты")

if auto:
     st.rerun()
