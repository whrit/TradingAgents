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

    def test_build_trade_instruction_buy(self):
        graph = self._bare_graph()
        instruction = graph._build_trade_instruction("AAPL", "BUY")
        assert instruction["action"] == "buy"
        assert instruction["quantity"] == 1

    def test_build_trade_instruction_returns_none_for_hold(self):
        graph = self._bare_graph()
        assert graph._build_trade_instruction("AAPL", "HOLD") is None

    def test_execution_skipped_when_auto_execute_disabled(self):
        graph = self._bare_graph(auto_execute_trades=False)
        instruction = {"symbol": "AAPL", "quantity": 1, "action": "buy"}

        with patch("tradingagents.graph.trading_graph.route_to_broker") as mock_route:
            result = graph._maybe_execute_trade(instruction)

        assert result is None
        mock_route.assert_not_called()

    def test_buy_decision_routes_order_when_auto_enabled(self):
        graph = self._bare_graph(auto_execute_trades=True, default_trade_quantity=5)
        instruction = {
            "symbol": "AAPL",
            "quantity": 5,
            "action": "buy",
            "order_type": "market",
            "time_in_force": "day",
        }

        with patch("tradingagents.graph.trading_graph.route_to_broker") as mock_route:
            mock_route.return_value = "Order placed"
            result = graph._maybe_execute_trade(instruction)

        mock_route.assert_called_once_with(
            "place_order",
            "AAPL",
            5,
            "buy",
            order_type="market",
            time_in_force="day",
            limit_price=None,
        )
        assert result["result"] == "Order placed"
