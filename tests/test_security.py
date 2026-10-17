import base64
import hashlib
import hmac

import pytest
from fastapi.testclient import TestClient

from app import llm, security, store
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def db(tmp_path):
    store.reset_for_tests(str(tmp_path / "t.db"))
    security.limiter.reset()


def test_security_headers_on_api_and_page():
    r = client.get("/api/languages")
    assert r.headers["x-content-type-options"] == "nosniff" and r.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]
    assert "public" in r.headers["cache-control"]                        # shared reference data is cacheable
    page = client.get("/")
    assert "script-src 'self'" in page.headers["content-security-policy"]


def test_user_data_is_never_cached():
    r = client.get("/api/dashboard/u-abcdefghijklmnop?lang=en")
    assert r.headers["cache-control"] == "no-store"


def test_cors_allows_only_known_origins():
    ok = client.options("/chat", headers={"Origin": "https://gigsaathi-web.vercel.app", "Access-Control-Request-Method": "POST"})
    assert ok.headers.get("access-control-allow-origin") == "https://gigsaathi-web.vercel.app"
    bad = client.options("/chat", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in bad.headers


def test_oversized_body_rejected():
    r = client.post("/chat", content=b"x", headers={"content-length": str(security.MAX_BODY_BYTES + 1), "content-type": "application/json"})
    assert r.status_code == 413


def test_rate_limit_ai_routes(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT", "1")
    monkeypatch.setitem(security.LIMITS, "ai", (3, 60))
    codes = [client.post("/chat", json={"user": "rate-test-user-0001", "text": "hello"}).status_code for _ in range(4)]
    assert codes[:3] == [200, 200, 200] and codes[3] == 429


def test_rate_limiter_window_slides():
    rl = security.RateLimiter()
    limit = security.LIMITS["read"][0]
    assert all(rl.allow("1.2.3.4", "read", now=100.0)[0] for _ in range(limit))
    assert rl.allow("1.2.3.4", "read", now=100.0)[0] is False
    assert rl.allow("5.6.7.8", "read", now=100.0)[0] is True           # other clients unaffected
    assert rl.allow("1.2.3.4", "read", now=161.0)[0] is True           # window has passed


def test_twilio_signature_required_when_token_set(monkeypatch):
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "secret-token")
    url = "http://testserver/whatsapp"
    form = {"Body": "hello", "From": "whatsapp:+910000000000"}
    assert client.post("/whatsapp", data=form).status_code == 403
    payload = url + "".join(k + form[k] for k in sorted(form))
    sig = base64.b64encode(hmac.new(b"secret-token", payload.encode(), hashlib.sha1).digest()).decode()
    assert client.post("/whatsapp", data=form, headers={"X-Twilio-Signature": sig}).status_code == 200


def test_chat_rejects_malformed_user_id():
    assert client.post("/chat", json={"user": "<script>", "text": "hi"}).status_code == 422


def test_image_media_type_allowlist():
    assert client.post("/api/extract/payout-image", json={"image_b64": "AAAA", "media_type": "text/html"}).status_code == 422


def test_document_text_masked_before_llm(monkeypatch):
    sent = {}
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")

    class Fake:
        def post(self, path, headers, json, **kw):
            sent["body"] = json

            class R:
                def raise_for_status(self): pass
                def json(self): return {"content": [{"text": "ok"}]}
            return R()
    monkeypatch.setattr(llm, "_http", lambda: Fake())
    llm.complete("sys", "Aadhaar 1234 5678 9012, PAN ABCDE1234F")
    text = sent["body"]["messages"][0]["content"][-1]["text"]
    assert "1234 5678 9012" not in text and "ABCDE1234F" not in text


def test_errors_do_not_leak_internals(monkeypatch):
    from app import orchestrator
    monkeypatch.setattr(orchestrator, "handle", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("db password=hunter2")))
    r = TestClient(app, raise_server_exceptions=False).post("/chat", json={"user": "leak-test-user-01", "text": "hi"})
    assert r.status_code == 500 and "hunter2" not in r.text
