from __future__ import annotations

import base64
import json
from urllib import error, parse, request


def generate_gemini_text(
    *,
    api_key: str,
    model: str,
    system_instruction: str,
    prompt: str,
    images: list[object] | None = None,
) -> str:
    parts = [{"text": prompt}]

    for image in images or []:
        if image is None:
            continue

        mime_type = getattr(image, "type", None) or "image/png"
        image_data = base64.b64encode(image.getvalue()).decode("ascii")
        parts.append(
            {
                "inlineData": {
                    "mimeType": mime_type,
                    "data": image_data,
                }
            }
        )

    payload = {
        "systemInstruction": {
            "parts": [{"text": system_instruction}],
        },
        "contents": [
            {
                "role": "user",
                "parts": parts,
            }
        ],
        "generationConfig": {
            "maxOutputTokens": 500,
            "temperature": 0.4,
            "topP": 0.8,
        },
    }
    encoded_model = parse.quote(model, safe="")
    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/{encoded_model}:generateContent"
    )
    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
    )

    try:
        with request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, error.HTTPError, json.JSONDecodeError) as exc:
        raise RuntimeError("Gemini API 呼叫失敗，請確認 GEMINI_API_KEY 與 GEMINI_MODEL。") from exc

    texts = []
    for candidate in data.get("candidates", []):
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            text = part.get("text")
            if text:
                texts.append(text)

    generated_text = "\n".join(texts).strip()
    if not generated_text:
        raise RuntimeError("Gemini API 未回傳文字內容。")

    return generated_text


def clean_generated_text(text: str) -> str:
    cleaned = text.strip()
    cleaned = cleaned.removeprefix("```").removesuffix("```").strip()
    cleaned = cleaned.replace("\n", "")
    return cleaned


def fallback_teacher_comment(
    *,
    activity_name: str,
    activity_review: str,
    photo_descriptions: list[str],
) -> str:
    descriptions = [item.strip() for item in photo_descriptions if item.strip()]

    if descriptions:
        photo_summary = "、".join(descriptions)
        detail = f"從照片紀錄可見，活動包含{photo_summary}等內容，展現出社團活動的完整規劃與執行成果。"
    else:
        detail = "從活動紀錄可見，活動流程安排完整，參與同學能在過程中投入學習並完成預定目標。"

    review_sentence = ""
    if activity_review.strip():
        review_sentence = f"幹部亦能針對活動進行檢討，包含「{activity_review.strip()}」，有助於後續活動持續精進。"

    name = activity_name.strip() or "本次活動"

    return (
        f"{name}整體辦理情形良好，活動內容具教育意義，並能呈現茶道社重視禮節、實作與團隊合作的精神。"
        f"{detail}{review_sentence}期許社團持續累積經驗，讓未來活動更加完善。"
    )


def fallback_activity_overview(
    *,
    activity_name: str,
    photo_descriptions: list[str],
) -> str:
    descriptions = [item.strip() for item in photo_descriptions if item.strip()]
    name = activity_name.strip() or "本次活動"

    if descriptions:
        joined_descriptions = "、".join(descriptions)
        return (
            f"{name}以茶道學習與實作體驗為核心，透過{joined_descriptions}等活動內容，"
            "引導參與者認識茶席禮儀、茶具使用與泡茶流程，並在實際操作中體會茶道文化的精神。"
        )

    return (
        f"{name}以茶道學習與實作體驗為主軸，安排社員參與茶道相關流程，"
        "讓參與者在活動中認識茶文化、培養禮節觀念，並增進社團成員之間的互動與合作。"
    )


def is_weak_activity_overview(text: str) -> bool:
    stripped = clean_generated_text(text)
    if len(stripped) < 45:
        return True

    if not stripped.endswith(("。", "！", "？")):
        return True

    weak_phrases = (
        "本次活動內容豐富多元",
        "旨在提供社員",
        "透過多元活動",
        "活動內容豐富多元",
        "提供社員",
    )
    return any(phrase in stripped for phrase in weak_phrases)


def is_weak_teacher_comment(text: str) -> bool:
    stripped = clean_generated_text(text)
    if len(stripped) < 45:
        return True

    if not stripped.endswith(("。", "！", "？")):
        return True

    weak_phrases = (
        "本次茶道社的社團活動",
        "社員們展現了積極的參與熱情",
        "整體而言",
        "積極的參與熱情",
        "社團活動中",
    )
    return any(phrase in stripped for phrase in weak_phrases)


def repair_generated_text(
    *,
    api_key: str,
    model: str,
    system_instruction: str,
    original_prompt: str,
    weak_text: str,
    images: list[object] | None = None,
) -> str:
    repair_prompt = f"""
以下文字太短、太空泛或沒有完整結尾，請根據原始資料重寫成更好的成果書文字。

不佳草稿：
{weak_text}

原始資料與要求：
{original_prompt}

重寫要求：
- 只輸出改寫後的一段文字，不要解釋
- 不沿用不佳草稿的開頭
- 內容要具體、完整、自然
- 必須以句號結尾
- 禁止使用「豐富多元」、「積極參與熱情」、「收穫良多」、「圓滿成功」等套話
""".strip()

    return generate_gemini_text(
        api_key=api_key,
        model=model,
        system_instruction=system_instruction,
        prompt=repair_prompt,
        images=images,
    )


def ai_preview(
    *,
    final_text: str,
    raw_text: str = "",
    repaired_text: str = "",
    status: str,
) -> dict[str, str]:
    return {
        "status": status,
        "raw_text": raw_text,
        "repaired_text": repaired_text,
        "final_text": final_text,
    }


def generate_teacher_comment(
    *,
    api_key: str | None,
    model: str,
    activity_name: str,
    activity_review: str,
    photo_descriptions: list[str],
) -> str:
    return generate_teacher_comment_with_preview(
        api_key=api_key,
        model=model,
        activity_name=activity_name,
        activity_review=activity_review,
        photo_descriptions=photo_descriptions,
    )["final_text"]


def generate_teacher_comment_with_preview(
    *,
    api_key: str | None,
    model: str,
    activity_name: str,
    activity_review: str,
    photo_descriptions: list[str],
) -> dict[str, str]:
    if not api_key:
        fallback_text = fallback_teacher_comment(
            activity_name=activity_name,
            activity_review=activity_review,
            photo_descriptions=photo_descriptions,
        )
        return ai_preview(final_text=fallback_text, status="未設定 API key，使用本機草稿。")

    descriptions = "\n".join(
        f"- {description.strip()}"
        for description in photo_descriptions
        if description.strip()
    )

    prompt = f"""
請根據茶道社成果書資料，生成一段「指導老師評語」。

寫作方式：
1. 不要從「本次茶道社的社團活動」或「本次活動」開頭。
2. 開頭請直接使用活動名稱，或直接描述學生完成的具體任務。
3. 內容必須包含至少兩個具體元素，例如茶席布置、茶具整理、泡茶實作、流程分工、活動檢討。
4. 如果資料不足，只能根據已提供的活動名稱、活動檢討、照片說明寫，不要自行加入不存在的內容。

要求：
- 使用繁體中文
- 語氣像學校成果書中的老師評語
- 溫和、正式、肯定學生努力，但不要浮誇
- 先根據活動名稱、活動檢討、照片說明整理具體觀察，再寫成自然段落
- 需要點出活動執行、學習態度或團隊合作其中至少兩項
- 不要條列
- 90 到 140 字，必須是一段完整句子並以句號結尾
- 不要捏造未提供的活動細節
- 不要使用「本次茶道社的社團活動」或「社員們展現了積極的參與熱情」這類空泛模板語句
- 避免使用「豐富多元」、「收穫良多」、「圓滿成功」等套話

好範例風格：
茶席體驗辦理過程完整，學生能依照分工完成茶具整理、茶席布置與泡茶實作，並在活動後提出流程可提前確認的檢討，展現良好的學習態度與團隊合作精神。

壞範例，禁止模仿：
本次茶道社的社團活動，社員們展現了積極的參與熱情。

活動名稱：{activity_name or "未填"}
活動檢討：{activity_review or "未填"}
照片說明：
{descriptions or "未填"}
""".strip()

    system_instruction = "你是嚴謹的學校成果書編輯，只寫具體、可提交的繁體中文行政文字。"
    generated_text = clean_generated_text(generate_gemini_text(
        api_key=api_key,
        model=model,
        system_instruction=system_instruction,
        prompt=prompt,
    ))

    if is_weak_teacher_comment(generated_text):
        repaired_text = clean_generated_text(
            repair_generated_text(
                api_key=api_key,
                model=model,
                system_instruction=system_instruction,
                original_prompt=prompt,
                weak_text=generated_text,
            )
        )
        if not is_weak_teacher_comment(repaired_text):
            return ai_preview(
                final_text=repaired_text,
                raw_text=generated_text,
                repaired_text=repaired_text,
                status="Gemini 原始稿不符合品質規則，已使用 Gemini 重寫稿。",
            )

        fallback_text = fallback_teacher_comment(
            activity_name=activity_name,
            activity_review=activity_review,
            photo_descriptions=photo_descriptions,
        )
        return ai_preview(
            final_text=fallback_text,
            raw_text=generated_text,
            repaired_text=repaired_text,
            status="Gemini 重寫後仍不符合品質規則，使用本機草稿。",
        )

    return ai_preview(
        final_text=generated_text,
        raw_text=generated_text,
        status="使用 Gemini 原始稿。",
    )


def generate_activity_overview(
    *,
    api_key: str | None,
    model: str,
    activity_name: str,
    photo_descriptions: list[str],
    photos: list[object] | None = None,
) -> str:
    return generate_activity_overview_with_preview(
        api_key=api_key,
        model=model,
        activity_name=activity_name,
        photo_descriptions=photo_descriptions,
        photos=photos,
    )["final_text"]


def generate_activity_overview_with_preview(
    *,
    api_key: str | None,
    model: str,
    activity_name: str,
    photo_descriptions: list[str],
    photos: list[object] | None = None,
) -> dict[str, str]:
    if not api_key:
        fallback_text = fallback_activity_overview(
            activity_name=activity_name,
            photo_descriptions=photo_descriptions,
        )
        return ai_preview(final_text=fallback_text, status="未設定 API key，使用本機草稿。")

    descriptions = "\n".join(
        f"- {description.strip()}"
        for description in photo_descriptions
        if description.strip()
    )

    prompt = f"""
請根據茶道社成果書資料，生成一段「活動內容概述」。

寫作方式：
1. 不要從「本次活動內容豐富多元」、「旨在提供社員」或「本次活動」開頭。
2. 開頭請直接使用活動名稱；若活動名稱未填，才用「活動以...」開頭。
3. 段落順序必須是：活動主軸 → 實際進行內容 → 參與者學到或完成的事項。
4. 實際進行內容必須包含至少兩個具體元素，例如茶席布置、茶具介紹、泡茶練習、茶點搭配、分組實作。
5. 如果照片或照片說明沒有提供某項內容，不要自行加入。

要求：
- 使用繁體中文
- 適合放在學校活動成果報告表
- 內容正式、清楚、具體，像學校成果書欄位，不像廣告文案
- 先描述活動主軸，再描述實際進行內容，最後說明參與者學到或完成什麼
- 不要條列
- 90 到 140 字，必須是一段完整句子並以句號結尾
- 若有上傳照片，優先根據照片內容撰寫；照片說明只作為輔助線索
- 不要捏造未提供的細節
- 不要使用「本次活動內容豐富多元」或「旨在提供社員」這類空泛模板語句
- 避免使用「豐富多元」、「收穫良多」、「圓滿成功」等套話

好範例風格：
茶席體驗以茶道禮儀與泡茶實作為主軸，參與者依序完成茶具整理、茶席布置與沖泡練習，並透過實際操作熟悉茶席流程，理解茶道文化中重視禮節與專注的精神。

壞範例，禁止模仿：
本次活動內容豐富多元，旨在提供社員。

活動名稱：{activity_name or "未填"}
照片說明：
{descriptions or "未填"}
""".strip()

    system_instruction = "你是嚴謹的學校成果書編輯，只寫具體、可提交的繁體中文行政文字。"
    generated_text = clean_generated_text(generate_gemini_text(
        api_key=api_key,
        model=model,
        system_instruction=system_instruction,
        prompt=prompt,
        images=photos,
    ))

    if is_weak_activity_overview(generated_text):
        repaired_text = clean_generated_text(
            repair_generated_text(
                api_key=api_key,
                model=model,
                system_instruction=system_instruction,
                original_prompt=prompt,
                weak_text=generated_text,
                images=photos,
            )
        )
        if not is_weak_activity_overview(repaired_text):
            return ai_preview(
                final_text=repaired_text,
                raw_text=generated_text,
                repaired_text=repaired_text,
                status="Gemini 原始稿不符合品質規則，已使用 Gemini 重寫稿。",
            )

        fallback_text = fallback_activity_overview(
            activity_name=activity_name,
            photo_descriptions=photo_descriptions,
        )
        return ai_preview(
            final_text=fallback_text,
            raw_text=generated_text,
            repaired_text=repaired_text,
            status="Gemini 重寫後仍不符合品質規則，使用本機草稿。",
        )

    return ai_preview(
        final_text=generated_text,
        raw_text=generated_text,
        status="使用 Gemini 原始稿。",
    )
