"""Minimal wrapper for Feishu (Lark) API to interact with multi-dimensional tables and send messages."""
import requests
import logging
import time
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from . import config

logger = logging.getLogger(__name__)


class FeishuClient:
    def __init__(self):
        self.app_id = config.FEISHU_APP_ID
        self.app_secret = config.FEISHU_APP_SECRET
        self.app_token = config.FEISHU_APP_TOKEN
        self.table_id = config.FEISHU_TABLE_ID
        self.chat_id = config.FEISHU_CHAT_ID
        self.base_url = f"{config.FEISHU_HOST}/open-apis"
        self.token = None
        self.timeout = config.REQUEST_TIMEOUT_SECONDS
        self.max_retries = config.FEISHU_MAX_RETRIES
        self.retry_backoff = config.FEISHU_RETRY_BACKOFF_SECONDS
        self.session = requests.Session()
        retry_strategy = Retry(
            total=self.max_retries,
            connect=self.max_retries,
            read=self.max_retries,
            status=self.max_retries,
            allowed_methods=frozenset(["GET", "POST", "PUT"]),
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=self.retry_backoff,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _request_with_retry(self, method: str, url: str, **kwargs):
        """Perform HTTP request with retry for transient network/TLS issues."""
        kwargs.setdefault("timeout", self.timeout)
        last_exc = None
        for attempt in range(1, self.max_retries + 1):
            try:
                if method == "GET":
                    return self.session.get(url, **kwargs)
                if method == "POST":
                    return self.session.post(url, **kwargs)
                if method == "PUT":
                    return self.session.put(url, **kwargs)
                raise ValueError(f"Unsupported HTTP method: {method}")
            except (requests.exceptions.SSLError, requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
                last_exc = exc
                if attempt >= self.max_retries:
                    break
                wait_s = self.retry_backoff * (2 ** (attempt - 1))
                logger.warning(
                    "Transient %s error on %s attempt %d/%d, retrying in %.1fs: %s",
                    type(exc).__name__,
                    url,
                    attempt,
                    self.max_retries,
                    wait_s,
                    exc,
                )
                time.sleep(wait_s)
        raise last_exc

    def _check_feishu_business_error(self, resp, action: str, payload=None):
        """Feishu may return HTTP 200 with non-zero `code`; treat it as failure."""
        try:
            data = resp.json()
        except ValueError:
            return
        code = data.get("code", 0)
        if code == 0:
            return
        msg = data.get("msg", "unknown error")
        err_msg = data.get("error", {}).get("message", "")
        log_id = data.get("error", {}).get("log_id", "")
        if "bitable:app" in msg or "bitable:app" in err_msg:
            raise PermissionError(
                "Feishu token missing required 'bitable:app' scope. "
                "Update your app permissions and re-generate credentials."
            )
        if "im:chat:write" in msg or "im:chat:write" in err_msg:
            raise PermissionError(
                "Feishu token missing required 'im:chat:write' scope. "
                "Update your app permissions and re-generate credentials."
            )
        logger.error(
            "Feishu %s business error code=%s msg=%s log_id=%s payload=%s",
            action,
            code,
            msg,
            log_id,
            payload,
        )
        raise RuntimeError(f"Feishu {action} failed: code={code}, msg={msg}, log_id={log_id}, detail={err_msg}")

    def authenticate(self):
        if self.token:
            return self.token
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        payload = {"app_id": self.app_id, "app_secret": self.app_secret}
        resp = self._request_with_retry("POST", url, json=payload)
        self._check_feishu_business_error(resp, "authenticate", payload)
        resp.raise_for_status()
        data = resp.json()
        self.token = data.get("tenant_access_token")
        return self.token

    def create_row(self, row_data: dict) -> dict:
        """Insert a row into the configured table."""
        self.authenticate()
        url = f"{self.base_url}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records"
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {"fields": row_data}
        resp = self._request_with_retry("POST", url, json=payload, headers=headers)
        self._check_feishu_business_error(resp, "create_row", payload)
        if resp.status_code >= 400:
            logger.error("Feishu create_row failed (%d): %s\npayload=%s", resp.status_code, resp.text, payload)
            # common permission error when app lacks bitable scope
            try:
                data = resp.json()
                msg = data.get("msg", "")
                if "bitable:app" in msg:
                    raise PermissionError(
                        "Feishu token missing required 'bitable:app' scope. "
                        "Update your app permissions and re-generate credentials."
                    )
            except ValueError:
                # not JSON, ignore
                pass
        resp.raise_for_status()
        return resp.json()

    def get_records(self, filter_formula=None):
        """Retrieve records from the table, optionally filtered."""
        self.authenticate()
        url = f"{self.base_url}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records"
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {}
        if filter_formula:
            params["filter"] = filter_formula
        resp = self._request_with_retry("GET", url, headers=headers, params=params)
        self._check_feishu_business_error(resp, "get_records", params)
        resp.raise_for_status()
        return resp.json().get("data", {}).get("items", [])

    def update_row(self, record_id: str, row_data: dict) -> dict:
        """Update a row in the table."""
        self.authenticate()
        url = f"{self.base_url}/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records/{record_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {"fields": row_data}
        resp = self._request_with_retry("PUT", url, json=payload, headers=headers)
        self._check_feishu_business_error(resp, "update_row", payload)
        if resp.status_code >= 400:
            logger.error("Feishu update_row failed (%d): %s\npayload=%s", resp.status_code, resp.text, payload)
            try:
                data = resp.json()
                msg = data.get("msg", "")
                if "bitable:app" in msg:
                    raise PermissionError(
                        "Feishu token missing required 'bitable:app' scope. "
                        "Update your app permissions and re-generate credentials."
                    )
            except ValueError:
                pass
        resp.raise_for_status()
        return resp.json()

    def send_message(self, content: str):
        """Send a private message to the configured chat."""
        self.authenticate()
        url = f"{self.base_url}/im/v1/messages"
        headers = {"Authorization": f"Bearer {self.token}"}
        text = content if isinstance(content, str) else str(content)
        payload = {
            "receive_id": self.chat_id,
            "content": json.dumps({"text": text}, ensure_ascii=False),
            "msg_type": "text"
        }
        resp = self._request_with_retry(
            "POST",
            url,
            params={"receive_id_type": "chat_id"},
            json=payload,
            headers=headers,
        )
        self._check_feishu_business_error(resp, "send_message", payload)
        if resp.status_code >= 400:
            logger.error("Feishu send_message failed (%d): %s\npayload=%s", resp.status_code, resp.text, payload)
            try:
                data = resp.json()
                msg = data.get("msg", "")
                if "im:chat:write" in msg:
                    raise PermissionError(
                        "Feishu token missing required 'im:chat:write' scope. "
                        "Update your app permissions and re-generate credentials."
                    )
            except ValueError:
                pass
        resp.raise_for_status()
        return resp.json()
