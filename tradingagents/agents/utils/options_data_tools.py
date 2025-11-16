from typing import Annotated, Optional

from langchain_core.tools import tool

from tradingagents.dataflows.interface import route_to_vendor


@tool
def get_options_data(
    ticker: Annotated[str, "Ticker symbol (uppercase or lowercase)"],
    expiry: Annotated[Optional[str], "Optional option expiry in YYYY-MM-DD format"] = None,
    limit: Annotated[int, "Number of contracts per side to return"] = 5,
) -> str:
    """Retrieve an options chain snapshot for the provided ticker."""

    clean_ticker = (ticker or "").strip().upper()
    if not clean_ticker:
        raise ValueError("Ticker symbol is required for options data.")

    return route_to_vendor("get_options_data", clean_ticker, expiry, limit)
