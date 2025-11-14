"""
Alpaca Trading Module

Provides order placement, position management, and portfolio tracking capabilities.
"""

import logging
from typing import Optional, Dict, Any, List, Union
from decimal import Decimal

from .client import AlpacaClient
from .config import AlpacaConfig


logger = logging.getLogger(__name__)


class TradingError(Exception):
    """Base exception for trading operations."""
    pass


class OrderValidationError(TradingError):
    """Raised when order validation fails."""
    pass


class AlpacaTradingClient:
    """
    Client for Alpaca trading operations.

    Provides order placement, position management, and portfolio tracking.

    Attributes:
        client: Base AlpacaClient instance
        config: AlpacaConfig instance
    """

    # Valid order types
    VALID_ORDER_TYPES = ['market', 'limit', 'stop', 'stop_limit', 'trailing_stop']

    # Valid order sides
    VALID_SIDES = ['buy', 'sell']

    # Valid time in force options
    VALID_TIME_IN_FORCE = ['day', 'gtc', 'ioc', 'fok']

    def __init__(self, config: AlpacaConfig):
        """
        Initialize trading client.

        Args:
            config: AlpacaConfig instance
        """
        self.config = config
        self.client = AlpacaClient(config)
        logger.info(
            f"Initialized Alpaca trading client "
            f"(paper_trading={config.is_paper_trading})"
        )

    def _validate_quantity(self, qty: Union[int, float]) -> bool:
        """
        Validate order quantity.

        Args:
            qty: Order quantity

        Returns:
            bool: True if valid

        Raises:
            OrderValidationError: If quantity is invalid
        """
        if qty <= 0:
            raise OrderValidationError("Quantity must be positive")
        return True

    def _validate_side(self, side: str) -> bool:
        """
        Validate order side.

        Args:
            side: Order side (buy/sell)

        Returns:
            bool: True if valid

        Raises:
            OrderValidationError: If side is invalid
        """
        if side.lower() not in self.VALID_SIDES:
            raise OrderValidationError(
                f"Invalid side '{side}'. Valid options: {', '.join(self.VALID_SIDES)}"
            )
        return True

    def _validate_order_type(self, order_type: str) -> bool:
        """
        Validate order type.

        Args:
            order_type: Order type

        Returns:
            bool: True if valid

        Raises:
            OrderValidationError: If order type is invalid
        """
        if order_type.lower() not in self.VALID_ORDER_TYPES:
            raise OrderValidationError(
                f"Invalid order type '{order_type}'. "
                f"Valid options: {', '.join(self.VALID_ORDER_TYPES)}"
            )
        return True

    def submit_order(
        self,
        symbol: str,
        qty: Union[int, float],
        side: str,
        order_type: str = 'market',
        time_in_force: str = 'day',
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        trail_price: Optional[float] = None,
        trail_percent: Optional[float] = None,
        extended_hours: bool = False
    ) -> Dict[str, Any]:
        """
        Submit an order.

        Args:
            symbol: Stock symbol
            qty: Order quantity (supports fractional shares)
            side: Order side ('buy' or 'sell')
            order_type: Order type ('market', 'limit', 'stop', etc.)
            time_in_force: Time in force ('day', 'gtc', 'ioc', 'fok')
            limit_price: Limit price (required for limit orders)
            stop_price: Stop price (required for stop orders)
            trail_price: Trail price for trailing stop orders
            trail_percent: Trail percent for trailing stop orders
            extended_hours: Allow extended hours trading

        Returns:
            dict: Order confirmation data

        Raises:
            OrderValidationError: If order parameters are invalid
        """
        # Validate parameters
        self._validate_quantity(qty)
        self._validate_side(side)
        self._validate_order_type(order_type)

        # Check required parameters for specific order types
        if order_type == 'limit' and limit_price is None:
            raise OrderValidationError("limit_price is required for limit orders")
        if order_type == 'stop' and stop_price is None:
            raise OrderValidationError("stop_price is required for stop orders")
        if order_type == 'stop_limit' and (limit_price is None or stop_price is None):
            raise OrderValidationError("limit_price and stop_price are required for stop_limit orders")

        # Build order data
        order_data = {
            'symbol': symbol,
            'qty': str(qty),
            'side': side.lower(),
            'type': order_type.lower(),
            'time_in_force': time_in_force.lower()
        }

        if limit_price is not None:
            order_data['limit_price'] = str(limit_price)
        if stop_price is not None:
            order_data['stop_price'] = str(stop_price)
        if trail_price is not None:
            order_data['trail_price'] = str(trail_price)
        if trail_percent is not None:
            order_data['trail_percent'] = str(trail_percent)
        if extended_hours:
            order_data['extended_hours'] = True

        logger.info(f"Submitting {side} order for {qty} shares of {symbol}")
        return self.client._request('POST', '/v2/orders', data=order_data)

    def get_orders(
        self,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        after: Optional[str] = None,
        until: Optional[str] = None,
        direction: str = 'desc'
    ) -> List[Dict[str, Any]]:
        """
        Get orders.

        Args:
            status: Filter by order status ('open', 'closed', 'all')
            limit: Maximum number of orders to return
            after: Filter orders after this time
            until: Filter orders until this time
            direction: Sort direction ('asc' or 'desc')

        Returns:
            list: List of orders
        """
        params = {'direction': direction}

        if status:
            params['status'] = status
        if limit:
            params['limit'] = limit
        if after:
            params['after'] = after
        if until:
            params['until'] = until

        return self.client._request('GET', '/v2/orders', params=params)

    def get_order(self, order_id: str) -> Dict[str, Any]:
        """
        Get specific order by ID.

        Args:
            order_id: Order ID

        Returns:
            dict: Order data
        """
        return self.client._request('GET', f'/v2/orders/{order_id}')

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel an order.

        Args:
            order_id: Order ID to cancel

        Returns:
            dict: Cancellation confirmation
        """
        logger.info(f"Canceling order {order_id}")
        return self.client._request('DELETE', f'/v2/orders/{order_id}')

    def cancel_all_orders(self) -> List[Dict[str, Any]]:
        """
        Cancel all open orders.

        Returns:
            list: List of cancellation confirmations
        """
        logger.info("Canceling all open orders")
        return self.client._request('DELETE', '/v2/orders')

    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get all open positions.

        Returns:
            list: List of positions
        """
        return self.client._request('GET', '/v2/positions')

    def get_position(self, symbol: str) -> Dict[str, Any]:
        """
        Get specific position.

        Args:
            symbol: Stock symbol

        Returns:
            dict: Position data
        """
        return self.client._request('GET', f'/v2/positions/{symbol}')

    def close_position(
        self,
        symbol: str,
        qty: Optional[Union[int, float]] = None,
        percentage: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Close a position.

        Args:
            symbol: Stock symbol
            qty: Quantity to close (if None, closes entire position)
            percentage: Percentage of position to close

        Returns:
            dict: Order confirmation for closing position
        """
        params = {}
        if qty is not None:
            params['qty'] = str(qty)
        if percentage is not None:
            params['percentage'] = str(percentage)

        logger.info(f"Closing position for {symbol}")
        return self.client._request('DELETE', f'/v2/positions/{symbol}', params=params)

    def close_all_positions(self, cancel_orders: bool = True) -> List[Dict[str, Any]]:
        """
        Close all positions.

        Args:
            cancel_orders: Whether to cancel open orders

        Returns:
            list: List of order confirmations
        """
        params = {'cancel_orders': str(cancel_orders).lower()}
        logger.info("Closing all positions")
        return self.client._request('DELETE', '/v2/positions', params=params)

    def get_account(self) -> Dict[str, Any]:
        """
        Get account information including portfolio value.

        Returns:
            dict: Account information
        """
        return self.client.get_account()

    def is_paper_trading(self) -> bool:
        """
        Check if client is in paper trading mode.

        Returns:
            bool: True if paper trading
        """
        return self.config.is_paper_trading

    def close(self):
        """Close the client and cleanup resources."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
