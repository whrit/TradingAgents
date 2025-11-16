"""Alpaca data vendor utilities supporting both legacy CSV and DataFrame outputs."""

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


def _dataframe_to_csv(df: pd.DataFrame, header: str) -> str:
    csv_body = df.to_csv(date_format="%Y-%m-%d", float_format="%.2f") if not df.empty else ""
    return f"{header}\n{csv_body}" if csv_body else f"{header}\n"


def _resolve_client(as_dataframe: bool) -> AlpacaDataClient:
    return AlpacaDataClient() if as_dataframe else get_client()


def _fetch_bars(
    client: AlpacaDataClient,
    symbol: str,
    timeframe: str,
    start: datetime,
    end: datetime,
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
            response = client._request("GET", endpoint, params=params)
            return response.get("bars", [])
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
    if start > end:
        raise ValueError("start_date must be before end_date")

    timeframe = _map_interval(interval)
    client = _resolve_client(as_dataframe)
    bars = _fetch_bars(client, symbol, timeframe, start, end, max_retries)
    df = _bars_to_dataframe(bars)

    if as_dataframe:
        return df

    if df.empty:
        return f"No data found for symbol '{symbol}' between {start_date} and {end_date}"

    header = (
        f"# Stock data for {symbol} from {start_date} to {end_date}\n"
        f"# Total records: {len(df)}\n"
        f"# Data source: Alpaca Markets\n"
    )
    df_for_csv = df.reset_index().rename(columns={"index": "Date"})
    return _dataframe_to_csv(df_for_csv.set_index("Date"), header)


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
    if start > end:
        raise ValueError("start_date must be before end_date")

    client = _resolve_client(as_dataframe)
    bars = _fetch_bars(client, symbol, timeframe, start, end, max_retries)
    df = _bars_to_dataframe(bars)

    if as_dataframe:
        return df

    if df.empty:
        return f"No bar data found for {symbol} ({timeframe})"

    header = (
        f"# Bar data for {symbol} ({timeframe})\n"
        f"# Records: {len(df)}\n"
        f"# Data source: Alpaca Markets\n"
    )
    df_for_csv = df.reset_index().rename(columns={"index": "Timestamp"})
    return _dataframe_to_csv(df_for_csv.set_index("Timestamp"), header)
