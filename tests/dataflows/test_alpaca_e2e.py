"""
End-to-end test for Alpaca data vendor integration.

Verifies the complete flow from configuration to data retrieval.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd


class TestAlpacaEndToEnd:
    """End-to-end tests simulating real usage scenarios."""

    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Set up environment variables."""
        monkeypatch.setenv("ALPACA_API_KEY", "test_alpaca_key")
        monkeypatch.setenv("ALPACA_SECRET_KEY", "test_alpaca_secret")

    @pytest.fixture
    def sample_alpaca_bars(self):
        """Sample Alpaca bars response."""
        return {
            'bars': [
                {
                    't': '2025-01-10T05:00:00Z',
                    'o': 150.00,
                    'h': 152.00,
                    'l': 149.50,
                    'c': 151.50,
                    'v': 1000000,
                    'vw': 151.00
                },
                {
                    't': '2025-01-11T05:00:00Z',
                    'o': 151.50,
                    'h': 153.50,
                    'l': 150.50,
                    'c': 153.00,
                    'v': 1200000,
                    'vw': 152.50
                },
                {
                    't': '2025-01-12T05:00:00Z',
                    'o': 153.00,
                    'h': 154.00,
                    'l': 152.00,
                    'c': 153.50,
                    'v': 1100000,
                    'vw': 153.00
                }
            ]
        }

    def test_complete_flow_with_alpaca_primary(self, mock_env, sample_alpaca_bars):
        """Test complete flow using Alpaca as primary vendor."""
        # Mock configuration
        with patch("tradingagents.dataflows.interface.get_config") as mock_config:
            mock_config.return_value = {
                "data_vendors": {
                    "core_stock_apis": "alpaca"
                },
                "tool_vendors": {}
            }

            # Mock Alpaca client
            with patch('tradingagents.dataflows.alpaca.data.get_client') as mock_get_client:
                mock_client = Mock()
                mock_client._request.return_value = sample_alpaca_bars
                mock_get_client.return_value = mock_client

                # Import and use the routing function
                from tradingagents.dataflows.interface import route_to_vendor

                result = route_to_vendor(
                    'get_stock_data',
                    'AAPL',
                    '2025-01-10',
                    '2025-01-12'
                )

                payload = json.loads(result)
                assert payload["symbol"] == "AAPL"
                assert payload["meta"]["record_count"] == 3
                assert len(payload["records"]) == 3
                assert payload["records"][0]["close"] == 151.5

    def test_fallback_chain_alpaca_to_yfinance(self, mock_env):
        """Test fallback from Alpaca to yfinance when Alpaca fails."""
        from tradingagents.dataflows.alpaca.common import AlpacaRateLimitError

        # Mock configuration
        with patch("tradingagents.dataflows.interface.get_config") as mock_config:
            mock_config.return_value = {
                "data_vendors": {
                    "core_stock_apis": "alpaca"
                },
                "tool_vendors": {}
            }

            # Mock Alpaca to fail with rate limit
            with patch('tradingagents.dataflows.alpaca.data.get_client') as mock_alpaca_client:
                mock_alpaca_client.return_value._request.side_effect = AlpacaRateLimitError(
                    "Rate limit exceeded. Retry after 60 seconds."
                )

                # Mock yfinance to succeed
                with patch('tradingagents.dataflows.y_finance.yf.Ticker') as mock_ticker:
                    mock_data = pd.DataFrame({
                        'Open': [150.0, 151.5, 153.0],
                        'High': [152.0, 153.5, 154.0],
                        'Low': [149.5, 150.5, 152.0],
                        'Close': [151.5, 153.0, 153.5],
                        'Volume': [1000000, 1200000, 1100000],
                        'Adj Close': [151.5, 153.0, 153.5]
                    }, index=pd.DatetimeIndex(['2025-01-10', '2025-01-11', '2025-01-12']))

                    mock_ticker_instance = Mock()
                    mock_ticker_instance.history.return_value = mock_data
                    mock_ticker.return_value = mock_ticker_instance

                    from tradingagents.dataflows.interface import route_to_vendor

                    result = route_to_vendor(
                        'get_stock_data',
                        'AAPL',
                        '2025-01-10',
                        '2025-01-12'
                    )

                    payload = json.loads(result)
                    assert payload["symbol"] == "AAPL"
                    assert payload["source"] == "yfinance"
                    assert len(payload["records"]) == 3

    def test_multi_vendor_configuration(self, mock_env, sample_alpaca_bars):
        """Test using multiple vendors in configuration."""
        # Mock configuration with both vendors
        with patch("tradingagents.dataflows.interface.get_config") as mock_config:
            mock_config.return_value = {
                "data_vendors": {
                    "core_stock_apis": "alpaca,yfinance"
                },
                "tool_vendors": {}
            }

            # Mock Alpaca client
            with patch('tradingagents.dataflows.alpaca.data.get_client') as mock_get_client:
                mock_client = Mock()
                mock_client._request.return_value = sample_alpaca_bars
                mock_get_client.return_value = mock_client

                from tradingagents.dataflows.interface import route_to_vendor

                result = route_to_vendor(
                    'get_stock_data',
                    'AAPL',
                    '2025-01-10',
                    '2025-01-12'
                )

                payload = json.loads(result)
                assert payload["source"] == "alpaca"

    def test_alpaca_with_real_like_error_handling(self, mock_env):
        """Test realistic error scenarios."""
        with patch("tradingagents.dataflows.interface.get_config") as mock_config:
            mock_config.return_value = {
                "data_vendors": {
                    "core_stock_apis": "alpaca"
                },
                "tool_vendors": {}
            }

            # Scenario 1: Invalid symbol
            with patch('tradingagents.dataflows.alpaca.data.get_client') as mock_get_client:
                mock_client = Mock()
                mock_client._request.return_value = {'bars': []}
                mock_get_client.return_value = mock_client

                from tradingagents.dataflows.interface import route_to_vendor

                result = route_to_vendor(
                    'get_stock_data',
                    'INVALID_SYMBOL',
                    '2025-01-10',
                    '2025-01-12'
                )

                payload = json.loads(result)
                assert payload["records"] == []

    def test_alpaca_data_consistency_with_yfinance(self, mock_env):
        """Test that Alpaca returns data in the same format as yfinance."""
        sample_bars = {
            'bars': [
                {
                    't': '2025-01-10T05:00:00Z',
                    'o': 150.00,
                    'h': 152.00,
                    'l': 149.50,
                    'c': 151.50,
                    'v': 1000000,
                }
            ]
        }

        # Get data from Alpaca
        with patch('tradingagents.dataflows.alpaca.data.get_client') as mock_alpaca:
            mock_client = Mock()
            mock_client._request.return_value = sample_bars
            mock_alpaca.return_value = mock_client

            from tradingagents.dataflows.alpaca.data import get_stock_data as alpaca_get_stock
            alpaca_result = alpaca_get_stock('AAPL', '2025-01-10', '2025-01-10')

        # Get data from yfinance
        with patch('tradingagents.dataflows.y_finance.yf.Ticker') as mock_ticker:
            mock_data = pd.DataFrame({
                'Open': [150.0],
                'High': [152.0],
                'Low': [149.5],
                'Close': [151.5],
                'Volume': [1000000],
                'Adj Close': [151.5]
            }, index=pd.DatetimeIndex(['2025-01-10']))

            mock_ticker_instance = Mock()
            mock_ticker_instance.history.return_value = mock_data
            mock_ticker.return_value = mock_ticker_instance

            from tradingagents.dataflows.y_finance import get_YFin_data_online
            yfinance_result = get_YFin_data_online('AAPL', '2025-01-10', '2025-01-10')

        alpaca_payload = json.loads(alpaca_result)
        yfinance_payload = json.loads(yfinance_result)

        assert alpaca_payload["symbol"] == "AAPL"
        assert yfinance_payload["symbol"] == "AAPL"
        assert alpaca_payload["source"] == "alpaca"
        assert yfinance_payload["source"] == "yfinance"
        assert alpaca_payload["records"][0]["close"] == pytest.approx(
            yfinance_payload["records"][0]["close"]
        )

    def test_credentials_from_environment(self, mock_env):
        """Test that Alpaca correctly reads credentials from environment."""
        from tradingagents.dataflows.alpaca.common import get_alpaca_credentials

        api_key, secret_key = get_alpaca_credentials()
        assert api_key == "test_alpaca_key"
        assert secret_key == "test_alpaca_secret"

    def test_alpaca_client_singleton_pattern(self, mock_env):
        """Test that get_client returns the same instance (singleton)."""
        from tradingagents.dataflows.alpaca.common import get_client, _client_instance

        # Clear singleton
        import tradingagents.dataflows.alpaca.common as common_module
        common_module._client_instance = None

        client1 = get_client()
        client2 = get_client()

        # Should be same instance
        assert client1 is client2
