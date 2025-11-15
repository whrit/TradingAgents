"""
Alpaca data vendor module.

Provides market data retrieval following the project's data vendor pattern.
"""

from .data import get_stock_data, get_latest_quote, get_bars

__all__ = [
    'get_stock_data',
    'get_latest_quote',
    'get_bars',
]
