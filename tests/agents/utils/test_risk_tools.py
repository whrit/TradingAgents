import json
from unittest.mock import patch

from tradingagents.agents.utils import risk_tools


@patch("tradingagents.agents.utils.risk_tools.RiskEngine")
def test_calculate_portfolio_risk_formats_dashboard(mock_engine):
    mock_engine.return_value.generate.return_value = {
        "meta": {
            "ticker": "AAPL",
            "end_date": "2024-01-05",
            "lookback_days": 4,
            "data_points": 4,
        },
        "var": {
            "historical": {"0.95": {"value": -0.02, "expected_shortfall": -0.03, "confidence_interval": {"lower": -0.025, "upper": -0.015}}},
            "parametric": {"0.95": {"value": -0.021, "confidence_interval": {"lower": -0.03, "upper": -0.01}}},
        },
        "stress": {
            "market_crash_pct": -0.18,
            "sector_rotation_pct": -0.09,
            "vol_spike_cost": 4000,
            "liquidity_days": 1.2,
        },
        "liquidity": {"adv_dollars": 1_200_000, "days_to_exit": 1.2},
        "position_sizing": {"max_position": 200000, "optimal_position": 100000},
        "risk_limits": [
            {"metric": "VaR", "current": 0.02, "limit": 0.02, "status": "OK"},
        ],
    }

    report = risk_tools.calculate_portfolio_risk.invoke(
        {
            "ticker": "AAPL",
            "end_date": "2024-01-05",
            "lookback_days": 4,
            "confidence": 0.95,
        }
    )

    assert "Risk Dashboard" in report
    json_block = report.split("```json\n", 1)[1].split("```", 1)[0]
    payload = json.loads(json_block)
    assert payload["meta"]["ticker"] == "AAPL"
    mock_engine.return_value.generate.assert_called_once()
