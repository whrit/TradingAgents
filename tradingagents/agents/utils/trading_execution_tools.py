"""Trading execution tools for agent-driven trade execution.

These tools allow LangChain agents to execute trades, check positions,
and manage accounts via the configured broker.
"""

from langchain_core.tools import tool
from typing import Annotated

from tradingagents.brokers.interface import route_to_broker


@tool
def execute_trade(
    symbol: Annotated[str, "Stock symbol (e.g., AAPL)"],
    quantity: Annotated[float, "Number of shares to trade (supports fractional shares)"],
    action: Annotated[str, "Trade action: 'buy' or 'sell'"],
    order_type: Annotated[str, "Order type: market, limit, stop, stop_limit, trailing_stop"] = "market",
    limit_price: Annotated[float, "Limit price for limit/stop_limit orders (optional)"] = None,
    stop_price: Annotated[float, "Stop price for stop/stop_limit orders (optional)"] = None,
    trail_price: Annotated[float, "Trailing stop dollar offset (optional)"] = None,
    trail_percent: Annotated[float, "Trailing stop percent offset (optional)"] = None,
    time_in_force: Annotated[str, "Time in force (day, gtc, opg, cls, ioc, fok)"] = "day",
) -> str:
    """Execute a trade via configured broker.

    This tool allows agents to place buy/sell orders for stocks. By default,
    it uses paper trading mode unless explicitly configured otherwise.

    Args:
        symbol: Stock symbol (e.g., "AAPL", "TSLA")
        quantity: Number of shares to trade (fractional shares supported)
        action: "buy" or "sell"
        order_type: "market" for immediate execution or "limit" for price-limited orders
        limit_price: Required for limit/stop_limit orders - the max buy or min sell price
        stop_price: Required for stop or stop_limit orders - trigger price
        trail_price: Optional trailing stop offset in dollars
        trail_percent: Optional trailing stop offset in percent
        time_in_force: Order time-in-force, defaults to DAY

    Returns:
        str: Order confirmation message with order ID

    Example:
        >>> # Market buy order
        >>> execute_trade("AAPL", 10, "buy")
        "Order placed: AAPL buy 10 @ market (ID: abc123)"

        >>> # Limit sell order
        >>> execute_trade("TSLA", 5, "sell", order_type="limit", limit_price=250.50)
        "Order placed: TSLA sell 5 @ limit (ID: def456)"
    """
    return route_to_broker(
        "place_order",
        symbol,
        quantity,
        action,
        order_type,
        limit_price=limit_price,
        stop_price=stop_price,
        trail_price=trail_price,
        trail_percent=trail_percent,
        time_in_force=time_in_force,
    )


@tool
def get_portfolio_positions() -> str:
    """Get current portfolio positions with profit/loss information.

    Returns all open positions including symbol, quantity, current price,
    and unrealized P&L.

    Returns:
        str: Formatted string with position details

    Example:
        >>> get_portfolio_positions()
        "Current Positions:
        - AAPL: 10 shares @ $150.50 (P&L: $25.00)
        - TSLA: 5 shares @ $240.00 (P&L: -$12.50)"
    """
    return route_to_broker("get_positions")


@tool
def get_account_balance() -> str:
    """Get account balance, equity, and buying power.

    Returns current account information including available cash,
    total equity, and buying power.

    Returns:
        str: Formatted string with account summary

    Example:
        >>> get_account_balance()
        "Account Summary:
        Cash: $10000.00
        Equity: $15000.00
        Buying Power: $20000.00
        Status: ACTIVE"
    """
    return route_to_broker("get_account")


# Export all tools for easy import
__all__ = [
    "execute_trade",
    "get_portfolio_positions",
    "get_account_balance",
]
