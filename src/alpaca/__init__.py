"""
Alpaca Trading Integration Module

Provides comprehensive integration with Alpaca Markets API for trading operations.

Modules:
    - config: Configuration and environment management
    - client: Base API client with authentication
    - data: Market data retrieval and streaming
    - trading: Order placement and portfolio management

Example:
    >>> from src.alpaca import AlpacaConfig, AlpacaTradingClient
    >>> config = AlpacaConfig.from_env_file('.env')
    >>> with AlpacaTradingClient(config) as client:
    ...     order = client.submit_order('AAPL', qty=10, side='buy', order_type='market')
"""

from .config import AlpacaConfig, ConfigurationError
from .client import AlpacaClient, AlpacaAPIError, AuthenticationError
from .data import AlpacaDataClient, DataValidationError
from .trading import AlpacaTradingClient, OrderValidationError, TradingError

__all__ = [
    'AlpacaConfig',
    'AlpacaClient',
    'AlpacaDataClient',
    'AlpacaTradingClient',
    'ConfigurationError',
    'AlpacaAPIError',
    'AuthenticationError',
    'DataValidationError',
    'OrderValidationError',
    'TradingError',
]

__version__ = '1.0.0'
