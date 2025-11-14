"""
Mock Alpaca API client and helper functions for unit testing.

Provides mock implementations of Alpaca API responses without requiring
actual API calls, enabling fast and reliable unit tests.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from unittest.mock import MagicMock
import uuid


class MockAlpacaClient:
    """
    Mock Alpaca API client for unit testing.

    Simulates Alpaca API responses without making actual HTTP requests.
    Tracks all method calls for assertion in tests.
    """

    def __init__(self, responses: Optional[Dict[str, Any]] = None):
        """
        Initialize mock client with optional custom responses.

        Args:
            responses: Dictionary mapping method names to return values
        """
        self.responses = responses or {}
        self.calls: List[tuple] = []
        self._orders: Dict[str, Dict] = {}
        self._positions: Dict[str, Dict] = {}
        self._account = self._create_default_account()

    def _create_default_account(self) -> Dict[str, Any]:
        """Create default account data."""
        return {
            "id": "test-account-id",
            "account_number": "PA123456789",
            "status": "ACTIVE",
            "currency": "USD",
            "buying_power": "100000.00",
            "cash": "100000.00",
            "portfolio_value": "100000.00",
            "pattern_day_trader": False,
            "trading_blocked": False,
            "transfers_blocked": False,
            "account_blocked": False,
        }

    def get_account(self) -> Dict[str, Any]:
        """Get account information."""
        self.calls.append(("get_account", {}))
        return self.responses.get("get_account", self._account)

    def submit_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        type: str = "market",
        time_in_force: str = "day",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Submit a new order."""
        order_id = str(uuid.uuid4())
        order = {
            "id": order_id,
            "client_order_id": f"test-{order_id}",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "submitted_at": datetime.now().isoformat(),
            "filled_at": None,
            "symbol": symbol,
            "qty": str(qty),
            "filled_qty": "0",
            "type": type,
            "side": side,
            "time_in_force": time_in_force,
            "limit_price": str(limit_price) if limit_price else None,
            "stop_price": str(stop_price) if stop_price else None,
            "status": "accepted",
        }

        self._orders[order_id] = order
        self.calls.append(("submit_order", {
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "type": type,
            **kwargs
        }))

        return self.responses.get("submit_order", order)

    def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get order by ID."""
        self.calls.append(("get_order", {"order_id": order_id}))
        order = self._orders.get(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        return self.responses.get("get_order", order)

    def get_orders(self, status: str = "all", **kwargs) -> List[Dict[str, Any]]:
        """Get list of orders."""
        self.calls.append(("get_orders", {"status": status, **kwargs}))

        if status == "all":
            orders = list(self._orders.values())
        else:
            orders = [o for o in self._orders.values() if o["status"] == status]

        return self.responses.get("get_orders", orders)

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order."""
        self.calls.append(("cancel_order", {"order_id": order_id}))

        if order_id in self._orders:
            self._orders[order_id]["status"] = "canceled"
            self._orders[order_id]["canceled_at"] = datetime.now().isoformat()
            return self._orders[order_id]

        raise ValueError(f"Order {order_id} not found")

    def replace_order(
        self,
        order_id: str,
        qty: Optional[float] = None,
        limit_price: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Replace an existing order."""
        self.calls.append(("replace_order", {
            "order_id": order_id,
            "qty": qty,
            "limit_price": limit_price,
            **kwargs
        }))

        if order_id not in self._orders:
            raise ValueError(f"Order {order_id} not found")

        order = self._orders[order_id].copy()
        if qty is not None:
            order["qty"] = str(qty)
        if limit_price is not None:
            order["limit_price"] = str(limit_price)
        order["updated_at"] = datetime.now().isoformat()

        self._orders[order_id] = order
        return order

    def get_position(self, symbol: str) -> Dict[str, Any]:
        """Get position by symbol."""
        self.calls.append(("get_position", {"symbol": symbol}))

        position = self._positions.get(symbol)
        if not position:
            raise ValueError(f"Position {symbol} not found")

        return self.responses.get("get_position", position)

    def get_all_positions(self) -> List[Dict[str, Any]]:
        """Get all positions."""
        self.calls.append(("get_all_positions", {}))
        return self.responses.get("get_all_positions", list(self._positions.values()))

    def close_position(self, symbol: str) -> Dict[str, Any]:
        """Close a position."""
        self.calls.append(("close_position", {"symbol": symbol}))

        if symbol in self._positions:
            del self._positions[symbol]

        return self.responses.get("close_position", {"status": "filled"})

    def get_bars(
        self,
        symbol: str,
        timeframe: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 100,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Get historical bar data."""
        self.calls.append(("get_bars", {
            "symbol": symbol,
            "timeframe": timeframe,
            "start": start,
            "end": end,
            "limit": limit,
            **kwargs
        }))

        return self.responses.get("get_bars", create_mock_bars(symbol, limit))


def create_mock_bars(
    symbol: str,
    count: int = 100,
    timeframe: str = "1Min",
    base_price: float = 150.0,
) -> List[Dict[str, Any]]:
    """
    Create mock bar data for testing.

    Args:
        symbol: Stock symbol
        count: Number of bars to create
        timeframe: Timeframe (1Min, 5Min, 1H, 1D, etc.)
        base_price: Starting price

    Returns:
        List of bar dictionaries
    """
    bars = []
    current_time = datetime.now()
    current_price = base_price

    for i in range(count):
        # Simple random walk for price
        price_change = (hash(f"{symbol}{i}") % 100 - 50) / 100.0
        current_price += price_change

        open_price = current_price
        high_price = current_price + abs(price_change)
        low_price = current_price - abs(price_change)
        close_price = current_price + (hash(f"{symbol}{i}x") % 100 - 50) / 100.0

        bar = {
            "t": (current_time - timedelta(minutes=count-i)).isoformat(),
            "o": round(open_price, 2),
            "h": round(high_price, 2),
            "l": round(low_price, 2),
            "c": round(close_price, 2),
            "v": (hash(f"{symbol}{i}v") % 1000000) + 100000,
            "n": (hash(f"{symbol}{i}n") % 1000) + 100,
            "vw": round((open_price + close_price) / 2, 2),
        }
        bars.append(bar)
        current_price = close_price

    return bars


def create_mock_order(
    symbol: str = "AAPL",
    qty: float = 10,
    side: str = "buy",
    type: str = "market",
    status: str = "filled",
    **kwargs
) -> Dict[str, Any]:
    """
    Create a mock order for testing.

    Args:
        symbol: Stock symbol
        qty: Order quantity
        side: Order side (buy/sell)
        type: Order type (market/limit/stop/stop_limit)
        status: Order status
        **kwargs: Additional order fields

    Returns:
        Mock order dictionary
    """
    order_id = str(uuid.uuid4())
    now = datetime.now()

    order = {
        "id": order_id,
        "client_order_id": f"test-{order_id}",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "submitted_at": now.isoformat(),
        "filled_at": now.isoformat() if status == "filled" else None,
        "symbol": symbol,
        "qty": str(qty),
        "filled_qty": str(qty) if status == "filled" else "0",
        "type": type,
        "side": side,
        "time_in_force": "day",
        "status": status,
    }

    order.update(kwargs)
    return order


def create_mock_position(
    symbol: str = "AAPL",
    qty: float = 10,
    avg_entry_price: float = 150.0,
    current_price: float = 155.0,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a mock position for testing.

    Args:
        symbol: Stock symbol
        qty: Position quantity
        avg_entry_price: Average entry price
        current_price: Current market price
        **kwargs: Additional position fields

    Returns:
        Mock position dictionary
    """
    market_value = qty * current_price
    cost_basis = qty * avg_entry_price
    unrealized_pl = market_value - cost_basis
    unrealized_plpc = (unrealized_pl / cost_basis) if cost_basis > 0 else 0

    position = {
        "symbol": symbol,
        "qty": str(qty),
        "avg_entry_price": str(avg_entry_price),
        "current_price": str(current_price),
        "market_value": str(market_value),
        "cost_basis": str(cost_basis),
        "unrealized_pl": str(unrealized_pl),
        "unrealized_plpc": str(unrealized_plpc),
        "unrealized_intraday_pl": str(unrealized_pl * 0.1),
        "unrealized_intraday_plpc": str(unrealized_plpc * 0.1),
        "side": "long" if qty > 0 else "short",
    }

    position.update(kwargs)
    return position


def create_mock_account(
    buying_power: float = 100000.0,
    cash: float = 100000.0,
    portfolio_value: float = 100000.0,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a mock account for testing.

    Args:
        buying_power: Available buying power
        cash: Cash balance
        portfolio_value: Total portfolio value
        **kwargs: Additional account fields

    Returns:
        Mock account dictionary
    """
    account = {
        "id": str(uuid.uuid4()),
        "account_number": f"PA{uuid.uuid4().hex[:9].upper()}",
        "status": "ACTIVE",
        "currency": "USD",
        "buying_power": str(buying_power),
        "cash": str(cash),
        "portfolio_value": str(portfolio_value),
        "pattern_day_trader": False,
        "trading_blocked": False,
        "transfers_blocked": False,
        "account_blocked": False,
        "created_at": datetime.now().isoformat(),
    }

    account.update(kwargs)
    return account
