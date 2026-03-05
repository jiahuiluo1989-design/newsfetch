"""Generate summaries for high-score NEW records, send via Feishu, and mark as SUMMARIZED."""
import logging
from datetime import datetime

from . import feishu_api, summarizer, config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_url_from_field(url_field):
    if isinstance(url_field, str):
        return url_field
    if isinstance(url_field, dict):
        return url_field.get("link", "") or ""
    return ""


def normalize_score(value):
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def main():
    logger.info("Starting summarize_push")
    client = feishu_api.FeishuClient()

    # Query all records then filter in Python to avoid Feishu formula compatibility issues.
    try:
        records = client.get_records()
    except Exception as e:
        logger.error("Failed to fetch records: %s", e)
        return
    filtered = []
    for r in records:
        fields = r.get("fields", {})
        if fields.get("status") != "NEW":
            continue
        score = normalize_score(fields.get("importance_score"))
        if score is not None and score >= config.IMPORTANCE_THRESHOLD:
            filtered.append(r)
    records = filtered

    if not records:
        logger.info("No high-score NEW records to summarize")
        return

    logger.info("Found %d high-score NEW records", len(records))

    summaries = []
    for record in records:
        fields = record["fields"]
        title = fields.get("title", "")
        summary_text = fields.get("summary", "")
        link = extract_url_from_field(fields.get("url"))
        score = fields.get("importance_score", 0)

        text_to_summarize = f"{title} {summary_text}"
        try:
            summary = summarizer.summarize(text_to_summarize)
            if not summary:
                summary = text_to_summarize[:200] + "..."
        except Exception as e:
            logger.warning("Failed to summarize '%s': %s", title, e)
            summary = text_to_summarize[:200] + "..."

        summaries.append(f"**{title}** (Score: {score})\n{summary}\n[Link]({link})")

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    message = f"**Research Brief - {now}**\n\n" + "\n\n---\n\n".join(summaries)

    try:
        client.send_message(message)
        logger.info("Sent summary message")
    except Exception as e:
        logger.error("Failed to send message: %s", e)
        return

    for record in records:
        try:
            client.update_row(record["record_id"], {"status": "SUMMARIZED"})
            logger.debug("Marked as SUMMARIZED: %s", record["fields"].get("title"))
        except Exception as e:
            logger.error("Failed to update status for '%s': %s", record["fields"].get("title"), e)

    logger.info("Summarize and push complete")


if __name__ == "__main__":
    main()
