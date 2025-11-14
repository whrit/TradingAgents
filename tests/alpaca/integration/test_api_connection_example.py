"""
Integration tests for Alpaca API connection and authentication.

These tests make real API calls to Alpaca paper trading environment.
Requires ALPACA_PAPER_KEY and ALPACA_PAPER_SECRET environment variables.
"""

import pytest
import os
from tests.alpaca.utils import assert_account_valid, assert_no_trading_blocks


@pytest.mark.integration
class TestAPIConnection:
    """Test real API connection to Alpaca."""

    def test_connect_to_paper_trading(self, paper_trading_client):
        """Should successfully connect to paper trading API."""
        account = paper_trading_client.get_account()

        assert account is not None
        assert_account_valid(account)

    def test_account_is_paper_trading(self, paper_trading_client):
        """Should verify account is in paper trading mode."""
        account = paper_trading_client.get_account()

        # Paper trading accounts have specific account numbers
        assert account.account_number.startswith("PA")

    def test_account_has_no_blocks(self, paper_trading_client):
        """Should verify account has no trading restrictions."""
        account = paper_trading_client.get_account()

        assert_no_trading_blocks(account)

    def test_invalid_credentials_rejected(self):
        """Should reject invalid API credentials."""
        try:
            from alpaca.trading.client import TradingClient

            # Attempt connection with invalid credentials
            client = TradingClient(
                api_key="INVALID_KEY",
                secret_key="INVALID_SECRET",
                paper=True
            )

            # This should raise an authentication error
            with pytest.raises(Exception):
                client.get_account()

        except ImportError:
            pytest.skip("alpaca-py not installed")


@pytest.mark.integration
class TestRateLimiting:
    """Test API rate limiting behavior."""

    def test_respect_rate_limits(self, paper_trading_client):
        """Should handle rate limits gracefully."""
        # Make multiple rapid requests
        for i in range(10):
            account = paper_trading_client.get_account()
            assert account is not None

        # Should not hit rate limit with reasonable request rate

    def test_rate_limit_error_handling(self):
        """Should handle rate limit errors appropriately."""
        # This would require intentionally triggering rate limits
        # which is not ideal for regular test runs
        pytest.skip("Rate limit testing requires special setup")


@pytest.mark.integration
class TestAPIEndpoints:
    """Test various API endpoints are accessible."""

    def test_account_endpoint(self, paper_trading_client):
        """Should access account endpoint successfully."""
        account = paper_trading_client.get_account()

        assert hasattr(account, 'id')
        assert hasattr(account, 'buying_power')
        assert hasattr(account, 'cash')

    def test_positions_endpoint(self, paper_trading_client):
        """Should access positions endpoint successfully."""
        positions = paper_trading_client.get_all_positions()

        # Should return a list (may be empty for new account)
        assert isinstance(positions, list)

    def test_orders_endpoint(self, paper_trading_client):
        """Should access orders endpoint successfully."""
        orders = paper_trading_client.get_orders()

        # Should return a list (may be empty)
        assert isinstance(orders, list)


@pytest.mark.integration
@pytest.mark.slow
class TestConnectionStability:
    """Test connection stability and error recovery."""

    def test_connection_persists(self, paper_trading_client):
        """Should maintain connection across multiple requests."""
        # Make several requests to verify connection stability
        for i in range(5):
            account = paper_trading_client.get_account()
            assert account is not None

    def test_reconnect_after_error(self, paper_trading_client):
        """Should reconnect after transient errors."""
        # This would require simulating network errors
        # which is difficult in integration tests
        pytest.skip("Error recovery testing requires special setup")


# Template for additional integration tests:
#
# @pytest.mark.integration
# class TestMarketDataAPI:
#     """Test market data API endpoints."""
#
#     def test_get_latest_bars(self, paper_stock_client):
#         """Should retrieve latest bars for a symbol."""
#         from alpaca.data.requests import StockBarsRequest
#         from alpaca.data.timeframe import TimeFrame
#         from datetime import datetime, timedelta
#
#         request = StockBarsRequest(
#             symbol_or_symbols="AAPL",
#             timeframe=TimeFrame.Day,
#             start=datetime.now() - timedelta(days=5)
#         )
#
#         bars = paper_stock_client.get_stock_bars(request)
#         assert bars is not None
#
#     def test_get_latest_quotes(self, paper_stock_client):
#         """Should retrieve latest quotes for a symbol."""
#         from alpaca.data.requests import StockLatestQuoteRequest
#
#         request = StockLatestQuoteRequest(symbol_or_symbols="AAPL")
#         quote = paper_stock_client.get_stock_latest_quote(request)
#
#         assert quote is not None
#         assert "AAPL" in quote
