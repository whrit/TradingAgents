import json
from types import SimpleNamespace

import pytest
import requests

from tradingagents.dataflows import news_api_lite


class FakeResponse:
    def __init__(self, status_code=200, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.headers = headers or {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise news_api_lite.requests.HTTPError("boom", response=self)


def sample_post(**overrides):
    base = {
        "uuid": "123",
        "title": "Sample Headline",
        "text": "Sample body",
        "language": "english",
        "published": "2025-01-06T19:41:00.000+02:00",
        "sentiment": "neutral",
        "categories": ["Politics"],
        "thread": {
            "title": "Thread Title",
            "site": "example.com",
            "country": "US",
        },
    }
    base.update(overrides)
    return base


def setup_client(monkeypatch, responses):
    """Reset singleton client and patch requests.Session.get with a queue."""
    monkeypatch.setenv("WEBZ_API_TOKEN", "token-123")
    monkeypatch.setattr(news_api_lite, "_CLIENT", None, raising=False)

    calls = []

    def fake_get(self, url, params=None, timeout=None):
        calls.append(SimpleNamespace(url=url, params=params, timeout=timeout))
        if not responses:
            raise AssertionError("No more fake responses configured")
        return responses.pop(0)

    monkeypatch.setattr(news_api_lite.requests.Session, "get", fake_get, raising=False)
    return calls


def test_get_news_serializes_articles(monkeypatch):
    monkeypatch.setattr(news_api_lite, "_lookup_company_alias", lambda symbol: "Acme Inc")
    response_payload = {
        "posts": [sample_post(title="Ticker Headline")],
        "next": None,
        "totalResults": 1,
        "moreResultsAvailable": 0,
        "requestsLeft": 990,
    }
    calls = setup_client(monkeypatch, [FakeResponse(payload=response_payload)])

    payload = json.loads(
        news_api_lite.get_news_api_lite("AAPL", "2025-01-01", "2025-01-05")
    )

    assert payload["context"] == "ticker"
    assert payload["articles"][0]["title"] == "Ticker Headline"
    assert payload["meta"]["total_results"] == 1
    assert payload["meta"]["requests_left"] == 990

    assert calls[0].url == news_api_lite.BASE_URL
    query = calls[0].params["q"]
    assert 'ticker:"AAPL"' in query
    assert 'organization:"Acme Inc"' in query
    assert "published:>" in calls[0].params["q"]


def test_follow_next_page(monkeypatch):
    monkeypatch.setattr(news_api_lite, "_lookup_company_alias", lambda symbol: "Acme Inc")
    first_page = {
        "posts": [sample_post(uuid="1")],
        "next": "/newsApiLite?token=token-123&q=AAPL&ts=0&from=10",
        "totalResults": 15,
        "moreResultsAvailable": 5,
        "requestsLeft": 998,
    }
    second_page = {
        "posts": [sample_post(uuid="2")],
        "next": None,
        "totalResults": 15,
        "moreResultsAvailable": 0,
        "requestsLeft": 997,
    }
    calls = setup_client(monkeypatch, [FakeResponse(payload=first_page), FakeResponse(payload=second_page)])

    payload = json.loads(
        news_api_lite.get_news_api_lite("AAPL", "2025-01-01", "2025-01-05", max_pages=2)
    )

    assert len(payload["articles"]) == 2
    assert calls[1].url.startswith("https://")
    assert "/newsApiLite" in calls[1].url
    assert calls[1].params is None  # next URL already includes params


def test_get_global_news_uses_macro_query(monkeypatch):
    response_payload = {
        "posts": [sample_post(title="Macro Headline")],
        "next": None,
        "totalResults": 1,
        "moreResultsAvailable": 0,
        "requestsLeft": 999,
    }
    calls = setup_client(monkeypatch, [FakeResponse(payload=response_payload)])

    payload = json.loads(
        news_api_lite.get_news_api_lite_global("2025-01-20", 7, 5)
    )

    assert payload["context"] == "macro"
    assert payload["articles"][0]["title"] == "Macro Headline"
    assert "economy" in calls[0].params["q"]


def test_missing_token_raises(monkeypatch):
    monkeypatch.delenv("WEBZ_API_TOKEN", raising=False)
    with pytest.raises(ValueError):
        news_api_lite.get_news_api_lite("AAPL", "2025-01-01", "2025-01-05")


def test_alias_fallback_on_server_error(monkeypatch):
    monkeypatch.setattr(news_api_lite, "_lookup_company_alias", lambda symbol: "Acme Inc")

    class StubClient:
        def __init__(self):
            self.calls = []

        def fetch_posts(self, query, ts, limit, max_pages=5):
            self.calls.append(query)
            if len(self.calls) == 1:
                response = SimpleNamespace(status_code=500)
                raise requests.HTTPError("server error", response=response)
            return ([sample_post(title="Recovered")], {"totalResults": 1})

    stub = StubClient()
    monkeypatch.setattr(news_api_lite, "_client", lambda: stub)

    payload = json.loads(
        news_api_lite.get_news_api_lite("AAPL", "2025-01-01", "2025-01-05")
    )
    assert payload["articles"][0]["title"] == "Recovered"
    assert len(stub.calls) == 2
    assert "\"Acme Inc\"" in stub.calls[0]
    assert "\"Acme Inc\"" not in stub.calls[1]
