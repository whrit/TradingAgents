"""Alpaca trading operations including order placement and position management.

This module provides functions for executing trades, managing positions, and
retrieving account information via the Alpaca API.
"""

from typing import Optional
from alpaca.trading.requests import (
    LimitOrderRequest,
    MarketOrderRequest,
    OptionLegRequest,
    StopLimitOrderRequest,
    StopOrderRequest,
    StopLossRequest,
    TakeProfitRequest,
    TrailingStopOrderRequest,
)
from alpaca.trading.enums import OrderClass, OrderSide, TimeInForce

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
    asset_type: str = "equity",
    order_class: Optional[str] = None,
    take_profit: Optional[dict] = None,
    stop_loss_order: Optional[dict] = None,
    legs: Optional[list] = None,
    client_order_id: Optional[str] = None,
) -> str:
    """Place an order via Alpaca, supporting advanced order classes and options.

    Args:
        symbol: Symbol or option contract (ignored for multi-leg orders)
        qty: Quantity to trade (shares or option contracts)
        side: Order side - "buy" or "sell"
        order_type: market, limit, stop, stop_limit, trailing_stop
        limit_price: Limit price for limit/stop_limit orders
        stop_price: Trigger price for stop/stop_limit orders
        trail_price: Dollar trail for trailing stops
        trail_percent: Percent trail for trailing stops
        time_in_force: DAY, GTC, OPG, CLS, IOC, FOK
        asset_type: Informational label for downstream consumers
        order_class: Order class (simple, bracket, oco, oto, otoco, mleg)
        take_profit: Dict with take-profit parameters (limit_price)
        stop_loss_order: Dict with stop-loss parameters (stop_price / limit_price)
        legs: Optional list of leg definitions for multi-leg option orders
        client_order_id: Optional user-defined identifier

    Returns:
        str: Formatted order confirmation message

    Raises:
        ValueError: If invalid combinations or parameters are supplied
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

    order_side = OrderSide.BUY if side == "buy" else OrderSide.SELL

    tif = _parse_time_in_force(time_in_force)

    leg_requests = _build_option_legs(legs)
    order_class_enum = _parse_order_class(order_class, leg_requests)
    take_profit_req = _build_take_profit_request(take_profit)
    stop_loss_req = _build_stop_loss_request(stop_loss_order)

    base_kwargs = {
        "qty": qty,
        "time_in_force": tif,
    }
    if leg_requests:
        base_kwargs["legs"] = leg_requests
    else:
        base_kwargs.update({
            "symbol": symbol,
            "side": order_side,
        })

    if client_order_id:
        base_kwargs["client_order_id"] = client_order_id
    if order_class_enum:
        base_kwargs["order_class"] = order_class_enum
    if take_profit_req:
        base_kwargs["take_profit"] = take_profit_req
    if stop_loss_req:
        base_kwargs["stop_loss"] = stop_loss_req

    # Create order request based on type
    order_type = order_type.lower()
    if order_type == "market":
        order_data = MarketOrderRequest(
            **base_kwargs,
        )
    elif order_type == "limit":
        if limit_price is None:
            raise ValueError("limit_price required for limit orders")
        order_data = LimitOrderRequest(
            limit_price=limit_price,
            **base_kwargs,
        )
    elif order_type == "stop":
        if leg_requests:
            raise ValueError("Multi-leg orders support market or limit types only")
        if stop_price is None:
            raise ValueError("stop_price required for stop orders")
        order_data = StopOrderRequest(
            stop_price=stop_price,
            **base_kwargs,
        )
    elif order_type == "stop_limit":
        if leg_requests:
            raise ValueError("Multi-leg orders support market or limit types only")
        if stop_price is None or limit_price is None:
            raise ValueError("stop_limit orders require both stop_price and limit_price")
        order_data = StopLimitOrderRequest(
            limit_price=limit_price,
            stop_price=stop_price,
            **base_kwargs,
        )
    elif order_type == "trailing_stop":
        if leg_requests:
            raise ValueError("Trailing stops are not supported for multi-leg orders")
        if trail_price is None and trail_percent is None:
            raise ValueError("trailing_stop orders require trail_price or trail_percent")
        order_data = TrailingStopOrderRequest(
            trail_price=trail_price,
            trail_percent=trail_percent,
            **base_kwargs,
        )
    else:
        raise ValueError(
            f"Unsupported order_type: {order_type}. "
            f"Supported types: market, limit, stop, stop_limit, trailing_stop"
        )

    # Submit order to Alpaca
    order = client.submit_order(order_data)

    symbol_display = getattr(order, "symbol", None) or "multi-leg"
    side_display = getattr(order, "side", order_side).name if hasattr(order, "side") else side.upper()
    qty_display = getattr(order, "qty", qty)
    order_type_disp = getattr(order, "type", order_type)
    order_class_disp = getattr(order, "order_class", order_class_enum) or OrderClass.SIMPLE

    return (
        f"Order placed: {symbol_display} {side_display} {qty_display} @ {order_type_disp} "
        f"(Class: {order_class_disp.name}, Asset: {asset_type.upper()}, ID: {order.id})"
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


def _parse_order_class(value: Optional[str], legs=None) -> Optional[OrderClass]:
    if legs and not value:
        return OrderClass.MLEG
    if not value:
        return None
    key = value.upper()
    try:
        return OrderClass[key]
    except KeyError as exc:
        valid = ", ".join(OrderClass.__members__.keys())
        raise ValueError(f"Unsupported order_class '{value}'. Supported: {valid}") from exc


def _build_take_profit_request(data: Optional[dict]):
    if not data:
        return None
    limit = data.get("limit_price")
    if limit is None:
        raise ValueError("take_profit requires limit_price")
    return TakeProfitRequest(limit_price=float(limit))


def _build_stop_loss_request(data: Optional[dict]):
    if not data:
        return None
    stop_price = data.get("stop_price")
    if stop_price is None:
        raise ValueError("stop_loss requires stop_price")
    limit = data.get("limit_price")
    return StopLossRequest(stop_price=float(stop_price), limit_price=float(limit) if limit else None)


def _build_option_legs(legs: Optional[list]):
    if not legs:
        return None
    leg_requests = []
    for leg in legs:
        symbol = leg.get("symbol")
        if not symbol:
            raise ValueError("Each leg requires a symbol")
        side_value = leg.get("side", "buy").lower()
        if side_value not in {"buy", "sell"}:
            raise ValueError("Leg side must be 'buy' or 'sell'")
        ratio_qty = int(leg.get("ratio_qty", 1))
        ratio_qty = max(1, ratio_qty)
        leg_requests.append(
            OptionLegRequest(
                symbol=symbol,
                side=OrderSide.BUY if side_value == "buy" else OrderSide.SELL,
                ratio_qty=ratio_qty,
            )
        )
    return leg_requests


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
