import logging
import os
import sys
from config import load_sources, get_telegram_config
from fetchers import get_articles
from state import is_new, mark_seen, cleanup_old
from notifier import build_digest, send

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def run():
    # 清理 30 天前的旧记录
    cleanup_old(30)

    sources = load_sources()
    logger.info("加载了 %d 个信息源", len(sources))

    p1_items = []
    p2_items = []

    for source in sources:
        name = source["name"]
        priority = source["priority"]
        logger.info("抓取 [%s] %s ...", priority, name)

        articles = get_articles(source)
        if not articles:
            logger.info("  -> 无文章或抓取失败")
            continue

        # 过滤已推送的文章
        new_articles = [a for a in articles if a.get("url") and is_new(a["url"])]

        if not new_articles:
            logger.info("  -> 无新文章（共 %d 篇，全部已推送）", len(articles))
            continue

        # P2 只取最新 2 篇
        if priority == "P2":
            new_articles = new_articles[:2]

        # AI 增强处理（有 GEMINI_API_KEY 时才调用）
        if os.environ.get("GEMINI_API_KEY"):
            from ai_processor import enrich_article
            enriched = []
            for a in new_articles:
                ai_result = enrich_article(a["title"], a["url"], a.get("summary", ""))
                enriched.append({**a, **ai_result})
            new_articles = enriched

        logger.info("  -> %d 篇新文章", len(new_articles))

        if priority == "P1":
            p1_items.append((name, new_articles))
        else:
            p2_items.append((name, new_articles))

    if not p1_items and not p2_items:
        logger.info("今日无新内容，不发送 Telegram 消息")
        return

    token, chat_id = get_telegram_config()
    messages = build_digest(p1_items, p2_items)

    for msg in messages:
        send(token, chat_id, msg)

    # 标记所有已推送的文章
    all_urls = [
        a["url"]
        for _, articles in (p1_items + p2_items)
        for a in articles
    ]
    mark_seen(all_urls)
    logger.info("推送完成，共标记 %d 篇文章", len(all_urls))


if __name__ == "__main__":
    run()
