"""Broker interface for routing trading operations to configured broker.

This module provides a routing layer similar to tradingagents/dataflows/interface.py
but for broker trading operations instead of data fetching.
"""

from typing import Any


def _alpaca_module():
    from .alpaca import trading as alpaca_trading

    return alpaca_trading


def alpaca_place_order(*args, **kwargs):
    return _alpaca_module().place_order(*args, **kwargs)


def alpaca_get_positions(*args, **kwargs):
    return _alpaca_module().get_positions(*args, **kwargs)


def alpaca_get_account(*args, **kwargs):
    return _alpaca_module().get_account(*args, **kwargs)


def alpaca_cancel_order(*args, **kwargs):
    return _alpaca_module().cancel_order(*args, **kwargs)


def _get_method(action: str, broker: str):
    """Resolve broker method lazily so tests can patch at runtime."""
    if broker == "alpaca":
        mapping = {
            "place_order": alpaca_place_order,
            "get_positions": alpaca_get_positions,
            "get_account": alpaca_get_account,
            "cancel_order": alpaca_cancel_order,
        }
        return mapping.get(action)
    return None


def route_to_broker(action: str, *args, **kwargs) -> Any:
    """Route trading actions to configured broker.

    Args:
        action: Trading action to perform (e.g., "place_order", "get_positions")
        *args: Positional arguments to pass to broker method
        **kwargs: Keyword arguments to pass to broker method

    Returns:
        Result from broker-specific implementation

    Raises:
        ValueError: If action is unknown or broker doesn't support the action

    Example:
        >>> route_to_broker("place_order", "AAPL", 10, "buy")
        "Order placed: AAPL buy 10 @ market (ID: 12345)"
    """
    from tradingagents.dataflows.config import get_config

    config = get_config()
    broker = config.get("trading_broker", "alpaca")

    if action not in {"place_order", "get_positions", "get_account", "cancel_order"}:
        raise ValueError(f"Unknown broker action: {action}")

    method = _get_method(action, broker)
    if method is None:
        raise ValueError(
            f"Broker '{broker}' doesn't support action '{action}'."
        )

    return method(*args, **kwargs)
