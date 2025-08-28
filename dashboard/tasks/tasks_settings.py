from database.models.task import TaskSettings

import streamlit as st


st.set_page_config(page_title="Task Scripts", layout="wide")
st.title("⚙️ Скрипты задачи")

ts = TaskSettings.get(name="default") or TaskSettings.create(name="default", scripts=[])
scripts = list(ts.scripts or [])

"""
# Создание новых задач
"""
st.subheader("Создание новых задач")

current_enabled = bool(getattr(ts, "create_enabled", True))
status_text = "Вкл" if current_enabled else "Выкл"

c1, c2 = st.columns([6, 1])
with c1:
    st.write(f"**Создание задач:** {status_text}")
with c2:
    if st.button("Изменить", use_container_width=True, key="toggle_create"):
        ts.create_enabled = not current_enabled
        ts.save()
        st.rerun()

"""
# Настройка скриптов
"""
st.subheader("Добавить скрипт")
with st.form("add_script", clear_on_submit=True):
    col_inp, col_btn = st.columns([6, 1])
    new_script = col_inp.text_input("Путь к скрипту", key="new_script", placeholder="path/to/script.py", label_visibility="collapsed")
    add_clicked = col_btn.form_submit_button("➕ Добавить")
if add_clicked and new_script.strip():
    scripts.append(new_script.strip())
    ts.scripts = scripts
    ts.save()
    st.rerun()

st.subheader("Список скриптов")

if not scripts:
    st.info("Пока пусто")
else:
    changed_inline = False
    for i, s in enumerate(scripts):
        c1, c2, c3, c4 = st.columns([8, 1, 1, 1])
        new_val = c1.text_input(f"Скрипт #{i+1}", value=s, key=f"edit_{i}", label_visibility="collapsed")
        up = c2.button("⬆️", key=f"up_{i}", use_container_width=True, disabled=(i == 0))
        dn = c3.button("⬇️", key=f"dn_{i}", use_container_width=True, disabled=(i == len(scripts) - 1))
        rm = c4.button("🗑️", key=f"rm_{i}", use_container_width=True)

        if new_val != s:
            scripts[i] = new_val
            changed_inline = True

        if up:
            scripts[i-1], scripts[i] = scripts[i], scripts[i-1]
            ts.scripts = scripts
            ts.save()
            st.rerun()
        if dn:
            scripts[i+1], scripts[i] = scripts[i], scripts[i+1]
            ts.scripts = scripts
            ts.save()
            st.rerun()
        if rm:
            scripts.pop(i)
            ts.scripts = scripts
            ts.save()
            st.rerun()

    if changed_inline:
        ts.scripts = scripts
        ts.save()
        st.rerun()

