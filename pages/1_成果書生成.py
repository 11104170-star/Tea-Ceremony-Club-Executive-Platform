from datetime import date

import streamlit as st
from utils.achievement_report import (
    DEFAULT_TEMPLATE_PATH,
    LEGACY_ACTIVITY_OVERVIEW_TEXT,
    build_report,
)
from utils.auth import require_login, logout_button
from utils.calendar_store import format_event_label, load_events
from utils.officer_store import load_officers
from utils.report_filename import achievement_report_file_name
from utils.teacher_comment import (
    fallback_activity_overview,
    fallback_teacher_comment,
    generate_activity_overview,
    generate_activity_overview_with_preview,
    generate_teacher_comment,
    generate_teacher_comment_with_preview,
)


st.set_page_config(
    page_title="成果書生成 | 茶道社幹部平台",
    page_icon="🍵",
    layout="wide",
)

require_login()

with st.sidebar:
    st.success("已登入")
    logout_button()

st.title("成果書生成")
st.caption("匯入問卷資料與活動照片，產生 Word 成果書。")


def use_template_text(text_key: str, preview_key: str, template_text: str) -> None:
    st.session_state[text_key] = template_text
    st.session_state[preview_key] = {
        "status": "已改用套模板。",
        "raw_text": "",
        "repaired_text": "",
        "final_text": template_text,
        "raw_debug": {},
        "repaired_debug": {},
    }


def show_ai_preview(
    title: str,
    preview: dict[str, object] | None,
    *,
    text_key: str,
    preview_key: str,
    template_text: str,
) -> None:
    if not preview:
        return

    key_prefix = title.replace(" ", "_")
    status = str(preview.get("status", ""))

    if status == "使用 Gemini 原始稿。":
        st.success("AI 順利產出。")
        st.button(
            "改成套模板",
            key=f"{key_prefix}_use_template",
            on_click=use_template_text,
            args=(text_key, preview_key, template_text),
        )
        return

    with st.expander(title, expanded=True):
        st.caption(status)

        raw_text = preview.get("raw_text", "")
        if raw_text:
            st.text_area(
                "Gemini 原始輸出",
                raw_text,
                height=120,
                disabled=True,
                key=f"{key_prefix}_raw",
            )
            raw_debug = preview.get("raw_debug", {})
            if raw_debug:
                st.json(raw_debug)

        repaired_text = preview.get("repaired_text", "")
        if repaired_text:
            st.text_area(
                "Gemini 重寫輸出",
                repaired_text,
                height=120,
                disabled=True,
                key=f"{key_prefix}_repaired",
            )
            repaired_debug = preview.get("repaired_debug", {})
            if repaired_debug:
                st.json(repaired_debug)

        st.text_area(
            "最後採用文字",
            str(preview.get("final_text", "")),
            height=120,
            disabled=True,
            key=f"{key_prefix}_final",
        )

with st.expander("範本設定", expanded=False):
    st.write(f"目前預設範本：`{DEFAULT_TEMPLATE_PATH.name}`")
    template_file = st.file_uploader(
        "上傳自訂 Word 範本（可選）",
        type=["docx"],
        help="未上傳時會使用平台內建的成果書範本。",
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
        key="selected_calendar_event_index",
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

if st.session_state.get("last_calendar_event_index") != selected_calendar_event_index:
    if selected_calendar_event is not None:
        st.session_state["activity_name_input"] = event_name
        st.session_state["activity_place_input"] = event_place
        st.session_state["activity_date_input"] = event_date
        if event_leader:
            st.session_state["calendar_event_leader"] = event_leader
            for index, officer in enumerate(officers):
                if officer.get("姓名", "") == event_leader:
                    st.session_state["activity_leader_index"] = index
                    break
    st.session_state["last_calendar_event_index"] = selected_calendar_event_index

col1, col2, col3 = st.columns(3)

with col1:
    today = date.today()
    fill_date = f"{today.month}月{today.day}日"
    st.text_input("填寫日期", value=fill_date, disabled=True)
    activity_name = st.text_input("活動名稱", key="activity_name_input")
    activity_place = st.text_input("活動地點", key="activity_place_input")

with col2:
    activity_date = st.text_input("活動日期", key="activity_date_input")
    school_people = st.number_input("本校學生人數", min_value=0, step=1)
    outside_people = st.number_input("校外人士人數", min_value=0, step=1)
    

with col3:
    phone = st.text_input("連絡電話")
    if officers:
        if "activity_leader_index" not in st.session_state:
            st.session_state["activity_leader_index"] = 0

        selected_leader_index = st.selectbox(
            "活動負責人",
            list(range(len(officers))),
            format_func=lambda index: officers[index].get("姓名", ""),
            key="activity_leader_index",
        )
        selected_leader = officers[selected_leader_index]
        activity_leader = selected_leader.get("姓名", "")
    else:
        activity_leader = event_leader
        if event_leader:
            st.text_input("活動負責人", value=event_leader, disabled=True)
        else:
            st.selectbox("活動負責人", ["請先到幹部管理新增幹部"], disabled=True)

st.subheader("問卷資料")
questionnaire_file = st.file_uploader(
    "上傳問卷 Excel / CSV",
    type=["xlsx", "csv"],
)

st.subheader("照片")
image_col1, image_col2 = st.columns(2)

with image_col1:
    flow_photo = st.file_uploader("活動流程照片", type=["jpg", "jpeg", "png"])
    photo1 = st.file_uploader("照片 1", type=["jpg", "jpeg", "png"])
    photo1_desc = st.text_input("照片 1 說明")

with image_col2:
    group_photo = st.file_uploader("大合照", type=["jpg", "jpeg", "png"])
    photo2 = st.file_uploader("照片 2", type=["jpg", "jpeg", "png"])
    photo2_desc = st.text_input("照片 2 說明")

photo3 = st.file_uploader("照片 3", type=["jpg", "jpeg", "png"])
photo3_desc = st.text_input("照片 3 說明")

st.subheader("活動內容概述")
if "activity_overview_text" not in st.session_state:
    st.session_state["activity_overview_text"] = ""
elif st.session_state["activity_overview_text"].strip() == LEGACY_ACTIVITY_OVERVIEW_TEXT:
    st.session_state["activity_overview_text"] = ""

if "activity_overview_preview" not in st.session_state:
    st.session_state["activity_overview_preview"] = None

if st.button("由照片生成活動內容概述"):
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        model = st.secrets.get("GEMINI_MODEL", "gemini-2.5-flash")
        with st.spinner("正在用 AI 生成活動內容概述..."):
            preview = generate_activity_overview_with_preview(
                api_key=api_key,
                model=model,
                activity_name=activity_name,
                photo_descriptions=[photo1_desc, photo2_desc, photo3_desc],
                photos=[flow_photo, group_photo, photo1, photo2, photo3],
            )
            st.session_state["activity_overview_preview"] = preview
            st.session_state["activity_overview_text"] = preview["final_text"]
        st.success("已由照片生成活動內容概述。")
    except Exception as exc:
        st.error("活動內容概述生成失敗，請確認 GEMINI_API_KEY 是否正確，或稍後再試。")
        st.exception(exc)

activity_overview = st.text_area(
    "活動內容概述",
    key="activity_overview_text",
    height=140,
)
activity_overview_template = fallback_activity_overview(
    activity_name=activity_name,
    photo_descriptions=[photo1_desc, photo2_desc, photo3_desc],
)
show_ai_preview(
    "活動內容概述 AI 生成預覽",
    st.session_state["activity_overview_preview"],
    text_key="activity_overview_text",
    preview_key="activity_overview_preview",
    template_text=activity_overview_template,
)

st.subheader("活動檢討與建議事項")
activity_suggestion = st.text_area("活動檢討與建議事項", height=140)

st.subheader("指導老師評語")
if "teacher_comment_text" not in st.session_state:
    st.session_state["teacher_comment_text"] = ""

if "teacher_comment_preview" not in st.session_state:
    st.session_state["teacher_comment_preview"] = None

if st.button("由照片說明生成老師評語"):
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        model = st.secrets.get("GEMINI_MODEL", "gemini-2.5-flash")
        with st.spinner("正在用 AI 生成老師評語..."):
            preview = generate_teacher_comment_with_preview(
                api_key=api_key,
                model=model,
                activity_name=activity_name,
                activity_review=activity_suggestion,
                photo_descriptions=[photo1_desc, photo2_desc, photo3_desc],
            )
            st.session_state["teacher_comment_preview"] = preview
            st.session_state["teacher_comment_text"] = preview["final_text"]
    except Exception as exc:
        st.error("老師評語生成失敗，請確認 GEMINI_API_KEY 是否正確，或稍後再試。")
        st.exception(exc)

teacher_comment = st.text_area(
    "指導老師評語",
    key="teacher_comment_text",
    height=120,
)
teacher_comment_template = fallback_teacher_comment(
    activity_name=activity_name,
    activity_review=activity_suggestion,
    photo_descriptions=[photo1_desc, photo2_desc, photo3_desc],
)
show_ai_preview(
    "老師評語 AI 生成預覽",
    st.session_state["teacher_comment_preview"],
    text_key="teacher_comment_text",
    preview_key="teacher_comment_preview",
    template_text=teacher_comment_template,
)

fields = {
    
    "fill_date": fill_date,
    "activity_name": activity_name,
    "activity_place": activity_place,
    "activity_date": activity_date,
    "activity_people": "",
    "activity_leader": activity_leader,
    "phone": phone,
    "activity_overview": activity_overview,
    "activity_review": activity_suggestion,
    "teacher_comment": teacher_comment,
    "photo1_desc": photo1_desc,
    "photo2_desc": photo2_desc,
    "photo3_desc": photo3_desc,
}

images = {
    "flow_photo": flow_photo,
    "group_photo": group_photo,
    "photo1": photo1,
    "photo2": photo2,
    "photo3": photo3,
}

if st.button("產生成果書", type="primary"):
    total_people = school_people + outside_people
    fields["activity_people"] = (
        f"本校學生－{school_people}人、校外人士－{outside_people}人，"
        f"共計{total_people}人"
    )
    fields["activity_overview"] = activity_overview.strip()
    fields["activity_review"] = activity_suggestion.strip()
    fields["teacher_comment"] = teacher_comment.strip()

    if not fields["activity_overview"]:
        fields["activity_overview"] = generate_activity_overview(
            api_key=None,
            model="",
            activity_name=activity_name,
            photo_descriptions=[photo1_desc, photo2_desc, photo3_desc],
            photos=[flow_photo, group_photo, photo1, photo2, photo3],
        )
        st.session_state["activity_overview_text"] = fields["activity_overview"]

    if not fields["teacher_comment"]:
        fields["teacher_comment"] = generate_teacher_comment(
            api_key=None,
            model="",
            activity_name=activity_name,
            activity_review=activity_suggestion,
            photo_descriptions=[photo1_desc, photo2_desc, photo3_desc],
        )
        st.session_state["teacher_comment_text"] = fields["teacher_comment"]

    try:
        output, result_text = build_report(
            template_file=template_file,
            questionnaire_file=questionnaire_file,
            fields=fields,
            images=images,
        )
    except Exception as exc:
        st.error("成果書產生失敗，請確認範本、問卷或圖片格式是否正確。")
        st.exception(exc)
    else:
        file_name = achievement_report_file_name(activity_date, activity_name)
        st.success("成果書已產生。")

        with st.expander("問卷分析結果預覽", expanded=False):
            st.text(result_text)

        st.download_button(
            label="下載成果書",
            data=output,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
