"""Functions for fetching and parsing RSS/Atom feeds."""
import feedparser
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


def fetch_entries(feed_url: str) -> List[Dict]:
    """Retrieve and parse entries from a single RSS/Atom URL.

    Returns a list of dictionaries containing at least `title`, `link`, `published`, and `summary` if available.
    """
    logger.debug("Fetching feed %s", feed_url)
    try:
        feed = feedparser.parse(feed_url)
    except Exception as exc:
        logger.warning("Problem fetching/parsing feed %s: %s", feed_url, exc)
        return []
    if feed.bozo:
        logger.warning("Problem parsing feed %s: %s", feed_url, feed.bozo_exception)
        return []

    entries = []
    for entry in feed.entries:
        entries.append({
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "published": entry.get("published", entry.get("updated", "")),
            "summary": entry.get("summary", ""),
        })
    return entries


def fetch_all(feeds: List[str]) -> List[Dict]:
    """Fetch entries from a list of feed URLs."""
    results = []
    for url in feeds:
        if not url:
            continue
        results.extend(fetch_entries(url))
    return results
