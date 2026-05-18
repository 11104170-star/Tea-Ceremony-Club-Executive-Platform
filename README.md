# 茶道社幹部平台

Streamlit 多頁平台專案，提供茶道社幹部日常行政作業入口。首頁負責登入，成果書、問卷分析、AI 工具、幹部管理與行事曆功能放在 `pages` 資料夾由 Streamlit 自動管理。

## 專案結構

```text
.
├── app.py
├── assets
│   └── 成果書模板_已標記.docx
├── pages
│   ├── 1_成果書生成.py
│   ├── 2_問卷分析.py
│   ├── 3_AI工具.py
│   ├── 4_幹部管理.py
│   └── 5_行事曆.py
├── data
│   ├── calendar_events.json
│   └── officers.json
├── utils
│   ├── __init__.py
│   ├── achievement_report.py
│   ├── auth.py
│   ├── calendar_store.py
│   ├── github_json_store.py
│   ├── officer_store.py
│   ├── report_filename.py
│   └── teacher_comment.py
├── requirements.txt
└── .streamlit
    └── secrets.toml.example
```

## 啟動方式

1. 安裝套件：

```bash
pip install -r requirements.txt
```

2. 建立 `.streamlit/secrets.toml`：

```toml
PASSWORD = "你的平台密碼"
GEMINI_API_KEY = "你的 Gemini API key"
GEMINI_MODEL = "gemini-2.5-flash"
GROQ_API_KEY = "你的 Groq API key"
GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
GITHUB_TOKEN = "你的 GitHub fine-grained token"
```

3. 啟動平台：

```bash
streamlit run app.py
```

## 成果書生成

`成果書生成` 頁面已整合舊成果書系統，可使用內建 Word 範本，也可以上傳自訂 `.docx` 範本。問卷資料支援 `.xlsx` 與 `.csv`，照片支援 `.jpg`、`.jpeg`、`.png`。

主要功能：

- 可從行事曆選取活動並自動帶入活動名稱、日期、地點與活動負責人。
- 活動負責人來自幹部名單，成果書只寫入姓名。
- 填寫日期使用月曆選擇器，預設抓台灣時區日期，輸出格式為 `XXX 年 X 月 X 日`。
- 可由照片與照片說明使用 Gemini 生成活動內容概述。
- 可由活動檢討與照片說明使用 Gemini 生成指導老師評語。
- Gemini 失敗或額度用完時，可用 Groq 作為文字備用模型；頁面會顯示實際調用的 provider 與 model。
- 若 AI 輸出正常，頁面只顯示 AI 順利產出；若使用修復或模板，會顯示預覽供檢查。

未設定 `GEMINI_API_KEY` / `GROQ_API_KEY` 或所有 AI 呼叫失敗時，會使用本機規則產生可編輯草稿。

## 幹部管理

`幹部管理` 頁面維護成果書與行事曆使用的幹部名單。支援職位：

- 社長
- 副社長
- 總務
- 攝錄
- 點心
- 文書

幹部列表可刪除、上移、下移，也可以直接移到最上面。

## 行事曆

`行事曆` 頁面以月曆方式顯示活動，可新增與刪除活動。活動資料包含日期、活動名稱、活動負責人、地點與備註。活動負責人可從幹部名單選擇；若尚未建立幹部，也可手動輸入姓名。

## 永久儲存

若設定 `GITHUB_TOKEN`，幹部名單與行事曆會永久寫入 GitHub repo 的 `data/officers.json` 與 `data/calendar_events.json`。Token 需要能讀寫此 repo 的 Contents。未設定時會改用本機檔案儲存。

Streamlit Cloud 上若多人同時操作，GitHub 可能會出現 `Update officer list` 或 `Update calendar events` 之類的資料 commit。推送程式碼前請先 `git fetch origin main` 並 rebase，避免覆蓋線上資料。
