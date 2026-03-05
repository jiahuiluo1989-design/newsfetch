"""Main entry point to run the pipeline."""
import logging

from . import rss_fetcher, feishu_api, scoring, summarizer, config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run():
    logger.info("Starting pipeline")
    feeds = config.RSS_FEEDS
    if not feeds:
        logger.error("No RSS feeds configured. Set RSS_FEEDS environment variable.")
        return

    entries = rss_fetcher.fetch_all(feeds)
    logger.info("Fetched %d entries", len(entries))

    client = feishu_api.FeishuClient()
    for item in entries:
        score = scoring.score_item(item)
        item["importance_score"] = score
        try:
            client.create_row({
                "title": item.get("title"),
                "url": {"link": item.get("link")} if item.get("link") else None,
                "published_at": item.get("published"),
                "importance_score": score,
                "status": "NEW",
            })
        except Exception as e:
            logger.error("Failed to write row to Feishu: %s", e)

        if score >= config.IMPORTANCE_THRESHOLD:
            text = item.get("summary") or item.get("title")
            summary = summarizer.summarize(text)
            try:
                client.send_message(summary)
            except Exception as e:
                logger.error("Failed to send summary: %s", e)

    logger.info("Pipeline complete")


if __name__ == "__main__":
    run()
