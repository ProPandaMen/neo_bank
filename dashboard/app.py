import streamlit as st


pg = st.navigation({
    "Celery": [        
        st.Page("scheduler/task_settings.py", title="Настройка задач", icon="🛠")
    ]
})

pg.run()
