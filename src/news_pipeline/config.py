import os
from dotenv import load_dotenv

load_dotenv()

# RSS feeds configured via comma-separated list
RSS_FEEDS = os.getenv("RSS_FEEDS", "").split(",") if os.getenv("RSS_FEEDS") else []

# Feishu credentials
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET")
FEISHU_APP_TOKEN = os.getenv("FEISHU_APP_TOKEN")  # For Bitable
FEISHU_TABLE_ID = os.getenv("FEISHU_TABLE_ID")  # Table ID within app
FEISHU_CHAT_ID = os.getenv("FEISHU_CHAT_ID")  # For private messages
FEISHU_HOST = os.getenv("FEISHU_HOST", "https://open.feishu.cn")

# AI key for scoring/summarization
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUMMARIZER_API_BASE_URL = os.getenv("SUMMARIZER_API_BASE_URL", "https://api.gptsapi.net")
SUMMARIZER_API_KEY = os.getenv("SUMMARIZER_API_KEY")
SUMMARIZER_MODEL = os.getenv("SUMMARIZER_MODEL", "gpt-4o-mini")

# Optional HTTP/HTTPS proxy (e.g. http://localhost:15236)
HTTP_PROXY = os.getenv("HTTP_PROXY")
HTTPS_PROXY = os.getenv("HTTPS_PROXY")

# Apply proxy settings to environment so requests/urllib use them
if HTTP_PROXY:
    os.environ["HTTP_PROXY"] = HTTP_PROXY
if HTTPS_PROXY:
    os.environ["HTTPS_PROXY"] = HTTPS_PROXY


# Threshold for important articles (score 1-5, push if >=4)
IMPORTANCE_THRESHOLD = int(os.getenv("IMPORTANCE_THRESHOLD", "4"))

# Network resilience settings
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))
FEISHU_MAX_RETRIES = int(os.getenv("FEISHU_MAX_RETRIES", "3"))
FEISHU_RETRY_BACKOFF_SECONDS = float(os.getenv("FEISHU_RETRY_BACKOFF_SECONDS", "1.5"))
FEISHU_INTER_REQUEST_DELAY_SECONDS = float(os.getenv("FEISHU_INTER_REQUEST_DELAY_SECONDS", "0.2"))
SCORE_BATCH_SIZE = int(os.getenv("SCORE_BATCH_SIZE", "50"))
