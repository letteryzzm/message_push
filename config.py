import csv
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "vc信息源收集_数据表_表格.csv"


def load_sources():
    """解析 CSV，返回有效信息源列表，过滤掉 x.com/Twitter 源"""
    sources = []
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # 跳过表头
        for row in reader:
            if len(row) < 6:
                continue
            name = row[0].strip()
            url = row[2].strip()
            priority = row[5].strip()

            if not name or not url:
                continue
            if priority not in ("P1", "P2"):
                continue
            if "x.com" in url or "twitter.com" in url:
                continue

            sources.append({
                "name": name,
                "url": url,
                "type": row[1].strip(),
                "priority": priority,
            })
    return sources


def get_telegram_config():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        raise ValueError("请在 .env 文件中设置 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID")
    return token, chat_id


def get_gemini_config():
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise ValueError("请在 .env 文件中设置 GEMINI_API_KEY")
    return key
