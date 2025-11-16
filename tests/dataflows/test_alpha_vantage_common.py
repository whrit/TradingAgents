import types

import pytest

from tradingagents.dataflows import alpha_vantage_common as av


class DummyResponse:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self):
        return None


def _patch_requests(monkeypatch, text: str):
    def fake_get(*args, **kwargs):
        return DummyResponse(text)

    monkeypatch.setattr(av.requests, "get", fake_get)


def test_make_api_request_raises_premium(monkeypatch):
    _patch_requests(
        monkeypatch,
        '{"Information": "Thank you for using Alpha Vantage! This is a premium endpoint."}',
    )
    monkeypatch.setattr(av, "get_api_key", lambda: "demo")

    with pytest.raises(av.AlphaVantagePremiumError):
        av._make_api_request("TIME_SERIES_DAILY", {})


def test_make_api_request_raises_rate_limit(monkeypatch):
    _patch_requests(
        monkeypatch,
        '{"Information": "Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute and 500 calls per day."}',
    )
    monkeypatch.setattr(av, "get_api_key", lambda: "demo")

    with pytest.raises(av.AlphaVantageRateLimitError):
        av._make_api_request("TIME_SERIES_DAILY", {})


def test_make_api_request_raises_generic_error(monkeypatch):
    _patch_requests(
        monkeypatch,
        '{"Information": "Invalid inputs. Please refer to the API documentation https://www.alphavantage.co/documentation/#newsapi and try again."}',
    )
    monkeypatch.setattr(av, "get_api_key", lambda: "demo")

    with pytest.raises(ValueError):
        av._make_api_request("NEWS_SENTIMENT", {})
