from database.models.task import TaskSettings

import streamlit as st


def task_setting_field(task):
    st.title("⚙️ Настройки задач")

    options = {"Вкл": True, "Выкл": False}
    selected = st.selectbox(
        "Создание новых задач", 
        options.keys(),
        index=0 if task.planer_enabled else 1,
        key="create_enabled_select"
    )
    if options[selected] != task.planer_enabled:
        task.planer_enabled = options[selected]
        task.save()
        st.rerun()

    def editable_int(label, field, min_val=0, max_val=100000, step=1):
        value = st.number_input(
            label,
            min_value=min_val,
            max_value=max_val,
            step=step,
            value=getattr(task, field)
        )
        if value != getattr(task, field):
            setattr(task, field, value)
            task.save()
            st.rerun()

    def editable_float(label, field, min_val=0.0, max_val=100000.0, step=0.1):
        value = st.number_input(
            label,
            min_value=min_val,
            max_value=max_val,
            step=step,
            value=getattr(task, field),
            format="%.2f"
        )
        if value != getattr(task, field):
            setattr(task, field, value)
            task.save()
            st.rerun()

    editable_int("Параллельный лимит", "parallel_limit", 1, 100)
    editable_int("Размер пачки создания", "create_batch", 1, 100)
    editable_int("Таймаут шага (сек)", "step_timeout", 1, 86400)
    editable_int("Лимит ретраев", "retry_limit", 0, 100)
    editable_int("Начальная задержка (сек)", "backoff_initial", 1, 3600)
    editable_float("Множитель задержки", "backoff_factor", 1.0, 10.0, 0.1)
    editable_int("Макс. задержка (сек)", "backoff_max", 1, 86400)


def task_setting_scripts(task, scripts):
    st.title("🎻 Скрипты задачи")
    st.subheader("Добавить скрипт")

    with st.form("add_script", clear_on_submit=True):
        col_inp, col_btn = st.columns([6, 1])
        new_script = col_inp.text_input("Путь к скрипту", key="new_script", placeholder="path/to/script.py", label_visibility="collapsed")
        add_clicked = col_btn.form_submit_button("➕ Добавить")

    if add_clicked and new_script.strip():
        scripts.append(new_script.strip())
        task.scripts = scripts
        task.save()
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
                task.scripts = scripts
                task.save()
                st.rerun()
            if dn:
                scripts[i+1], scripts[i] = scripts[i], scripts[i+1]
                task.scripts = scripts
                task.save()
                st.rerun()
            if rm:
                scripts.pop(i)
                task.scripts = scripts
                task.save()
                st.rerun()

        if changed_inline:
            task.scripts = scripts
            task.save()
            st.rerun()

def main():
    st.set_page_config(page_title="Насстройка задач", layout="wide")

    task_settings = TaskSettings.get(name="default") or TaskSettings.create(name="default", scripts=[])
    task_scripts = list(task_settings.scripts or [])

    tab_field, tab_scripts = st.tabs([
        "Параметры"
        "Скрипты"
    ])

    with tab_field:
        task_setting_field(task_settings)
    with tab_scripts:
        task_setting_scripts(task_settings, task_scripts)

main()
