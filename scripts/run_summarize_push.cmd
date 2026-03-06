@echo off
cd /d E:\git_projects\news-pipeline
set PYTHONPATH=E:\git_projects\news-pipeline\src
if not exist logs mkdir logs
echo [%date% %time%] START summarize_push>> logs\summarize_push.log
"E:\git_projects\news-pipeline\.venv\Scripts\python.exe" -m news_pipeline.summarize_push >> logs\summarize_push.log 2>&1
echo [%date% %time%] END summarize_push>> logs\summarize_push.log
