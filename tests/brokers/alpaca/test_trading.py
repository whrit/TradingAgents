"""Tests for Alpaca trading operations."""

import pytest
from unittest.mock import patch, MagicMock


class TestAlpacaTrading:
    """Test Alpaca trading operations."""

    def test_place_order_market_buy(self):
        """Test placing a market buy order."""
        with patch('tradingagents.brokers.alpaca.trading.get_trading_client') as mock_get_client:
            with patch('tradingagents.brokers.alpaca.trading.get_config') as mock_config:
                mock_config.return_value = {"broker_mode": "paper"}

                # Mock client
                mock_client = MagicMock()
                mock_order = MagicMock()
                mock_order.id = "12345"
                mock_order.symbol = "AAPL"
                mock_order.side = "buy"
                mock_order.qty = 10
                mock_order.type = "market"
                mock_client.submit_order.return_value = mock_order
                mock_get_client.return_value = mock_client

                from tradingagents.brokers.alpaca.trading import place_order
                result = place_order("AAPL", 10, "buy", order_type="market")

                assert "Order placed" in result
                assert "AAPL" in result
                assert "buy" in result
                assert "12345" in result
                mock_client.submit_order.assert_called_once()

    @patch('tradingagents.brokers.alpaca.trading.get_trading_client')
    def test_place_order_limit_sell(self, mock_get_client):
        """Test placing a limit sell order."""
        from tradingagents.brokers.alpaca.trading import place_order

        mock_client = MagicMock()
        mock_order = MagicMock()
        mock_order.id = "67890"
        mock_order.symbol = "TSLA"
        mock_order.side = "sell"
        mock_order.qty = 5
        mock_order.type = "limit"
        mock_client.submit_order.return_value = mock_order
        mock_get_client.return_value = mock_client

        result = place_order("TSLA", 5, "sell", order_type="limit", limit_price=250.50)

        assert "Order placed" in result
        assert "TSLA" in result
        mock_client.submit_order.assert_called_once()

    @patch('tradingagents.brokers.alpaca.trading.get_trading_client')
    def test_place_order_stop_market(self, mock_get_client):
        """Test placing a stop market order."""
        from tradingagents.brokers.alpaca.trading import place_order, StopOrderRequest

        mock_client = MagicMock()
        mock_order = MagicMock()
        mock_order.id = "789"
        mock_order.symbol = "MSFT"
        mock_order.side = "sell"
        mock_order.qty = 3
        mock_order.type = "stop"
        mock_client.submit_order.return_value = mock_order
        mock_get_client.return_value = mock_client

        place_order("MSFT", 3, "sell", order_type="stop", stop_price=340.0)

        submitted = mock_client.submit_order.call_args[0][0]
        assert isinstance(submitted, StopOrderRequest)
        assert submitted.stop_price == 340.0

    @patch('tradingagents.brokers.alpaca.trading.get_trading_client')
    def test_place_order_stop_limit(self, mock_get_client):
        """Test placing a stop limit order."""
        from tradingagents.brokers.alpaca.trading import place_order, StopLimitOrderRequest

        mock_client = MagicMock()
        mock_order = MagicMock()
        mock_order.id = "111"
        mock_order.symbol = "AMZN"
        mock_order.side = "buy"
        mock_order.qty = 1
        mock_order.type = "stop_limit"
        mock_client.submit_order.return_value = mock_order
        mock_get_client.return_value = mock_client

        place_order(
            "AMZN",
            1,
            "buy",
            order_type="stop_limit",
            stop_price=3100.0,
            limit_price=3105.0,
        )

        submitted = mock_client.submit_order.call_args[0][0]
        assert isinstance(submitted, StopLimitOrderRequest)
        assert submitted.limit_price == 3105.0
        assert submitted.stop_price == 3100.0

    @patch('tradingagents.brokers.alpaca.trading.get_trading_client')
    def test_place_order_trailing_stop(self, mock_get_client):
        """Test placing a trailing stop order."""
        from tradingagents.brokers.alpaca.trading import place_order, TrailingStopOrderRequest

        mock_client = MagicMock()
        mock_order = MagicMock()
        mock_order.id = "555"
        mock_order.symbol = "NFLX"
        mock_order.side = "sell"
        mock_order.qty = 2
        mock_order.type = "trailing_stop"
        mock_client.submit_order.return_value = mock_order
        mock_get_client.return_value = mock_client

        place_order(
            "NFLX",
            2,
            "sell",
            order_type="trailing_stop",
            trail_percent=2.5,
        )

        submitted = mock_client.submit_order.call_args[0][0]
        assert isinstance(submitted, TrailingStopOrderRequest)
        assert submitted.trail_percent == 2.5

    @patch('tradingagents.brokers.alpaca.trading.get_trading_client')
    def test_time_in_force_conversion(self, mock_get_client):
        """Test time in force values are normalized."""
        from tradingagents.brokers.alpaca.trading import place_order, TimeInForce

        mock_client = MagicMock()
        mock_order = MagicMock()
        mock_order.id = "222"
        mock_order.symbol = "AAPL"
        mock_order.side = "buy"
        mock_order.qty = 1
        mock_order.type = "market"
        mock_client.submit_order.return_value = mock_order
        mock_get_client.return_value = mock_client

        place_order("AAPL", 1, "buy", order_type="market", time_in_force="gtc")

        submitted = mock_client.submit_order.call_args[0][0]
        assert submitted.time_in_force == TimeInForce.GTC

    @patch('tradingagents.brokers.alpaca.trading.get_trading_client')
    def test_place_order_invalid_side(self, mock_get_client):
        """Test that invalid order side raises ValueError."""
        from tradingagents.brokers.alpaca.trading import place_order

        with pytest.raises(ValueError, match="Invalid side"):
            place_order("AAPL", 10, "invalid_side")

    @patch('tradingagents.brokers.alpaca.trading.get_trading_client')
    def test_place_order_limit_without_price(self, mock_get_client):
        """Test that limit order without price raises ValueError."""
        from tradingagents.brokers.alpaca.trading import place_order

        with pytest.raises(ValueError, match="limit_price required"):
            place_order("AAPL", 10, "buy", order_type="limit")

    @patch('tradingagents.brokers.alpaca.trading.get_trading_client')
    def test_get_positions_with_positions(self, mock_get_client):
        """Test getting positions when positions exist."""
        from tradingagents.brokers.alpaca.trading import get_positions

        mock_client = MagicMock()
        mock_position = MagicMock()
        mock_position.symbol = "AAPL"
        mock_position.qty = 10
        mock_position.current_price = 150.50
        mock_position.unrealized_pl = 25.00
        mock_client.get_all_positions.return_value = [mock_position]
        mock_get_client.return_value = mock_client

        result = get_positions()

        assert "Current Positions" in result
        assert "AAPL" in result
        assert "10" in result

    @patch('tradingagents.brokers.alpaca.trading.get_trading_client')
    def test_get_positions_no_positions(self, mock_get_client):
        """Test getting positions when no positions exist."""
        from tradingagents.brokers.alpaca.trading import get_positions

        mock_client = MagicMock()
        mock_client.get_all_positions.return_value = []
        mock_get_client.return_value = mock_client

        result = get_positions()

        assert "No open positions" in result

    @patch('tradingagents.brokers.alpaca.trading.get_trading_client')
    def test_get_account(self, mock_get_client):
        """Test getting account information."""
        from tradingagents.brokers.alpaca.trading import get_account

        mock_client = MagicMock()
        mock_account = MagicMock()
        mock_account.cash = 10000.00
        mock_account.equity = 15000.00
        mock_account.buying_power = 20000.00
        mock_account.status = "ACTIVE"
        mock_client.get_account.return_value = mock_account
        mock_get_client.return_value = mock_client

        result = get_account()

        assert "Account Summary" in result
        assert "10,000.00" in result
        assert "15,000.00" in result
        assert "ACTIVE" in result

    @patch('tradingagents.brokers.alpaca.trading.get_trading_client')
    def test_cancel_order(self, mock_get_client):
        """Test canceling an order."""
        from tradingagents.brokers.alpaca.trading import cancel_order

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = cancel_order("12345")

        assert "Order 12345 cancelled" in result
        mock_client.cancel_order_by_id.assert_called_once_with("12345")

    @patch('tradingagents.brokers.alpaca.trading.get_trading_client')
    def test_place_order_uses_broker_mode_config(self, mock_get_client):
        """Test that place_order respects broker_mode configuration."""
        from tradingagents.brokers.alpaca.trading import place_order

        with patch('tradingagents.dataflows.config.get_config') as mock_config:
            mock_config.return_value = {"broker_mode": "paper"}

            mock_client = MagicMock()
            mock_order = MagicMock()
            mock_order.id = "123"
            mock_order.symbol = "AAPL"
            mock_order.side = "buy"
            mock_order.qty = 10
            mock_order.type = "market"
            mock_client.submit_order.return_value = mock_order
            mock_get_client.return_value = mock_client

            place_order("AAPL", 10, "buy")

            # Verify paper mode was used
            mock_get_client.assert_called_with(paper=True)

    @patch('tradingagents.brokers.alpaca.trading.get_trading_client')
    def test_place_order_fractional_shares(self, mock_get_client):
        """Test placing order with fractional shares."""
        from tradingagents.brokers.alpaca.trading import place_order

        mock_client = MagicMock()
        mock_order = MagicMock()
        mock_order.id = "456"
        mock_order.symbol = "AAPL"
        mock_order.side = "buy"
        mock_order.qty = 2.5
        mock_order.type = "market"
        mock_client.submit_order.return_value = mock_order
        mock_get_client.return_value = mock_client

        result = place_order("AAPL", 2.5, "buy")

        assert "Order placed" in result
        assert "2.5" in result
