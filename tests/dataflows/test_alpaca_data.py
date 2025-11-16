"""
Unit tests for Alpaca data vendor integration.

Tests market data retrieval functions following TDD approach.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from tradingagents.dataflows.alpaca.data import get_stock_data, get_latest_quote, get_bars
from tradingagents.dataflows.alpaca.common import (
    AlpacaDataClient,
    AlpacaAPIError,
    AlpacaRateLimitError,
    get_alpaca_credentials
)


class TestAlpacaCredentials:
    """Test credential retrieval."""

    def test_get_credentials_from_env(self, monkeypatch):
        """Test retrieving credentials from environment variables."""
        monkeypatch.setenv("ALPACA_API_KEY", "test_key")
        monkeypatch.setenv("ALPACA_SECRET_KEY", "test_secret")

        api_key, secret_key = get_alpaca_credentials()
        assert api_key == "test_key"
        assert secret_key == "test_secret"

    def test_missing_api_key_raises_error(self, monkeypatch):
        """Test that missing API key raises ValueError."""
        monkeypatch.delenv("ALPACA_API_KEY", raising=False)
        monkeypatch.setenv("ALPACA_SECRET_KEY", "test_secret")

        with pytest.raises(ValueError, match="ALPACA_API_KEY"):
            get_alpaca_credentials()

    def test_missing_secret_key_raises_error(self, monkeypatch):
        """Test that missing secret key raises ValueError."""
        monkeypatch.setenv("ALPACA_API_KEY", "test_key")
        monkeypatch.delenv("ALPACA_SECRET_KEY", raising=False)

        with pytest.raises(ValueError, match="ALPACA_SECRET_KEY"):
            get_alpaca_credentials()


class TestAlpacaDataClient:
    """Test suite for AlpacaDataClient class."""

    @pytest.fixture
    def mock_credentials(self, monkeypatch):
        """Mock environment credentials."""
        monkeypatch.setenv("ALPACA_API_KEY", "test_key")
        monkeypatch.setenv("ALPACA_SECRET_KEY", "test_secret")

    @pytest.fixture
    def client(self, mock_credentials):
        """Create client instance for testing."""
        return AlpacaDataClient()

    def test_client_initialization(self, client):
        """Test client initialization."""
        assert client.api_key == "test_key"
        assert client.secret_key == "test_secret"
        assert client.data_url == "https://data.alpaca.markets"
        assert client.session is not None

    def test_client_with_explicit_credentials(self):
        """Test client with explicitly provided credentials."""
        client = AlpacaDataClient(api_key="explicit_key", secret_key="explicit_secret")
        assert client.api_key == "explicit_key"
        assert client.secret_key == "explicit_secret"

    def test_get_headers(self, client):
        """Test header generation."""
        headers = client._get_headers()
        assert headers['APCA-API-KEY-ID'] == "test_key"
        assert headers['APCA-API-SECRET-KEY'] == "test_secret"
        assert headers['Content-Type'] == 'application/json'

    def test_request_success(self, client):
        """Test successful API request."""
        with patch.object(client.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'data': 'test'}
            mock_response.content = b'{"data": "test"}'
            mock_request.return_value = mock_response

            result = client._request('GET', '/test')
            assert result == {'data': 'test'}

    def test_request_authentication_error(self, client):
        """Test authentication error handling."""
        with patch.object(client.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.json.return_value = {'message': 'Unauthorized'}
            mock_response.content = b'{"message": "Unauthorized"}'
            mock_request.return_value = mock_response

            with pytest.raises(AlpacaAPIError, match="Authentication failed"):
                client._request('GET', '/test')

    def test_request_rate_limit_error(self, client):
        """Test rate limit error handling."""
        with patch.object(client.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.headers = {'Retry-After': '60'}
            mock_response.json.return_value = {}
            mock_response.content = b'{}'
            mock_request.return_value = mock_response

            with pytest.raises(AlpacaRateLimitError, match="Rate limit exceeded"):
                client._request('GET', '/test')


class TestGetStockData:
    """Test suite for get_stock_data function."""

    @pytest.fixture
    def mock_alpaca_response(self):
        """Mock Alpaca API response."""
        return {
            'bars': [
                {
                    't': '2025-01-10T05:00:00Z',
                    'o': 150.00,
                    'h': 152.00,
                    'l': 149.50,
                    'c': 151.50,
                    'v': 1000000,
                    'vw': 151.00
                },
                {
                    't': '2025-01-11T05:00:00Z',
                    'o': 151.50,
                    'h': 153.00,
                    'l': 150.00,
                    'c': 152.00,
                    'v': 1200000,
                    'vw': 152.00
                }
            ]
        }

    def test_get_stock_data_success(self, monkeypatch, mock_alpaca_response):
        """Test successful stock data retrieval."""
        monkeypatch.setenv("ALPACA_API_KEY", "test_key")
        monkeypatch.setenv("ALPACA_SECRET_KEY", "test_secret")

        with patch('tradingagents.dataflows.alpaca.data.get_client') as mock_get_client:
            mock_client = Mock()
            mock_client._request.return_value = mock_alpaca_response
            mock_get_client.return_value = mock_client

            result = get_stock_data('AAPL', '2025-01-10', '2025-01-11')

            payload = json.loads(result)
            assert payload["symbol"] == "AAPL"
            assert payload["source"] == "alpaca"
            assert payload["meta"]["record_count"] == 2
            assert len(payload["records"]) == 2
            assert payload["records"][0]["close"] == mock_alpaca_response["bars"][0]["c"]

    def test_get_stock_data_no_data(self, monkeypatch):
        """Test handling when no data is returned."""
        monkeypatch.setenv("ALPACA_API_KEY", "test_key")
        monkeypatch.setenv("ALPACA_SECRET_KEY", "test_secret")

        with patch('tradingagents.dataflows.alpaca.data.get_client') as mock_get_client:
            mock_client = Mock()
            mock_client._request.return_value = {'bars': []}
            mock_get_client.return_value = mock_client

            result = get_stock_data('INVALID', '2025-01-10', '2025-01-11')
            payload = json.loads(result)
            assert payload["records"] == []
            assert payload["meta"]["record_count"] == 0

    def test_get_stock_data_invalid_date_format(self):
        """Test that invalid date format raises error."""
        with pytest.raises(ValueError):
            get_stock_data('AAPL', 'invalid-date', '2025-01-11')

    def test_get_stock_data_rate_limit(self, monkeypatch):
        """Test rate limit error handling."""
        monkeypatch.setenv("ALPACA_API_KEY", "test_key")
        monkeypatch.setenv("ALPACA_SECRET_KEY", "test_secret")

        with patch('tradingagents.dataflows.alpaca.data.get_client') as mock_get_client:
            mock_client = Mock()
            mock_client._request.side_effect = AlpacaRateLimitError("Rate limit exceeded")
            mock_get_client.return_value = mock_client

            with pytest.raises(AlpacaRateLimitError):
                get_stock_data('AAPL', '2025-01-10', '2025-01-11')


class TestGetLatestQuote:
    """Test suite for get_latest_quote function."""

    def test_get_latest_quote_success(self, monkeypatch):
        """Test successful quote retrieval."""
        monkeypatch.setenv("ALPACA_API_KEY", "test_key")
        monkeypatch.setenv("ALPACA_SECRET_KEY", "test_secret")

        mock_response = {
            'quote': {
                'bp': 150.00,
                'ap': 150.10,
                'bs': 100,
                'as': 200,
                't': '2025-01-14T10:00:00Z'
            }
        }

        with patch('tradingagents.dataflows.alpaca.data.get_client') as mock_get_client:
            mock_client = Mock()
            mock_client._request.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = get_latest_quote('AAPL')

            assert result['symbol'] == 'AAPL'
            assert result['bid'] == 150.00
            assert result['ask'] == 150.10
            assert result['bid_size'] == 100
            assert result['ask_size'] == 200

    def test_get_latest_quote_error(self, monkeypatch):
        """Test error handling in quote retrieval."""
        monkeypatch.setenv("ALPACA_API_KEY", "test_key")
        monkeypatch.setenv("ALPACA_SECRET_KEY", "test_secret")

        with patch('tradingagents.dataflows.alpaca.data.get_client') as mock_get_client:
            mock_client = Mock()
            mock_client._request.side_effect = AlpacaAPIError("API Error")
            mock_get_client.return_value = mock_client

            result = get_latest_quote('AAPL')
            assert 'error' in result


class TestGetBars:
    """Test suite for get_bars function."""

    def test_get_bars_success(self, monkeypatch):
        """Test successful bars retrieval."""
        monkeypatch.setenv("ALPACA_API_KEY", "test_key")
        monkeypatch.setenv("ALPACA_SECRET_KEY", "test_secret")

        mock_response = {
            'bars': [
                {
                    't': '2025-01-14T10:00:00Z',
                    'o': 150.00,
                    'h': 151.00,
                    'l': 149.50,
                    'c': 150.50,
                    'v': 1000000,
                    'vw': 150.25
                }
            ]
        }

        with patch('tradingagents.dataflows.alpaca.data.get_client') as mock_get_client:
            mock_client = Mock()
            mock_client._request.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = get_bars('AAPL', '1Hour', '2025-01-14', '2025-01-14')

            payload = json.loads(result)
            assert payload["symbol"] == "AAPL"
            assert payload["meta"]["timeframe"] == '1Hour'
            assert len(payload["records"]) == 1

    def test_get_bars_no_data(self, monkeypatch):
        """Test handling when no bars are returned."""
        monkeypatch.setenv("ALPACA_API_KEY", "test_key")
        monkeypatch.setenv("ALPACA_SECRET_KEY", "test_secret")

        with patch('tradingagents.dataflows.alpaca.data.get_client') as mock_get_client:
            mock_client = Mock()
            mock_client._request.return_value = {'bars': []}
            mock_get_client.return_value = mock_client

            result = get_bars('AAPL', '1Day', '2025-01-14', '2025-01-14')
            payload = json.loads(result)
            assert payload["records"] == []
            assert payload["meta"]["record_count"] == 0
