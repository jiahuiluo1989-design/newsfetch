@echo off
cd /d E:\git_projects\news-pipeline
set PYTHONPATH=E:\git_projects\news-pipeline\src
if not exist logs mkdir logs
echo [%date% %time%] START startup_bootstrap>> logs\startup_bootstrap.log
"E:\git_projects\news-pipeline\.venv\Scripts\python.exe" -m news_pipeline.ingest_news >> logs\startup_bootstrap.log 2>&1
"E:\git_projects\news-pipeline\.venv\Scripts\python.exe" -m news_pipeline.score_news >> logs\startup_bootstrap.log 2>&1
echo [%date% %time%] END startup_bootstrap>> logs\startup_bootstrap.log
