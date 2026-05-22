from __future__ import annotations

from utils.teacher_comment import (
    DEFAULT_GROQ_MODEL,
    DEFAULT_HF_MODEL,
    DEFAULT_HF_VISION_MODEL,
    generate_ai_result,
    result_source,
)


AI_TOOL_TYPES = [
    "LINE官方帳號活動預告",
    "活動公告",
    "社群貼文",
    "成果摘要",
    "會議紀錄整理",
    "行政訊息",
]

TOOL_REQUIREMENTS = {
    "LINE官方帳號活動預告": (
        "請把輸入的小宣、活動資訊或零散文字，改寫成 LINE 官方帳號可直接發送的茶道社活動預告。"
        "格式必須像茶道社 LINE 官方帳號小宣：開頭是總預告，接著放最近一場提醒，"
        "再依日期分段列出活動；若有不用報名、報名提醒、費用、地點、茶品、點心或晚餐，"
        "請放在醒目位置。只要活動有報名費、費用、收費或社員免費資訊，就必須提醒「請於活動前兩天完成報名」。"
        "語氣輕鬆、有溫度、吸引人，但不要過度浮誇。可使用適量 emoji，例如 🌿 🍵 ✨ 📅 📍 💰 ⏰。"
    ),
    "活動公告": (
        "請輸出可直接貼到社團群組的活動公告，包含標題、活動資訊、活動內容、"
        "注意事項與一句提醒。語氣清楚親切，不要過度浮誇。"
    ),
    "社群貼文": (
        "請輸出適合 Instagram 或 Facebook 的社群貼文，包含一段主文與 3 到 6 個相關標籤。"
        "語氣活潑但仍符合學校社團形象，不要使用過多 emoji。"
    ),
    "成果摘要": (
        "請輸出適合放入成果紀錄或回報訊息的摘要，內容要具體描述活動做了什麼、"
        "參與者完成什麼，以及可以延伸追蹤的重點。"
    ),
    "會議紀錄整理": (
        "請將原始紀錄整理成正式會議紀錄，包含會議重點、決議事項、待辦事項、"
        "負責人與下次確認事項。若資料沒有負責人，不要自行捏造。"
    ),
    "行政訊息": (
        "請輸出可傳給幹部或社員的行政訊息，包含目的、需要對方完成的事項、期限或提醒。"
        "語氣禮貌、明確、好執行。"
    ),
}


def build_ai_tool_prompt(
    *,
    tool_type: str,
    material: str,
    activity_name: str,
    target: str,
    tone: str,
    length: str,
) -> str:
    requirement = TOOL_REQUIREMENTS.get(tool_type, TOOL_REQUIREMENTS["行政訊息"])
    return f"""
請根據以下資料產生茶道社幹部可使用的文字。

工具類型：{tool_type}
活動或主題名稱：{activity_name or "未填"}
使用對象：{target}
語氣：{tone}
篇幅：{length}

寫作任務：
{requirement}

共同要求：
- 使用繁體中文。
- 內容要能直接複製使用。
- 不要捏造未提供的日期、地點、費用、姓名或活動細節。
- 如果資料不足，請以「可補上：」標示需要人工補充的資訊。
- 不要輸出前言或解釋，不要說「以下是」。
- 避免空泛套話，例如「豐富多元」、「收穫良多」、「圓滿成功」。
- 若有上傳圖片，圖片可能是社課小宣、活動海報或截圖；請優先讀取圖片中的日期、活動名稱、地點、費用、報名資訊與餐點/茶品，再結合輸入素材撰寫。

LINE官方帳號活動預告的額外要求：
- 必須模仿以下架構，不要改成正式公文：
  1. 第一行：「🌿 茶道社｜X月活動總預告 🍵」或「🌿 茶道社｜活動名稱 🍵」。
  2. 接 1 到 2 行總開場，例如「X月準備了不同主題的茶活動」。
  3. 若可判斷最近一場，加入「✨ 最近一場｜...」並把最重要提醒放在這裡。
  4. 每場活動用「📅 日期」開頭，下一行放活動名稱，再用短句寫亮點。
  5. 茶品、點心或晚餐用「🍃」、「🍱」、「🍞」等符號列出。
  6. 時間用「⏰」，地點用「📍」，費用用「💰」。
  7. 結尾用 2 到 3 行邀請大家來喝茶、吃點東西、認識新朋友。
- 若素材包含多場活動，請依日期分段整理，每場保留活動名稱、亮點、茶品或點心、時間、地點、費用與報名提醒。
- 若素材只有單場活動，也要寫成 LINE 可直接發送的小宣，不要變成正式公文。
- 「不用報名」、「社員免費」、「快點報名」、「最近一場」這類提醒要放明顯。
- 只要某場活動有「報名費」、「費用」、「收費」、「社員免費」、「元」、「$」等資訊，就必須在該場活動段落加上「❗請於活動前兩天完成報名」或語意相同的提醒。
- 若活動明確寫「不用報名」，就不要加活動前兩天報名提醒。
- emoji 可以使用，但每行不要過度堆疊。

輸入素材：
{material or "未提供"}
""".strip()


def fallback_ai_tool_content(
    *,
    tool_type: str,
    material: str,
    activity_name: str,
    target: str,
    tone: str,
    length: str,
) -> str:
    title = activity_name.strip() or "茶道社活動"
    body = material.strip() or "可補上：活動時間、地點、流程、注意事項。"

    if tool_type == "LINE官方帳號活動預告":
        return (
            f"🌿 茶道社｜{title} 🍵\n\n"
            "這次準備了不同主題的茶活動\n"
            "有體驗、有美食，也有輕鬆聊天的時光 ✨\n\n"
            "✨ 最近一場｜請留意活動資訊\n"
            f"📌 活動資訊\n{body}\n\n"
            "💰 若本場活動有報名費或費用，請於活動前兩天完成報名。\n\n"
            "想喝杯茶、吃點東西、認識新朋友的話，歡迎直接來找我們。\n"
            "詳細報名、費用與地點請以幹部最新公告為準 🍃"
        )

    if tool_type == "活動公告":
        return (
            f"【{title}】\n"
            f"各位{target}好，茶道社將辦理「{title}」。\n\n"
            f"活動重點：\n{body}\n\n"
            "請大家留意活動時間、地點與需攜帶物品；若有不克參與或需要協助的情況，請提前告知幹部。"
        )

    if tool_type == "社群貼文":
        return (
            f"{title}紀錄\n\n"
            f"{body}\n\n"
            "透過這次活動，我們一起認識茶道流程，也在實作中累積社課經驗。\n\n"
            "#茶道社 #社團活動 #茶文化 #社課紀錄"
        )

    if tool_type == "成果摘要":
        return (
            f"{title}以茶道學習與社課交流為主軸，活動內容包含：{body}。"
            "後續可依參與情形與幹部檢討，補充活動成效與需要調整的流程。"
        )

    if tool_type == "會議紀錄整理":
        return (
            f"{title}會議紀錄\n\n"
            f"一、會議重點\n{body}\n\n"
            "二、決議事項\n可補上：本次會議確認的事項。\n\n"
            "三、待辦事項\n可補上：待辦內容、負責人與期限。\n\n"
            "四、下次確認\n可補上：下次需要追蹤的項目。"
        )

    return (
        f"各位{target}好，關於「{title}」有以下事項需要協助確認：\n\n"
        f"{body}\n\n"
        "請依照訊息內容協助完成，若有問題請提前告知，方便幹部後續統整。"
    )


def generate_ai_tool_content(
    *,
    gemini_api_key: str | None,
    gemini_model: str,
    groq_api_key: str | None,
    groq_model: str,
    tool_type: str,
    material: str,
    activity_name: str,
    target: str,
    tone: str,
    length: str,
    hf_api_key: str | None = None,
    hf_model: str = DEFAULT_HF_MODEL,
    hf_vision_model: str = DEFAULT_HF_VISION_MODEL,
    images: list[object] | None = None,
) -> dict[str, object]:
    if not gemini_api_key and not groq_api_key and not hf_api_key:
        return {
            "text": fallback_ai_tool_content(
                tool_type=tool_type,
                material=material,
                activity_name=activity_name,
                target=target,
                tone=tone,
                length=length,
            ),
            "status": "未設定 API key，已使用本機草稿。",
            "provider": "本機草稿",
            "model": "",
            "debug": {},
        }

    prompt = build_ai_tool_prompt(
        tool_type=tool_type,
        material=material,
        activity_name=activity_name,
        target=target,
        tone=tone,
        length=length,
    )
    system_instruction = "你是茶道社幹部的行政文字助手，專門產生可直接使用的繁體中文社團文案。"

    try:
        result = generate_ai_result(
            gemini_api_key=gemini_api_key,
            gemini_model=gemini_model,
            groq_api_key=groq_api_key,
            groq_model=groq_model,
            hf_api_key=hf_api_key,
            hf_model=hf_model,
            hf_vision_model=hf_vision_model,
            system_instruction=system_instruction,
            prompt=prompt,
            images=images,
        )
    except RuntimeError as exc:
        return {
            "text": fallback_ai_tool_content(
                tool_type=tool_type,
                material=material,
                activity_name=activity_name,
                target=target,
                tone=tone,
                length=length,
            ),
            "status": f"AI 呼叫失敗，已使用本機草稿。{exc}",
            "provider": "本機草稿",
            "model": "",
            "debug": {},
        }

    return {
        "text": str(result.get("text", "")).strip(),
        "status": f"使用 {result_source(result)} 產生。",
        "provider": result.get("provider", "AI"),
        "model": result.get("model", ""),
        "debug": result.get("debug", {}),
    }


def fallback_site_usage_guide() -> str:
    return "先到「幹部管理」建立名單，再用「行事曆」建立活動；成果書、活動申請書與 AI 工具都可以接著使用這些資料。"


SITE_FEATURES = """
平台頁面：
- 成果書生成：從行事曆帶入活動資料，上傳問卷與照片，產生 Word 成果書，可用 AI 生成活動內容概述與指導老師評語。
- 問卷分析：匯入問卷資料並檢視分析結果。
- AI工具：產生活動公告、社群貼文、成果摘要、會議紀錄整理與行政訊息。
- 幹部管理：建立與排序幹部名單，職位包含社長、副社長、總務、攝錄、點心、文書。
- 行事曆：用月曆管理社課、會議與活動，填寫日期、活動名稱、活動負責人、地點與備註。
- 活動申請書生成：從行事曆與幹部名單帶入資料，可用 AI 產生活動進行與活動宗旨，下載 Word 申請書。
- 常用連結：整理幹部常用網站，私密雲端上傳網址從 Secrets 載入。
""".strip()


def fallback_site_help_answer(question: str) -> str:
    normalized = question.strip()
    if not normalized:
        return "請先輸入想問的操作，例如「我要做成果書要去哪裡？」或「我要新增活動負責人怎麼做？」"

    if any(keyword in normalized for keyword in ("成果", "成果書", "照片", "問卷")):
        return "請前往「成果書生成」。建議先在「行事曆」建立活動並在「幹部管理」建立負責人，進入成果書頁後選取行事曆活動、上傳問卷與照片，再產生 Word 檔。"

    if any(keyword in normalized for keyword in ("申請", "活動宗旨", "活動進行", "計畫書")):
        return "請前往「活動申請書生成」。可以先從行事曆帶入活動資料，再填副負責人、電話、茶品與點心；活動進行和活動宗旨可用 AI 產生，送出前請檢查流程是否合理。"

    if any(keyword in normalized for keyword in ("幹部", "負責人", "職位", "社員")):
        return "請前往「幹部管理」。在那裡新增幹部姓名、學號與職位，也可以調整順序；成果書和行事曆選活動負責人時會使用這份名單。"

    if any(keyword in normalized for keyword in ("行事曆", "活動", "日期", "月曆")):
        return "請前往「行事曆」。新增活動時填日期、活動名稱、活動負責人、地點與備註，之後成果書和活動申請書就能直接選取並帶入資料。"

    if any(keyword in normalized for keyword in ("公告", "貼文", "會議", "行政", "文案")):
        return "請前往「AI工具」。選擇活動公告、社群貼文、成果摘要、會議紀錄整理或行政訊息，輸入素材後產生草稿，再依實際情況修改。"

    if any(keyword in normalized for keyword in ("連結", "網址", "上傳", "雲端")):
        return "請前往「常用連結」。公開網站可直接新增到頁面；不能放在 GitHub 的雲端上傳網址要放在 Streamlit Secrets，會顯示在私密連結區。"

    return "可以先從首頁的功能連結進入相關頁面。若是要建立基本資料，先用「幹部管理」與「行事曆」；若要產生文件，使用「成果書生成」或「活動申請書生成」；若只是要寫文字草稿，使用「AI工具」。"


def generate_site_usage_guide(
    *,
    gemini_api_key: str | None,
    gemini_model: str,
    groq_api_key: str | None,
    groq_model: str,
    hf_api_key: str | None = None,
    hf_model: str = DEFAULT_HF_MODEL,
) -> dict[str, object]:
    fallback_text = fallback_site_usage_guide()

    if not gemini_api_key and not groq_api_key and not hf_api_key:
        return {
            "text": fallback_text,
            "status": "未設定 API key，已使用本機說明。",
            "provider": "本機說明",
            "model": "",
            "debug": {},
        }

    prompt = f"""
請替茶道社幹部平台產生首頁簡短使用說明，放在登入後首頁的小型說明區塊。

{SITE_FEATURES}

要求：
- 使用繁體中文。
- 只寫 2 到 3 句，不要超過 120 字。
- 語氣清楚、親切、像幹部交接文件，不要像廣告。
- 不要提到程式碼、repo、GitHub token 或內部實作。
- 不要使用條列符號，直接用自然段落。
""".strip()

    try:
        result = generate_ai_result(
            gemini_api_key=gemini_api_key,
            gemini_model=gemini_model,
            groq_api_key=groq_api_key,
            groq_model=groq_model,
            hf_api_key=hf_api_key,
            hf_model=hf_model,
            system_instruction="你是茶道社幹部平台的使用說明編輯，專門寫清楚、可執行的繁體中文操作指引。",
            prompt=prompt,
        )
    except RuntimeError as exc:
        return {
            "text": fallback_text,
            "status": f"AI 呼叫失敗，已使用本機說明。{exc}",
            "provider": "本機說明",
            "model": "",
            "debug": {},
        }

    return {
        "text": str(result.get("text", "")).strip() or fallback_text,
        "status": f"使用 {result_source(result)} 產生。",
        "provider": result.get("provider", "AI"),
        "model": result.get("model", ""),
        "debug": result.get("debug", {}),
    }


def generate_site_help_answer(
    *,
    gemini_api_key: str | None,
    gemini_model: str,
    groq_api_key: str | None,
    groq_model: str,
    question: str,
    hf_api_key: str | None = None,
    hf_model: str = DEFAULT_HF_MODEL,
) -> dict[str, object]:
    fallback_text = fallback_site_help_answer(question)

    if not gemini_api_key and not groq_api_key and not hf_api_key:
        return {
            "text": fallback_text,
            "status": "未設定 API key，已使用本機回答。",
            "provider": "本機回答",
            "model": "",
            "debug": {},
        }

    prompt = f"""
使用者正在茶道社幹部平台首頁詢問操作方式，請根據平台功能回答。

{SITE_FEATURES}

使用者問題：
{question}

回答要求：
- 使用繁體中文。
- 回答要短，3 到 5 句內。
- 明確告訴使用者應該前往哪個頁面。
- 若需要前置步驟，請用「先...再...」說明。
- 不要提到程式碼、repo、API key 或內部實作。
- 不要捏造平台不存在的功能。
""".strip()

    try:
        result = generate_ai_result(
            gemini_api_key=gemini_api_key,
            gemini_model=gemini_model,
            groq_api_key=groq_api_key,
            groq_model=groq_model,
            hf_api_key=hf_api_key,
            hf_model=hf_model,
            system_instruction="你是茶道社幹部平台的操作客服，只回答此平台實際有的功能與頁面。",
            prompt=prompt,
        )
    except RuntimeError as exc:
        return {
            "text": fallback_text,
            "status": f"AI 呼叫失敗，已使用本機回答。{exc}",
            "provider": "本機回答",
            "model": "",
            "debug": {},
        }

    return {
        "text": str(result.get("text", "")).strip() or fallback_text,
        "status": f"使用 {result_source(result)} 回答。",
        "provider": result.get("provider", "AI"),
        "model": result.get("model", ""),
        "debug": result.get("debug", {}),
    }


def default_groq_model() -> str:
    return DEFAULT_GROQ_MODEL


def default_hf_model() -> str:
    return DEFAULT_HF_MODEL


def default_hf_vision_model() -> str:
    return DEFAULT_HF_VISION_MODEL
