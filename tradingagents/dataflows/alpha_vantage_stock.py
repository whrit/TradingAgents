import json
from datetime import datetime
from typing import Dict

import pandas as pd

from .alpha_vantage_common import _make_api_request
from .utils import build_price_payload

_STOCK_CACHE: Dict[str, pd.DataFrame] = {}


def _fetch_symbol_timeseries(symbol: str) -> pd.DataFrame:
    """Fetch and cache the full daily time series for a symbol."""
    normalized = symbol.upper()
    if normalized in _STOCK_CACHE:
        return _STOCK_CACHE[normalized]

    params = {
        "symbol": normalized,
        "outputsize": "full",
    }
    response = _make_api_request("TIME_SERIES_DAILY", params)
    payload = json.loads(response)
    series_key = next(
        (key for key in payload.keys() if "Time Series" in key),
        None,
    )
    if not series_key or series_key not in payload:
        raise ValueError(f"Alpha Vantage response missing time series for {symbol}")

    series = payload[series_key]
    records = []
    for date_str, values in series.items():
        close_value = float(values["4. close"])
        records.append(
            {
                "date": datetime.strptime(date_str, "%Y-%m-%d"),
                "open": float(values["1. open"]),
                "high": float(values["2. high"]),
                "low": float(values["3. low"]),
                "close": close_value,
                "adjusted_close": float(values.get("5. adjusted close", close_value)),
                "volume": int(values.get("5. volume", values.get("6. volume", 0))),
                "dividend_amount": float(values.get("7. dividend amount", 0.0)),
                "split_coefficient": float(values.get("8. split coefficient", 1.0)),
            }
        )

    df = pd.DataFrame(records).sort_values("date").reset_index(drop=True)
    _STOCK_CACHE[normalized] = df
    return df


def _filter_dataframe_by_date_range(df: pd.DataFrame, start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
    mask = (df["date"] >= start_dt) & (df["date"] <= end_dt)
    return df.loc[mask].copy()


def get_stock(symbol: str, start_date: str, end_date: str) -> str:
    """
    Returns raw daily OHLCV values, adjusted close values, and historical split/dividend events
    filtered to the specified date range.

    Args:
        symbol: The name of the equity. For example: symbol=IBM
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format

    Returns:
        JSON string containing the daily adjusted time series data filtered to the date range.
    """
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    if end_dt < start_dt:
        raise ValueError("end_date must be on or after start_date.")

    df = _fetch_symbol_timeseries(symbol)
    filtered = _filter_dataframe_by_date_range(df, start_dt, end_dt)
    if filtered.empty:
        filtered = df.iloc[0:0]

    return build_price_payload(
        symbol,
        start_date,
        end_date,
        "alpha_vantage",
        filtered,
        date_column="date",
    )
