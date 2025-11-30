import streamlit as st
import datetime
import os
import pickle
import pandas as pd
import plotly.express as px

# ---------------- Storage ---------------- #
DATA_FILE = "/mount/data/tasks_data.pkl"


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "rb") as f:
            return pickle.load(f)
    return {"regular": [], "daily": {}, "completed": {}}

def save_data(data):
    with open(DATA_FILE, "wb") as f:
        pickle.dump(data, f)

# ---------------- Page Setup ---------------- #
st.set_page_config(page_title="Task Manager", layout="wide")

# ---------------- Mobile Detection ---------------- #
is_mobile = st.session_state.get("is_mobile", None)

st.markdown("""
<script>
    const width = window.innerWidth;
    if (width < 650) {
        window.parent.postMessage({"is_mobile": true}, "*");
    } else {
        window.parent.postMessage({"is_mobile": false}, "*");
    }
</script>
""", unsafe_allow_html=True)

msg = st.query_params
if "is_mobile" in msg:
    st.session_state.is_mobile = msg["is_mobile"][0] == "true"


# ---------------- CSS ---------------- #
st.markdown("""
<style>

    body {
        background: #f5f5f5;
    }

    .task-card {
        background: white;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 8px;
        box-shadow: 0px 2px 6px rgba(0,0,0,0.1);
    }

    .calendar-card {
        padding: 10px;
        border-radius: 10px;
        background: #e8edff;
        text-align: center;
        font-weight: bold;
        border: 1px solid #ccd7ff;
        margin-bottom: 5px;
    }

    @media (max-width: 650px) {
        .task-card { padding: 10px; }
        .calendar-card { padding: 8px; font-size: 14px; }
    }

</style>
""", unsafe_allow_html=True)

# ---------------- Load Data ---------------- #
data = load_data()

# ---------------- Title ---------------- #
st.markdown("<h2 style='text-align:center;color:#365899;'>Task Manager</h2>", unsafe_allow_html=True)

# ---------------- Tabs ---------------- #
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Add Task", "Today", "Weekly", "Daily Progress", "Weekly Score", "Trend"
])


# ---------------- Helper Functions ---------------- #
def mark_completed(date, task):
    s = str(date)
    data["completed"].setdefault(s, []).append(task)
    save_data(data)

def day_stats(date):
    s = str(date)
    total = len(data["regular"]) + len(data["daily"].get(s, []))
    completed = len(data["completed"].get(s, []))
    return completed, total

def weekly_stats():
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    week = [monday + datetime.timedelta(days=i) for i in range(7)]
    result = []
    for d in week:
        c, t = day_stats(d)
        result.append({"day": d.strftime("%a"), "completed": c, "total": t})
    return result


# ---------------- TAB 1: ADD TASK ---------------- #
with tab1:
    st.subheader("Add New Task")

    task = st.text_input("Task Title")
    type_ = st.selectbox("Task Type", ["Regular Task", "Day Task"])

    if type_ == "Day Task":
        date = st.date_input("Select Date", datetime.date.today())

    if st.button("Add", use_container_width=True):
        if task.strip() == "":
            st.warning("Enter a valid task")
        else:
            if type_ == "Regular Task":
                data["regular"].append(task)
            else:
                ds = str(date)
                data["daily"].setdefault(ds, []).append(task)

            save_data(data)
            st.success("Task added!")


# ---------------- TAB 2: TODAY ---------------- #
with tab2:
    st.subheader("Today's Tasks")

    today = datetime.date.today()
    s = str(today)

    st.write("Regular Tasks:")
    for i, t in enumerate(data["regular"]):
        if st.checkbox(t, key=f"reg_{i}"):
            mark_completed(today, t)
            data["regular"].pop(i)
            save_data(data)
            st.experimental_rerun()

    st.write("Day Tasks:")
    if s in data["daily"]:
        for i, t in enumerate(data["daily"][s]):
            if st.checkbox(t, key=f"day_{i}"):
                mark_completed(today, t)
                data["daily"][s].pop(i)
                save_data(data)
                st.experimental_rerun()


# ---------------- TAB 3: WEEKLY CALENDAR ---------------- #
with tab3:
    st.subheader("Weekly Calendar")

    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    week = [monday + datetime.timedelta(days=i) for i in range(7)]

    # MOBILE: show 2 columns
    # DESKTOP: show 7 columns
    if is_mobile:
        cols = st.columns(2)
    else:
        cols = st.columns(7)

    for i, d in enumerate(week):
        col = cols[i % len(cols)]
        with col:
            st.markdown(
                f"<div class='calendar-card'>{d.strftime('%a')}<br>{d.strftime('%d %b')}</div>",
                unsafe_allow_html=True
            )

            ds = str(d)

            for task in data["regular"]:
                st.markdown(f"<div class='task-card'>{task}</div>", unsafe_allow_html=True)

            if ds in data["daily"]:
                for task in data["daily"][ds]:
                    st.markdown(f"<div class='task-card'>{task}</div>", unsafe_allow_html=True)


# ---------------- TAB 4: DAILY PROGRESS ---------------- #
with tab4:
    st.subheader("Daily Progress")

    completed, total = day_stats(datetime.date.today())

    col1, col2 = st.columns(2)
    col1.metric("Completed", completed)
    col2.metric("Total Tasks", total)

    df = pd.DataFrame({
        "Status": ["Completed", "Remaining"],
        "Count": [completed, total - completed]
    })

    fig = px.bar(df, x="Status", y="Count", text="Count")
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)


# ---------------- TAB 5: WEEKLY SCORE ---------------- #
with tab5:
    st.subheader("Weekly Score")

    stats = weekly_stats()
    total = sum(x["total"] for x in stats)
    completed = sum(x["completed"] for x in stats)
    score = int((completed / total) * 100) if total else 0

    st.metric("Score", f"{score}/100")

    df = pd.DataFrame(stats)
    fig = px.bar(df, x="day", y="completed", text="completed", color="total")
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)


# ---------------- TAB 6: TREND ---------------- #
with tab6:
    st.subheader("Consistency Trend")

    history = []
    for d, tasks in data["completed"].items():
        history.append({"date": d, "completed": len(tasks)})

    if history:
        df = pd.DataFrame(history)
        df["date"] = pd.to_datetime(df["date"])

        fig = px.line(df, x="date", y="completed", markers=True)
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No history yet.")
