from datetime import datetime, timedelta
from unittest.mock import patch

import json
import pytest

from tradingagents.agents.utils.risk_engine import RiskEngine, RiskInputs


def _build_csv(prices, start_date="2024-01-01", base_volume=5_000_000):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    lines = ["Date,Open,High,Low,Close,Volume"]
    for idx, price in enumerate(prices):
        day = start + timedelta(days=idx)
        open_px = round(price * 0.995, 4)
        high = round(price * 1.01, 4)
        low = round(price * 0.99, 4)
        volume = base_volume + idx * 50000
        lines.append(
            f"{day.date()},{open_px},{high},{low},{price},{volume}"
        )
    return "\n".join(lines)


SAMPLE_SERIES = {
    "AAPL": [100, 102, 101, 103, 105, 104, 107, 106],
    "SPY": [400, 401, 398, 404, 406, 405, 407, 409],
    "XLK": [150, 151, 149, 152, 153, 154, 155, 156],
}


SAMPLE_CSVS = {
    symbol: _build_csv(prices, base_volume=5_000_000 + idx * 100_000)
    for idx, (symbol, prices) in enumerate(SAMPLE_SERIES.items())
}


def _fake_vendor(method, symbol, start_date, end_date):
    assert method == "get_stock_data"
    return SAMPLE_CSVS[symbol]


@patch("tradingagents.agents.utils.risk_engine.route_to_vendor", side_effect=_fake_vendor)
def test_risk_engine_generates_structured_metrics(mock_vendor):
    engine = RiskEngine()
    inputs = RiskInputs(
        ticker="AAPL",
        benchmark="SPY",
        sector="XLK",
        end_date="2024-01-08",
        lookback_days=7,
        confidence_levels=(0.95, 0.99),
        portfolio_value=1_000_000,
        position_notional=150_000,
    )

    report = engine.generate(inputs)

    hist_95 = report["var"]["historical"]["0.95"]["value"]
    beta = report["beta"]["vs_benchmark"]

    assert hist_95 == pytest.approx(-0.0097198879, rel=1e-6)
    assert beta == pytest.approx(1.5087, rel=1e-4)
    assert report["liquidity"]["days_to_exit"] > 0
    assert report["stress"]["market_crash_pct"] < 0
    assert report["var"]["parametric"]["0.99"]["value"] < report["var"]["parametric"]["0.95"]["value"]
    assert mock_vendor.call_count == 3


@patch("tradingagents.agents.utils.risk_tools.RiskEngine")
def test_tool_returns_markdown_with_json(mock_engine):
    mock_engine.return_value.generate.return_value = {
        "meta": {
            "ticker": "AAPL",
            "end_date": "2024-01-08",
            "lookback_days": 7,
            "data_points": 5,
        },
        "var": {
            "historical": {"0.95": {"value": -0.02}},
            "parametric": {"0.95": {"value": -0.03}},
        },
        "liquidity": {"days_to_exit": 1.2, "adv_dollars": 1_000_000},
        "stress": {
            "market_crash_pct": -0.18,
            "sector_rotation_pct": -0.1,
            "vol_spike_cost": 5000,
            "liquidity_days": 1.2,
        },
        "position_sizing": {
            "max_position": 200000,
            "optimal_position": 100000,
        },
        "risk_limits": [
            {"metric": "VaR", "current": 0.02, "limit": 0.02, "status": "OK"}
        ],
    }

    from tradingagents.agents.utils import risk_tools

    text = risk_tools.calculate_portfolio_risk.invoke(
        {
            "ticker": "AAPL",
            "end_date": "2024-01-08",
            "lookback_days": 7,
            "confidence": 0.95,
        }
    )

    assert "Risk Dashboard" in text
    assert "```json" in text
    json_block = text.split("```json\n", 1)[1].split("```", 1)[0]
    payload = json.loads(json_block)
    assert payload["meta"]["ticker"] == "AAPL"
    mock_engine.return_value.generate.assert_called_once()
