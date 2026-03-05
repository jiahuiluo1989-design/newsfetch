from news_pipeline.feishu_api import FeishuClient
import requests

c = FeishuClient()
c.authenticate()
url = f"{c.base_url}/bitable/v1/apps/{c.app_token}/tables/{c.table_id}/records"
headers = {"Authorization": f"Bearer {c.token}"}
payload = {"fields": {"Title": "Test title","Link": "https://example.com/test","Published": "2026-01-01","Summary": "Short","Status": "NEW","Score": None}}

print('sending payload', payload)
resp = requests.post(url, json=payload, headers=headers, timeout=60)
print('status', resp.status_code)
print('text', resp.text)
print('request body', resp.request.body)
