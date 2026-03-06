@echo off
cd /d E:\git_projects\news-pipeline
set PYTHONPATH=E:\git_projects\news-pipeline\src
if not exist logs mkdir logs
echo [%date% %time%] START score_news>> logs\score_news.log
"E:\git_projects\news-pipeline\.venv\Scripts\python.exe" -m news_pipeline.score_news >> logs\score_news.log 2>&1
echo [%date% %time%] END score_news>> logs\score_news.log
