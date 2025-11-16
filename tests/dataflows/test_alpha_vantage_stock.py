import json

import pytest

from tradingagents.dataflows import alpha_vantage_stock as av_stock


def _sample_response():
    return json.dumps(
        {
            "Time Series (Daily)": {
                "2024-01-03": {
                    "1. open": "100.0",
                    "2. high": "110.0",
                    "3. low": "95.0",
                    "4. close": "108.0",
                    "5. adjusted close": "108.0",
                    "6. volume": "100000",
                    "7. dividend amount": "0.0",
                    "8. split coefficient": "1.0",
                },
                "2024-01-02": {
                    "1. open": "90.0",
                    "2. high": "105.0",
                    "3. low": "89.0",
                    "4. close": "100.0",
                    "5. adjusted close": "100.0",
                    "6. volume": "120000",
                    "7. dividend amount": "0.0",
                    "8. split coefficient": "1.0",
                },
            }
        }
    )


def test_get_stock_uses_cache(monkeypatch):
    av_stock._STOCK_CACHE.clear()
    call_counter = {"count": 0}

    def fake_request(*args, **kwargs):
        call_counter["count"] += 1
        return _sample_response()

    monkeypatch.setattr(av_stock, "_make_api_request", fake_request)

    csv_one = av_stock.get_stock("AAPL", "2024-01-02", "2024-01-03")
    csv_two = av_stock.get_stock("aapl", "2024-01-03", "2024-01-03")

    assert call_counter["count"] == 1
    assert "2024-01-03" in csv_one
    assert "2024-01-03" in csv_two


def test_get_stock_validates_dates(monkeypatch):
    av_stock._STOCK_CACHE.clear()
    monkeypatch.setattr(av_stock, "_make_api_request", lambda *_, **__: _sample_response())

    with pytest.raises(ValueError):
        av_stock.get_stock("AAPL", "2024-01-04", "2024-01-01")
