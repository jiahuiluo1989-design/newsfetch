"""Generate concise summaries using an OpenAI-compatible chat completion API."""
import logging
import requests

from . import config

logger = logging.getLogger(__name__)

SYSTEM = """你是资深宏观与多资产策略分析师。请把输入的新闻条目汇总成一份“投研快报”。
要求：
- 按板块输出：宏观 / 市场 / 科技 / Crypto / 中国
- 每条一句话：发生了什么 + 可能影响什么资产
- 最后给“今日主线叙事”和“风险点”
输出为纯文本（适合飞书私信）。"""


def _chat_completion(system_prompt: str, user_text: str, max_tokens: int) -> str:
    url = f"{config.SUMMARIZER_API_BASE_URL.rstrip('/')}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.SUMMARIZER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.SUMMARIZER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }
    # Some gpt-5-compatible gateways may return empty message content unless reasoning effort is constrained.
    if str(config.SUMMARIZER_MODEL).startswith("gpt-5"):
        payload["reasoning_effort"] = "low"
    resp = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=config.REQUEST_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    data = resp.json()
    choices = data.get("choices", [])
    if choices:
        content = choices[0].get("message", {}).get("content", "")
        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(part.get("text", ""))
                elif isinstance(part, str):
                    text_parts.append(part)
            content = "\n".join([x for x in text_parts if x])
        if content:
            return str(content).strip()
    raise ValueError("No summary content in API response")


def summarize(text: str, max_tokens: int = 200) -> str:
    """Return a short summary for the given text."""
    if config.SUMMARIZER_API_KEY:
        try:
            return _chat_completion(
                "你是资深投研助理。请将输入新闻压缩成2-3句，突出事件和资产影响。输出纯文本。",
                text,
                max_tokens,
            )
        except Exception as e:
            logger.warning("AI summarization failed: %s", e)
    else:
        logger.warning("SUMMARIZER_API_KEY is not set; falling back to truncation")
    return text[:300] + ("..." if len(text) > 300 else "")


def summarize_brief(items, max_tokens: int = 1200) -> str:
    """Build one investment brief from multiple news items."""
    if not items:
        return "今日无可总结新闻。"
    lines = []
    for i, item in enumerate(items, 1):
        lines.append(
            f"{i}. 标题: {item.get('title','')}\n"
            f"来源: {item.get('source','')}\n"
            f"分数: {item.get('score','')}\n"
            f"内容: {item.get('summary','')}\n"
            f"链接: {item.get('url','')}"
        )
    prompt_text = "请基于以下新闻条目生成投研快报：\n\n" + "\n\n".join(lines)
    if config.SUMMARIZER_API_KEY:
        try:
            return _chat_completion(SYSTEM, prompt_text, max_tokens)
        except Exception as e:
            logger.warning("AI brief summarization failed: %s", e)
    else:
        logger.warning("SUMMARIZER_API_KEY is not set; using degraded brief mode")
    return "投研快报（降级模式）\n" + "\n".join([f"- {x.get('title','')}" for x in items[:20]])
