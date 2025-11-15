"""Broker interface for routing trading operations to configured broker.

This module provides a routing layer similar to tradingagents/dataflows/interface.py
but for broker trading operations instead of data fetching.
"""

from typing import Any


# Import broker-specific implementations
from .alpaca.trading import (
    place_order as alpaca_place_order,
    get_positions as alpaca_get_positions,
    get_account as alpaca_get_account,
    cancel_order as alpaca_cancel_order,
)


# Mapping of trading actions to broker-specific implementations
BROKER_METHODS = {
    "place_order": {
        "alpaca": alpaca_place_order,
    },
    "get_positions": {
        "alpaca": alpaca_get_positions,
    },
    "get_account": {
        "alpaca": alpaca_get_account,
    },
    "cancel_order": {
        "alpaca": alpaca_cancel_order,
    },
}


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

    if action not in BROKER_METHODS:
        raise ValueError(f"Unknown broker action: {action}")

    if broker not in BROKER_METHODS[action]:
        raise ValueError(
            f"Broker '{broker}' doesn't support action '{action}'. "
            f"Available brokers for {action}: {list(BROKER_METHODS[action].keys())}"
        )

    return BROKER_METHODS[action][broker](*args, **kwargs)
