from database.models.task import TaskSettings

import streamlit as st


def task_setting_field(ts):
    st.subheader("⚙️ Настройки задач")

    planer_enabled = bool(ts.planer_enabled)
    options = {"Вкл": True, "Выкл": False}

    selected = st.selectbox(
        "Создание новых задач", 
        options.keys(), 
        index=0 if planer_enabled else 1,
        key="create_enabled_select"
    )

    if options[selected] != planer_enabled:
        ts.planer_enabled = options[selected]
        ts.save()
        st.rerun()

def task_setting_scripts(ts, scripts):
    st.title("🎻 Скрипты задачи")
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

def main():
    st.set_page_config(page_title="Task Scripts", layout="wide")

    task_settings = TaskSettings.get(name="default") or TaskSettings.create(name="default", scripts=[])
    task_scripts = list(task_settings.scripts or [])

    task_setting_field(task_settings)
    task_setting_scripts(task_settings, task_scripts)

main()
