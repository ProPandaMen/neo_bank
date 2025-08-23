import streamlit as st


pg = st.navigation({
    "Tasks": [
        st.Page("scheduler/tasks_overview.py", title="Список задач", icon="📋"),
        st.Page("scheduler/task_settings.py", title="Настройка задач", icon="🛠")
    ]
})

pg.run()
