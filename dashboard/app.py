import streamlit as st


pg = st.navigation({
    "Данные": [
        st.Page("information/cards_table.py", title="Карты", icon="💳"),
    ],
    "Задачи": [
        st.Page("tasks/tasks_table.py", title="Список задач", icon="📋"),
        st.Page("tasks/tasks_settings.py", title="Настройка задач", icon="🛠"),
        st.Page("tasks/celery_logs.py", title="Логи фоновых задач", icon="🥦")
    ]
})

pg.run()
