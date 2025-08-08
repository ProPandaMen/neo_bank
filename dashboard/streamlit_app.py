import streamlit as st

def page_2():
    st.title("Page 2")

pg = st.navigation([
    st.Page("tasks.py", title="Задачи", icon="📋"),
    st.Page("logs.py", title="Логи", icon="📝"),
    st.Page("manage_tasks.py", title="Управление задачами", icon="🛠")
])

pg.run()
