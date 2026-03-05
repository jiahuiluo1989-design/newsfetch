"""Ingest news from RSS feeds, deduplicate, and write to Feishu Bitable with status=NEW."""
import hashlib
import logging
import time
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
from typing import Set

from . import rss_fetcher, feishu_api, config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def to_feishu_timestamp_ms(date_text: str):
    """Convert feed published date to Feishu date-time timestamp in milliseconds."""
    if not date_text:
        return None
    try:
        dt = parsedate_to_datetime(date_text)
        return int(dt.timestamp() * 1000)
    except Exception:
        return None


def extract_url_from_field(url_field):
    """Normalize Feishu url field to plain URL string."""
    if isinstance(url_field, str):
        return url_field
    if isinstance(url_field, dict):
        return url_field.get("link", "") or ""
    return ""


def deduplicate_entries(entries, existing_links: Set[str]):
    """Remove entries that are already in the table or duplicates in this batch."""
    seen = set()
    unique = []
    for entry in entries:
        link = entry.get("link", "")
        if link and link not in existing_links and link not in seen:
            seen.add(link)
            unique.append(entry)
    return unique


def main():
    logger.info("Starting ingest_news")
    feeds = config.RSS_FEEDS
    if not feeds:
        logger.error("No RSS feeds configured. Set RSS_FEEDS environment variable.")
        return

    # Fetch all entries
    entries = rss_fetcher.fetch_all(feeds)
    logger.info("Fetched %d entries", len(entries))

    # Get existing links from Feishu to avoid duplicates
    client = feishu_api.FeishuClient()
    try:
        records = client.get_records()
        existing_links = set()
        for record in records:
            url_value = extract_url_from_field(record["fields"].get("url"))
            if url_value:
                existing_links.add(url_value)
    except Exception as e:
        logger.warning("Failed to fetch existing records: %s", e)
        existing_links = set()

    # Deduplicate
    unique_entries = deduplicate_entries(entries, existing_links)
    logger.info("After deduplication: %d entries", len(unique_entries))

    # Insert new entries
    consecutive_failures = 0
    max_consecutive_failures = 5
    inserted_count = 0
    failed_count = 0
    for entry in unique_entries:
        link = entry.get("link", "")
        source = urlparse(link).netloc.replace("www.", "") if link else ""
        row_hash = hashlib.sha256(link.encode("utf-8")).hexdigest()[:16] if link else ""
        row_data = {
            "source": source,
            "title": entry.get("title", ""),
            "url": {"link": link} if link else None,
            "published_at": to_feishu_timestamp_ms(entry.get("published", "")),
            "hash": row_hash,
            "summary": entry.get("summary", ""),
            "status": "NEW",
            "importance_score": None,  # Will be scored later
        }
        try:
            client.create_row(row_data)
            logger.debug("Inserted: %s", entry.get("title"))
            consecutive_failures = 0
            inserted_count += 1
        except Exception as e:
            consecutive_failures += 1
            failed_count += 1
            logger.error("Failed to insert row for '%s': %s", entry.get("title"), e)
            if consecutive_failures >= max_consecutive_failures:
                logger.error(
                    "Stopping ingest after %d consecutive insert failures. "
                    "Likely transient network/API issue; retry in next run.",
                    consecutive_failures,
                )
                break
        delay_s = config.FEISHU_INTER_REQUEST_DELAY_SECONDS
        if delay_s > 0:
            time.sleep(delay_s)

    logger.info("Ingest complete. inserted=%d failed=%d", inserted_count, failed_count)


if __name__ == "__main__":
    main()
