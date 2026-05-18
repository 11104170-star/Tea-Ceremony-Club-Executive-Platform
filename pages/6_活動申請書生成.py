import re

import streamlit as st

from utils.application_form import (
    DEFAULT_APPLICATION_TEMPLATE_PATH,
    build_application_form,
    roc_date_from_iso,
)
from utils.auth import require_login, logout_button
from utils.calendar_store import format_event_label, load_events
from utils.officer_store import load_officers
from utils.teacher_comment import (
    DEFAULT_GROQ_MODEL,
    fallback_application_purpose,
    generate_application_purpose_with_preview,
)


DEFAULT_PURPOSE = fallback_application_purpose(activity_name="")


st.set_page_config(
    page_title="活動申請書生成 | 茶道社幹部平台",
    page_icon="🍵",
    layout="wide",
)

require_login()

with st.sidebar:
    st.success("已登入")
    logout_button()

st.title("活動申請書生成")
st.caption("從行事曆與幹部名單帶入資料，產生 Word 活動申請計畫書。")


def application_form_file_name(activity_date: str, activity_name: str) -> str:
    compact_date = re.sub(r"[^0-9]", "", activity_date)
    clean_name = re.sub(r'[\\/:*?"<>|\\s]+', "_", activity_name).strip("_")
    if not clean_name:
        clean_name = "活動申請書"
    prefix = f"{compact_date}_" if compact_date else ""
    return f"{prefix}{clean_name}_活動申請書.docx"


with st.expander("範本設定", expanded=False):
    st.write(f"目前預設範本：`{DEFAULT_APPLICATION_TEMPLATE_PATH.name}`")
    template_file = st.file_uploader(
        "上傳自訂 Word 範本（可選）",
        type=["docx"],
        help="未上傳時會使用平台內建的活動申請書範本。",
    )

st.subheader("基本資料")
officers = load_officers()
calendar_events = load_events()
selected_calendar_event = None

if calendar_events:
    calendar_options = list(range(len(calendar_events) + 1))
    selected_calendar_event_index = st.selectbox(
        "從行事曆帶入活動資料",
        calendar_options,
        format_func=lambda index: (
            "不帶入行事曆資料"
            if index == 0
            else format_event_label(calendar_events[index - 1])
        ),
        key="application_selected_calendar_event_index",
    )
    if selected_calendar_event_index > 0:
        selected_calendar_event = calendar_events[selected_calendar_event_index - 1]
else:
    selected_calendar_event_index = 0
    st.selectbox("從行事曆帶入活動資料", ["尚無行事曆活動"], disabled=True)

event_name = selected_calendar_event.get("活動名稱", "") if selected_calendar_event else ""
event_date = selected_calendar_event.get("日期", "") if selected_calendar_event else ""
event_place = selected_calendar_event.get("地點", "") if selected_calendar_event else ""
event_leader = selected_calendar_event.get("活動負責人", "") if selected_calendar_event else ""

if st.session_state.get("application_last_calendar_event_index") != selected_calendar_event_index:
    if selected_calendar_event is not None:
        st.session_state["application_activity_name_input"] = event_name
        st.session_state["application_activity_date_input"] = roc_date_from_iso(event_date)
        st.session_state["application_activity_place_input"] = event_place or "靜心書院A202"
        if event_leader:
            st.session_state["application_calendar_event_leader"] = event_leader
            for index, officer in enumerate(officers):
                if officer.get("姓名", "") == event_leader:
                    st.session_state["application_leader_index"] = index
                    break
    st.session_state["application_last_calendar_event_index"] = selected_calendar_event_index

if "application_activity_place_input" not in st.session_state:
    st.session_state["application_activity_place_input"] = "靜心書院A202"
if "application_tea_topic_input" not in st.session_state:
    st.session_state["application_tea_topic_input"] = "茶"
if "application_snack_purpose_input" not in st.session_state:
    st.session_state["application_snack_purpose_input"] = "活動點心與材料費"
if "application_activity_purpose_input" not in st.session_state:
    st.session_state["application_activity_purpose_input"] = DEFAULT_PURPOSE
if "application_activity_purpose_preview" not in st.session_state:
    st.session_state["application_activity_purpose_preview"] = None

col1, col2, col3 = st.columns(3)

with col1:
    activity_name = st.text_input("活動名稱", key="application_activity_name_input")
    activity_date = st.text_input(
        "活動日期 / 時間",
        key="application_activity_date_input",
        help="會寫入申請書的活動日期與活動時間欄位，例如 115/5/18 或 115/5/18 19:00~21:00。",
    )
    activity_place = st.text_input(
        "活動地點",
        key="application_activity_place_input",
    )

with col2:
    if officers:
        if "application_leader_index" not in st.session_state:
            st.session_state["application_leader_index"] = 0
        selected_leader_index = st.selectbox(
            "活動聯絡人",
            list(range(len(officers))),
            format_func=lambda index: officers[index].get("姓名", ""),
            key="application_leader_index",
        )
        activity_leader = officers[selected_leader_index].get("姓名", "")
    else:
        activity_leader = st.text_input(
            "活動聯絡人",
            value=event_leader,
            key="application_activity_leader_input",
        )
    leader_phone = st.text_input("聯絡人電話", key="application_leader_phone_input")
    estimated_people = st.number_input(
        "預估人數",
        min_value=0,
        step=1,
        value=30,
        key="application_estimated_people_input",
    )

with col3:
    tea_topic = st.text_input("介紹茶品", key="application_tea_topic_input")
    snack_unit_price = st.number_input(
        "點心單價",
        min_value=0,
        step=10,
        value=100,
        key="application_snack_unit_price_input",
    )
    snack_purpose = st.text_input(
        "點心用途說明",
        key="application_snack_purpose_input",
    )

purpose_col1, purpose_col2 = st.columns([1, 3])
with purpose_col1:
    generate_purpose = st.button("由活動名稱生成活動宗旨")
with purpose_col2:
    purpose_preview = st.session_state["application_activity_purpose_preview"]
    if purpose_preview:
        status = str(purpose_preview.get("status", ""))
        provider = str(purpose_preview.get("provider", ""))
        model = str(purpose_preview.get("model", ""))
        model_text = f"{provider}: {model}" if model else provider
        if status.startswith("使用 ") and status.endswith("原始稿。"):
            st.success(f"AI 順利產出。調用模型：{model_text}")
        else:
            st.info(status)
            if model_text:
                st.caption(f"調用模型：{model_text}")

if generate_purpose:
    if not activity_name.strip():
        st.error("請先輸入活動名稱，再生成活動宗旨。")
    else:
        try:
            api_key = st.secrets.get("GEMINI_API_KEY")
            model = st.secrets.get("GEMINI_MODEL", "gemini-2.5-flash")
            groq_api_key = st.secrets.get("GROQ_API_KEY")
            groq_model = st.secrets.get("GROQ_MODEL", DEFAULT_GROQ_MODEL)
            with st.spinner("正在用 AI 生成活動宗旨..."):
                preview = generate_application_purpose_with_preview(
                    api_key=api_key,
                    model=model,
                    groq_api_key=groq_api_key,
                    groq_model=groq_model,
                    activity_name=activity_name,
                )
                st.session_state["application_activity_purpose_preview"] = preview
                st.session_state["application_activity_purpose_input"] = preview["final_text"]
            st.rerun()
        except Exception as exc:
            st.error("活動宗旨生成失敗，請確認 GEMINI_API_KEY / GROQ_API_KEY 是否正確，或稍後再試。")
            st.exception(exc)

activity_purpose = st.text_area(
    "活動宗旨",
    height=120,
    key="application_activity_purpose_input",
)

fields = {
    "activity_name": activity_name,
    "activity_date": activity_date,
    "activity_place": activity_place,
    "activity_leader": activity_leader,
    "leader_phone": leader_phone,
    "activity_purpose": activity_purpose,
    "estimated_people": estimated_people,
    "snack_unit_price": snack_unit_price,
    "snack_purpose": snack_purpose,
    "tea_topic": tea_topic,
}

if st.button("產生活動申請書", type="primary"):
    if not activity_name.strip():
        st.error("請先輸入活動名稱。")
    else:
        try:
            output = build_application_form(
                template_file=template_file,
                fields=fields,
                officers=officers,
            )
        except Exception as exc:
            st.error("活動申請書產生失敗，請確認範本格式是否正確。")
            st.exception(exc)
        else:
            st.success("活動申請書已產生。")
            st.download_button(
                label="下載活動申請書",
                data=output,
                file_name=application_form_file_name(activity_date, activity_name),
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
