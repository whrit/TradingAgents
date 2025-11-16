import re
from datetime import datetime, date
from typing import Annotated, Optional

from langchain_core.tools import tool

from tradingagents.dataflows.interface import route_to_vendor

MAX_NEWS_LIMIT = 50
VALID_TICKER_PATTERN = re.compile(r"^[A-Z0-9\._:,\-]+$")


def _normalized_ticker(value: Optional[str]) -> str:
    normalized = (value or "").strip().upper()
    if not normalized:
        raise ValueError("Ticker symbol is required before requesting news.")
    if " " in normalized:
        raise ValueError(
            "Alpha Vantage news lookups require pure ticker strings without spaces."
        )
    if not VALID_TICKER_PATTERN.fullmatch(normalized):
        raise ValueError(
            "Ticker symbols may only contain letters, numbers, dashes, underscores, periods, colons, and commas."
        )
    return normalized


def _parse_date(value: Optional[str], label: str) -> date:
    if not value:
        raise ValueError(f"{label} is required in yyyy-mm-dd format.")
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"{label} must be in yyyy-mm-dd format.") from exc


def _validate_window(start: date, end: date):
    today = datetime.utcnow().date()
    if end < start:
        raise ValueError("end_date must not be earlier than start_date.")
    if start > today or end > today:
        raise ValueError("News queries cannot extend into the future.")

@tool
def get_news(
    ticker: Annotated[str, "Ticker symbol"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """Fetch ticker-scoped news while validating ticker and date inputs."""
    ticker_clean = _normalized_ticker(ticker)
    start_dt = _parse_date(start_date, "start_date")
    end_dt = _parse_date(end_date, "end_date")
    _validate_window(start_dt, end_dt)

    return route_to_vendor(
        "get_news",
        ticker_clean,
        start_dt.strftime("%Y-%m-%d"),
        end_dt.strftime("%Y-%m-%d"),
    )

@tool
def get_global_news(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "Number of days to look back"] = 7,
    limit: Annotated[int, "Maximum number of articles to return"] = 5,
) -> str:
    """Fetch macro/global news with validated dates and capped limits."""
    curr_dt = _parse_date(curr_date, "curr_date")
    today = datetime.utcnow().date()
    if curr_dt > today:
        raise ValueError("curr_date for global news cannot be in the future.")
    if look_back_days <= 0:
        raise ValueError("look_back_days must be positive.")

    sanitized_limit = max(1, min(MAX_NEWS_LIMIT, limit))

    return route_to_vendor(
        "get_global_news",
        curr_dt.strftime("%Y-%m-%d"),
        look_back_days,
        sanitized_limit,
    )

@tool
def get_insider_sentiment(
    ticker: Annotated[str, "ticker symbol for the company"],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
) -> str:
    """
    Retrieve insider sentiment information about a company.
    Uses the configured news_data vendor.
    Args:
        ticker (str): Ticker symbol of the company
        curr_date (str): Current date you are trading at, yyyy-mm-dd
    Returns:
        str: A report of insider sentiment data
    """
    return route_to_vendor("get_insider_sentiment", ticker, curr_date)

@tool
def get_insider_transactions(
    ticker: Annotated[str, "ticker symbol"],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
) -> str:
    """
    Retrieve insider transaction information about a company.
    Uses the configured news_data vendor.
    Args:
        ticker (str): Ticker symbol of the company
        curr_date (str): Current date you are trading at, yyyy-mm-dd
    Returns:
        str: A report of insider transaction data
    """
    return route_to_vendor("get_insider_transactions", ticker, curr_date)
