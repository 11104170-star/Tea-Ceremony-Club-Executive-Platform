import streamlit as st

from utils.auth import init_auth_state, logout_button


st.set_page_config(
    page_title="茶道社幹部平台",
    page_icon="🍵",
    layout="wide",
)

init_auth_state()

st.title("茶道社幹部平台")
st.caption("社團幹部日常作業入口")

with st.sidebar:
    st.header("茶道社幹部平台")
    if st.session_state["authenticated"]:
        st.success("已登入")
        logout_button()
    else:
        st.info("請先登入後使用功能頁面")


if st.session_state["authenticated"]:
    st.success("登入成功，請從左側 sidebar 選擇功能頁面。")

    st.subheader("平台功能")
    col1, col2 = st.columns(2)

    with col1:
        st.info("成果書生成\n\n整理活動資料並產生成果書文件。")
        st.info("活動申請書生成\n\n帶入活動資料並產生申請計畫書。")
        st.info("問卷分析\n\n匯入問卷資料並檢視分析結果。")

    with col2:
        st.info("AI工具\n\n提供幹部行政與文案輔助工具。")
        st.info("幹部管理\n\n維護幹部資料與職位分工。")
        st.info("行事曆\n\n記錄社課、會議與活動時程。")
else:
    st.subheader("登入")
    password = st.text_input("請輸入平台密碼", type="password")

    if st.button("登入", type="primary"):
        if password == st.secrets["PASSWORD"]:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("密碼錯誤，請再試一次。")
