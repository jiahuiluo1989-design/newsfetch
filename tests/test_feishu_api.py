import pytest

from news_pipeline import feishu_api


class DummyResponse:
    def __init__(self, status_code, text, json_data=None):
        self.status_code = status_code
        self.text = text
        self._json = json_data or {}
        self.request = type("Req", (), {"body": text})

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"{self.status_code} {self.text}")


@pytest.fixture(autouse=True)
def patch_auth(monkeypatch):
    # avoid actual network in authenticate()
    monkeypatch.setattr(feishu_api.FeishuClient, "authenticate", lambda self: "fake-token")


def test_create_row_scope_error(monkeypatch):
    client = feishu_api.FeishuClient()
    # simulate bitable scope error
    resp = DummyResponse(
        400,
        "error",
        json_data={"msg": "Access denied. One of the following scopes is required: [bitable:app]"},
    )
    monkeypatch.setattr(client, "_request_with_retry", lambda *args, **kwargs: resp)
    with pytest.raises(PermissionError) as excinfo:
        client.create_row({"foo": "bar"})
    assert "bitable:app" in str(excinfo.value)


def test_update_row_scope_error(monkeypatch):
    client = feishu_api.FeishuClient()
    resp = DummyResponse(
        400,
        "error",
        json_data={"msg": "Access denied. One of the following scopes is required: [bitable:app]"},
    )
    monkeypatch.setattr(client, "_request_with_retry", lambda *args, **kwargs: resp)
    with pytest.raises(PermissionError):
        client.update_row("id", {"foo": "bar"})


def test_send_message_scope_error(monkeypatch):
    client = feishu_api.FeishuClient()
    resp = DummyResponse(
        400,
        "error",
        json_data={"msg": "Access denied. One of the following scopes is required: [im:chat:write]"},
    )
    monkeypatch.setattr(client, "_request_with_retry", lambda *args, **kwargs: resp)
    with pytest.raises(PermissionError):
        client.send_message("hello")


def test_create_row_business_error_raises(monkeypatch):
    client = feishu_api.FeishuClient()
    resp = DummyResponse(
        200,
        "ok",
        json_data={
            "code": 1254068,
            "msg": "URLFieldConvFail",
            "error": {"message": "the value of 'Link' must be an object.", "log_id": "abc"},
        },
    )
    monkeypatch.setattr(client, "_request_with_retry", lambda *args, **kwargs: resp)
    with pytest.raises(RuntimeError) as excinfo:
        client.create_row({"url": "https://example.com"})
    assert "URLFieldConvFail" in str(excinfo.value)
