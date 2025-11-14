"""
Alpaca Data Module

Provides market data retrieval, historical queries, and real-time streaming capabilities.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from .client import AlpacaClient
from .config import AlpacaConfig


logger = logging.getLogger(__name__)


class DataValidationError(Exception):
    """Raised when data validation fails."""
    pass


class AlpacaDataClient:
    """
    Client for Alpaca market data operations.

    Provides access to quotes, bars, trades, and real-time streaming.

    Attributes:
        client: Base AlpacaClient instance
        config: AlpacaConfig instance
    """

    # Valid timeframe options
    VALID_TIMEFRAMES = [
        '1Min', '5Min', '15Min', '30Min',
        '1Hour', '2Hour', '4Hour',
        '1Day', '1Week', '1Month'
    ]

    def __init__(self, config: AlpacaConfig):
        """
        Initialize data client.

        Args:
            config: AlpacaConfig instance
        """
        self.config = config
        self.client = AlpacaClient(config)
        logger.info("Initialized Alpaca data client")

    def _validate_symbol(self, symbol: str) -> bool:
        """
        Validate stock symbol.

        Args:
            symbol: Stock symbol to validate

        Returns:
            bool: True if valid

        Raises:
            DataValidationError: If symbol is invalid
        """
        if not symbol or not isinstance(symbol, str):
            raise DataValidationError("Symbol must be a non-empty string")
        if len(symbol) > 10:
            raise DataValidationError("Symbol too long")
        return True

    def _validate_timeframe(self, timeframe: str) -> bool:
        """
        Validate timeframe parameter.

        Args:
            timeframe: Timeframe string

        Returns:
            bool: True if valid

        Raises:
            DataValidationError: If timeframe is invalid
        """
        if timeframe not in self.VALID_TIMEFRAMES:
            raise DataValidationError(
                f"Invalid timeframe '{timeframe}'. "
                f"Valid options: {', '.join(self.VALID_TIMEFRAMES)}"
            )
        return True

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse ISO timestamp string to datetime.

        Args:
            timestamp_str: ISO format timestamp

        Returns:
            datetime: Parsed datetime object
        """
        return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

    def get_latest_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get latest quote for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            dict: Latest quote data with bid, ask, and timestamp
        """
        self._validate_symbol(symbol)
        endpoint = f'/v2/stocks/{symbol}/quotes/latest'
        return self.client._request('GET', endpoint, base_url=self.config.data_url)

    def get_latest_trade(self, symbol: str) -> Dict[str, Any]:
        """
        Get latest trade for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            dict: Latest trade data
        """
        self._validate_symbol(symbol)
        endpoint = f'/v2/stocks/{symbol}/trades/latest'
        return self.client._request('GET', endpoint, base_url=self.config.data_url)

    def get_bars(
        self,
        symbol: str,
        timeframe: str = '1Day',
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get historical bar data.

        Args:
            symbol: Stock symbol
            timeframe: Bar timeframe (1Min, 1Hour, 1Day, etc.)
            start: Start date/time (ISO format)
            end: End date/time (ISO format)
            limit: Maximum number of bars to return

        Returns:
            dict: Historical bar data
        """
        self._validate_symbol(symbol)
        self._validate_timeframe(timeframe)

        endpoint = f'/v2/stocks/{symbol}/bars'
        params = {'timeframe': timeframe}

        if start:
            params['start'] = start
        if end:
            params['end'] = end
        if limit:
            params['limit'] = limit

        return self.client._request('GET', endpoint, params=params, base_url=self.config.data_url)

    def get_trades(
        self,
        symbol: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get historical trade data.

        Args:
            symbol: Stock symbol
            start: Start date/time (ISO format)
            end: End date/time (ISO format)
            limit: Maximum number of trades to return

        Returns:
            dict: Historical trade data
        """
        self._validate_symbol(symbol)

        endpoint = f'/v2/stocks/{symbol}/trades'
        params = {}

        if start:
            params['start'] = start
        if end:
            params['end'] = end
        if limit:
            params['limit'] = limit

        return self.client._request('GET', endpoint, params=params, base_url=self.config.data_url)

    def get_snapshot(self, symbol: str) -> Dict[str, Any]:
        """
        Get market snapshot for a symbol.

        Includes latest trade, quote, minute bar, and daily bar.

        Args:
            symbol: Stock symbol

        Returns:
            dict: Market snapshot data
        """
        self._validate_symbol(symbol)
        endpoint = f'/v2/stocks/{symbol}/snapshot'
        return self.client._request('GET', endpoint, base_url=self.config.data_url)

    def get_snapshots(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Get market snapshots for multiple symbols.

        Args:
            symbols: List of stock symbols

        Returns:
            dict: Snapshot data for each symbol
        """
        for symbol in symbols:
            self._validate_symbol(symbol)

        endpoint = '/v2/stocks/snapshots'
        params = {'symbols': ','.join(symbols)}
        return self.client._request('GET', endpoint, params=params, base_url=self.config.data_url)

    def subscribe_trades(self, symbols: List[str], handler=None):
        """
        Subscribe to real-time trade updates.

        Note: This is a placeholder for WebSocket streaming implementation.
        Full implementation would require WebSocket client setup.

        Args:
            symbols: List of symbols to subscribe to
            handler: Callback function for trade updates
        """
        logger.info(f"Trade streaming subscription requested for: {symbols}")
        # WebSocket implementation would go here
        raise NotImplementedError("Real-time streaming requires WebSocket implementation")

    def subscribe_quotes(self, symbols: List[str], handler=None):
        """
        Subscribe to real-time quote updates.

        Note: This is a placeholder for WebSocket streaming implementation.

        Args:
            symbols: List of symbols to subscribe to
            handler: Callback function for quote updates
        """
        logger.info(f"Quote streaming subscription requested for: {symbols}")
        # WebSocket implementation would go here
        raise NotImplementedError("Real-time streaming requires WebSocket implementation")

    def close(self):
        """Close the client and cleanup resources."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
