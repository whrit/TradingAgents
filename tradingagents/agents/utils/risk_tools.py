from langchain_core.tools import tool
from typing import Annotated
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from io import StringIO

from tradingagents.dataflows.interface import route_to_vendor


def _clean_price_csv(csv_string: str) -> pd.DataFrame:
    """Convert the vendor CSV string into a pandas DataFrame."""
    if not csv_string:
        raise ValueError("Empty price data")

    lines = [
        line for line in csv_string.splitlines() if line and not line.startswith("#")
    ]
    if not lines:
        raise ValueError("Price data missing rows")

    df = pd.read_csv(StringIO("\n".join(lines)))
    df["Date"] = pd.to_datetime(df.index if "Date" not in df.columns else df["Date"])
    df = df.set_index("Date", drop=False)
    return df


@tool
def calculate_portfolio_risk(
    ticker: Annotated[str, "Ticker symbol"],
    end_date: Annotated[str, "Analysis end date in yyyy-mm-dd format"],
    lookback_days: Annotated[int, "How many days of history to use"] = 90,
    confidence: Annotated[float, "VaR confidence level e.g. 0.95"] = 0.95,
) -> str:
    """
    Compute simple historical VaR/Expected Shortfall metrics for the ticker.
    """

    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    start_dt = end_dt - timedelta(days=lookback_days)

    prices_csv = route_to_vendor(
        "get_stock_data", ticker, start_dt.strftime("%Y-%m-%d"), end_date
    )
    df = _clean_price_csv(prices_csv)
    closes = df["Close"].astype(float).tail(lookback_days)
    returns = closes.pct_change().dropna()
    if returns.empty:
        raise ValueError("Insufficient return history for risk calculation")

    var_level = np.quantile(returns, 1 - confidence)
    expected_shortfall = returns[returns <= var_level].mean()
    annualized_vol = returns.std() * np.sqrt(252)

    return (
        f"### Risk Snapshot for {ticker.upper()} ({lookback_days}d window)\n"
        f"- Historical VaR {confidence:.0%}: {var_level:.2%}\n"
        f"- Expected Shortfall: {expected_shortfall:.2%}\n"
        f"- Annualized Volatility: {annualized_vol:.2%}\n"
        "Assume a one-unit position; scale linearly for sizing guidance."
    )
