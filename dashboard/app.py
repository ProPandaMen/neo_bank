import streamlit as st


pg = st.navigation({
    "Celery": [
        st.Page("scheduler/monitoring.py", title="Мониторинг задач", icon="📊"),
        st.Page("scheduler/management.py", title="Управление задачами", icon="🛠")
    ]
})

pg.run()
