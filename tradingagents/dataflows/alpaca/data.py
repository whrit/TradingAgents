"""Alpaca data vendor utilities for JSON and DataFrame outputs."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
import time

import pandas as pd

from .common import (
    get_client,
    AlpacaDataClient,
    AlpacaRateLimitError,
    AlpacaAPIError,
)
from ..utils import build_price_payload


DEFAULT_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


def _validate_symbol(symbol: str) -> str:
    if not symbol or not symbol.strip():
        raise ValueError("symbol cannot be empty or blank")
    return symbol.upper()


def _parse_date(value) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.strptime(value, "%Y-%m-%d")
    raise ValueError("Dates must be strings in YYYY-MM-DD format or datetime objects")


def _map_interval(interval: Optional[str]) -> str:
    mapping = {
        None: "1Day",
        "1d": "1Day",
        "1h": "1Hour",
        "15m": "15Min",
        "5m": "5Min",
        "1m": "1Min",
    }
    if interval not in mapping:
        raise ValueError(
            f"Unsupported interval '{interval}'. Supported values: 1d, 1h, 15m, 5m, 1m"
        )
    return mapping[interval]


def _bars_to_dataframe(bars) -> pd.DataFrame:
    if isinstance(bars, pd.DataFrame):
        df = bars.copy()
        rename_map = {
            "o": "Open",
            "h": "High",
            "l": "Low",
            "c": "Close",
            "v": "Volume",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
        df = df.rename(columns=rename_map)
        if isinstance(df.index, pd.DatetimeIndex):
            if df.index.tz is not None:
                df.index = df.index.tz_convert(None)
        else:
            df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        df.index.name = "Date"
        return df[[col for col in DEFAULT_COLUMNS if col in df.columns]]

    if hasattr(bars, "df"):
        return _bars_to_dataframe(bars.df)

    if not bars:
        return pd.DataFrame(columns=DEFAULT_COLUMNS)

    df = pd.DataFrame(bars)
    if "t" in df.columns:
        df["Date"] = pd.to_datetime(df["t"]).dt.tz_convert(None)
    elif "Timestamp" in df.columns:
        df["Date"] = pd.to_datetime(df["Timestamp"]).dt.tz_convert(None)
    else:
        df["Date"] = pd.RangeIndex(start=0, stop=len(df))

    rename_map = {
        "o": "Open",
        "h": "High",
        "l": "Low",
        "c": "Close",
        "v": "Volume",
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume",
    }
    df = df.rename(columns=rename_map)
    df = df.set_index("Date")
    df = df[[col for col in DEFAULT_COLUMNS if col in df.columns]]
    return df.sort_index()


def _dataframe_to_json_payload(
    df: pd.DataFrame,
    symbol: str,
    start_date: str,
    end_date: str,
    source: str,
    metadata: Optional[dict] = None,
):
    df_for_json = df.reset_index()
    date_col = df.index.name or "index"
    if date_col not in df_for_json.columns:
        date_col = "Date" if "Date" in df_for_json.columns else df_for_json.columns[0]
    return build_price_payload(
        symbol,
        start_date,
        end_date,
        source,
        df_for_json,
        date_column=date_col,
        metadata=metadata,
    )


def _empty_price_payload(symbol: str, start_date: str, end_date: str, source: str, metadata: Optional[dict] = None) -> str:
    empty_df = pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
    return build_price_payload(
        symbol,
        start_date,
        end_date,
        source,
        empty_df,
        date_column="date",
        metadata=metadata,
    )


def _resolve_client(as_dataframe: bool):
    return (
        (AlpacaDataClient(), True)
        if as_dataframe
        else (get_client(), False)
    )


def _fetch_bars(
    client,
    symbol: str,
    timeframe: str,
    start: datetime,
    end: datetime,
    use_sdk: bool,
    max_retries: int = 3,
):
    endpoint = f"/v2/stocks/{symbol}/bars"
    params = {
        "timeframe": timeframe,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "limit": 10000,
    }

    attempts = 0
    while True:
        try:
            if use_sdk:
                result = client.get_bars(
                    symbol=symbol,
                    timeframe=timeframe,
                    start=start.isoformat(),
                    end=end.isoformat(),
                )
            else:
                response = client._request("GET", endpoint, params=params)
                result = response.get("bars", [])

            if isinstance(result, pd.DataFrame):
                return result
            if hasattr(result, "df"):
                return result.df
            if isinstance(result, dict):
                return result.get("bars", [])
            return result
        except Exception as exc:  # pragma: no cover - delegated to tests
            name = exc.__class__.__name__
            if "RateLimit" in name:
                attempts += 1
                if attempts > max_retries:
                    raise AlpacaRateLimitError("Rate limit exceeded")
                time.sleep(1)
                continue
            raise


def get_stock_data(
    symbol: str,
    start_date,
    end_date,
    interval: Optional[str] = None,
    as_dataframe: bool = False,
    max_retries: int = 3,
):
    symbol = _validate_symbol(symbol)
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    start_label = start.strftime("%Y-%m-%d")
    end_label = end.strftime("%Y-%m-%d")
    if start > end:
        raise ValueError("start_date must be before end_date")

    timeframe = _map_interval(interval)
    client, use_sdk = _resolve_client(as_dataframe)
    try:
        bars = _fetch_bars(client, symbol, timeframe, start, end, use_sdk, max_retries)
        df = _bars_to_dataframe(bars)
    except AlpacaAPIError as exc:
        if isinstance(exc, AlpacaRateLimitError):
            raise
        if as_dataframe:
            raise
        return _empty_price_payload(
            symbol,
            start_label,
            end_label,
            "alpaca",
            metadata={"error": str(exc), "record_count": 0},
        )

    if as_dataframe:
        return df

    metadata = {"record_count": len(df)}
    return _dataframe_to_json_payload(
        df,
        symbol,
        start_label,
        end_label,
        "alpaca",
        metadata=metadata,
    )


def get_latest_quote(symbol: str) -> dict:
    symbol = _validate_symbol(symbol)
    client = get_client()
    endpoint = f"/v2/stocks/{symbol}/quotes/latest"
    try:
        response = client._request("GET", endpoint)
        quote = response.get("quote", {})
        if not quote:
            return response
        return {
            "symbol": symbol,
            "bid": quote.get("bp", 0.0),
            "ask": quote.get("ap", 0.0),
            "bid_size": quote.get("bs", 0),
            "ask_size": quote.get("as", 0),
            "timestamp": quote.get("t", ""),
        }
    except AlpacaAPIError as exc:
        return {"error": str(exc)}


def get_bars(
    symbol: str,
    timeframe: str,
    start_date,
    end_date,
    as_dataframe: bool = False,
    max_retries: int = 3,
):
    symbol = _validate_symbol(symbol)
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    start_label = start.strftime("%Y-%m-%d")
    end_label = end.strftime("%Y-%m-%d")
    if start > end:
        raise ValueError("start_date must be before end_date")

    client, use_sdk = _resolve_client(as_dataframe)
    try:
        bars = _fetch_bars(client, symbol, timeframe, start, end, use_sdk, max_retries)
        df = _bars_to_dataframe(bars)
    except AlpacaAPIError as exc:
        if isinstance(exc, AlpacaRateLimitError):
            raise
        if as_dataframe:
            raise
        return _empty_price_payload(
            symbol,
            start_label,
            end_label,
            "alpaca",
            metadata={"timeframe": timeframe, "record_count": 0, "error": str(exc)},
        )

    if as_dataframe:
        return df

    metadata = {"timeframe": timeframe, "record_count": len(df)}
    return _dataframe_to_json_payload(
        df,
        symbol,
        start_label,
        end_label,
        "alpaca",
        metadata=metadata,
    )
