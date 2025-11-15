"""Tests for broker execution hook inside TradingAgentsGraph."""

from unittest.mock import patch, MagicMock

import pytest

from tradingagents.graph.trading_graph import TradingAgentsGraph


class TestTradingGraphExecutionHook:
    """Verify orders are triggered only once final decisions are approved."""

    def _bare_graph(self, **overrides):
        graph = TradingAgentsGraph.__new__(TradingAgentsGraph)
        base_config = {
            "auto_execute_trades": False,
            "default_trade_quantity": 1,
            "default_order_type": "market",
            "default_time_in_force": "day",
            "trading_broker": "alpaca",
        }
        base_config.update(overrides)
        graph.config = base_config
        graph.last_execution_result = None
        return graph

    def test_execution_skipped_when_auto_execute_disabled(self):
        graph = self._bare_graph(auto_execute_trades=False)

        with patch("tradingagents.graph.trading_graph.route_to_broker") as mock_route:
            result = graph._maybe_execute_trade("AAPL", "BUY")

        assert result is None
        mock_route.assert_not_called()

    def test_buy_decision_routes_order_when_auto_enabled(self):
        graph = self._bare_graph(auto_execute_trades=True, default_trade_quantity=5)

        with patch("tradingagents.graph.trading_graph.route_to_broker") as mock_route:
            mock_route.return_value = "Order placed"
            result = graph._maybe_execute_trade("AAPL", "BUY")

        mock_route.assert_called_once_with(
            "place_order",
            "AAPL",
            5,
            "buy",
            order_type="market",
            time_in_force="day",
        )
        assert result["result"] == "Order placed"
        assert result["decision"] == "BUY"

    def test_non_action_decisions_do_not_route(self):
        graph = self._bare_graph(auto_execute_trades=True)

        with patch("tradingagents.graph.trading_graph.route_to_broker") as mock_route:
            graph._maybe_execute_trade("AAPL", "HOLD")

        mock_route.assert_not_called()
