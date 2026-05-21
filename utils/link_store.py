from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path

from utils.github_json_store import github_token, load_json, save_json

try:
    import streamlit as st
except Exception:
    st = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
LINKS_PATH = DATA_DIR / "useful_links.json"
GITHUB_DATA_PATH = "data/useful_links.json"

DEFAULT_LINKS = [
    {
        "名稱": "課外組空間借用",
        "網址": "https://wdsa.nttu.edu.tw/p/412-1009-8099.php?Lang=zh-tw",
        "分類": "學校網站",
        "備註": "課外活動組空間借用資訊、申請表與場地規定。",
    }
]


def normalize_url(url: str) -> str:
    text = url.strip()
    if text and not text.startswith(("http://", "https://")):
        return f"https://{text}"
    return text


def normalize_links(data: object) -> list[dict[str, str]]:
    if not isinstance(data, list):
        return []

    links = []
    for item in data:
        if not isinstance(item, dict):
            continue

        name = str(item.get("名稱", "")).strip()
        url = normalize_url(str(item.get("網址", "")))
        category = str(item.get("分類", "")).strip()
        note = str(item.get("備註", "")).strip()

        if name and url:
            links.append(
                {
                    "名稱": name,
                    "網址": url,
                    "分類": category,
                    "備註": note,
                }
            )

    return links


def config_value(name: str, default: object = "") -> object:
    env_value = os.environ.get(name)
    if env_value:
        return env_value

    if st is None:
        return default

    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def link_from_config(item: Mapping[str, object]) -> dict[str, str] | None:
    name = str(item.get("name") or item.get("名稱") or "").strip()
    url = normalize_url(str(item.get("url") or item.get("網址") or ""))
    category = str(item.get("category") or item.get("分類") or "私密連結").strip()
    note = str(item.get("note") or item.get("備註") or "").strip()

    if not name or not url:
        return None

    return {
        "名稱": name,
        "網址": url,
        "分類": category,
        "備註": note,
    }


def load_private_links() -> list[dict[str, str]]:
    links: list[dict[str, str]] = []

    upload_url = normalize_url(
        str(config_value("OFFICER_UPLOAD_URL") or config_value("PRIVATE_UPLOAD_URL"))
    )
    if upload_url:
        links.append(
            {
                "名稱": str(config_value("OFFICER_UPLOAD_NAME", "幹部資料上傳")),
                "網址": upload_url,
                "分類": str(config_value("OFFICER_UPLOAD_CATEGORY", "私密連結")),
                "備註": str(config_value("OFFICER_UPLOAD_NOTE", "幹部上傳社團資料用。")),
            }
        )

    configured_links = config_value("PRIVATE_LINKS", [])
    if isinstance(configured_links, Mapping):
        configured_links = [configured_links]

    if isinstance(configured_links, (list, tuple)):
        for item in configured_links:
            if isinstance(item, Mapping):
                link = link_from_config(item)
                if link:
                    links.append(link)

    private_links_json = str(config_value("PRIVATE_LINKS_JSON", "")).strip()
    if private_links_json:
        try:
            parsed_links = json.loads(private_links_json)
        except json.JSONDecodeError:
            parsed_links = []

        if isinstance(parsed_links, Mapping):
            parsed_links = [parsed_links]

        if isinstance(parsed_links, list):
            for item in parsed_links:
                if isinstance(item, Mapping):
                    link = link_from_config(item)
                    if link:
                        links.append(link)

    return normalize_links(links)


def load_links() -> list[dict[str, str]]:
    if github_token():
        remote_links = load_json(GITHUB_DATA_PATH)
        if remote_links is not None:
            return normalize_links(remote_links)

    if not LINKS_PATH.exists():
        return DEFAULT_LINKS

    try:
        data = json.loads(LINKS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return DEFAULT_LINKS

    return normalize_links(data)


def save_links(links: list[dict[str, str]]) -> None:
    links = normalize_links(links)

    if github_token() and save_json(GITHUB_DATA_PATH, links, "Update useful links"):
        return

    DATA_DIR.mkdir(exist_ok=True)
    LINKS_PATH.write_text(
        json.dumps(links, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def add_link(*, name: str, url: str, category: str, note: str) -> None:
    links = load_links()
    links.append(
        {
            "名稱": name.strip(),
            "網址": normalize_url(url),
            "分類": category.strip(),
            "備註": note.strip(),
        }
    )
    save_links(links)


def delete_link(index: int) -> None:
    links = load_links()
    if 0 <= index < len(links):
        del links[index]
        save_links(links)


def move_link(index: int, direction: int) -> None:
    links = load_links()
    new_index = index + direction

    if not 0 <= index < len(links):
        return

    if not 0 <= new_index < len(links):
        return

    links[index], links[new_index] = links[new_index], links[index]
    save_links(links)
