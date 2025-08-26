from database.models.task import Task, TaskLogs, StepStatus
import streamlit as st


st.set_page_config(page_title="Логи задачи", layout="wide")
st.title("🧾 Логи задачи")

qid = st.query_params.get("task_id")
task = None
if qid and str(qid).isdigit():
    task = Task.get(id=int(qid))

if not task:
    st.warning("Не выбран task_id")
    ids = [t.id for t in Task.filter(order_by=Task.created_at.desc(), limit=50)]
    sel = st.selectbox("Выберите задачу", options=ids)
    if sel:
        st.query_params["task_id"] = str(sel)
        st.rerun()

else:
    st.subheader(f"Задача #{task.id}")
    cols = st.columns(4)
    cols[0].metric("Создано", task.created_at.strftime("%Y-%m-%d %H:%M:%S"))
    cols[1].metric("Шаг", f"{task.step_index + 1}/{task.steps_total}")
    cols[2].metric("Статус", task.step_status.value if hasattr(task.step_status, "value") else str(task.step_status))
    cols[3].metric("Карта", (task.card_number or "")[-4:] if task.card_number else "—")

    st.divider()
    st.subheader("Логи")

    page_size = st.selectbox("Размер страницы", [50, 100, 200], index=0)
    page = int(st.query_params.get("logs_page", "1"))
    if page < 1:
        page = 1
    offset = (page - 1) * page_size
    rows = TaskLogs.filter_ex(where=[TaskLogs.task_id == task.id], order_by=TaskLogs.created_at.desc(), limit=page_size + 1, offset=offset)
    has_next = len(rows) > page_size
    rows = rows[:page_size]

    if not rows:
        st.info("Логи отсутствуют")
    else:
        for r in rows:
            with st.expander(r.created_at.strftime("%Y-%m-%d %H:%M:%S"), expanded=False):
                st.code(r.description)

    nav = st.columns(3)
    if nav[0].button("← Назад", disabled=(page == 1)):
        st.query_params["logs_page"] = str(max(1, page - 1))
        st.rerun()
    nav[1].markdown(f"Стр. **{page}**")
    if nav[2].button("Вперёд →", disabled=not has_next):
        st.query_params["logs_page"] = str(page + 1)
        st.rerun()
