import calendar
from datetime import date

import streamlit as st

from utils.auth import require_login, logout_button
from utils.calendar_store import (
    add_event,
    delete_event,
    format_event_label,
    load_events,
    storage_label,
)
from utils.officer_store import format_officer_label, load_officers


st.set_page_config(
    page_title="行事曆 | 茶道社幹部平台",
    page_icon="🍵",
    layout="wide",
)

require_login()

with st.sidebar:
    st.success("已登入")
    logout_button()

st.title("行事曆")
st.caption("記錄社課、會議與活動時程。")
st.caption(f"目前儲存方式：{storage_label()}")

events = load_events()
officers = load_officers()

st.subheader("月曆")
today = date.today()
month_col1, month_col2 = st.columns(2)

with month_col1:
    selected_year = st.number_input("年份", min_value=2020, max_value=2100, value=today.year, step=1)
with month_col2:
    selected_month = st.selectbox("月份", list(range(1, 13)), index=today.month - 1)

events_by_date: dict[str, list[dict[str, str]]] = {}
for event in events:
    events_by_date.setdefault(event["日期"], []).append(event)

weekdays = ["一", "二", "三", "四", "五", "六", "日"]
for column, weekday in zip(st.columns(7), weekdays):
    column.markdown(f"**{weekday}**")

calendar_weeks = calendar.Calendar(firstweekday=0).monthdatescalendar(
    int(selected_year),
    int(selected_month),
)

for week in calendar_weeks:
    columns = st.columns(7)
    for column, day in zip(columns, week):
        day_key = day.strftime("%Y-%m-%d")
        day_events = events_by_date.get(day_key, [])
        muted = day.month != selected_month
        heading = f"**{day.day}**" if not muted else f":gray[{day.day}]"

        with column.container(border=True):
            st.markdown(heading)
            if day_events:
                for event in day_events:
                    leader = event.get("活動負責人", "")
                    title = event.get("活動名稱", "")
                    location = event.get("地點", "")
                    st.caption(title)
                    if leader:
                        st.caption(f"負責：{leader}")
                    if location:
                        st.caption(f"@ {location}")
            else:
                st.caption(" ")

st.subheader("新增行程")
with st.form("calendar_event_form", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)

    with col1:
        event_date = st.date_input("日期")
    with col2:
        if officers:
            selected_leader = st.selectbox(
                "活動負責人",
                officers,
                format_func=format_officer_label,
            )
            event_leader = selected_leader.get("姓名", "")
        else:
            event_leader = st.text_input("活動負責人")
    with col3:
        title = st.text_input("活動名稱")

    location = st.text_input("地點")
    note = st.text_area("備註", height=90)

    submitted = st.form_submit_button("新增行程", type="primary")

if submitted:
    if not title.strip():
        st.error("請輸入活動名稱。")
    else:
        add_event(
            title=title,
            date=event_date.strftime("%Y-%m-%d"),
            leader=event_leader,
            location=location,
            note=note,
        )
        st.success("已新增行程。")
        st.rerun()

st.subheader("行程列表")

if events:
    st.dataframe(events, use_container_width=True, hide_index=True)

    event_options = list(range(len(events)))
    selected_index = st.selectbox(
        "選擇要刪除的行程",
        event_options,
        format_func=lambda index: format_event_label(events[index]),
    )

    if st.button("刪除行程"):
        delete_event(selected_index)
        st.success("已刪除行程。")
        st.rerun()
else:
    st.info("目前尚未新增行程。")
