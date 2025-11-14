"""
Unit tests for Alpaca data module.

Tests market data retrieval, historical queries, and real-time streaming.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from src.alpaca.data import AlpacaDataClient, DataValidationError
from src.alpaca.config import AlpacaConfig


class TestAlpacaDataClient:
    """Test suite for AlpacaDataClient class."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration for testing."""
        return AlpacaConfig(api_key='test_key', secret_key='test_secret', paper_trading=True)

    @pytest.fixture
    def data_client(self, mock_config):
        """Create data client instance for testing."""
        return AlpacaDataClient(mock_config)

    def test_client_initialization(self, data_client):
        """Test data client initialization."""
        assert data_client.client is not None

    def test_get_latest_quote(self, data_client):
        """Test getting latest quote for a symbol."""
        with patch.object(data_client.client, '_request') as mock_request:
            mock_request.return_value = {
                'symbol': 'AAPL',
                'bid': 150.00,
                'ask': 150.10,
                'timestamp': '2025-01-14T10:00:00Z'
            }
            quote = data_client.get_latest_quote('AAPL')
            assert quote['symbol'] == 'AAPL'
            assert quote['bid'] == 150.00

    def test_get_bars(self, data_client):
        """Test getting historical bar data."""
        with patch.object(data_client.client, '_request') as mock_request:
            mock_request.return_value = {
                'bars': [
                    {
                        'timestamp': '2025-01-14T10:00:00Z',
                        'open': 150.00,
                        'high': 151.00,
                        'low': 149.50,
                        'close': 150.50,
                        'volume': 1000000
                    }
                ]
            }
            bars = data_client.get_bars('AAPL', timeframe='1Day', start='2025-01-01')
            assert len(bars['bars']) == 1
            assert bars['bars'][0]['symbol'] == 'AAPL' or 'open' in bars['bars'][0]

    def test_get_bars_with_date_range(self, data_client):
        """Test getting bars with specific date range."""
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()

        with patch.object(data_client.client, '_request') as mock_request:
            mock_request.return_value = {'bars': []}
            bars = data_client.get_bars(
                'AAPL',
                timeframe='1Hour',
                start=start_date.isoformat(),
                end=end_date.isoformat()
            )
            assert 'bars' in bars

    def test_get_trades(self, data_client):
        """Test getting trade data."""
        with patch.object(data_client.client, '_request') as mock_request:
            mock_request.return_value = {
                'trades': [
                    {
                        'timestamp': '2025-01-14T10:00:00Z',
                        'price': 150.25,
                        'size': 100
                    }
                ]
            }
            trades = data_client.get_trades('AAPL', start='2025-01-14')
            assert len(trades['trades']) == 1

    def test_get_latest_trade(self, data_client):
        """Test getting latest trade for a symbol."""
        with patch.object(data_client.client, '_request') as mock_request:
            mock_request.return_value = {
                'symbol': 'AAPL',
                'price': 150.25,
                'size': 100,
                'timestamp': '2025-01-14T10:00:00Z'
            }
            trade = data_client.get_latest_trade('AAPL')
            assert trade['price'] == 150.25

    def test_get_snapshot(self, data_client):
        """Test getting market snapshot."""
        with patch.object(data_client.client, '_request') as mock_request:
            mock_request.return_value = {
                'symbol': 'AAPL',
                'latestTrade': {'price': 150.25},
                'latestQuote': {'bid': 150.00, 'ask': 150.10},
                'dailyBar': {'open': 149.00, 'close': 150.25}
            }
            snapshot = data_client.get_snapshot('AAPL')
            assert snapshot['symbol'] == 'AAPL'
            assert 'latestTrade' in snapshot

    def test_validate_symbol(self, data_client):
        """Test symbol validation."""
        assert data_client._validate_symbol('AAPL') is True
        with pytest.raises(DataValidationError):
            data_client._validate_symbol('')
        with pytest.raises(DataValidationError):
            data_client._validate_symbol('INVALID_SYMBOL_TOO_LONG')

    def test_validate_timeframe(self, data_client):
        """Test timeframe validation."""
        valid_timeframes = ['1Min', '5Min', '15Min', '1Hour', '1Day']
        for tf in valid_timeframes:
            assert data_client._validate_timeframe(tf) is True

    def test_invalid_timeframe_raises_error(self, data_client):
        """Test invalid timeframe raises error."""
        with pytest.raises(DataValidationError):
            data_client._validate_timeframe('InvalidTimeframe')

    def test_parse_timestamp(self, data_client):
        """Test timestamp parsing."""
        timestamp_str = '2025-01-14T10:00:00Z'
        parsed = data_client._parse_timestamp(timestamp_str)
        assert isinstance(parsed, datetime)

    def test_get_multiple_symbols_snapshot(self, data_client):
        """Test getting snapshots for multiple symbols."""
        symbols = ['AAPL', 'GOOGL', 'MSFT']
        with patch.object(data_client.client, '_request') as mock_request:
            mock_request.return_value = {
                symbol: {'symbol': symbol, 'latestTrade': {'price': 100.0}}
                for symbol in symbols
            }
            snapshots = data_client.get_snapshots(symbols)
            assert len(snapshots) == 3

    def test_stream_trades_setup(self, data_client):
        """Test trade streaming setup."""
        # This tests the setup, actual streaming would need WebSocket mocking
        assert hasattr(data_client, 'subscribe_trades')

    def test_data_pagination(self, data_client):
        """Test data pagination handling."""
        with patch.object(data_client.client, '_request') as mock_request:
            mock_request.return_value = {
                'bars': [{'timestamp': '2025-01-14T10:00:00Z'}],
                'next_page_token': 'token123'
            }
            bars = data_client.get_bars('AAPL', timeframe='1Day')
            assert 'next_page_token' in bars
