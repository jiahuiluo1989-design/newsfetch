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
- `SCORE_BATCH_SIZE=100`
- `REQUEST_TIMEOUT_SECONDS=20`
- `FEISHU_MAX_RETRIES=3`
- `FEISHU_RETRY_BACKOFF_SECONDS=1.5`
- `FEISHU_INTER_REQUEST_DELAY_SECONDS=0.2`
- `SUMMARIZER_API_BASE_URL=https://api.gptsapi.net`
- `SUMMARIZER_API_KEY=...`
- `SCORE_MODEL=gemini-2.5-flash`
- `SUMMARIZER_MODEL=gemini-3-flash-preview`

Note:
- Scoring and summary both use OpenAI-compatible API (`SUMMARIZER_API_BASE_URL` + `SUMMARIZER_API_KEY`).
- Scoring model: `SCORE_MODEL` (default `gemini-2.5-flash`).
- Summary model: `SUMMARIZER_MODEL` (default `gemini-3-flash-preview`).
- `OPENAI_API_KEY` is currently optional/legacy.

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

## Runbook (PowerShell)

Run from project root: `E:\git_projects\news-pipeline`

1. Create and install venv dependencies (first time):

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m ensurepip --upgrade
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

2. Manual run (one-time):

```powershell
$env:PYTHONPATH="E:\git_projects\news-pipeline\src"
.venv\Scripts\python.exe -m news_pipeline.ingest_news
.venv\Scripts\python.exe -m news_pipeline.score_news
.venv\Scripts\python.exe -m news_pipeline.summarize_push
```

3. Create scheduled tasks (already used in this project):

```powershell
cmd /c schtasks /Create /TN "news-pipeline-ingest-30min" /TR "wscript.exe ""E:\git_projects\news-pipeline\scripts\run_hidden.vbs"" ""E:\git_projects\news-pipeline\scripts\run_ingest_news.cmd""" /SC MINUTE /MO 30 /ST 00:00 /F
cmd /c schtasks /Create /TN "news-pipeline-score-30min" /TR "wscript.exe ""E:\git_projects\news-pipeline\scripts\run_hidden.vbs"" ""E:\git_projects\news-pipeline\scripts\run_score_news.cmd""" /SC MINUTE /MO 15 /ST 00:05 /F
cmd /c schtasks /Create /TN "news-pipeline-summarize-0930" /TR "wscript.exe ""E:\git_projects\news-pipeline\scripts\run_hidden.vbs"" ""E:\git_projects\news-pipeline\scripts\run_summarize_push.cmd""" /SC DAILY /ST 09:30 /F
cmd /c schtasks /Create /TN "news-pipeline-summarize-1600" /TR "wscript.exe ""E:\git_projects\news-pipeline\scripts\run_hidden.vbs"" ""E:\git_projects\news-pipeline\scripts\run_summarize_push.cmd""" /SC DAILY /ST 16:00 /F
```

4. Query tasks:

```powershell
schtasks /Query /TN "news-pipeline-ingest-30min" /V /FO LIST
schtasks /Query /TN "news-pipeline-score-30min" /V /FO LIST
schtasks /Query /TN "news-pipeline-summarize-0930" /V /FO LIST
schtasks /Query /TN "news-pipeline-summarize-1600" /V /FO LIST
```

5. Run task immediately:

```powershell
schtasks /Run /TN "news-pipeline-ingest-30min"
schtasks /Run /TN "news-pipeline-score-30min"
schtasks /Run /TN "news-pipeline-summarize-0930"
```

6. View recent logs:

```powershell
Get-Content logs\ingest_news.log -Tail 100
Get-Content logs\score_news.log -Tail 100
Get-Content logs\summarize_push.log -Tail 100
```

7. Delete tasks (if needed):

```powershell
schtasks /Delete /TN "news-pipeline-ingest-30min" /F
schtasks /Delete /TN "news-pipeline-score-30min" /F
schtasks /Delete /TN "news-pipeline-summarize-0930" /F
schtasks /Delete /TN "news-pipeline-summarize-1600" /F
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

5. AI API quota/rate-limit exhausted
- Effect: summary/scoring falls back; pipeline still runs.

## Recommended Scheduling

- `ingest_news`: every 30 minutes
- `score_news`: every 15 minutes (recommended with `SCORE_BATCH_SIZE=100`)
- `summarize_push`: 2 times/day (e.g. 09:30, 16:00)

