import json
from datetime import datetime, timedelta
from pathlib import Path

STATE_FILE = Path(__file__).parent / "seen_articles.json"


def _load():
    if STATE_FILE.exists():
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save(data):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_new(url: str) -> bool:
    return url not in _load()


def mark_seen(urls: list[str]):
    data = _load()
    today = datetime.now().strftime("%Y-%m-%d")
    for url in urls:
        data[url] = today
    _save(data)


def cleanup_old(days: int = 30):
    data = _load()
    cutoff = datetime.now() - timedelta(days=days)
    cleaned = {
        url: date
        for url, date in data.items()
        if datetime.strptime(date, "%Y-%m-%d") >= cutoff
    }
    _save(cleaned)
