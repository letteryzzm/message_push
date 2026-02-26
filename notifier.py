import requests
import logging

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_MSG_LEN = 4096

logger = logging.getLogger(__name__)


def _split_message(text: str) -> list[str]:
    """将超长消息按 MAX_MSG_LEN 分割"""
    parts = []
    while len(text) > MAX_MSG_LEN:
        split_at = text.rfind("\n", 0, MAX_MSG_LEN)
        if split_at == -1:
            split_at = MAX_MSG_LEN
        parts.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    if text:
        parts.append(text)
    return parts


def send(token: str, chat_id: str, text: str):
    url = TELEGRAM_API.format(token=token)
    for part in _split_message(text):
        resp = requests.post(url, json={
            "chat_id": chat_id,
            "text": part,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }, timeout=15)
        if not resp.ok:
            logger.error("Telegram 发送失败: %s", resp.text)


def format_articles(priority: str, source_name: str, articles: list[dict]) -> str:
    icon = "🔴" if priority == "P1" else "🟡"
    lines = [f"{icon} [{priority}] {source_name}"]
    for a in articles:
        title = a.get("title", "无标题")
        url = a.get("url", "")
        zh_summary = a.get("zh_summary", "")
        key_points = a.get("key_points", [])

        if zh_summary:
            block = f'📌 <b>{title}</b>\n🔗 {url}\n📝 {zh_summary}'
            if key_points:
                points_text = "\n".join(f"- {p}" for p in key_points)
                block += f'\n💡 核心观点：\n{points_text}'
            lines.append(block)
        else:
            summary = a.get("summary", "")
            if summary:
                summary = summary[:200].replace("<", "&lt;").replace(">", "&gt;")
                lines.append(f'📌 <b>{title}</b>\n🔗 {url}\n{summary}')
            else:
                lines.append(f'📌 <b>{title}</b>\n🔗 {url}')
    return "\n\n".join(lines)


def build_digest(p1_items: list[tuple], p2_items: list[tuple]) -> list[str]:
    """
    p1_items / p2_items: [(source_name, articles), ...]
    返回待发送的消息列表
    """
    messages = []

    if p1_items:
        blocks = []
        for name, articles in p1_items:
            blocks.append(format_articles("P1", name, articles))
        messages.extend(_split_message("\n\n---\n\n".join(blocks)))

    if p2_items:
        blocks = []
        for name, articles in p2_items:
            blocks.append(format_articles("P2", name, articles))
        messages.extend(_split_message("\n\n---\n\n".join(blocks)))

    return messages
