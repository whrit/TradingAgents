import pytest

from tradingagents.agents.utils import news_data_tools as tools_module


def test_get_news_validates_and_calls_route(monkeypatch):
    captured = {}

    def fake_route(method, *args):
        captured["method"] = method
        captured["args"] = args
        return "payload"

    monkeypatch.setattr(tools_module, "route_to_vendor", fake_route)

    result = tools_module.get_news.invoke(
        {"ticker": "aapl", "start_date": "2024-01-01", "end_date": "2024-01-05"}
    )

    assert result == "payload"
    assert captured["method"] == "get_news"
    assert captured["args"][0] == "AAPL"
    assert captured["args"][1:] == ("2024-01-01", "2024-01-05")


def test_get_news_rejects_future_window(monkeypatch):
    future = "2999-01-01"
    with pytest.raises(ValueError):
        tools_module.get_news.invoke(
            {"ticker": "AAPL", "start_date": future, "end_date": future}
        )


def test_get_global_news_caps_limit(monkeypatch):
    captured = {}

    def fake_route(method, *args):
        captured["method"] = method
        captured["args"] = args
        return "ok"

    monkeypatch.setattr(tools_module, "route_to_vendor", fake_route)

    result = tools_module.get_global_news.invoke(
        {"curr_date": "2024-06-01", "look_back_days": 5, "limit": 999}
    )

    assert result == "ok"
    assert captured["method"] == "get_global_news"
    assert captured["args"][0] == "2024-06-01"
    assert captured["args"][2] == tools_module.MAX_NEWS_LIMIT


def test_get_global_news_rejects_future_date(monkeypatch):
    with pytest.raises(ValueError):
        tools_module.get_global_news.invoke(
            {"curr_date": "2999-05-01", "look_back_days": 3, "limit": 10}
        )
