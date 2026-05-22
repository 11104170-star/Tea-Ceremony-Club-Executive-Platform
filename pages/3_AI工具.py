import streamlit as st

from utils.ai_tools import (
    AI_TOOL_TYPES,
    default_hf_model,
    default_hf_vision_model,
    default_groq_model,
    generate_ai_tool_content,
)
from utils.auth import require_login, logout_button
from utils.calendar_store import format_event_label, load_events
from utils.teacher_comment import DEFAULT_GROQ_MODEL


st.set_page_config(
    page_title="AI工具 | 茶道社幹部平台",
    page_icon="🍵",
    layout="wide",
)

require_login()


def secret_value(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, default)).strip()
    except Exception:
        return default


def event_to_material(event: dict[str, str]) -> str:
    lines = [
        f"活動名稱：{event.get('活動名稱', '')}",
        f"日期：{event.get('日期', '')}",
        f"活動負責人：{event.get('活動負責人', '')}",
        f"地點：{event.get('地點', '')}",
        f"備註：{event.get('備註', '')}",
    ]
    return "\n".join(line for line in lines if not line.endswith("："))


def selected_ai_config(model_choice: str) -> dict[str, str]:
    config = {
        "gemini_api_key": secret_value("GEMINI_API_KEY"),
        "gemini_model": secret_value("GEMINI_MODEL", "gemini-2.5-flash"),
        "groq_api_key": secret_value("GROQ_API_KEY"),
        "groq_model": secret_value("GROQ_MODEL", default_groq_model() or DEFAULT_GROQ_MODEL),
        "hf_api_key": secret_value("HF_API_KEY"),
        "hf_model": secret_value("HF_MODEL", default_hf_model()),
        "hf_vision_model": secret_value("HF_VISION_MODEL", default_hf_vision_model()),
    }

    if model_choice == "Gemini":
        config["groq_api_key"] = ""
        config["hf_api_key"] = ""
    elif model_choice == "Groq":
        config["gemini_api_key"] = ""
        config["hf_api_key"] = ""
    elif model_choice == "Hugging Face":
        config["gemini_api_key"] = ""
        config["groq_api_key"] = ""
    elif model_choice == "Hugging Face Vision":
        config["gemini_api_key"] = ""
        config["groq_api_key"] = ""
        config["hf_model"] = config["hf_vision_model"]

    return config


with st.sidebar:
    st.success("已登入")
    logout_button()

st.title("AI工具")
st.caption("協助產生活動文案、LINE 小宣、公告草稿、會議紀錄與行政訊息。")

events = load_events()
event_options = ["不帶入行事曆"] + [format_event_label(event) for event in events]
selected_event_label = st.selectbox("從行事曆帶入資料", event_options)
selected_event = None
if selected_event_label != "不帶入行事曆":
    selected_event = events[event_options.index(selected_event_label) - 1]

if "ai_tool_material" not in st.session_state:
    st.session_state["ai_tool_material"] = ""

if selected_event:
    event_material = event_to_material(selected_event)
    col_apply, col_hint = st.columns([1, 4])
    with col_apply:
        if st.button("套用行事曆資料"):
            st.session_state["ai_tool_material"] = event_material
            st.session_state["ai_tool_activity_name"] = selected_event.get("活動名稱", "")
            st.rerun()
    with col_hint:
        st.caption("套用後仍可手動修改素材，再交給 AI 生成。")

with st.form("ai_tool_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        tool_type = st.selectbox("工具類型", AI_TOOL_TYPES)
    with col2:
        target = st.selectbox("使用對象", ["社員", "幹部", "指導老師", "課外組", "校內師生"])
    with col3:
        tone = st.selectbox("語氣", ["清楚親切", "正式行政", "活潑社群", "簡短提醒"])

    col4, col5 = st.columns([2, 1])
    with col4:
        activity_name = st.text_input(
            "活動或主題名稱",
            key="ai_tool_activity_name",
            placeholder="例：封箱茶會、幹部會議、期初社課",
        )
    with col5:
        length = st.selectbox("篇幅", ["短版", "一般", "詳細"])

    model_choice = st.selectbox(
        "AI 模型",
        ["自動", "Gemini", "Groq", "Hugging Face", "Hugging Face Vision"],
        help=(
            "自動：有圖片時 Gemini → Hugging Face Vision；無圖片時 Gemini → Groq → Hugging Face。"
            "Groq 只能處理文字，Hugging Face Vision 適合讀小宣圖片。"
        ),
    )

    material = st.text_area(
        "輸入素材",
        key="ai_tool_material",
        height=220,
        placeholder="貼上社課小宣、活動資訊、流程、會議原始紀錄或想傳達的重點...",
    )
    images = st.file_uploader(
        "上傳小宣圖片或活動海報",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        help="可上傳社課小宣截圖或活動海報；AI 會讀取圖片文字與內容後產生文案。",
    )

    submitted = st.form_submit_button("產生內容", type="primary")

if submitted:
    if not activity_name.strip() and not material.strip() and not images:
        st.error("請至少輸入活動名稱、素材，或上傳小宣圖片。")
    elif images and model_choice == "Groq":
        st.error("Groq 不能讀圖片。請改選「自動」、「Gemini」或「Hugging Face Vision」。")
    elif not images and model_choice == "Hugging Face Vision":
        st.error("Hugging Face Vision 需要上傳圖片。純文字請改選「自動」、「Gemini」、「Groq」或「Hugging Face」。")
    else:
        ai_config = selected_ai_config(model_choice)
        with st.spinner("正在用 AI 生成內容..."):
            result = generate_ai_tool_content(
                gemini_api_key=ai_config["gemini_api_key"],
                gemini_model=ai_config["gemini_model"],
                groq_api_key=ai_config["groq_api_key"],
                groq_model=ai_config["groq_model"],
                hf_api_key=ai_config["hf_api_key"],
                hf_model=ai_config["hf_model"],
                hf_vision_model=ai_config["hf_vision_model"],
                tool_type=tool_type,
                material=material,
                activity_name=activity_name,
                target=target,
                tone=tone,
                length=length,
                images=images,
            )

        st.session_state["ai_tool_result"] = result
        st.session_state["ai_tool_model_choice"] = model_choice

st.subheader("輸出結果")
result = st.session_state.get("ai_tool_result")
if result:
    st.success(str(result.get("status", "已產生內容。")))
    if result.get("provider") and result.get("provider") != "本機草稿":
        st.caption(f"調用模型：{result.get('provider')} / {result.get('model')}")
    if st.session_state.get("ai_tool_model_choice"):
        st.caption(f"選擇模式：{st.session_state['ai_tool_model_choice']}")

    st.text_area(
        "產生結果",
        value=str(result.get("text", "")),
        height=300,
        key="ai_tool_result_text",
    )

    with st.expander("模型資訊", expanded=False):
        st.json(result.get("debug", {}))
else:
    st.info("選擇工具類型並輸入素材後，就可以產生可直接使用的文字。")
