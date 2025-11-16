import datetime
from unittest.mock import patch


class TestAlphaVantageGlobalNews:
    def test_get_global_news_builds_topic_params(self):
        from tradingagents.dataflows.alpha_vantage_news import get_global_news

        with patch(
            "tradingagents.dataflows.alpha_vantage_news._make_api_request"
        ) as mock_request:
            mock_request.return_value = "{}"

            result = get_global_news("2025-01-10", look_back_days=3, limit=7)

        mock_request.assert_called_once()
        called_function, params = mock_request.call_args[0]

        assert called_function == "NEWS_SENTIMENT"
        assert params["topics"] == "financial_markets,economy,earnings"
        assert params["limit"] == "7"
        assert params["sort"] == "LATEST"
        assert params["time_to"].endswith("T2359")
        assert params["time_from"] < params["time_to"]
        assert result == "{}"
