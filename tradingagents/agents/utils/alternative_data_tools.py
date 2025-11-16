from langchain_core.tools import tool
from typing import Annotated

from tradingagents.dataflows.alternative_data import get_alternative_data_snapshot


@tool
def fetch_alternative_data(
    ticker: Annotated[str, "Ticker symbol (upper or lower case)"]
) -> str:
    """Retrieve a curated alternative-data snapshot for the provided ticker."""

    return get_alternative_data_snapshot(ticker)
