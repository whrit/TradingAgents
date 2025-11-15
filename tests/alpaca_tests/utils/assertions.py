"""
Custom assertions for Alpaca integration tests.

Provides domain-specific assertion helpers for validating Alpaca API
responses and data structures.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


def assert_valid_order(order: Dict[str, Any], expected_symbol: Optional[str] = None):
    """
    Assert that an order object has all required fields and valid values.

    Args:
        order: Order dictionary to validate
        expected_symbol: Optional expected symbol to match

    Raises:
        AssertionError: If order is invalid
    """
    # Required fields
    required_fields = [
        "id", "symbol", "qty", "side", "type", "status",
        "created_at", "updated_at", "submitted_at"
    ]

    for field in required_fields:
        assert field in order, f"Order missing required field: {field}"
        assert order[field] is not None, f"Order field {field} is None"

    # Validate symbol
    if expected_symbol:
        assert order["symbol"] == expected_symbol, \
            f"Expected symbol {expected_symbol}, got {order['symbol']}"

    # Validate side
    assert order["side"] in ["buy", "sell"], \
        f"Invalid order side: {order['side']}"

    # Validate type
    valid_types = ["market", "limit", "stop", "stop_limit", "trailing_stop"]
    assert order["type"] in valid_types, \
        f"Invalid order type: {order['type']}"

    # Validate status
    valid_statuses = [
        "accepted", "pending_new", "accepted_for_bidding",
        "new", "partially_filled", "filled",
        "done_for_day", "canceled", "expired",
        "replaced", "pending_cancel", "pending_replace",
        "rejected", "suspended", "calculated"
    ]
    assert order["status"] in valid_statuses, \
        f"Invalid order status: {order['status']}"

    # Validate quantities
    qty = float(order["qty"])
    assert qty > 0, "Order quantity must be positive"

    if "filled_qty" in order:
        filled_qty = float(order["filled_qty"])
        assert filled_qty >= 0, "Filled quantity cannot be negative"
        assert filled_qty <= qty, "Filled quantity cannot exceed total quantity"

    # Validate timestamps
    try:
        datetime.fromisoformat(order["created_at"].replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        raise AssertionError(f"Invalid created_at timestamp: {order['created_at']}")


def assert_valid_position(
    position: Dict[str, Any],
    expected_symbol: Optional[str] = None
):
    """
    Assert that a position object has all required fields and valid values.

    Args:
        position: Position dictionary to validate
        expected_symbol: Optional expected symbol to match

    Raises:
        AssertionError: If position is invalid
    """
    # Required fields
    required_fields = [
        "symbol", "qty", "avg_entry_price", "current_price",
        "market_value", "cost_basis", "unrealized_pl", "side"
    ]

    for field in required_fields:
        assert field in position, f"Position missing required field: {field}"
        assert position[field] is not None, f"Position field {field} is None"

    # Validate symbol
    if expected_symbol:
        assert position["symbol"] == expected_symbol, \
            f"Expected symbol {expected_symbol}, got {position['symbol']}"

    # Validate side
    assert position["side"] in ["long", "short"], \
        f"Invalid position side: {position['side']}"

    # Validate quantities and prices
    qty = float(position["qty"])
    avg_entry_price = float(position["avg_entry_price"])
    current_price = float(position["current_price"])
    market_value = float(position["market_value"])
    cost_basis = float(position["cost_basis"])

    assert qty != 0, "Position quantity cannot be zero"
    assert avg_entry_price > 0, "Average entry price must be positive"
    assert current_price > 0, "Current price must be positive"

    # Validate calculations (with small tolerance for rounding)
    expected_market_value = abs(qty) * current_price
    assert abs(market_value - expected_market_value) < 0.01, \
        f"Market value mismatch: expected {expected_market_value}, got {market_value}"

    expected_cost_basis = abs(qty) * avg_entry_price
    assert abs(cost_basis - expected_cost_basis) < 0.01, \
        f"Cost basis mismatch: expected {expected_cost_basis}, got {cost_basis}"


def assert_valid_bars(
    bars: List[Dict[str, Any]],
    expected_symbol: Optional[str] = None,
    min_count: int = 1
):
    """
    Assert that bar data has all required fields and valid values.

    Args:
        bars: List of bar dictionaries to validate
        expected_symbol: Optional expected symbol (if bars include symbol)
        min_count: Minimum expected number of bars

    Raises:
        AssertionError: If bars are invalid
    """
    assert len(bars) >= min_count, \
        f"Expected at least {min_count} bars, got {len(bars)}"

    for i, bar in enumerate(bars):
        # Required fields
        required_fields = ["t", "o", "h", "l", "c", "v"]

        for field in required_fields:
            assert field in bar, \
                f"Bar {i} missing required field: {field}"
            assert bar[field] is not None, \
                f"Bar {i} field {field} is None"

        # Validate symbol if present
        if "S" in bar and expected_symbol:
            assert bar["S"] == expected_symbol, \
                f"Bar {i}: expected symbol {expected_symbol}, got {bar['S']}"

        # Validate OHLC relationships
        open_price = float(bar["o"])
        high_price = float(bar["h"])
        low_price = float(bar["l"])
        close_price = float(bar["c"])
        volume = int(bar["v"])

        assert high_price >= open_price, \
            f"Bar {i}: high ({high_price}) < open ({open_price})"
        assert high_price >= close_price, \
            f"Bar {i}: high ({high_price}) < close ({close_price})"
        assert low_price <= open_price, \
            f"Bar {i}: low ({low_price}) > open ({open_price})"
        assert low_price <= close_price, \
            f"Bar {i}: low ({low_price}) > close ({close_price})"
        assert high_price >= low_price, \
            f"Bar {i}: high ({high_price}) < low ({low_price})"
        assert volume >= 0, \
            f"Bar {i}: volume ({volume}) is negative"

        # Validate timestamp
        try:
            datetime.fromisoformat(bar["t"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            raise AssertionError(f"Bar {i}: invalid timestamp {bar['t']}")


def assert_price_in_range(
    price: float,
    min_price: float,
    max_price: float,
    field_name: str = "price"
):
    """
    Assert that a price is within an expected range.

    Args:
        price: Price to validate
        min_price: Minimum expected price
        max_price: Maximum expected price
        field_name: Name of the price field (for error messages)

    Raises:
        AssertionError: If price is out of range
    """
    assert isinstance(price, (int, float)), \
        f"{field_name} must be numeric, got {type(price)}"

    assert price >= min_price, \
        f"{field_name} ({price}) below minimum ({min_price})"

    assert price <= max_price, \
        f"{field_name} ({price}) above maximum ({max_price})"


def assert_account_valid(account: Dict[str, Any]):
    """
    Assert that an account object has all required fields and valid values.

    Args:
        account: Account dictionary to validate

    Raises:
        AssertionError: If account is invalid
    """
    # Required fields
    required_fields = [
        "id", "account_number", "status", "currency",
        "buying_power", "cash", "portfolio_value"
    ]

    for field in required_fields:
        assert field in account, f"Account missing required field: {field}"
        assert account[field] is not None, f"Account field {field} is None"

    # Validate status
    valid_statuses = ["ACTIVE", "ACCOUNT_CLOSED", "ACCOUNT_UPDATED"]
    assert account["status"] in valid_statuses, \
        f"Invalid account status: {account['status']}"

    # Validate currency
    assert account["currency"] == "USD", \
        f"Expected USD currency, got {account['currency']}"

    # Validate monetary values
    buying_power = float(account["buying_power"])
    cash = float(account["cash"])
    portfolio_value = float(account["portfolio_value"])

    assert buying_power >= 0, "Buying power cannot be negative"
    assert cash >= 0, "Cash cannot be negative"
    assert portfolio_value >= 0, "Portfolio value cannot be negative"


def assert_order_filled(order: Dict[str, Any]):
    """
    Assert that an order is filled.

    Args:
        order: Order dictionary to validate

    Raises:
        AssertionError: If order is not filled
    """
    assert order["status"] == "filled", \
        f"Expected filled order, got status: {order['status']}"

    assert order["filled_at"] is not None, \
        "Filled order must have filled_at timestamp"

    filled_qty = float(order["filled_qty"])
    total_qty = float(order["qty"])

    assert filled_qty == total_qty, \
        f"Expected filled_qty ({filled_qty}) to equal qty ({total_qty})"


def assert_no_trading_blocks(account: Dict[str, Any]):
    """
    Assert that an account has no trading blocks.

    Args:
        account: Account dictionary to validate

    Raises:
        AssertionError: If account has trading blocks
    """
    assert not account.get("trading_blocked", False), \
        "Account has trading_blocked flag set"

    assert not account.get("transfers_blocked", False), \
        "Account has transfers_blocked flag set"

    assert not account.get("account_blocked", False), \
        "Account has account_blocked flag set"
