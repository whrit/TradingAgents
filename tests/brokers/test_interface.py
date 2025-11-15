"""Tests for broker interface routing."""

import pytest
from unittest.mock import patch, MagicMock


class TestBrokerInterface:
    """Test broker interface routing logic."""

    def test_route_to_broker_place_order_alpaca(self):
        """Test routing place_order to Alpaca."""
        from tradingagents.brokers.interface import route_to_broker

        with patch('tradingagents.brokers.interface.alpaca_place_order') as mock_order:
            mock_order.return_value = "Order placed: AAPL buy 10 @ market (ID: 12345)"

            result = route_to_broker("place_order", "AAPL", 10, "buy")

            assert "Order placed" in result
            assert "AAPL" in result
            mock_order.assert_called_once_with("AAPL", 10, "buy")

    def test_route_to_broker_get_positions_alpaca(self):
        """Test routing get_positions to Alpaca."""
        from tradingagents.brokers.interface import route_to_broker

        with patch('tradingagents.brokers.interface.alpaca_get_positions') as mock_positions:
            mock_positions.return_value = "Current Positions:\n- AAPL: 10 shares @ $150"

            result = route_to_broker("get_positions")

            assert "Current Positions" in result
            mock_positions.assert_called_once()

    def test_route_to_broker_get_account_alpaca(self):
        """Test routing get_account to Alpaca."""
        from tradingagents.brokers.interface import route_to_broker

        with patch('tradingagents.brokers.interface.alpaca_get_account') as mock_account:
            mock_account.return_value = "Account Summary:\nCash: $10000"

            result = route_to_broker("get_account")

            assert "Account Summary" in result
            mock_account.assert_called_once()

    def test_route_to_broker_cancel_order_alpaca(self):
        """Test routing cancel_order to Alpaca."""
        from tradingagents.brokers.interface import route_to_broker

        with patch('tradingagents.brokers.interface.alpaca_cancel_order') as mock_cancel:
            mock_cancel.return_value = "Order 12345 cancelled"

            result = route_to_broker("cancel_order", "12345")

            assert "cancelled" in result
            mock_cancel.assert_called_once_with("12345")

    def test_route_to_broker_unknown_action(self):
        """Test that unknown action raises ValueError."""
        from tradingagents.brokers.interface import route_to_broker

        with pytest.raises(ValueError, match="Unknown broker action"):
            route_to_broker("unknown_action")

    def test_route_to_broker_uses_config(self):
        """Test that routing uses configuration."""
        from tradingagents.brokers.interface import route_to_broker

        with patch('tradingagents.dataflows.config.get_config') as mock_config:
            mock_config.return_value = {"trading_broker": "alpaca"}

            with patch('tradingagents.brokers.interface.alpaca_place_order') as mock_order:
                mock_order.return_value = "Order placed"

                route_to_broker("place_order", "AAPL", 10, "buy")

                mock_config.assert_called()
