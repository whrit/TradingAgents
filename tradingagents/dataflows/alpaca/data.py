"""Alpaca data vendor following the yfinance-compatible contract tested in TDD."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
import time
from typing import Optional

import pandas as pd


class AlpacaDataError(Exception):
    """Base class for Alpaca data errors."""


class AlpacaRateLimitError(AlpacaDataError):
    """Raised when Alpaca rate limit is hit."""


def _is_rate_limit_error(exc: Exception) -> bool:
    name = exc.__class__.__name__
    return isinstance(exc, AlpacaRateLimitError) or "RateLimit" in name


class AlpacaDataClient:
    """Thin client wrapper so tests can mock get_bars without real API calls."""

    def __init__(self, api_key: str, secret_key: str, base_url: str = "https://data.alpaca.markets"):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url
        # Real implementation would initialize REST client; omitted for tests.

    def get_bars(self, symbol: str, timeframe: str, start: str, end: str):
        raise NotImplementedError("Client methods should be mocked in tests")


def _load_credentials() -> tuple[str, str]:
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    if not api_key or not secret_key:
        raise ValueError("ALPACA_API_KEY and ALPACA_SECRET_KEY must be set for Alpaca data access")
    return api_key, secret_key


def _validate_symbol(symbol: str) -> str:
    if not symbol or not symbol.strip():
        raise ValueError("symbol cannot be empty or blank")
    return symbol.upper()


def _parse_date(value) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.strptime(value, "%Y-%m-%d")
    raise ValueError("Dates must be str 'YYYY-MM-DD' or datetime")


def _map_timeframe(interval: Optional[str]) -> str:
    mapping = {
        None: "1Day",
        "1d": "1Day",
        "1h": "1Hour",
        "15m": "15Min",
        "5m": "5Min",
        "1m": "1Min",
    }
    if interval not in mapping:
        raise ValueError(f"Unsupported interval '{interval}'. Supported: {list(mapping.keys())[1:]}")
    return mapping[interval]


def _format_bars(bars: pd.DataFrame) -> pd.DataFrame:
    if bars is None or bars.empty:
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
    df = bars.copy()
    df = df.rename(columns={
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume",
    })
    df = df[[col for col in ["Open", "High", "Low", "Close", "Volume"] if col in df.columns]]
    df = df.sort_index()
    return df


def get_stock_data(
    symbol: str,
    start_date,
    end_date,
    interval: Optional[str] = None,
    max_retries: int = 3,
) -> pd.DataFrame:
    symbol = _validate_symbol(symbol)
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if start > end:
        raise ValueError("start_date must be before end_date")
    timeframe = _map_timeframe(interval)

    api_key, secret_key = _load_credentials()
    client = AlpacaDataClient(api_key, secret_key)

    attempt = 0
    while True:
        try:
            bars_response = client.get_bars(
                symbol=symbol,
                timeframe=timeframe,
                start=start.isoformat(),
                end=end.isoformat(),
            )
            bars_df = bars_response.df if hasattr(bars_response, "df") else bars_response
            return _format_bars(bars_df)
        except Exception as exc:
            if _is_rate_limit_error(exc):
                attempt += 1
                if attempt > max_retries:
                    raise AlpacaRateLimitError("Exceeded retries after rate limit") from exc
                time.sleep(1)
                continue
            raise
