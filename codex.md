# Codex Notes

## Project

茶道社幹部平台，使用 Streamlit 多頁架構，主要服務茶道社幹部處理成果書、問卷分析、AI 文案、幹部名單與行事曆。

## Run

```bash
streamlit run app.py
```

## Key Pages

- `app.py`: 首頁與登入入口；登入後顯示平台功能、快速跳轉、小型平台說明與「問 AI 怎麼操作」。
- `pages/1_成果書生成.py`: 成果書生成、問卷分析結果填入 Word、活動負責人選擇、行事曆活動帶入、Gemini 生成活動內容概述與老師評語。
- `pages/2_問卷分析.py`: 問卷資料分析。
- `pages/3_AI工具.py`: AI 輔助工具，可從行事曆帶入資料或上傳小宣圖片，並產生 LINE 官方帳號活動預告、公告、貼文、成果摘要、會議紀錄與行政訊息；可選自動模型或指定 Gemini、Groq、Hugging Face、Hugging Face Vision。
- `pages/4_幹部管理.py`: 幹部名單管理，提供成果書與行事曆的活動負責人選項。
- `pages/5_行事曆.py`: 月曆式活動管理，可供成果書帶入活動資料。
- `pages/6_活動申請書生成.py`: 活動申請書生成，可從行事曆與幹部名單帶入活動資料。
- `pages/7_常用連結.py`: 幹部常用網站入口，可新增、刪除、排序與直接跳轉；私密連結由 Streamlit Secrets 載入。

## Current Behavior

- 成果書的填寫日期使用 `st.date_input` 月曆選擇器。
- 填寫日期預設使用 `Asia/Taipei`，輸出為民國格式：`XXX 年 X 月 X 日`。
- 成果書活動負責人只輸出姓名，不輸出職位或學號。
- 行事曆活動欄位使用 `活動負責人`，不使用時間欄位。
- 從行事曆選取活動時，會自動帶入活動名稱、日期、地點與活動負責人。
- 活動申請書使用 `assets/活動申請書模板.docx`，只替換 `{{...}}` 標註欄位，不調整未標註內容；活動進行可由活動名稱透過 AI 生成，一行一個流程，並可勾選是否包含破冰活動、點心 DIY 與健康聊齋；活動宗旨可再依活動進行生成。
- AI 工具頁使用 `utils/ai_tools.py`，支援行事曆資料套用、文字用途選擇、語氣與篇幅選擇；AI 失敗時會產生本機草稿。
- 首頁登入後顯示小型網站使用說明與頁面跳轉連結，也可輸入操作問題讓 Gemini/Groq 回答；AI 失敗時使用本機回答。
- 常用連結預設包含課外組空間借用頁面，公開資料儲存在 `data/useful_links.json`。
- 私密連結從 `OFFICER_UPLOAD_URL` / `PRIVATE_LINKS` 讀取，不寫入 GitHub，適合幹部雲端資料上傳網址。
- 幹部職位固定為：社長、副社長、總務、攝錄、點心、文書。
- 幹部列表可刪除、上移、下移、移到最上面。
- AI 生成會先使用 Gemini；若 Gemini 失敗或額度用完，會使用 Groq 作為文字備用模型；若 Groq 也失敗，會使用 Hugging Face 作為第三順位文字備援。
- AI 正常產出時顯示「AI 順利產出」與實際調用模型；若有修復或 fallback，才顯示預覽內容。

## Persistent Data

- `data/officers.json`: 幹部名單。
- `data/calendar_events.json`: 行事曆活動。
- `data/useful_links.json`: 常用連結。
- 若設定 `GITHUB_TOKEN`，資料會優先永久寫入 GitHub repo。
- 未設定 `GITHUB_TOKEN` 時，改用本機檔案儲存。

GitHub data writes may create remote commits such as `Update officer list` and `Update calendar events`. Before pushing code changes, always fetch and rebase onto `origin/main` so online data commits are preserved.

## Secrets

Streamlit Secrets 可設定：

```toml
PASSWORD = "平台密碼"
GEMINI_API_KEY = "Gemini API key"
GEMINI_MODEL = "gemini-2.5-flash"
GROQ_API_KEY = "Groq API key"
GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
HF_API_KEY = "Hugging Face token"
HF_MODEL = "openai/gpt-oss-120b:fastest"
HF_VISION_MODEL = "CohereLabs/aya-vision-32b:cohere"
GITHUB_TOKEN = "GitHub fine-grained token"
OFFICER_UPLOAD_URL = "幹部資料上傳網址"
OFFICER_UPLOAD_NAME = "幹部資料上傳"
```

`GITHUB_TOKEN` 需要 repo `Contents` 的 read/write 權限。

`GEMINI_MODEL` 目前預設為 `gemini-2.5-flash`。Gemini calls in `utils/teacher_comment.py` disable thinking for short report text and request enough output tokens to avoid truncated responses.

`GROQ_MODEL` 目前預設為 `meta-llama/llama-4-scout-17b-16e-instruct`。Groq fallback uses the OpenAI-compatible chat completions endpoint and is text-only, so activity overview fallback relies on photo descriptions rather than image bytes.

`HF_MODEL` 目前預設為 `openai/gpt-oss-120b:fastest`，透過 Hugging Face Inference Providers OpenAI-compatible chat completions endpoint 作為文字備援。`HF_VISION_MODEL` 目前預設為 `CohereLabs/aya-vision-32b:cohere`，用在成果書照片讀圖備援。

