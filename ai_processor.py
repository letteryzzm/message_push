import logging
import os

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """你是一位 VC/科技行业分析师助手。以下是一篇文章：
标题：{title}
原文摘要：{raw_summary}

请用中文完成以下两项：
1. 用 2-3 句话概括文章核心内容（中文摘要）
2. 列出 3-5 个最重要的核心观点（每条一行，以"-"开头）

直接输出结果，格式如下：
【摘要】
...
【核心观点】
- ...
- ..."""


def enrich_article(title: str, url: str, raw_summary: str) -> dict:
    """
    调用 Gemini 对文章生成中文摘要和核心观点。
    返回 {"zh_summary": str, "key_points": [str, ...]}
    失败时返回空 dict，不阻断推送。
    """
    try:
        from google import genai

        api_key = os.environ.get("GEMINI_API_KEY", "")
        client = genai.Client(api_key=api_key)

        prompt = PROMPT_TEMPLATE.format(
            title=title,
            raw_summary=raw_summary or "（无摘要，请根据标题推断）",
        )

        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
        )

        text = response.text or ""
        return _parse_response(text)

    except Exception as e:
        logger.warning("Gemini 处理失败 [%s]: %s", title, e)
        return {}


def _parse_response(text: str) -> dict:
    zh_summary = ""
    key_points = []

    if "【摘要】" in text and "【核心观点】" in text:
        summary_part = text.split("【摘要】")[1].split("【核心观点】")[0].strip()
        points_part = text.split("【核心观点】")[1].strip()

        zh_summary = summary_part
        key_points = [
            line.lstrip("- ").strip()
            for line in points_part.splitlines()
            if line.strip().startswith("-")
        ]

    if not zh_summary and not key_points:
        return {}

    return {"zh_summary": zh_summary, "key_points": key_points}
