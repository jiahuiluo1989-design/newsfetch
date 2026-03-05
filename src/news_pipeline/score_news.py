"""Score unscored NEW records in Feishu Bitable."""
import logging

from . import feishu_api, scoring, config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_url_from_field(url_field):
    if isinstance(url_field, str):
        return url_field
    if isinstance(url_field, dict):
        return url_field.get("link", "") or ""
    return ""


def main():
    logger.info("Starting score_news")
    client = feishu_api.FeishuClient()

    # Query all records then filter in Python to avoid Feishu formula compatibility issues.
    try:
        records = client.get_records()
    except Exception as e:
        logger.error("Failed to fetch records: %s", e)
        return
    records = [
        r for r in records
        if r.get("fields", {}).get("status") == "NEW"
        and r.get("fields", {}).get("importance_score") in (None, "")
    ]

    total_unscored = len(records)
    batch_size = max(1, config.SCORE_BATCH_SIZE)
    records = records[:batch_size]
    logger.info("Found %d unscored NEW records, processing %d this run", total_unscored, len(records))

    for idx, record in enumerate(records, 1):
        fields = record["fields"]
        item = {
            "title": fields.get("title", ""),
            "summary": fields.get("summary", ""),
            "link": extract_url_from_field(fields.get("url")),
        }
        score = scoring.score_item(item)
        try:
            client.update_row(record["record_id"], {"importance_score": score})
            logger.debug("Scored '%s' as %d", item["title"], score)
        except Exception as e:
            logger.error("Failed to update score for '%s': %s", item["title"], e)
        if idx % 10 == 0:
            logger.info("Scoring progress: %d/%d", idx, len(records))

    logger.info("Scoring complete")


if __name__ == "__main__":
    main()
