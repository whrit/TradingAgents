"""
Integration tests for Alpaca vendor routing through interface.py.

Tests that Alpaca is properly integrated with the data vendor routing system.
"""

import json
import pytest
from unittest.mock import Mock, patch
from tradingagents.dataflows.interface import route_to_vendor, get_vendor, VENDOR_METHODS
from tradingagents.dataflows.alpaca.common import AlpacaRateLimitError, AlpacaAPIError


class TestAlpacaRouting:
    """Test Alpaca integration with vendor routing system."""

    @pytest.fixture
    def mock_credentials(self, monkeypatch):
        """Mock environment credentials."""
        monkeypatch.setenv("ALPACA_API_KEY", "test_key")
        monkeypatch.setenv("ALPACA_SECRET_KEY", "test_secret")

    @pytest.fixture
    def mock_config(self, monkeypatch):
        """Mock configuration to use Alpaca as primary vendor."""
        def mock_get_config():
            return {
                "data_vendors": {
                    "core_stock_apis": "alpaca"
                },
                "tool_vendors": {}
            }
        monkeypatch.setattr("tradingagents.dataflows.interface.get_config", mock_get_config)

    def test_alpaca_in_vendor_methods(self):
        """Test that Alpaca is registered in VENDOR_METHODS."""
        assert "get_stock_data" in VENDOR_METHODS
        assert "alpaca" in VENDOR_METHODS["get_stock_data"]

        # Verify the function is callable
        alpaca_func = VENDOR_METHODS["get_stock_data"]["alpaca"]
        assert callable(alpaca_func)

    def test_route_to_alpaca_success(self, mock_credentials, mock_config):
        """Test successful routing to Alpaca vendor."""
        mock_response = {
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

        with patch('tradingagents.dataflows.alpaca.data.get_client') as mock_get_client:
            mock_client = Mock()
            mock_client._request.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = route_to_vendor(
                'get_stock_data',
                'AAPL',
                '2025-01-10',
                '2025-01-10'
            )

            payload = json.loads(result)
            assert payload["symbol"] == "AAPL"
            assert payload["source"] == "alpaca"

    def test_route_fallback_from_alpaca_to_yfinance(self, mock_credentials):
        """Test fallback from Alpaca to yfinance on rate limit."""
        # Mock config to prefer alpaca with fallback
        def mock_get_config():
            return {
                "data_vendors": {
                    "core_stock_apis": "alpaca"
                },
                "tool_vendors": {}
            }

        with patch("tradingagents.dataflows.interface.get_config", mock_get_config):
            # Mock Alpaca to raise rate limit error
            with patch('tradingagents.dataflows.alpaca.data.get_client') as mock_alpaca_client:
                mock_alpaca_client.return_value._request.side_effect = AlpacaRateLimitError(
                    "Rate limit exceeded"
                )

                # Mock yfinance to succeed
                with patch('tradingagents.dataflows.y_finance.yf.Ticker') as mock_ticker:
                    import pandas as pd
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

                    result = route_to_vendor(
                        'get_stock_data',
                        'AAPL',
                        '2025-01-10',
                        '2025-01-10'
                    )

                    payload = json.loads(result)
                    assert payload["source"] == "yfinance"
                    assert len(payload["records"]) == 1

    def test_alpaca_handles_empty_data(self, mock_credentials, mock_config):
        """Test Alpaca handles empty data responses gracefully."""
        with patch('tradingagents.dataflows.alpaca.data.get_client') as mock_get_client:
            mock_client = Mock()
            mock_client._request.return_value = {'bars': []}
            mock_get_client.return_value = mock_client

            result = route_to_vendor(
                'get_stock_data',
                'INVALID',
                '2025-01-10',
                '2025-01-10'
            )

            payload = json.loads(result)
            assert payload["records"] == []

    def test_alpaca_authentication_error(self, mock_credentials, mock_config):
        """Test Alpaca handles authentication errors."""
        from tradingagents.dataflows.alpaca.common import AlpacaAuthenticationError

        with patch('tradingagents.dataflows.alpaca.data.get_client') as mock_get_client:
            mock_client = Mock()
            mock_client._request.side_effect = AlpacaAuthenticationError("Invalid credentials")
            mock_get_client.return_value = mock_client

            # Should handle error gracefully and not crash
            result = route_to_vendor(
                'get_stock_data',
                'AAPL',
                '2025-01-10',
                '2025-01-10'
            )

            payload = json.loads(result)
            assert payload.get("meta", {}).get("error")

    def test_get_vendor_config_for_alpaca(self):
        """Test that vendor configuration recognizes Alpaca."""
        with patch("tradingagents.dataflows.interface.get_config") as mock_config:
            mock_config.return_value = {
                "data_vendors": {
                    "core_stock_apis": "alpaca"
                },
                "tool_vendors": {}
            }

            vendor = get_vendor("core_stock_apis")
            assert vendor == "alpaca"

    def test_multiple_vendors_including_alpaca(self):
        """Test comma-separated vendor configuration with Alpaca."""
        with patch("tradingagents.dataflows.interface.get_config") as mock_config:
            mock_config.return_value = {
                "data_vendors": {
                    "core_stock_apis": "alpaca,yfinance"
                },
                "tool_vendors": {}
            }

            vendor = get_vendor("core_stock_apis")
            assert "alpaca" in vendor
            assert "yfinance" in vendor


class TestAlpacaDataFormats:
    """Test that Alpaca returns data in the expected formats."""

    @pytest.fixture
    def mock_credentials(self, monkeypatch):
        """Mock environment credentials."""
        monkeypatch.setenv("ALPACA_API_KEY", "test_key")
        monkeypatch.setenv("ALPACA_SECRET_KEY", "test_secret")

    def test_get_stock_data_json_format(self, mock_credentials):
        """Test that get_stock_data returns properly formatted JSON payload."""
        mock_response = {
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

        with patch('tradingagents.dataflows.alpaca.data.get_client') as mock_get_client:
            mock_client = Mock()
            mock_client._request.return_value = mock_response
            mock_get_client.return_value = mock_client

            from tradingagents.dataflows.alpaca.data import get_stock_data
            result = get_stock_data('AAPL', '2025-01-10', '2025-01-10')

            payload = json.loads(result)
            assert payload["symbol"] == "AAPL"
            assert payload["source"] == "alpaca"
            assert payload["meta"]["record_count"] == 1
            assert len(payload["records"]) == 1
            record = payload["records"][0]
            assert record["close"] == 151.5
            assert record["volume"] == 1000000

    def test_get_latest_quote_dict_format(self, mock_credentials):
        """Test that get_latest_quote returns proper dict format."""
        mock_response = {
            'quote': {
                'bp': 150.00,
                'ap': 150.10,
                'bs': 100,
                'as': 200,
                't': '2025-01-14T10:00:00Z'
            }
        }

        with patch('tradingagents.dataflows.alpaca.data.get_client') as mock_get_client:
            mock_client = Mock()
            mock_client._request.return_value = mock_response
            mock_get_client.return_value = mock_client

            from tradingagents.dataflows.alpaca.data import get_latest_quote
            result = get_latest_quote('AAPL')

            assert isinstance(result, dict)
            assert 'symbol' in result
            assert 'bid' in result
            assert 'ask' in result
            assert result['symbol'] == 'AAPL'
            assert result['bid'] == 150.00
            assert result['ask'] == 150.10
