import json
from typing import Optional, Dict, Any

import pandas as pd
import yfinance as yf


def _serialize_records(df: pd.DataFrame, limit: int) -> list[Dict[str, Any]]:
    if df is None or df.empty:
        return []
    subset = df.sort_values("openInterest", ascending=False).head(limit)
    records = subset.to_dict(orient="records")
    normalized = []
    for row in records:
        normalized.append(
            {
                "contractSymbol": row.get("contractSymbol"),
                "strike": float(row.get("strike", 0.0)),
                "lastPrice": float(row.get("lastPrice", 0.0)),
                "bid": float(row.get("bid", 0.0)),
                "ask": float(row.get("ask", 0.0)),
                "volume": int(row.get("volume", 0) or 0),
                "openInterest": int(row.get("openInterest", 0) or 0),
                "impliedVolatility": float(row.get("impliedVolatility", 0.0)),
                "inTheMoney": bool(row.get("inTheMoney", False)),
                "delta": row.get("delta"),
                "gamma": row.get("gamma"),
                "theta": row.get("theta"),
                "vega": row.get("vega"),
                "rho": row.get("rho"),
            }
        )
    return normalized


def get_options_chain(
    ticker: str,
    expiry: Optional[str] = None,
    limit: int = 5,
) -> str:
    """
    Retrieve an options chain snapshot for the specified ticker.

    Args:
        ticker: Equity symbol (e.g., AAPL)
        expiry: Optional option expiry (YYYY-MM-DD). Defaults to nearest available.
        limit: Number of call/put contracts to include (sorted by open interest).

    Returns:
        JSON string containing calls, puts, and metadata.
    """
    yf_ticker = yf.Ticker(ticker)
    expirations = list(yf_ticker.options or [])
    if not expirations:
        return json.dumps(
            {
                "symbol": ticker.upper(),
                "message": "No listed option expirations available.",
            }
        )

    target_expiry = expiry if expiry in expirations else expirations[0]

    try:
        chain = yf_ticker.option_chain(target_expiry)
    except Exception as exc:
        return json.dumps(
            {
                "symbol": ticker.upper(),
                "expiry": target_expiry,
                "error": f"Failed to load option chain: {exc}",
            }
        )

    response = {
        "symbol": ticker.upper(),
        "expiry": target_expiry,
        "available_expirations": expirations,
        "calls": _serialize_records(chain.calls, limit),
        "puts": _serialize_records(chain.puts, limit),
    }
    return json.dumps(response)
