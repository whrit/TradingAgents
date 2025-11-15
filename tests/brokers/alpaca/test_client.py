"""Tests for Alpaca broker client."""

import pytest
from unittest.mock import patch, MagicMock


class TestAlpacaClient:
    """Test Alpaca trading client initialization and configuration."""

    def test_get_trading_client_paper_mode(self):
        """Test getting paper trading client."""
        # Must patch where it's used, not where it's defined
        with patch('tradingagents.brokers.alpaca.client.TradingClient') as mock_trading_client:
            with patch('tradingagents.brokers.alpaca.client.get_config') as mock_config:
                mock_config.return_value = {
                    "alpaca_paper_api_key": "test_paper_key",
                    "alpaca_paper_secret_key": "test_paper_secret"
                }

                from tradingagents.brokers.alpaca.client import get_trading_client
                client = get_trading_client(paper=True)

                mock_trading_client.assert_called_once_with(
                    "test_paper_key",
                    "test_paper_secret",
                    paper=True
                )

    def test_get_trading_client_live_mode_requires_flag(self):
        """Test that live trading requires auto_execute_trades flag."""
        with patch('tradingagents.brokers.alpaca.client.get_config') as mock_config:
            mock_config.return_value = {
                "auto_execute_trades": False,
                "alpaca_live_api_key": "test_live_key",
                "alpaca_live_secret_key": "test_live_secret"
            }

            from tradingagents.brokers.alpaca.client import get_trading_client
            with pytest.raises(ValueError, match="Live trading requires auto_execute_trades=True"):
                get_trading_client(paper=False)

    def test_get_trading_client_live_mode_with_flag(self):
        """Test getting live trading client with proper flag."""
        with patch('tradingagents.brokers.alpaca.client.TradingClient') as mock_trading_client:
            with patch('tradingagents.brokers.alpaca.client.get_config') as mock_config:
                mock_config.return_value = {
                    "auto_execute_trades": True,
                    "alpaca_live_api_key": "test_live_key",
                    "alpaca_live_secret_key": "test_live_secret"
                }

                from tradingagents.brokers.alpaca.client import get_trading_client
                client = get_trading_client(paper=False)

                mock_trading_client.assert_called_once_with(
                    "test_live_key",
                    "test_live_secret",
                    paper=False
                )

    def test_get_trading_client_defaults_to_paper(self):
        """Test that client defaults to paper trading mode."""
        with patch('tradingagents.brokers.alpaca.client.TradingClient') as mock_trading_client:
            with patch('tradingagents.brokers.alpaca.client.get_config') as mock_config:
                mock_config.return_value = {
                    "alpaca_paper_api_key": "test_paper_key",
                    "alpaca_paper_secret_key": "test_paper_secret"
                }

                from tradingagents.brokers.alpaca.client import get_trading_client
                client = get_trading_client()

                mock_trading_client.assert_called_once()
                # Verify paper=True was passed
                call_args = mock_trading_client.call_args
                assert call_args[1]['paper'] == True
