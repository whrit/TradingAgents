"""Tests for TradingAgents trading execution LangChain tools."""

from unittest.mock import patch

import pytest

from tradingagents.agents.utils.trading_execution_tools import (
    execute_trade,
    get_portfolio_positions,
    get_account_balance,
)


class TestExecuteTradeTool:
    """Validate execute_trade metadata and routing."""

    def test_metadata_exposes_langchain_schema(self):
        assert execute_trade.name == "execute_trade"
        assert "symbol" in execute_trade.args
        assert execute_trade.description

    def test_execute_trade_routes_market_orders(self):
        with patch(
            "tradingagents.agents.utils.trading_execution_tools.route_to_broker",
            create=True,
        ) as mock_route:
            mock_route.return_value = "Order placed"
            payload = {
                "symbol": "AAPL",
                "quantity": 2,
                "action": "buy",
                "order_type": "market",
            }

            result = execute_trade.invoke(payload)

        assert result == "Order placed"
        mock_route.assert_called_once_with(
            "place_order",
            "AAPL",
            2,
            "buy",
            "market",
            limit_price=None,
            stop_price=None,
            trail_price=None,
            trail_percent=None,
            time_in_force="day",
        )

    def test_execute_trade_passes_limit_price(self):
        with patch(
            "tradingagents.agents.utils.trading_execution_tools.route_to_broker",
            create=True,
        ) as mock_route:
            payload = {
                "symbol": "TSLA",
                "quantity": 5,
                "action": "sell",
                "order_type": "limit",
                "limit_price": 250.5,
            }
            execute_trade.invoke(payload)

        mock_route.assert_called_once_with(
            "place_order",
            "TSLA",
            5,
            "sell",
            "limit",
            limit_price=250.5,
            stop_price=None,
            trail_price=None,
            trail_percent=None,
            time_in_force="day",
        )


class TestPortfolioTools:
    """Ensure read-only portfolio/account tools call the broker interface."""

    def test_get_portfolio_positions_routes(self):
        with patch(
            "tradingagents.agents.utils.trading_execution_tools.route_to_broker",
            create=True,
        ) as mock_route:
            mock_route.return_value = "positions"
            result = get_portfolio_positions.invoke({})

        assert result == "positions"
        mock_route.assert_called_once_with("get_positions")

    def test_get_account_balance_routes(self):
        with patch(
            "tradingagents.agents.utils.trading_execution_tools.route_to_broker",
            create=True,
        ) as mock_route:
            mock_route.return_value = "account"
            result = get_account_balance.invoke({})

        assert result == "account"
        mock_route.assert_called_once_with("get_account")


pytestmark = [
    pytest.mark.agents,
    pytest.mark.tools,
    pytest.mark.unit,
]
