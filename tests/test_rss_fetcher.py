from news_pipeline import rss_fetcher


def test_fetch_entries_invalid():
    # invalid URL should return empty list without throwing
    entries = rss_fetcher.fetch_entries("http://not.a.real.feed")
    assert isinstance(entries, list)
