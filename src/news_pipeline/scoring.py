"""Assign importance scores to articles."""
import json
import logging
from typing import Dict

import requests

from . import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是宏观和市场策略分析师。请对新闻进行“市场重要性评分”(1-5)。
评分标准：
1=几乎无市场影响/重复信息
2=轻微影响，非主线
3=值得关注，可能影响某个板块/资产
4=重要催化，可能影响多个资产或主线叙事
5=重大市场事件（央行/关键数据/重大政策/系统性风险）

仅输出 JSON（不要输出多余文本），格式：
{
  "score": 1-5,
  "asset_impact": ["rates","equities","fx","commodities","crypto","credit","real_estate"],
  "time_horizon": "intraday|days|weeks|months",
  "tags": ["macro","policy","data","geopolitics","ai","energy","crypto","china","earnings"],
  "why": "不超过40字"
}
"""

# keep this switch so tests can force heuristic by monkeypatching
AI_AVAILABLE = True


def _extract_score_from_output(output: str):
    output = (output or "").strip()
    if output.startswith("```"):
        output = output.strip("`")
        output = output.replace("json", "", 1).strip()
    parsed = json.loads(output)
    score = parsed.get("score", 1)
    if isinstance(score, int) and 1 <= score <= 5:
        return score
    return None


def score_item(item: Dict) -> int:
    """Return a score between 1 and 5 using AI or heuristic."""
    title = item.get("title") or ""
    summary = item.get("summary") or ""
    text = f"{title} {summary}".strip()

    if AI_AVAILABLE and config.SUMMARIZER_API_KEY:
        try:
            url = f"{config.SUMMARIZER_API_BASE_URL.rstrip('/')}/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {config.SUMMARIZER_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": config.SCORE_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"News:\n{text}"},
                ],
                "temperature": 0.1,
                "max_tokens": 300,
            }
            resp = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=config.REQUEST_TIMEOUT_SECONDS,
            )
            resp.raise_for_status()
            data = resp.json()
            output = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            score = _extract_score_from_output(output)
            if score is not None:
                logger.debug("AI scored item '%s' as %d", item.get("title"), score)
                return score
            logger.warning("Invalid AI score output: %s", output)
        except Exception as e:
            logger.warning("AI scoring failed: %s", e)

    if not text:
        return 1
    length = len(text)
    if length < 100:
        return 1
    if length < 500:
        return 2
    if length < 1000:
        return 3
    if length < 2000:
        return 4
    return 5


def is_important(item: Dict) -> bool:
    return score_item(item) >= config.IMPORTANCE_THRESHOLD
