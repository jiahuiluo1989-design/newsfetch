"""Assign importance scores to articles."""
import json
import logging
from typing import Dict

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

try:
    import google.genai as genai
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    logger.warning("GenAI client not available, falling back to heuristic scoring")


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

    if AI_AVAILABLE and config.OPENAI_API_KEY:
        try:
            client = genai.Client(api_key=config.OPENAI_API_KEY)
            response = client.models.generate_content(
                model="models/gemini-3-pro-preview",
                contents=f"{SYSTEM_PROMPT}\n\nNews:\n{text}",
            )
            output = response.candidates[0].content.parts[0].text.strip()
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
