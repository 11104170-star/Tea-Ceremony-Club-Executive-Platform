# Codex Notes

## Project

茶道社幹部平台，使用 Streamlit 多頁架構，主要服務茶道社幹部處理成果書、問卷分析、AI 文案、幹部名單與行事曆。

## Run

```bash
streamlit run app.py
```

## Key Pages

- `app.py`: 首頁與登入入口。
- `pages/1_成果書生成.py`: 成果書生成、問卷分析結果填入 Word、活動負責人選擇、行事曆活動帶入、Gemini 生成活動內容概述與老師評語。
- `pages/2_問卷分析.py`: 問卷資料分析。
- `pages/3_AI工具.py`: AI 輔助工具入口。
- `pages/4_幹部管理.py`: 幹部名單管理，提供成果書與行事曆的活動負責人選項。
- `pages/5_行事曆.py`: 月曆式活動管理，可供成果書帶入活動資料。

## Current Behavior

- 成果書的填寫日期使用 `st.date_input` 月曆選擇器。
- 填寫日期預設使用 `Asia/Taipei`，輸出為民國格式：`XXX 年 X 月 X 日`。
- 成果書活動負責人只輸出姓名，不輸出職位或學號。
- 行事曆活動欄位使用 `活動負責人`，不使用時間欄位。
- 從行事曆選取活動時，會自動帶入活動名稱、日期、地點與活動負責人。
- 幹部職位固定為：社長、副社長、總務、攝錄、點心、文書。
- 幹部列表可刪除、上移、下移、移到最上面。
- Gemini 正常產出時只顯示「AI 順利產出」；若有修復或 fallback，才顯示預覽內容。

## Persistent Data

- `data/officers.json`: 幹部名單。
- `data/calendar_events.json`: 行事曆活動。
- 若設定 `GITHUB_TOKEN`，資料會優先永久寫入 GitHub repo。
- 未設定 `GITHUB_TOKEN` 時，改用本機檔案儲存。

GitHub data writes may create remote commits such as `Update officer list` and `Update calendar events`. Before pushing code changes, always fetch and rebase onto `origin/main` so online data commits are preserved.

## Secrets

Streamlit Secrets 可設定：

```toml
PASSWORD = "平台密碼"
GEMINI_API_KEY = "Gemini API key"
GEMINI_MODEL = "gemini-2.5-flash"
GITHUB_TOKEN = "GitHub fine-grained token"
```

`GITHUB_TOKEN` 需要 repo `Contents` 的 read/write 權限。

`GEMINI_MODEL` 目前預設為 `gemini-2.5-flash`。Gemini calls in `utils/teacher_comment.py` disable thinking for short report text and request enough output tokens to avoid truncated responses.

## Git

Remote 使用 SSH：

```text
git@github.com:11104170-star/Tea-Ceremony-Club-Executive-Platform.git
```
