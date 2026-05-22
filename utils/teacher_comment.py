from __future__ import annotations

import base64
import json
from urllib import error, parse, request


DEFAULT_GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
DEFAULT_HF_MODEL = "openai/gpt-oss-120b:fastest"
DEFAULT_HF_VISION_MODEL = "CohereLabs/aya-vision-32b:cohere"


def generate_gemini_text(
    *,
    api_key: str,
    model: str,
    system_instruction: str,
    prompt: str,
    images: list[object] | None = None,
) -> str:
    return generate_gemini_result(
        api_key=api_key,
        model=model,
        system_instruction=system_instruction,
        prompt=prompt,
        images=images,
    )["text"]


def gemini_debug_info(data: dict, text: str) -> dict[str, object]:
    candidates = data.get("candidates", [])
    finish_reasons = []
    safety_ratings = []
    part_count = 0

    for candidate in candidates:
        finish_reason = candidate.get("finishReason")
        if finish_reason:
            finish_reasons.append(finish_reason)

        if candidate.get("safetyRatings"):
            safety_ratings.append(candidate.get("safetyRatings"))

        content = candidate.get("content", {})
        part_count += len(content.get("parts", []))

    usage = data.get("usageMetadata", {})
    return {
        "candidate_count": len(candidates),
        "part_count": part_count,
        "finish_reasons": finish_reasons,
        "text_length": len(text),
        "prompt_token_count": usage.get("promptTokenCount"),
        "candidates_token_count": usage.get("candidatesTokenCount"),
        "thoughts_token_count": usage.get("thoughtsTokenCount"),
        "total_token_count": usage.get("totalTokenCount"),
        "safety_ratings": safety_ratings,
    }


def generate_gemini_result(
    *,
    api_key: str,
    model: str,
    system_instruction: str,
    prompt: str,
    images: list[object] | None = None,
) -> dict[str, object]:
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
            "maxOutputTokens": 2048,
            "temperature": 0.4,
            "topP": 0.8,
            "thinkingConfig": {
                "thinkingBudget": 0,
            },
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

    return {
        "text": generated_text,
        "debug": gemini_debug_info(data, generated_text),
        "provider": "Gemini",
        "model": model,
    }


def groq_debug_info(data: dict, text: str) -> dict[str, object]:
    usage = data.get("usage", {})
    choices = data.get("choices", [])
    finish_reasons = [
        choice.get("finish_reason")
        for choice in choices
        if choice.get("finish_reason")
    ]

    return {
        "choice_count": len(choices),
        "finish_reasons": finish_reasons,
        "text_length": len(text),
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
    }


def generate_groq_result(
    *,
    api_key: str,
    model: str,
    system_instruction: str,
    prompt: str,
) -> dict[str, object]:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 1024,
        "temperature": 0.4,
        "top_p": 0.8,
    }
    req = request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "tea-club-platform/1.0",
            "Accept": "application/json",
        },
    )

    try:
        with request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, error.HTTPError, json.JSONDecodeError) as exc:
        raise RuntimeError("Groq API 呼叫失敗，請確認 GROQ_API_KEY 與 GROQ_MODEL。") from exc

    texts = []
    for choice in data.get("choices", []):
        content = choice.get("message", {}).get("content")
        if content:
            texts.append(content)

    generated_text = "\n".join(texts).strip()
    if not generated_text:
        raise RuntimeError("Groq API 未回傳文字內容。")

    return {
        "text": generated_text,
        "debug": groq_debug_info(data, generated_text),
        "provider": "Groq",
        "model": model,
    }


def huggingface_debug_info(data: dict, text: str) -> dict[str, object]:
    usage = data.get("usage", {})
    choices = data.get("choices", [])
    finish_reasons = [
        choice.get("finish_reason")
        for choice in choices
        if choice.get("finish_reason")
    ]

    return {
        "choice_count": len(choices),
        "finish_reasons": finish_reasons,
        "text_length": len(text),
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
    }


def generate_huggingface_result(
    *,
    api_key: str,
    model: str,
    system_instruction: str,
    prompt: str,
    images: list[object] | None = None,
) -> dict[str, object]:
    message_content: str | list[dict[str, object]] = prompt
    image_parts = []
    for image in images or []:
        if image is None:
            continue

        mime_type = getattr(image, "type", None) or "image/png"
        image_data = base64.b64encode(image.getvalue()).decode("ascii")
        image_parts.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{image_data}",
                },
            }
        )

    if image_parts:
        message_content = [{"type": "text", "text": prompt}, *image_parts]

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": message_content},
        ],
        "max_tokens": 2048,
        "temperature": 0.4,
        "top_p": 0.8,
        "stream": False,
    }
    req = request.Request(
        "https://router.huggingface.co/v1/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "tea-club-platform/1.0",
            "Accept": "application/json",
        },
    )

    try:
        with request.urlopen(req, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, error.HTTPError, json.JSONDecodeError) as exc:
        raise RuntimeError("Hugging Face API 呼叫失敗，請確認 HF_API_KEY 與 HF_MODEL。") from exc

    texts = []
    for choice in data.get("choices", []):
        content = choice.get("message", {}).get("content")
        if content:
            texts.append(content)

    generated_text = "\n".join(texts).strip()
    if not generated_text:
        raise RuntimeError("Hugging Face API 未回傳文字內容。")

    return {
        "text": generated_text,
        "debug": huggingface_debug_info(data, generated_text),
        "provider": "Hugging Face",
        "model": str(data.get("model") or model),
    }


def generate_ai_result(
    *,
    gemini_api_key: str | None,
    gemini_model: str,
    groq_api_key: str | None,
    groq_model: str,
    system_instruction: str,
    prompt: str,
    images: list[object] | None = None,
    hf_api_key: str | None = None,
    hf_model: str = DEFAULT_HF_MODEL,
    hf_vision_model: str = DEFAULT_HF_VISION_MODEL,
) -> dict[str, object]:
    last_error = ""
    tried_huggingface = False

    if gemini_api_key:
        try:
            return generate_gemini_result(
                api_key=gemini_api_key,
                model=gemini_model,
                system_instruction=system_instruction,
                prompt=prompt,
                images=images,
            )
        except RuntimeError as exc:
            last_error = str(exc)

    has_images = any(image is not None for image in images or [])
    if has_images and hf_api_key:
        tried_huggingface = True
        try:
            result = generate_huggingface_result(
                api_key=hf_api_key,
                model=hf_vision_model,
                system_instruction=system_instruction,
                prompt=prompt,
                images=images,
            )
            if last_error:
                result["debug"]["fallback_from"] = last_error
            return result
        except RuntimeError as exc:
            if last_error:
                last_error = f"{last_error}；{exc}"
            else:
                last_error = str(exc)

    if has_images:
        if last_error:
            raise RuntimeError(last_error)
        raise RuntimeError("圖片任務未設定可用的 Gemini 或 Hugging Face Vision API key。")

    if groq_api_key:
        try:
            result = generate_groq_result(
                api_key=groq_api_key,
                model=groq_model,
                system_instruction=system_instruction,
                prompt=prompt,
            )
            if last_error:
                result["debug"]["fallback_from"] = last_error
            return result
        except RuntimeError as exc:
            if last_error:
                last_error = f"{last_error}；{exc}"
            else:
                last_error = str(exc)

    if hf_api_key and not tried_huggingface:
        try:
            result = generate_huggingface_result(
                api_key=hf_api_key,
                model=hf_model,
                system_instruction=system_instruction,
                prompt=prompt,
                images=images,
            )
            if last_error:
                result["debug"]["fallback_from"] = last_error
            return result
        except RuntimeError as exc:
            if last_error:
                raise RuntimeError(f"{last_error}；{exc}") from exc
            raise

    if last_error:
        raise RuntimeError(last_error)

    raise RuntimeError("未設定可用的 AI API key。")


def result_source(result: dict[str, object]) -> str:
    provider = str(result.get("provider", "AI"))
    model = str(result.get("model", ""))
    if model:
        return f"{provider}: {model}"
    return provider


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


def fallback_application_purpose(*, activity_name: str, activity_progress: str = "") -> str:
    name = activity_name.strip() or "本次活動"
    progress = "、".join(
        line.split(" ", 1)[-1].strip()
        for line in activity_progress.splitlines()
        if line.strip()
    )
    if progress:
        return (
            f"{name}旨在透過{progress}等流程，引導參與學生認識茶道活動內容與社團運作方式，"
            "並在實作與互動過程中培養團隊合作、溝通表達與行政執行能力。"
        )

    return (
        f"{name}旨在透過茶席布置、茶具介紹與泡茶實作，引導參與學生認識茶道禮儀與茶文化，"
        "並在活動分工與互動過程中培養團隊合作、溝通表達與行政執行能力。"
    )


def format_activity_time(minutes: int) -> str:
    hour = minutes // 60
    minute = minutes % 60
    return f"{hour:02d}:{minute:02d}"


def activity_segment(start: int, duration: int, title: str) -> tuple[int, str]:
    end = start + duration
    return end, f"{format_activity_time(start)}-{format_activity_time(end)} {title}"


def fallback_application_progress(
    *,
    activity_name: str,
    tea_topic: str,
    snack_item: str,
    include_icebreaker: bool = True,
    include_snack_diy: bool = False,
    include_health_chat: bool = False,
) -> str:
    name = activity_name.strip()
    tea = tea_topic.strip() or "茶"
    snack = snack_item.strip() or "點心"
    current = 19 * 60 + 35
    segments = []

    if include_icebreaker:
        current, segment = activity_segment(current, 10, "破冰活動")
        segments.append(segment)

    if any(keyword in name for keyword in ("封箱", "期末")):
        current, segment = activity_segment(current, 15, "本學期回顧影片欣賞與社歌練唱")
        segments.append(segment)
    elif any(keyword in name for keyword in ("開箱", "開春", "期初")):
        current, segment = activity_segment(current, 15, "期初回顧影片欣賞與社歌練唱")
        segments.append(segment)

    if include_health_chat:
        current, segment = activity_segment(current, 10, "健康聊齋")
        segments.append(segment)

    if include_snack_diy:
        diy_label = snack if "DIY" in snack.upper() else f"{snack}DIY"
        current, segment = activity_segment(current, 20, diy_label)
        segments.append(segment)

    remaining = max((20 * 60 + 50) - current, 20)
    intro_duration = 15 if remaining >= 30 else 10
    current, segment = activity_segment(current, intro_duration, f"介紹{tea}")
    segments.append(segment)

    if current < 20 * 60 + 50:
        _, segment = activity_segment(current, (20 * 60 + 50) - current, "泡茶與品茶交流")
        segments.append(segment)
    else:
        segments.append("20:40-20:50 泡茶與品茶交流")

    return "\n".join(segments)


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
    api_key: str | None,
    model: str,
    groq_api_key: str | None = None,
    groq_model: str = DEFAULT_GROQ_MODEL,
    system_instruction: str,
    original_prompt: str,
    weak_text: str,
    images: list[object] | None = None,
    hf_api_key: str | None = None,
    hf_model: str = DEFAULT_HF_MODEL,
    hf_vision_model: str = DEFAULT_HF_VISION_MODEL,
) -> str:
    return repair_generated_text_with_preview(
        api_key=api_key,
        model=model,
        groq_api_key=groq_api_key,
        groq_model=groq_model,
        hf_api_key=hf_api_key,
        hf_model=hf_model,
        hf_vision_model=hf_vision_model,
        system_instruction=system_instruction,
        original_prompt=original_prompt,
        weak_text=weak_text,
        images=images,
    )["text"]


def repair_generated_text_with_preview(
    *,
    api_key: str | None,
    model: str,
    groq_api_key: str | None = None,
    groq_model: str = DEFAULT_GROQ_MODEL,
    system_instruction: str,
    original_prompt: str,
    weak_text: str,
    images: list[object] | None = None,
    hf_api_key: str | None = None,
    hf_model: str = DEFAULT_HF_MODEL,
    hf_vision_model: str = DEFAULT_HF_VISION_MODEL,
) -> dict[str, object]:
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

    return generate_ai_result(
        gemini_api_key=api_key,
        gemini_model=model,
        groq_api_key=groq_api_key,
        groq_model=groq_model,
        hf_api_key=hf_api_key,
        hf_model=hf_model,
        hf_vision_model=hf_vision_model,
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
    raw_debug: dict[str, object] | None = None,
    repaired_debug: dict[str, object] | None = None,
    provider: str = "",
    model: str = "",
) -> dict[str, object]:
    return {
        "status": status,
        "raw_text": raw_text,
        "repaired_text": repaired_text,
        "final_text": final_text,
        "raw_debug": raw_debug or {},
        "repaired_debug": repaired_debug or {},
        "provider": provider,
        "model": model,
    }


def generate_teacher_comment(
    *,
    api_key: str | None,
    model: str,
    groq_api_key: str | None = None,
    groq_model: str = DEFAULT_GROQ_MODEL,
    activity_name: str,
    activity_review: str,
    photo_descriptions: list[str],
    hf_api_key: str | None = None,
    hf_model: str = DEFAULT_HF_MODEL,
) -> str:
    return generate_teacher_comment_with_preview(
        api_key=api_key,
        model=model,
        groq_api_key=groq_api_key,
        groq_model=groq_model,
        hf_api_key=hf_api_key,
        hf_model=hf_model,
        activity_name=activity_name,
        activity_review=activity_review,
        photo_descriptions=photo_descriptions,
    )["final_text"]


def generate_teacher_comment_with_preview(
    *,
    api_key: str | None,
    model: str,
    groq_api_key: str | None = None,
    groq_model: str = DEFAULT_GROQ_MODEL,
    activity_name: str,
    activity_review: str,
    photo_descriptions: list[str],
    hf_api_key: str | None = None,
    hf_model: str = DEFAULT_HF_MODEL,
) -> dict[str, object]:
    if not api_key and not groq_api_key and not hf_api_key:
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
    try:
        generated_result = generate_ai_result(
            gemini_api_key=api_key,
            gemini_model=model,
            groq_api_key=groq_api_key,
            groq_model=groq_model,
            hf_api_key=hf_api_key,
            hf_model=hf_model,
            system_instruction=system_instruction,
            prompt=prompt,
        )
    except RuntimeError as exc:
        fallback_text = fallback_teacher_comment(
            activity_name=activity_name,
            activity_review=activity_review,
            photo_descriptions=photo_descriptions,
        )
        return ai_preview(
            final_text=fallback_text,
            status=f"AI 呼叫失敗，已使用本機草稿。{exc}",
        )
    generated_text = clean_generated_text(str(generated_result["text"]))
    generated_debug = generated_result["debug"]
    generated_provider = str(generated_result.get("provider", "AI"))
    generated_model = str(generated_result.get("model", ""))
    generated_source = result_source(generated_result)

    if is_weak_teacher_comment(generated_text):
        try:
            repaired_result = repair_generated_text_with_preview(
                api_key=api_key,
                model=model,
                groq_api_key=groq_api_key,
                groq_model=groq_model,
                hf_api_key=hf_api_key,
                hf_model=hf_model,
                system_instruction=system_instruction,
                original_prompt=prompt,
                weak_text=generated_text,
            )
        except RuntimeError as exc:
            fallback_text = fallback_teacher_comment(
                activity_name=activity_name,
                activity_review=activity_review,
                photo_descriptions=photo_descriptions,
            )
            return ai_preview(
                final_text=fallback_text,
                raw_text=generated_text,
                status=f"{generated_source} 原始稿不符合品質規則，AI 重寫失敗，已使用本機草稿。{exc}",
                raw_debug=generated_debug,
                provider=generated_provider,
                model=generated_model,
            )
        repaired_text = clean_generated_text(str(repaired_result["text"]))
        repaired_debug = repaired_result["debug"]
        repaired_provider = str(repaired_result.get("provider", "AI"))
        repaired_model = str(repaired_result.get("model", ""))
        repaired_source = result_source(repaired_result)
        if not is_weak_teacher_comment(repaired_text):
            return ai_preview(
                final_text=repaired_text,
                raw_text=generated_text,
                repaired_text=repaired_text,
                status=f"{generated_source} 原始稿不符合品質規則，已使用 {repaired_source} 重寫稿。",
                raw_debug=generated_debug,
                repaired_debug=repaired_debug,
                provider=repaired_provider,
                model=repaired_model,
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
            status=f"{repaired_source} 重寫後仍不符合品質規則，使用本機草稿。",
            raw_debug=generated_debug,
            repaired_debug=repaired_debug,
            provider=repaired_provider,
            model=repaired_model,
        )

    return ai_preview(
        final_text=generated_text,
        raw_text=generated_text,
        status=f"使用 {generated_source} 原始稿。",
        raw_debug=generated_debug,
        provider=generated_provider,
        model=generated_model,
    )


def generate_application_purpose_with_preview(
    *,
    api_key: str | None,
    model: str,
    groq_api_key: str | None = None,
    groq_model: str = DEFAULT_GROQ_MODEL,
    activity_name: str,
    activity_progress: str = "",
    hf_api_key: str | None = None,
    hf_model: str = DEFAULT_HF_MODEL,
) -> dict[str, object]:
    if not api_key and not groq_api_key and not hf_api_key:
        fallback_text = fallback_application_purpose(
            activity_name=activity_name,
            activity_progress=activity_progress,
        )
        return ai_preview(final_text=fallback_text, status="未設定 API key，使用本機草稿。")

    prompt = f"""
請根據茶道社活動名稱與活動進行內容，生成活動申請計畫書中的「活動宗旨」。

活動名稱：{activity_name or "未填"}
活動進行：
{activity_progress or "未填"}

要求：
- 使用繁體中文
- 適合放在學校社團活動申請書
- 語氣正式、清楚、可提交
- 內容需呼應活動進行中的實際流程，再整理成活動目的
- 內容需包含參與者能學到什麼，以及社團行政或團隊合作意義
- 不要條列
- 80 到 120 字，必須是一段完整文字並以句號結尾
- 不要使用「豐富多元」、「收穫良多」、「圓滿成功」等套話
- 不要捏造活動名稱與活動進行以外無法推知的具體細節
""".strip()

    system_instruction = "你是嚴謹的學校活動申請書編輯，只寫具體、可提交的繁體中文行政文字。"
    try:
        generated_result = generate_ai_result(
            gemini_api_key=api_key,
            gemini_model=model,
            groq_api_key=groq_api_key,
            groq_model=groq_model,
            hf_api_key=hf_api_key,
            hf_model=hf_model,
            system_instruction=system_instruction,
            prompt=prompt,
        )
    except RuntimeError as exc:
        fallback_text = fallback_application_purpose(
            activity_name=activity_name,
            activity_progress=activity_progress,
        )
        return ai_preview(
            final_text=fallback_text,
            status=f"AI 呼叫失敗，已使用本機草稿。{exc}",
        )

    generated_text = clean_generated_text(str(generated_result["text"]))
    if not generated_text.endswith(("。", "！", "？")) or len(generated_text) < 40:
        fallback_text = fallback_application_purpose(
            activity_name=activity_name,
            activity_progress=activity_progress,
        )
        return ai_preview(
            final_text=fallback_text,
            raw_text=generated_text,
            status=f"{result_source(generated_result)} 原始稿不符合品質規則，使用本機草稿。",
            raw_debug=generated_result["debug"],
            provider=str(generated_result.get("provider", "AI")),
            model=str(generated_result.get("model", "")),
        )

    return ai_preview(
        final_text=generated_text,
        raw_text=generated_text,
        status=f"使用 {result_source(generated_result)} 原始稿。",
        raw_debug=generated_result["debug"],
        provider=str(generated_result.get("provider", "AI")),
        model=str(generated_result.get("model", "")),
    )


def generate_application_progress_with_preview(
    *,
    api_key: str | None,
    model: str,
    groq_api_key: str | None = None,
    groq_model: str = DEFAULT_GROQ_MODEL,
    activity_name: str,
    tea_topic: str,
    snack_item: str,
    include_icebreaker: bool = True,
    include_snack_diy: bool = False,
    include_health_chat: bool = False,
    hf_api_key: str | None = None,
    hf_model: str = DEFAULT_HF_MODEL,
) -> dict[str, object]:
    if not api_key and not groq_api_key and not hf_api_key:
        fallback_text = fallback_application_progress(
            activity_name=activity_name,
            tea_topic=tea_topic,
            snack_item=snack_item,
            include_icebreaker=include_icebreaker,
            include_snack_diy=include_snack_diy,
            include_health_chat=include_health_chat,
        )
        return ai_preview(final_text=fallback_text, status="未設定 API key，使用本機草稿。")

    icebreaker_rule = "需要安排破冰活動。" if include_icebreaker else "不要安排破冰活動。"
    snack_rule = "需要安排點心DIY。" if include_snack_diy else "不要安排點心DIY。"
    health_rule = "需要安排健康聊齋。" if include_health_chat else "不要安排健康聊齋。"
    prompt = f"""
請根據茶道社活動資料，生成活動申請書「活動進行」欄位文字。

活動名稱：{activity_name or "未填"}
介紹茶品：{tea_topic or "茶"}
點心內容：{snack_item or "未填"}
是否安排破冰活動：{"是" if include_icebreaker else "否"}
是否安排點心DIY：{"是" if include_snack_diy else "否"}
是否安排健康聊齋：{"是" if include_health_chat else "否"}

固定背景：
- 封箱茶會通常是期末或本學期最後社課。
- 開箱或開春通常是期初社課。
- 期初與期末活動通常會安排回顧影片與唱社歌。
- 常見活動元素包含介紹茶、喝茶。
- 健康聊齋是茶道社可安排的主題交流活動。
- {icebreaker_rule}
- {snack_rule}
- {health_rule}

輸出要求：
- 只輸出流程內容，不要加標題、解釋或條列符號。
- 一行一個流程，使用「19:35-19:45 破冰活動」這種格式。
- 時間需接在 19:30-19:35 開場之後，並在 20:50 前結束，因為模板後面已保留 20:50-21:00 小組時間。
- 流程需合理、可執行，不要排太多項目。
- 必須包含介紹茶、喝茶。
- 若判斷為期初或期末，需加入回顧影片與唱社歌。
- 不要捏造不合理的活動項目。
""".strip()

    system_instruction = "你是嚴謹的社團活動企劃，只輸出可放入活動申請書的繁體中文流程文字。"
    try:
        generated_result = generate_ai_result(
            gemini_api_key=api_key,
            gemini_model=model,
            groq_api_key=groq_api_key,
            groq_model=groq_model,
            hf_api_key=hf_api_key,
            hf_model=hf_model,
            system_instruction=system_instruction,
            prompt=prompt,
        )
    except RuntimeError as exc:
        fallback_text = fallback_application_progress(
            activity_name=activity_name,
            tea_topic=tea_topic,
            snack_item=snack_item,
            include_icebreaker=include_icebreaker,
            include_snack_diy=include_snack_diy,
            include_health_chat=include_health_chat,
        )
        return ai_preview(
            final_text=fallback_text,
            status=f"AI 呼叫失敗，已使用本機草稿。{exc}",
        )

    generated_text = str(generated_result["text"]).strip()
    required_terms = ["介紹", "茶"]
    if include_icebreaker:
        required_terms.append("破冰")
    if include_snack_diy:
        required_terms.append("DIY")
    if include_health_chat:
        required_terms.append("健康聊齋")
    if not generated_text or any(term not in generated_text for term in required_terms):
        fallback_text = fallback_application_progress(
            activity_name=activity_name,
            tea_topic=tea_topic,
            snack_item=snack_item,
            include_icebreaker=include_icebreaker,
            include_snack_diy=include_snack_diy,
            include_health_chat=include_health_chat,
        )
        return ai_preview(
            final_text=fallback_text,
            raw_text=generated_text,
            status=f"{result_source(generated_result)} 原始稿不符合流程規則，使用本機草稿。",
            raw_debug=generated_result["debug"],
            provider=str(generated_result.get("provider", "AI")),
            model=str(generated_result.get("model", "")),
        )

    return ai_preview(
        final_text=generated_text,
        raw_text=generated_text,
        status=f"使用 {result_source(generated_result)} 原始稿。",
        raw_debug=generated_result["debug"],
        provider=str(generated_result.get("provider", "AI")),
        model=str(generated_result.get("model", "")),
    )


def generate_activity_overview(
    *,
    api_key: str | None,
    model: str,
    groq_api_key: str | None = None,
    groq_model: str = DEFAULT_GROQ_MODEL,
    activity_name: str,
    photo_descriptions: list[str],
    photos: list[object] | None = None,
    hf_api_key: str | None = None,
    hf_model: str = DEFAULT_HF_MODEL,
    hf_vision_model: str = DEFAULT_HF_VISION_MODEL,
) -> str:
    return generate_activity_overview_with_preview(
        api_key=api_key,
        model=model,
        groq_api_key=groq_api_key,
        groq_model=groq_model,
        hf_api_key=hf_api_key,
        hf_model=hf_model,
        hf_vision_model=hf_vision_model,
        activity_name=activity_name,
        photo_descriptions=photo_descriptions,
        photos=photos,
    )["final_text"]


def generate_activity_overview_with_preview(
    *,
    api_key: str | None,
    model: str,
    groq_api_key: str | None = None,
    groq_model: str = DEFAULT_GROQ_MODEL,
    activity_name: str,
    photo_descriptions: list[str],
    photos: list[object] | None = None,
    hf_api_key: str | None = None,
    hf_model: str = DEFAULT_HF_MODEL,
    hf_vision_model: str = DEFAULT_HF_VISION_MODEL,
) -> dict[str, object]:
    if not api_key and not groq_api_key and not hf_api_key:
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
    try:
        generated_result = generate_ai_result(
            gemini_api_key=api_key,
            gemini_model=model,
            groq_api_key=groq_api_key,
            groq_model=groq_model,
            hf_api_key=hf_api_key,
            hf_model=hf_model,
            hf_vision_model=hf_vision_model,
            system_instruction=system_instruction,
            prompt=prompt,
            images=photos,
        )
    except RuntimeError as exc:
        fallback_text = fallback_activity_overview(
            activity_name=activity_name,
            photo_descriptions=photo_descriptions,
        )
        return ai_preview(
            final_text=fallback_text,
            status=f"AI 呼叫失敗，已使用本機草稿。{exc}",
        )

    generated_text = clean_generated_text(str(generated_result["text"]))
    generated_debug = generated_result["debug"]
    generated_provider = str(generated_result.get("provider", "AI"))
    generated_model = str(generated_result.get("model", ""))
    generated_source = result_source(generated_result)

    if is_weak_activity_overview(generated_text):
        try:
            repaired_result = repair_generated_text_with_preview(
                api_key=api_key,
                model=model,
                groq_api_key=groq_api_key,
                groq_model=groq_model,
                hf_api_key=hf_api_key,
                hf_model=hf_model,
                hf_vision_model=hf_vision_model,
                system_instruction=system_instruction,
                original_prompt=prompt,
                weak_text=generated_text,
                images=photos,
            )
        except RuntimeError as exc:
            fallback_text = fallback_activity_overview(
                activity_name=activity_name,
                photo_descriptions=photo_descriptions,
            )
            return ai_preview(
                final_text=fallback_text,
                raw_text=generated_text,
                status=f"{generated_source} 原始稿不符合品質規則，AI 重寫失敗，已使用本機草稿。{exc}",
                raw_debug=generated_debug,
                provider=generated_provider,
                model=generated_model,
            )

        repaired_text = clean_generated_text(str(repaired_result["text"]))
        repaired_debug = repaired_result["debug"]
        repaired_provider = str(repaired_result.get("provider", "AI"))
        repaired_model = str(repaired_result.get("model", ""))
        repaired_source = result_source(repaired_result)
        if not is_weak_activity_overview(repaired_text):
            return ai_preview(
                final_text=repaired_text,
                raw_text=generated_text,
                repaired_text=repaired_text,
                status=f"{generated_source} 原始稿不符合品質規則，已使用 {repaired_source} 重寫稿。",
                raw_debug=generated_debug,
                repaired_debug=repaired_debug,
                provider=repaired_provider,
                model=repaired_model,
            )

        fallback_text = fallback_activity_overview(
            activity_name=activity_name,
            photo_descriptions=photo_descriptions,
        )
        return ai_preview(
            final_text=fallback_text,
            raw_text=generated_text,
            repaired_text=repaired_text,
            status=f"{repaired_source} 重寫後仍不符合品質規則，使用本機草稿。",
            raw_debug=generated_debug,
            repaired_debug=repaired_debug,
            provider=repaired_provider,
            model=repaired_model,
        )

    return ai_preview(
        final_text=generated_text,
        raw_text=generated_text,
        status=f"使用 {generated_source} 原始稿。",
        raw_debug=generated_debug,
        provider=generated_provider,
        model=generated_model,
    )
