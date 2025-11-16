from datetime import datetime, timedelta

from .alpha_vantage_common import _make_api_request, format_datetime_for_api

def get_news(ticker, start_date, end_date) -> dict[str, str] | str:
    """Returns live and historical market news & sentiment data from premier news outlets worldwide.

    Covers stocks, cryptocurrencies, forex, and topics like fiscal policy, mergers & acquisitions, IPOs.

    Args:
        ticker: Stock symbol for news articles.
        start_date: Start date for news search.
        end_date: End date for news search.

    Returns:
        Dictionary containing news sentiment data or JSON string.
    """

    params = {
        "tickers": ticker,
        "time_from": format_datetime_for_api(start_date),
        "time_to": format_datetime_for_api(end_date),
        "sort": "LATEST",
        "limit": "50",
    }
    
    return _make_api_request("NEWS_SENTIMENT", params)

def get_insider_transactions(symbol: str) -> dict[str, str] | str:
    """Returns latest and historical insider transactions by key stakeholders.

    Covers transactions by founders, executives, board members, etc.

    Args:
        symbol: Ticker symbol. Example: "IBM".

    Returns:
        Dictionary containing insider transaction data or JSON string.
    """

    params = {
        "symbol": symbol,
    }

    return _make_api_request("INSIDER_TRANSACTIONS", params)


def get_global_news(curr_date: str, look_back_days: int = 7, limit: int = 5) -> dict | str:
    """Fetch macro/global news via Alpha Vantage's NEWS_SENTIMENT topics capability."""

    end_dt = datetime.strptime(curr_date, "%Y-%m-%d") + timedelta(hours=23, minutes=59)
    start_dt = end_dt - timedelta(days=look_back_days)

    params = {
        "topics": "financial_markets,economy,earnings",
        "time_from": format_datetime_for_api(start_dt),
        "time_to": format_datetime_for_api(end_dt),
        "sort": "LATEST",
        "limit": str(limit),
    }

    return _make_api_request("NEWS_SENTIMENT", params)
