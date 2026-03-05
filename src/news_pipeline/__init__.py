"""news_pipeline package."""

# core components; avoid heavy imports on package initialization
# import configuration first so proxy/env vars are applied before other modules
from . import config
from . import rss_fetcher, feishu_api, runner
# delay imports of scoring/summarizer until needed in scripts
def load_scoring():
    from . import scoring
    return scoring

def load_summarizer():
    from . import summarizer
    return summarizer

def load_ingest():
    from . import ingest_news
    return ingest_news

def load_score_news():
    from . import score_news
    return score_news

def load_summarize_push():
    from . import summarize_push
    return summarize_push

