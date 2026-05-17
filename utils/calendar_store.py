from __future__ import annotations

import json
from pathlib import Path

from utils.github_json_store import github_token, load_json, save_json, storage_label


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
CALENDAR_PATH = DATA_DIR / "calendar_events.json"
GITHUB_DATA_PATH = "data/calendar_events.json"


def normalize_events(data: object) -> list[dict[str, str]]:
    if not isinstance(data, list):
        return []

    events = []
    for item in data:
        if not isinstance(item, dict):
            continue

        title = str(item.get("活動名稱", "")).strip()
        date = str(item.get("日期", "")).strip()
        leader = str(item.get("活動負責人", "")).strip()
        location = str(item.get("地點", "")).strip()
        note = str(item.get("備註", "")).strip()

        if title and date:
            events.append(
                {
                    "日期": date,
                    "活動負責人": leader,
                    "活動名稱": title,
                    "地點": location,
                    "備註": note,
                }
            )

    return sorted(events, key=lambda event: (event["日期"], event["活動名稱"]))


def load_events() -> list[dict[str, str]]:
    if github_token():
        remote_events = load_json(GITHUB_DATA_PATH)
        if remote_events is not None:
            return normalize_events(remote_events)

    if not CALENDAR_PATH.exists():
        return []

    try:
        data = json.loads(CALENDAR_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    return normalize_events(data)


def save_events(events: list[dict[str, str]]) -> None:
    events = normalize_events(events)

    if github_token() and save_json(GITHUB_DATA_PATH, events, "Update calendar events"):
        return

    DATA_DIR.mkdir(exist_ok=True)
    CALENDAR_PATH.write_text(
        json.dumps(events, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def add_event(*, title: str, date: str, leader: str, location: str, note: str) -> None:
    events = load_events()
    events.append(
        {
            "日期": date.strip(),
            "活動負責人": leader.strip(),
            "活動名稱": title.strip(),
            "地點": location.strip(),
            "備註": note.strip(),
        }
    )
    save_events(events)


def delete_event(index: int) -> None:
    events = load_events()
    if 0 <= index < len(events):
        del events[index]
        save_events(events)


def format_event_label(event: dict[str, str]) -> str:
    date = event.get("日期", "")
    leader = event.get("活動負責人", "")
    title = event.get("活動名稱", "")

    when = " ".join(item for item in (date, leader) if item)
    if when:
        return f"{when}｜{title}"

    return title
