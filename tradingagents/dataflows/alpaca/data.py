"""
Alpaca Data Functions

Market data retrieval functions following the project's vendor pattern.
Matches signatures from yfinance and alpha_vantage for seamless integration.
"""

from typing import Annotated, Optional
from datetime import datetime
import pandas as pd
from io import StringIO

from .common import get_client, AlpacaAPIError, AlpacaRateLimitError


def get_stock_data(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """
    Get OHLCV stock data from Alpaca.

    Matches the signature of get_YFin_data_online and get_alpha_vantage_stock
    for seamless integration with the routing system.

    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL')
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format

    Returns:
        CSV string containing stock data with header information

    Raises:
        AlpacaRateLimitError: If rate limit is exceeded
        AlpacaAPIError: If API request fails
    """
    # Validate dates
    datetime.strptime(start_date, "%Y-%m-%d")
    datetime.strptime(end_date, "%Y-%m-%d")

    try:
        client = get_client()

        # Get bars from Alpaca (daily timeframe)
        endpoint = f'/v2/stocks/{symbol.upper()}/bars'
        params = {
            'timeframe': '1Day',
            'start': start_date,
            'end': end_date,
            'limit': 10000  # Max allowed by Alpaca
        }

        response = client._request('GET', endpoint, params=params)

        # Check if we got data
        if 'bars' not in response or not response['bars']:
            return f"No data found for symbol '{symbol}' between {start_date} and {end_date}"

        # Convert bars to DataFrame for formatting
        bars = response['bars']
        df = pd.DataFrame(bars)

        # Rename columns to match yfinance format
        column_mapping = {
            't': 'Date',
            'o': 'Open',
            'h': 'High',
            'l': 'Low',
            'c': 'Close',
            'v': 'Volume',
            'n': 'Trades',
            'vw': 'VWAP'
        }
        df = df.rename(columns=column_mapping)

        # Convert timestamp to datetime
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')

        # Select and order columns similar to yfinance
        available_cols = [col for col in ['Date', 'Open', 'High', 'Low', 'Close', 'Volume'] if col in df.columns]
        df = df[available_cols]

        # Round numerical values to 2 decimal places
        numeric_columns = ['Open', 'High', 'Low', 'Close']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].round(2)

        # Set Date as index for CSV output
        if 'Date' in df.columns:
            df = df.set_index('Date')

        # Convert to CSV string
        csv_string = df.to_csv()

        # Add header information (matching yfinance format)
        header = f"# Stock data for {symbol.upper()} from {start_date} to {end_date}\n"
        header += f"# Total records: {len(df)}\n"
        header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += f"# Data source: Alpaca Markets\n\n"

        return header + csv_string

    except AlpacaRateLimitError:
        # Re-raise rate limit errors to trigger fallback
        raise
    except Exception as e:
        return f"Error retrieving data from Alpaca for {symbol}: {str(e)}"


def get_latest_quote(
    symbol: Annotated[str, "ticker symbol of the company"]
) -> dict:
    """
    Get latest quote for a symbol.

    Args:
        symbol: Stock ticker symbol

    Returns:
        dict: Latest quote data with bid, ask, and timestamp
    """
    try:
        client = get_client()
        endpoint = f'/v2/stocks/{symbol.upper()}/quotes/latest'
        response = client._request('GET', endpoint)

        # Extract quote data
        if 'quote' in response:
            quote = response['quote']
            return {
                'symbol': symbol.upper(),
                'bid': quote.get('bp', 0),
                'ask': quote.get('ap', 0),
                'bid_size': quote.get('bs', 0),
                'ask_size': quote.get('as', 0),
                'timestamp': quote.get('t', '')
            }
        return response

    except Exception as e:
        return {'error': f"Error getting quote for {symbol}: {str(e)}"}


def get_bars(
    symbol: Annotated[str, "ticker symbol of the company"],
    timeframe: Annotated[str, "Bar timeframe (1Min, 1Hour, 1Day, etc.)"],
    start: Annotated[str, "Start date/time in yyyy-mm-dd format"],
    end: Annotated[str, "End date/time in yyyy-mm-dd format"],
) -> str:
    """
    Get historical bar data for technical analysis.

    Args:
        symbol: Stock ticker symbol
        timeframe: Bar timeframe (1Min, 5Min, 15Min, 1Hour, 1Day, etc.)
        start: Start date/time
        end: End date/time

    Returns:
        CSV string containing bar data
    """
    try:
        client = get_client()

        endpoint = f'/v2/stocks/{symbol.upper()}/bars'
        params = {
            'timeframe': timeframe,
            'start': start,
            'end': end,
            'limit': 10000
        }

        response = client._request('GET', endpoint, params=params)

        if 'bars' not in response or not response['bars']:
            return f"No bar data found for {symbol} ({timeframe})"

        # Convert to DataFrame
        bars = response['bars']
        df = pd.DataFrame(bars)

        # Rename columns
        column_mapping = {
            't': 'Timestamp',
            'o': 'Open',
            'h': 'High',
            'l': 'Low',
            'c': 'Close',
            'v': 'Volume',
            'vw': 'VWAP'
        }
        df = df.rename(columns=column_mapping)

        # Convert timestamp
        if 'Timestamp' in df.columns:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            df = df.set_index('Timestamp')

        # Round numerical values
        numeric_columns = ['Open', 'High', 'Low', 'Close', 'VWAP']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].round(2)

        csv_string = df.to_csv()

        # Add header
        header = f"# Bar data for {symbol.upper()} ({timeframe})\n"
        header += f"# Period: {start} to {end}\n"
        header += f"# Total bars: {len(df)}\n\n"

        return header + csv_string

    except Exception as e:
        return f"Error getting bars for {symbol}: {str(e)}"
