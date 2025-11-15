"""Alpaca trading client initialization and configuration.

This module provides functions to create and configure Alpaca TradingClient instances
with proper authentication and paper/live trading mode selection.
"""

from alpaca.trading.client import TradingClient
from tradingagents.dataflows.config import get_config


def get_trading_client(paper: bool = True) -> TradingClient:
    """Get Alpaca trading client configured for paper or live trading.

    This function retrieves API credentials from the configuration and creates
    a TradingClient instance. By default, it uses paper trading mode for safety.

    Args:
        paper: If True, use paper trading credentials. If False, use live trading
               credentials. Live trading requires auto_execute_trades=True in config.

    Returns:
        TradingClient: Configured Alpaca trading client

    Raises:
        ValueError: If live trading is requested but auto_execute_trades is not enabled
        KeyError: If required API credentials are not found in configuration

    Example:
        >>> # Get paper trading client (default, safe)
        >>> client = get_trading_client()
        >>>
        >>> # Get live trading client (requires explicit config)
        >>> client = get_trading_client(paper=False)
    """
    config = get_config()

    if paper:
        # Paper trading mode - safe for testing
        api_key = config.get("alpaca_paper_api_key")
        secret_key = config.get("alpaca_paper_secret_key")

        if not api_key or not secret_key:
            raise KeyError(
                "Alpaca paper trading credentials not found in configuration. "
                "Please set 'alpaca_paper_api_key' and 'alpaca_paper_secret_key'."
            )
    else:
        # Live trading mode - requires explicit enable flag for safety
        if not config.get("auto_execute_trades", False):
            raise ValueError(
                "Live trading requires auto_execute_trades=True in config. "
                "This is a safety feature to prevent accidental live trading."
            )

        api_key = config.get("alpaca_live_api_key")
        secret_key = config.get("alpaca_live_secret_key")

        if not api_key or not secret_key:
            raise KeyError(
                "Alpaca live trading credentials not found in configuration. "
                "Please set 'alpaca_live_api_key' and 'alpaca_live_secret_key'."
            )

    return TradingClient(api_key, secret_key, paper=paper)
