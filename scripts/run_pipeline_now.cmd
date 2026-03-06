@echo off
cd /d E:\git_projects\news-pipeline
schtasks /Run /TN "news-pipeline-ingest-30min"
schtasks /Run /TN "news-pipeline-score-30min"
schtasks /Run /TN "news-pipeline-summarize-0930"
echo Triggered tasks: ingest + score + summarize(0930)
