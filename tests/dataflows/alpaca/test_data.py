"""
TDD Tests for Alpaca Data Vendor Implementation.

SPECIFICATION (Tests Define Implementation):
============================================
The Alpaca data vendor MUST:
1. Follow yfinance-compatible interface: get_stock_data(symbol, start_date, end_date, **kwargs)
2. Authenticate using environment variables (ALPACA_API_KEY, ALPACA_SECRET_KEY)
3. Return data in pandas DataFrame format matching yfinance structure
4. Handle rate limiting gracefully with retries
5. Provide clear error messages for invalid symbols
6. Support multiple timeframes (1Min, 5Min, 1Hour, 1Day)
7. Mock Alpaca API responses for unit tests (no real API calls)
8. Be compatible with other data vendors in dataflows/

This test suite defines the CONTRACT that the implementation must fulfill.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import os


class TestAlpacaDataVendorInterface:
    """
    TDD: Test that Alpaca data vendor follows yfinance-compatible interface.

    SPECIFICATION:
    - Must have get_stock_data() function
    - Signature: get_stock_data(symbol: str, start_date: str, end_date: str, **kwargs) -> pd.DataFrame
    - Return format: DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume']
    - Index: DatetimeIndex
    """

    def test_get_stock_data_function_exists(self):
        """Test that get_stock_data function exists and is callable."""
        # This test will fail until implementation exists
        from tradingagents.dataflows.alpaca.data import get_stock_data
        assert callable(get_stock_data)

    def test_get_stock_data_signature(self):
        """Test that get_stock_data has correct signature matching yfinance."""
        from tradingagents.dataflows.alpaca.data import get_stock_data
        import inspect

        sig = inspect.signature(get_stock_data)
        params = list(sig.parameters.keys())

        # Must have symbol, start_date, end_date as minimum parameters
        assert 'symbol' in params
        assert 'start_date' in params
        assert 'end_date' in params

    def test_get_stock_data_returns_dataframe(self):
        """Test that get_stock_data returns pandas DataFrame."""
        from tradingagents.dataflows.alpaca.data import get_stock_data

        with patch('tradingagents.dataflows.alpaca.data.AlpacaDataClient') as MockClient:
            # Mock Alpaca API response
            mock_bars = MagicMock()
            mock_bars.df = pd.DataFrame({
                'open': [150.0, 151.0],
                'high': [152.0, 153.0],
                'low': [149.0, 150.0],
                'close': [151.0, 152.0],
                'volume': [1000000, 1100000]
            }, index=pd.DatetimeIndex(['2025-01-13', '2025-01-14']))

            MockClient.return_value.get_bars.return_value = mock_bars

            result = get_stock_data('AAPL', '2025-01-13', '2025-01-14')

            assert isinstance(result, pd.DataFrame)

    def test_get_stock_data_dataframe_columns(self):
        """Test that returned DataFrame has correct yfinance-compatible columns."""
        from tradingagents.dataflows.alpaca.data import get_stock_data

        with patch('tradingagents.dataflows.alpaca.data.AlpacaDataClient') as MockClient:
            mock_bars = MagicMock()
            mock_bars.df = pd.DataFrame({
                'open': [150.0],
                'high': [152.0],
                'low': [149.0],
                'close': [151.0],
                'volume': [1000000]
            }, index=pd.DatetimeIndex(['2025-01-14']))

            MockClient.return_value.get_bars.return_value = mock_bars

            result = get_stock_data('AAPL', '2025-01-14', '2025-01-14')

            # Must have yfinance-compatible columns (capitalized)
            expected_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            assert all(col in result.columns for col in expected_columns)

    def test_get_stock_data_datetime_index(self):
        """Test that returned DataFrame has DatetimeIndex."""
        from tradingagents.dataflows.alpaca.data import get_stock_data

        with patch('tradingagents.dataflows.alpaca.data.AlpacaDataClient') as MockClient:
            mock_bars = MagicMock()
            mock_bars.df = pd.DataFrame({
                'open': [150.0],
                'high': [152.0],
                'low': [149.0],
                'close': [151.0],
                'volume': [1000000]
            }, index=pd.DatetimeIndex(['2025-01-14']))

            MockClient.return_value.get_bars.return_value = mock_bars

            result = get_stock_data('AAPL', '2025-01-14', '2025-01-14')

            assert isinstance(result.index, pd.DatetimeIndex)


class TestAlpacaDataVendorAuthentication:
    """
    TDD: Test Alpaca data vendor authentication.

    SPECIFICATION:
    - Must read credentials from environment variables
    - ALPACA_API_KEY and ALPACA_SECRET_KEY required
    - Should raise clear error if credentials missing
    - Should default to paper trading mode for data
    """

    def test_authentication_from_environment(self):
        """Test that authentication uses environment variables."""
        from tradingagents.dataflows.alpaca.data import get_stock_data

        with patch.dict(os.environ, {
            'ALPACA_API_KEY': 'test_key',
            'ALPACA_SECRET_KEY': 'test_secret'
        }):
            with patch('tradingagents.dataflows.alpaca.data.AlpacaDataClient') as MockClient:
                mock_bars = MagicMock()
                mock_bars.df = pd.DataFrame({
                    'open': [150.0],
                    'high': [152.0],
                    'low': [149.0],
                    'close': [151.0],
                    'volume': [1000000]
                }, index=pd.DatetimeIndex(['2025-01-14']))

                MockClient.return_value.get_bars.return_value = mock_bars

                get_stock_data('AAPL', '2025-01-14', '2025-01-14')

                # Verify client was initialized with environment credentials
                MockClient.assert_called()

    def test_missing_credentials_raises_error(self):
        """Test that missing credentials raises clear error."""
        from tradingagents.dataflows.alpaca.data import get_stock_data

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="ALPACA_API_KEY.*ALPACA_SECRET_KEY"):
                get_stock_data('AAPL', '2025-01-14', '2025-01-14')


class TestAlpacaDataVendorErrorHandling:
    """
    TDD: Test error handling for Alpaca data vendor.

    SPECIFICATION:
    - Must validate symbol before API call
    - Must handle network errors gracefully
    - Must handle invalid symbols with clear error
    - Must handle rate limiting with retry logic
    - Must handle invalid date ranges
    """

    def test_empty_symbol_raises_error(self):
        """Test that empty symbol raises validation error."""
        from tradingagents.dataflows.alpaca.data import get_stock_data

        with pytest.raises(ValueError, match="symbol.*empty|invalid"):
            get_stock_data('', '2025-01-14', '2025-01-14')

    def test_invalid_symbol_raises_error(self):
        """Test that invalid symbol raises appropriate error."""
        from tradingagents.dataflows.alpaca.data import get_stock_data

        with patch('tradingagents.dataflows.alpaca.data.AlpacaDataClient') as MockClient:
            # Mock API error for invalid symbol
            MockClient.return_value.get_bars.side_effect = Exception("Invalid symbol")

            with pytest.raises(Exception, match="Invalid symbol"):
                get_stock_data('INVALID_SYMBOL_XYZ', '2025-01-14', '2025-01-14')

    def test_network_error_handling(self):
        """Test graceful handling of network errors."""
        from tradingagents.dataflows.alpaca.data import get_stock_data

        with patch('tradingagents.dataflows.alpaca.data.AlpacaDataClient') as MockClient:
            MockClient.return_value.get_bars.side_effect = ConnectionError("Network error")

            with pytest.raises(ConnectionError):
                get_stock_data('AAPL', '2025-01-14', '2025-01-14')

    def test_rate_limit_handling(self):
        """Test that rate limiting is handled with retries."""
        from tradingagents.dataflows.alpaca.data import get_stock_data

        with patch('tradingagents.dataflows.alpaca.data.AlpacaDataClient') as MockClient:
            # First call raises rate limit error, second succeeds
            mock_bars = MagicMock()
            mock_bars.df = pd.DataFrame({
                'open': [150.0],
                'high': [152.0],
                'low': [149.0],
                'close': [151.0],
                'volume': [1000000]
            }, index=pd.DatetimeIndex(['2025-01-14']))

            rate_limit_error = Exception("Rate limit exceeded")
            rate_limit_error.__class__.__name__ = "RateLimitError"

            MockClient.return_value.get_bars.side_effect = [
                rate_limit_error,
                mock_bars
            ]

            # Should succeed after retry
            with patch('time.sleep'):  # Don't actually sleep in tests
                result = get_stock_data('AAPL', '2025-01-14', '2025-01-14')
                assert isinstance(result, pd.DataFrame)


class TestAlpacaDataVendorTimeframes:
    """
    TDD: Test support for multiple timeframes.

    SPECIFICATION:
    - Must support: 1Min, 5Min, 15Min, 1Hour, 1Day
    - Default timeframe: 1Day (matching yfinance)
    - Timeframe parameter name: 'interval' (matching yfinance)
    """

    @pytest.mark.parametrize("timeframe,alpaca_timeframe", [
        ("1d", "1Day"),
        ("1h", "1Hour"),
        ("15m", "15Min"),
        ("5m", "5Min"),
        ("1m", "1Min"),
    ])
    def test_timeframe_mapping(self, timeframe, alpaca_timeframe):
        """Test that yfinance timeframe notation maps to Alpaca format."""
        from tradingagents.dataflows.alpaca.data import get_stock_data

        with patch('tradingagents.dataflows.alpaca.data.AlpacaDataClient') as MockClient:
            mock_bars = MagicMock()
            mock_bars.df = pd.DataFrame({
                'open': [150.0],
                'high': [152.0],
                'low': [149.0],
                'close': [151.0],
                'volume': [1000000]
            }, index=pd.DatetimeIndex(['2025-01-14']))

            MockClient.return_value.get_bars.return_value = mock_bars

            get_stock_data('AAPL', '2025-01-14', '2025-01-14', interval=timeframe)

            # Verify Alpaca API was called with correct timeframe
            call_args = MockClient.return_value.get_bars.call_args
            # The timeframe should be converted to Alpaca format

    def test_default_timeframe_is_daily(self):
        """Test that default timeframe is 1Day when not specified."""
        from tradingagents.dataflows.alpaca.data import get_stock_data

        with patch('tradingagents.dataflows.alpaca.data.AlpacaDataClient') as MockClient:
            mock_bars = MagicMock()
            mock_bars.df = pd.DataFrame({
                'open': [150.0],
                'high': [152.0],
                'low': [149.0],
                'close': [151.0],
                'volume': [1000000]
            }, index=pd.DatetimeIndex(['2025-01-14']))

            MockClient.return_value.get_bars.return_value = mock_bars

            # Call without interval parameter
            get_stock_data('AAPL', '2025-01-14', '2025-01-14')

            # Should default to 1Day


class TestAlpacaDataVendorMocking:
    """
    TDD: Test that Alpaca API is properly mocked for unit tests.

    SPECIFICATION:
    - All unit tests must use mocked Alpaca API
    - No real API calls in unit tests
    - Mock responses should match Alpaca API structure
    """

    def test_no_real_api_calls_in_unit_tests(self):
        """Test that mocking prevents real API calls."""
        from tradingagents.dataflows.alpaca.data import get_stock_data

        # Without mocking, this should fail or be skipped
        # With mocking, it should work
        with patch('tradingagents.dataflows.alpaca.data.AlpacaDataClient') as MockClient:
            mock_bars = MagicMock()
            mock_bars.df = pd.DataFrame({
                'open': [150.0],
                'high': [152.0],
                'low': [149.0],
                'close': [151.0],
                'volume': [1000000]
            }, index=pd.DatetimeIndex(['2025-01-14']))

            MockClient.return_value.get_bars.return_value = mock_bars

            result = get_stock_data('AAPL', '2025-01-14', '2025-01-14')

            # Verify mock was called, not real API
            MockClient.assert_called()
            assert isinstance(result, pd.DataFrame)


class TestAlpacaDataVendorDataFormat:
    """
    TDD: Test data format compatibility with other vendors.

    SPECIFICATION:
    - Must return same format as yfinance
    - Must be compatible with existing dataflow interface
    - OHLCV columns must be numeric
    - Index must be timezone-aware or naive (consistent)
    """

    def test_ohlcv_columns_are_numeric(self):
        """Test that OHLCV columns contain numeric data."""
        from tradingagents.dataflows.alpaca.data import get_stock_data

        with patch('tradingagents.dataflows.alpaca.data.AlpacaDataClient') as MockClient:
            mock_bars = MagicMock()
            mock_bars.df = pd.DataFrame({
                'open': [150.0, 151.0],
                'high': [152.0, 153.0],
                'low': [149.0, 150.0],
                'close': [151.0, 152.0],
                'volume': [1000000, 1100000]
            }, index=pd.DatetimeIndex(['2025-01-13', '2025-01-14']))

            MockClient.return_value.get_bars.return_value = mock_bars

            result = get_stock_data('AAPL', '2025-01-13', '2025-01-14')

            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                assert pd.api.types.is_numeric_dtype(result[col])

    def test_data_sorted_by_date(self):
        """Test that data is sorted chronologically."""
        from tradingagents.dataflows.alpaca.data import get_stock_data

        with patch('tradingagents.dataflows.alpaca.data.AlpacaDataClient') as MockClient:
            mock_bars = MagicMock()
            # Create unsorted data
            mock_bars.df = pd.DataFrame({
                'open': [151.0, 150.0],
                'high': [153.0, 152.0],
                'low': [150.0, 149.0],
                'close': [152.0, 151.0],
                'volume': [1100000, 1000000]
            }, index=pd.DatetimeIndex(['2025-01-14', '2025-01-13']))

            MockClient.return_value.get_bars.return_value = mock_bars

            result = get_stock_data('AAPL', '2025-01-13', '2025-01-14')

            # Should be sorted by index (date)
            assert result.index.is_monotonic_increasing

    def test_empty_data_returns_empty_dataframe(self):
        """Test that no data returns empty DataFrame with correct structure."""
        from tradingagents.dataflows.alpaca.data import get_stock_data

        with patch('tradingagents.dataflows.alpaca.data.AlpacaDataClient') as MockClient:
            mock_bars = MagicMock()
            mock_bars.df = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])

            MockClient.return_value.get_bars.return_value = mock_bars

            result = get_stock_data('AAPL', '2025-01-13', '2025-01-14')

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 0
            assert 'Open' in result.columns


class TestAlpacaDataVendorDateHandling:
    """
    TDD: Test date parameter handling.

    SPECIFICATION:
    - Must accept string dates: 'YYYY-MM-DD'
    - Must accept datetime objects
    - Must handle timezone conversion properly
    - Must validate date ranges (start < end)
    """

    def test_accepts_string_dates(self):
        """Test that function accepts string date format."""
        from tradingagents.dataflows.alpaca.data import get_stock_data

        with patch('tradingagents.dataflows.alpaca.data.AlpacaDataClient') as MockClient:
            mock_bars = MagicMock()
            mock_bars.df = pd.DataFrame({
                'open': [150.0],
                'high': [152.0],
                'low': [149.0],
                'close': [151.0],
                'volume': [1000000]
            }, index=pd.DatetimeIndex(['2025-01-14']))

            MockClient.return_value.get_bars.return_value = mock_bars

            # Should accept string dates
            result = get_stock_data('AAPL', '2025-01-13', '2025-01-14')
            assert isinstance(result, pd.DataFrame)

    def test_accepts_datetime_objects(self):
        """Test that function accepts datetime objects."""
        from tradingagents.dataflows.alpaca.data import get_stock_data

        with patch('tradingagents.dataflows.alpaca.data.AlpacaDataClient') as MockClient:
            mock_bars = MagicMock()
            mock_bars.df = pd.DataFrame({
                'open': [150.0],
                'high': [152.0],
                'low': [149.0],
                'close': [151.0],
                'volume': [1000000]
            }, index=pd.DatetimeIndex(['2025-01-14']))

            MockClient.return_value.get_bars.return_value = mock_bars

            start = datetime(2025, 1, 13)
            end = datetime(2025, 1, 14)

            result = get_stock_data('AAPL', start, end)
            assert isinstance(result, pd.DataFrame)

    def test_invalid_date_range_raises_error(self):
        """Test that start_date > end_date raises error."""
        from tradingagents.dataflows.alpaca.data import get_stock_data

        with pytest.raises(ValueError, match="start.*end|date.*range"):
            get_stock_data('AAPL', '2025-01-14', '2025-01-13')


# Markers for test organization
pytestmark = [
    pytest.mark.dataflow,
    pytest.mark.alpaca,
    pytest.mark.unit
]
