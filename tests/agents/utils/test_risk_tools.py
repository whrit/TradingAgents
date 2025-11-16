from unittest.mock import patch

from tradingagents.agents.utils import risk_tools


SAMPLE_CSV = """Date,Open,High,Low,Close,Volume
2024-01-01,100,101,99,100,1000
2024-01-02,100,102,99,101,1000
2024-01-03,101,103,100,102,1000
2024-01-04,102,104,101,103,1000
2024-01-05,103,105,102,104,1000
"""


@patch("tradingagents.agents.utils.risk_tools.route_to_vendor", return_value=SAMPLE_CSV)
def test_calculate_portfolio_risk(mock_route):
    report = risk_tools.calculate_portfolio_risk.invoke(
        {
            "ticker": "AAPL",
            "end_date": "2024-01-05",
            "lookback_days": 4,
            "confidence": 0.95,
        }
    )
    assert "Risk Snapshot" in report
    assert "AAPL" in report
    mock_route.assert_called_once()
