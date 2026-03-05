# News Pipeline

RSS -> Feishu Bitable -> scoring -> summary push.

## What It Does

1. `ingest_news`: fetch RSS, deduplicate by URL, write records to Feishu with `status=NEW`.
2. `score_news`: score `NEW` records without score and write `importance_score`.
3. `summarize_push`: collect `NEW` records with score >= threshold, send Feishu message, then set `status=SUMMARIZED`.

## Architecture

`RSS feeds -> ingest_news -> Feishu Bitable -> score_news -> summarize_push -> Feishu chat`

## Install

```powershell
python -m pip install -r requirements.txt
```

## Configuration (.env)

Required:

- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_APP_TOKEN` (Bitable app token, e.g. `WC7...`)
- `FEISHU_TABLE_ID` (table id, e.g. `tbl...`)
- `FEISHU_CHAT_ID` (target chat)
- `RSS_FEEDS` (comma-separated URLs)

Recommended:

- `FEISHU_HOST=https://open.feishu.cn` (China Feishu)
- `HTTP_PROXY=http://127.0.0.1:15236`
- `HTTPS_PROXY=http://127.0.0.1:15236`
- `IMPORTANCE_THRESHOLD=4`
- `SCORE_BATCH_SIZE=20`
- `REQUEST_TIMEOUT_SECONDS=20`
- `FEISHU_MAX_RETRIES=3`
- `FEISHU_RETRY_BACKOFF_SECONDS=1.5`
- `FEISHU_INTER_REQUEST_DELAY_SECONDS=0.2`

Note: `OPENAI_API_KEY` is currently used by the Gemini client in code. If quota is exhausted, scoring/summarization falls back to heuristic/truncated text.

## Feishu Table Schema

Current code expects these field names (case-sensitive):

- `source` (text)
- `title` (text)
- `url` (link)
- `published_at` (date-time)
- `hash` (text)
- `status` (single select, includes `NEW` and `SUMMARIZED`)
- `importance_score` (number)
- `asset_impact` (text or empty)
- `time_horizon` (single select or empty)
- `tags` (multi select or empty)
- `why` (text or empty)
- `summary` (text)

## Feishu App Scopes

Grant these scopes in Feishu Open Platform:

- `bitable:app`
- `im:chat:write`

Docs: <https://open.feishu.cn/document/>

## Usage

Run in order:

```powershell
python -m news_pipeline.ingest_news
python -m news_pipeline.score_news
python -m news_pipeline.summarize_push
```

## Operational Notes

- `score_news` processes records in batches (`SCORE_BATCH_SIZE`) to avoid long single runs.
- Feishu API can return HTTP 200 with business failure (`code != 0`). The client now treats this as error and logs `log_id`.
- RSS source instability is expected; failed feeds are skipped with warnings.

## Common Troubleshooting

1. "Ingest says inserted=N but table has no new rows"
- Cause: Feishu business error hidden under HTTP 200 in old versions.
- Now fixed: logs include `Feishu ... business error code=...`.

2. `URLFieldConvFail`
- Cause: `url` link field format mismatch.
- Fix: code now sends link as object (`{"link":"..."}`).

3. `InvalidFilter`
- Cause: Feishu filter formula incompatibility.
- Fix: code fetches records then filters in Python.

4. `SSLEOFError` / timeout
- Cause: unstable network/proxy.
- Fix: tune retries/timeouts and verify proxy in `.env`.

5. Gemini 429 quota exhausted
- Effect: summary/scoring falls back; pipeline still runs.

## Recommended Scheduling

- `ingest_news`: every 30 minutes
- `score_news`: every 30 minutes (or more frequently with small batch)
- `summarize_push`: 2 times/day (e.g. 09:30, 16:00)
