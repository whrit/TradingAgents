"""Alpaca trading operations including order placement and position management.

This module provides functions for executing trades, managing positions, and
retrieving account information via the Alpaca API.
"""

from typing import Optional
from alpaca.trading.requests import (
    LimitOrderRequest,
    MarketOrderRequest,
    StopLimitOrderRequest,
    StopOrderRequest,
    TrailingStopOrderRequest,
)
from alpaca.trading.enums import OrderSide, TimeInForce

from tradingagents.dataflows.config import get_config

from .client import get_trading_client


def place_order(
    symbol: str,
    qty: float,
    side: str,
    order_type: str = "market",
    limit_price: Optional[float] = None,
    stop_price: Optional[float] = None,
    trail_price: Optional[float] = None,
    trail_percent: Optional[float] = None,
    time_in_force: str = "day",
    **kwargs
) -> str:
    """Place an order via Alpaca.

    Args:
        symbol: Stock symbol (e.g., "AAPL")
        qty: Quantity to trade (supports fractional shares)
        side: Order side - "buy" or "sell"
        order_type: Order type - market, limit, stop, stop_limit, trailing_stop
        limit_price: Limit price for limit and stop_limit orders
        stop_price: Stop trigger price for stop or stop_limit orders
        trail_price: Trailing stop price (dollar based)
        trail_percent: Trailing stop percentage
        time_in_force: Time in force (DAY, GTC, OPG, CLS, IOC, FOK)
        **kwargs: Additional order parameters (currently unused, for future expansion)

    Returns:
        str: Formatted order confirmation message

    Raises:
        ValueError: If side is invalid, order_type is unsupported, or
                   limit_price is missing for limit orders

    Example:
        >>> # Market buy order
        >>> place_order("AAPL", 10, "buy")
        "Order placed: AAPL buy 10 @ market (ID: abc123)"

        >>> # Limit sell order
        >>> place_order("TSLA", 5, "sell", order_type="limit", limit_price=250.50)
        "Order placed: TSLA sell 5 @ limit (ID: def456)"
    """
    config = get_config()

    # Determine paper/live mode from configuration
    paper_mode = config.get("broker_mode", "paper") == "paper"
    client = get_trading_client(paper=paper_mode)

    # Validate order side
    if side not in ["buy", "sell"]:
        raise ValueError(
            f"Invalid side: {side}. Must be 'buy' or 'sell'"
        )

    # Convert side to Alpaca enum
    order_side = OrderSide.BUY if side == "buy" else OrderSide.SELL

    tif = _parse_time_in_force(time_in_force)

    # Create order request based on type
    order_type = order_type.lower()
    if order_type == "market":
        order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=order_side,
            time_in_force=tif
        )
    elif order_type == "limit":
        if limit_price is None:
            raise ValueError("limit_price required for limit orders")

        order_data = LimitOrderRequest(
            symbol=symbol,
            qty=qty,
            side=order_side,
            time_in_force=tif,
            limit_price=limit_price
        )
    elif order_type == "stop":
        if stop_price is None:
            raise ValueError("stop_price required for stop orders")

        order_data = StopOrderRequest(
            symbol=symbol,
            qty=qty,
            side=order_side,
            stop_price=stop_price,
            time_in_force=tif,
        )
    elif order_type == "stop_limit":
        if stop_price is None or limit_price is None:
            raise ValueError("stop_limit orders require both stop_price and limit_price")

        order_data = StopLimitOrderRequest(
            symbol=symbol,
            qty=qty,
            side=order_side,
            limit_price=limit_price,
            stop_price=stop_price,
            time_in_force=tif,
        )
    elif order_type == "trailing_stop":
        if trail_price is None and trail_percent is None:
            raise ValueError("trailing_stop orders require trail_price or trail_percent")

        order_data = TrailingStopOrderRequest(
            symbol=symbol,
            qty=qty,
            side=order_side,
            time_in_force=tif,
            trail_price=trail_price,
            trail_percent=trail_percent,
        )
    else:
        raise ValueError(
            f"Unsupported order_type: {order_type}. "
            f"Supported types: market, limit, stop, stop_limit, trailing_stop"
        )

    # Submit order to Alpaca
    order = client.submit_order(order_data)

    # Return formatted confirmation
    return (
        f"Order placed: {order.symbol} {order.side} {order.qty} @ {order.type} "
        f"(ID: {order.id})"
    )


def get_positions() -> str:
    """Get all current positions.

    Returns:
        str: Formatted string with position details including symbol, quantity,
             current price, and unrealized P&L

    Example:
        >>> get_positions()
        "Current Positions:
        - AAPL: 10 shares @ $150.50 (P&L: $25.00)
        - TSLA: 5 shares @ $240.00 (P&L: -$12.50)"

        >>> # When no positions
        >>> get_positions()
        "No open positions"
    """
    config = get_config()
    paper_mode = config.get("broker_mode", "paper") == "paper"
    client = get_trading_client(paper=paper_mode)

    positions = client.get_all_positions()

    if not positions:
        return "No open positions"

    result = "Current Positions:\n"
    for pos in positions:
        result += (
            f"- {pos.symbol}: {pos.qty} shares @ "
            f"${pos.current_price} (P&L: ${pos.unrealized_pl})\n"
        )

    return result


def get_account() -> str:
    """Get account information including balance, equity, and buying power.

    Returns:
        str: Formatted string with account summary

    Example:
        >>> get_account()
        "Account Summary:
        Cash: $10000.00
        Equity: $15000.00
        Buying Power: $20000.00
        Status: ACTIVE"
    """
    config = get_config()
    paper_mode = config.get("broker_mode", "paper") == "paper"
    client = get_trading_client(paper=paper_mode)

    account = client.get_account()

    def _format_money(value):
        return f"{float(value):,.2f}"

    return f"""Account Summary:
Cash: ${_format_money(account.cash)}
Equity: ${_format_money(account.equity)}
Buying Power: ${_format_money(account.buying_power)}
Status: {account.status}
"""


def cancel_order(order_id: str) -> str:
    """Cancel an order by ID.

    Args:
        order_id: Alpaca order ID to cancel

    Returns:
        str: Cancellation confirmation message

    Example:
        >>> cancel_order("abc123")
        "Order abc123 cancelled"
    """
    config = get_config()
    paper_mode = config.get("broker_mode", "paper") == "paper"
    client = get_trading_client(paper=paper_mode)

    client.cancel_order_by_id(order_id)
    return f"Order {order_id} cancelled"


def _parse_time_in_force(value: Optional[str]) -> TimeInForce:
    """Normalize time-in-force strings to Alpaca enums."""
    mapping = {
        "DAY": TimeInForce.DAY,
        "GTC": TimeInForce.GTC,
        "OPG": TimeInForce.OPG,
        "CLS": TimeInForce.CLS,
        "IOC": TimeInForce.IOC,
        "FOK": TimeInForce.FOK,
    }
    key = (value or "day").upper()
    if key not in mapping:
        raise ValueError(
            f"Unsupported time_in_force '{value}'. "
            f"Supported: {', '.join(mapping.keys())}"
        )
    return mapping[key]
