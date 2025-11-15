"""Alpaca trading operations including order placement and position management.

This module provides functions for executing trades, managing positions, and
retrieving account information via the Alpaca API.
"""

from typing import Optional
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

from .client import get_trading_client


def place_order(
    symbol: str,
    qty: float,
    side: str,
    order_type: str = "market",
    limit_price: Optional[float] = None,
    **kwargs
) -> str:
    """Place an order via Alpaca.

    Args:
        symbol: Stock symbol (e.g., "AAPL")
        qty: Quantity to trade (supports fractional shares)
        side: Order side - "buy" or "sell"
        order_type: Order type - "market" or "limit"
        limit_price: Limit price for limit orders (required for limit orders)
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
    from tradingagents.dataflows.config import get_config

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

    # Create order request based on type
    if order_type == "market":
        order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=order_side,
            time_in_force=TimeInForce.DAY
        )
    elif order_type == "limit":
        if not limit_price:
            raise ValueError("limit_price required for limit orders")

        order_data = LimitOrderRequest(
            symbol=symbol,
            qty=qty,
            side=order_side,
            time_in_force=TimeInForce.DAY,
            limit_price=limit_price
        )
    else:
        raise ValueError(
            f"Unsupported order_type: {order_type}. "
            f"Supported types: market, limit"
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
    from tradingagents.dataflows.config import get_config

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
    from tradingagents.dataflows.config import get_config

    config = get_config()
    paper_mode = config.get("broker_mode", "paper") == "paper"
    client = get_trading_client(paper=paper_mode)

    account = client.get_account()

    return f"""Account Summary:
Cash: ${account.cash}
Equity: ${account.equity}
Buying Power: ${account.buying_power}
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
    from tradingagents.dataflows.config import get_config

    config = get_config()
    paper_mode = config.get("broker_mode", "paper") == "paper"
    client = get_trading_client(paper=paper_mode)

    client.cancel_order_by_id(order_id)
    return f"Order {order_id} cancelled"
