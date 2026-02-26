import logging
from datetime import datetime
from urllib.parse import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
TIMEOUT = 15

# 域名 -> RSS URL 映射
RSS_MAP = {
    "techmeme.com":              "https://www.techmeme.com/feed.op",
    "newsletter.strictlyvc.com": "https://newsletter.strictlyvc.com/feed",
    "every.to":                  "https://every.to/feed",
    "a16z.news":                 "https://www.a16z.news/feed",
    "tomtunguz.com":             "https://tomtunguz.com/index.xml",
    "avc.com":                   "https://avc.com/feed/",
    "hunterwalk.com":            "https://hunterwalk.com/feed/",
    "blog.eladgil.com":          "https://blog.eladgil.com/feed",
    "stratechery.com":           "https://stratechery.com/feed/",
    "ben-evans.com":             "https://www.ben-evans.com/benedictevans/rss.xml",
    "bensbites.co":              "https://news.bensbites.co/feed",
    "techurls.com":              "https://techurls.com/feed",
    "lennysnewsletter.com":      "https://www.lennysnewsletter.com/feed",
    "latent.space":              "https://www.latent.space/feed",
    "generalist.com":            "https://www.generalist.com/briefing/rss",
    "joincolossus.com":          "https://www.joincolossus.com/feed",
}

# 跳过这些域名（静态归档或无法抓取）
SKIP_DOMAINS = {"pmarchive.com", "pitchbook.com", "theinformation.com", "openvc.app"}


def _parse_date(entry) -> datetime:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6])
            except Exception:
                pass
    return datetime.min


def _entry_to_article(entry) -> dict:
    summary = entry.get("summary", "")
    # 去除 HTML 标签
    if summary:
        soup = BeautifulSoup(summary, "html.parser")
        summary = soup.get_text(" ", strip=True)
    return {
        "title": entry.get("title", "").strip(),
        "url": entry.get("link", "").strip(),
        "published": _parse_date(entry),
        "summary": summary[:300],
    }


def fetch_rss(rss_url: str) -> list[dict]:
    try:
        feed = feedparser.parse(rss_url)
        if feed.bozo and not feed.entries:
            logger.warning("RSS 解析异常: %s", rss_url)
            return []
        articles = [_entry_to_article(e) for e in feed.entries if e.get("link")]
        articles.sort(key=lambda a: a["published"], reverse=True)
        return articles
    except Exception as e:
        logger.warning("RSS 抓取失败 %s: %s", rss_url, e)
        return []


def fetch_paul_graham() -> list[dict]:
    """抓取 paulgraham.com/articles.html 文章列表"""
    try:
        resp = requests.get("https://paulgraham.com/articles.html", headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        articles = []
        for a in soup.select("table a[href]"):
            href = a["href"]
            if not href.startswith("http"):
                href = "https://paulgraham.com/" + href
            articles.append({
                "title": a.get_text(strip=True),
                "url": href,
                "published": datetime.min,
                "summary": "",
            })
        return articles[:10]  # 只取最新列出的前 10 篇
    except Exception as e:
        logger.warning("Paul Graham 抓取失败: %s", e)
        return []


def fetch_first_round() -> list[dict]:
    """抓取 First Round Review 文章列表"""
    try:
        resp = requests.get("https://review.firstround.com/articles/", headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        articles = []
        for a in soup.select("a[href*='/articles/']"):
            href = a["href"]
            if not href.startswith("http"):
                href = "https://review.firstround.com" + href
            title = a.get_text(strip=True)
            if title and href not in [x["url"] for x in articles]:
                articles.append({
                    "title": title,
                    "url": href,
                    "published": datetime.min,
                    "summary": "",
                })
        return articles[:10]
    except Exception as e:
        logger.warning("First Round Review 抓取失败: %s", e)
        return []


def fetch_superscout() -> list[dict]:
    """抓取 Superscout 文章列表"""
    try:
        resp = requests.get("https://superscout.co/", headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        articles = []
        for a in soup.select("a[href*='/scenario/'], a[href*='/article/'], a[href*='/post/']"):
            href = a["href"]
            if not href.startswith("http"):
                href = "https://superscout.co" + href
            title = a.get_text(strip=True)
            if title:
                articles.append({
                    "title": title,
                    "url": href,
                    "published": datetime.min,
                    "summary": "",
                })
        return articles[:5]
    except Exception as e:
        logger.warning("Superscout 抓取失败: %s", e)
        return []


def fetch_ark() -> list[dict]:
    """尝试抓取 ARK Invest 文章"""
    # 先尝试 RSS
    rss = fetch_rss("https://www.ark-funds.com/feed")
    if rss:
        return rss
    # 降级到 HTTP 抓取
    try:
        resp = requests.get("https://www.ark-funds.com/articles", headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        articles = []
        for a in soup.select("a[href*='/articles/']"):
            href = a["href"]
            if not href.startswith("http"):
                href = "https://www.ark-funds.com" + href
            title = a.get_text(strip=True)
            if title and len(title) > 5:
                articles.append({
                    "title": title,
                    "url": href,
                    "published": datetime.min,
                    "summary": "",
                })
        return articles[:5]
    except Exception as e:
        logger.warning("ARK Invest 抓取失败（JS 渲染页面，跳过）: %s", e)
        return []


def fetch_coatue() -> list[dict]:
    """尝试抓取 Coatue insights（JS 渲染，可能失败）"""
    try:
        resp = requests.get("https://www.coatue.com/insights", headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        articles = []
        for a in soup.select("a[href*='/blog/']"):
            href = a["href"]
            if not href.startswith("http"):
                href = "https://www.coatue.com" + href
            title = a.get_text(strip=True)
            if title and len(title) > 5:
                articles.append({
                    "title": title,
                    "url": href,
                    "published": datetime.min,
                    "summary": "",
                })
        return articles[:5]
    except Exception as e:
        logger.warning("Coatue 抓取失败（JS 渲染页面，跳过）: %s", e)
        return []


def fetch_youtube_rss(channel_id: str) -> list[dict]:
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    return fetch_rss(rss_url)


# Lex Fridman YouTube channel ID
LEX_CHANNEL_ID = "UCSHZKyawb77ixDdsGog4iWA"


def get_articles(source: dict) -> list[dict]:
    """根据信息源 URL 分发到对应的抓取策略"""
    url = source["url"]
    name = source["name"]
    domain = urlparse(url).netloc.lstrip("www.")

    # 跳过无法抓取的源
    for skip in SKIP_DOMAINS:
        if skip in domain:
            logger.info("跳过 %s（%s）", name, domain)
            return []

    # YouTube
    if "youtube.com" in domain or "music.youtube.com" in domain:
        return fetch_youtube_rss(LEX_CHANNEL_ID)

    # 特殊抓取
    if "paulgraham.com" in domain:
        return fetch_paul_graham()
    if "firstround.com" in domain:
        return fetch_first_round()
    if "superscout.co" in domain:
        return fetch_superscout()
    if "ark-funds.com" in domain:
        return fetch_ark()
    if "coatue.com" in domain:
        return fetch_coatue()

    # RSS 映射
    for key, rss_url in RSS_MAP.items():
        if key in domain:
            return fetch_rss(rss_url)

    logger.info("未找到 %s 的抓取策略（%s），跳过", name, domain)
    return []
