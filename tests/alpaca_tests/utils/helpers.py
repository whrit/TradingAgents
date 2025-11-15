"""
Test helper functions for Alpaca integration tests.

Provides utilities for common testing operations like waiting for order fills,
generating test data, and calculating expected values.
"""

import time
import random
import string
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta


def generate_test_symbol(prefix: str = "TEST") -> str:
    """
    Generate a random test stock symbol.

    Args:
        prefix: Prefix for the symbol

    Returns:
        Random test symbol (e.g., "TEST_ABCD")
    """
    suffix = ''.join(random.choices(string.ascii_uppercase, k=4))
    return f"{prefix}_{suffix}"


def wait_for_order_fill(
    client: Any,
    order_id: str,
    timeout: int = 30,
    poll_interval: float = 0.5
) -> Dict[str, Any]:
    """
    Wait for an order to be filled.

    Args:
        client: Alpaca client instance
        order_id: Order ID to monitor
        timeout: Maximum time to wait in seconds
        poll_interval: Time between status checks in seconds

    Returns:
        Filled order object

    Raises:
        TimeoutError: If order not filled within timeout
        ValueError: If order is canceled or rejected
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        order = client.get_order(order_id)

        if order.status == "filled":
            return order

        if order.status in ["canceled", "rejected", "expired"]:
            raise ValueError(f"Order {order_id} ended with status: {order.status}")

        time.sleep(poll_interval)

    raise TimeoutError(f"Order {order_id} not filled within {timeout} seconds")


def wait_for_condition(
    condition: Callable[[], bool],
    timeout: int = 30,
    poll_interval: float = 0.5,
    error_message: str = "Condition not met within timeout"
) -> None:
    """
    Wait for a condition to become true.

    Args:
        condition: Callable that returns True when condition is met
        timeout: Maximum time to wait in seconds
        poll_interval: Time between checks in seconds
        error_message: Error message if timeout occurs

    Raises:
        TimeoutError: If condition not met within timeout
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        if condition():
            return
        time.sleep(poll_interval)

    raise TimeoutError(error_message)


def calculate_expected_pnl(
    qty: float,
    entry_price: float,
    exit_price: float,
    side: str = "long"
) -> float:
    """
    Calculate expected profit/loss for a position.

    Args:
        qty: Position quantity
        entry_price: Entry price
        exit_price: Exit price
        side: Position side ("long" or "short")

    Returns:
        Expected P&L
    """
    if side == "long":
        return qty * (exit_price - entry_price)
    elif side == "short":
        return qty * (entry_price - exit_price)
    else:
        raise ValueError(f"Invalid side: {side}")


def calculate_expected_market_value(
    qty: float,
    current_price: float
) -> float:
    """
    Calculate expected market value for a position.

    Args:
        qty: Position quantity
        current_price: Current market price

    Returns:
        Expected market value
    """
    return abs(qty) * current_price


def calculate_expected_cost_basis(
    qty: float,
    avg_entry_price: float
) -> float:
    """
    Calculate expected cost basis for a position.

    Args:
        qty: Position quantity
        avg_entry_price: Average entry price

    Returns:
        Expected cost basis
    """
    return abs(qty) * avg_entry_price


def generate_test_bars(
    symbol: str,
    count: int = 100,
    start_time: Optional[datetime] = None,
    interval_minutes: int = 1,
    base_price: float = 150.0,
    volatility: float = 0.02
) -> list:
    """
    Generate realistic test bar data.

    Args:
        symbol: Stock symbol
        count: Number of bars to generate
        start_time: Starting timestamp (defaults to now - count*interval)
        interval_minutes: Minutes between bars
        base_price: Starting price
        volatility: Price volatility factor (0-1)

    Returns:
        List of bar dictionaries
    """
    if start_time is None:
        start_time = datetime.now() - timedelta(minutes=count * interval_minutes)

    bars = []
    current_price = base_price
    current_time = start_time

    for i in range(count):
        # Simulate price movement with random walk
        price_change = random.gauss(0, volatility) * current_price

        open_price = current_price
        close_price = current_price + price_change

        # Generate realistic high/low
        high_price = max(open_price, close_price) + random.random() * volatility * current_price
        low_price = min(open_price, close_price) - random.random() * volatility * current_price

        # Generate realistic volume
        base_volume = 100000
        volume = int(base_volume * (1 + random.gauss(0, 0.5)))
        volume = max(volume, 1000)  # Minimum volume

        bar = {
            "t": current_time.isoformat() + "Z",
            "S": symbol,
            "o": round(open_price, 2),
            "h": round(high_price, 2),
            "l": round(low_price, 2),
            "c": round(close_price, 2),
            "v": volume,
            "n": random.randint(50, 500),  # Number of trades
            "vw": round((open_price + close_price) / 2, 2),  # VWAP approximation
        }

        bars.append(bar)
        current_price = close_price
        current_time += timedelta(minutes=interval_minutes)

    return bars


def is_market_open(dt: Optional[datetime] = None) -> bool:
    """
    Check if the market is currently open.

    Args:
        dt: Datetime to check (defaults to now)

    Returns:
        True if market is open

    Note:
        This is a simplified check. For production, use Alpaca's calendar API.
    """
    if dt is None:
        dt = datetime.now()

    # Check if weekend
    if dt.weekday() >= 5:  # Saturday or Sunday
        return False

    # Check market hours (9:30 AM - 4:00 PM ET)
    # Note: This doesn't handle holidays or early closes
    market_open = dt.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = dt.replace(hour=16, minute=0, second=0, microsecond=0)

    return market_open <= dt <= market_close


def create_test_account_data(
    buying_power: float = 100000.0,
    **overrides
) -> Dict[str, Any]:
    """
    Create test account data with sensible defaults.

    Args:
        buying_power: Account buying power
        **overrides: Override any default values

    Returns:
        Account data dictionary
    """
    account = {
        "id": "test-account-id",
        "account_number": "PA123456789",
        "status": "ACTIVE",
        "currency": "USD",
        "buying_power": str(buying_power),
        "cash": str(buying_power),
        "portfolio_value": str(buying_power),
        "pattern_day_trader": False,
        "trading_blocked": False,
        "transfers_blocked": False,
        "account_blocked": False,
        "created_at": datetime.now().isoformat(),
    }

    account.update(overrides)
    return account


def create_test_order_data(
    symbol: str = "AAPL",
    qty: float = 10,
    side: str = "buy",
    **overrides
) -> Dict[str, Any]:
    """
    Create test order data with sensible defaults.

    Args:
        symbol: Stock symbol
        qty: Order quantity
        side: Order side
        **overrides: Override any default values

    Returns:
        Order data dictionary
    """
    order = {
        "id": f"test-order-{random.randint(1000, 9999)}",
        "symbol": symbol,
        "qty": str(qty),
        "side": side,
        "type": "market",
        "time_in_force": "day",
        "status": "accepted",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "submitted_at": datetime.now().isoformat(),
        "filled_qty": "0",
    }

    order.update(overrides)
    return order


def create_test_position_data(
    symbol: str = "AAPL",
    qty: float = 10,
    avg_entry_price: float = 150.0,
    **overrides
) -> Dict[str, Any]:
    """
    Create test position data with calculated values.

    Args:
        symbol: Stock symbol
        qty: Position quantity
        avg_entry_price: Average entry price
        **overrides: Override any calculated values

    Returns:
        Position data dictionary
    """
    current_price = avg_entry_price * 1.05  # 5% gain by default
    market_value = abs(qty) * current_price
    cost_basis = abs(qty) * avg_entry_price
    unrealized_pl = market_value - cost_basis

    position = {
        "symbol": symbol,
        "qty": str(qty),
        "avg_entry_price": str(avg_entry_price),
        "current_price": str(current_price),
        "market_value": str(market_value),
        "cost_basis": str(cost_basis),
        "unrealized_pl": str(unrealized_pl),
        "unrealized_plpc": str(unrealized_pl / cost_basis),
        "side": "long" if qty > 0 else "short",
    }

    position.update(overrides)
    return position
