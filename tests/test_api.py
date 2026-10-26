import uuid

from fastapi.testclient import TestClient

from app.db import get_conn
from app.main import app

client = TestClient(app)


def unique_alias():
    return "t" + uuid.uuid4().hex[:10]


def test_shorten_and_redirect():
    r = client.post("/shorten", json={"url": "https://www.wikipedia.org"})
    assert r.status_code == 200
    code = r.json()["short_code"]

    r2 = client.get(f"/{code}", follow_redirects=False)
    assert r2.status_code == 302
    assert r2.headers["location"].startswith("https://www.wikipedia.org")


def test_custom_alias_and_duplicate():
    alias = unique_alias()
    body = {"url": "https://www.wikipedia.org", "alias": alias}
    assert client.post("/shorten", json=body).status_code == 200
    assert client.post("/shorten", json=body).status_code == 409


def test_invalid_alias_and_reserved():
    url = "https://www.wikipedia.org"
    assert client.post("/shorten", json={"url": url, "alias": "a b"}).status_code == 422
    assert client.post("/shorten", json={"url": url, "alias": "docs"}).status_code == 422


def test_invalid_url():
    assert client.post("/shorten", json={"url": "hello"}).status_code == 422


def test_unknown_code():
    assert client.get("/doesnotexist999", follow_redirects=False).status_code == 404


def test_expiry_limits():
    url = "https://www.wikipedia.org"
    assert client.post("/shorten", json={"url": url, "expires_in_days": 0}).status_code == 422
    assert client.post("/shorten", json={"url": url, "expires_in_days": 999}).status_code == 422


def test_expired_link_returns_410():
    alias = unique_alias()
    body = {"url": "https://www.wikipedia.org", "alias": alias, "expires_in_days": 1}
    client.post("/shorten", json=body)
    with get_conn() as conn:
        conn.execute(
            "UPDATE urls SET expires_at = now() - interval '1 hour' WHERE short_code = %s",
            (alias,),
        )
    assert client.get(f"/{alias}", follow_redirects=False).status_code == 410


def test_stats_counts_clicks():
    alias = unique_alias()
    client.post("/shorten", json={"url": "https://www.wikipedia.org", "alias": alias})
    client.get(f"/{alias}", follow_redirects=False)
    client.get(f"/{alias}", follow_redirects=False)

    r = client.get(f"/stats/{alias}")
    assert r.status_code == 200
    assert r.json()["total_clicks"] == 2


def test_stats_unknown_code():
    assert client.get("/stats/doesnotexist999").status_code == 404