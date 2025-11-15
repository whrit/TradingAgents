"""
Unit tests for Alpaca client module.

Tests API authentication, communication, and error handling.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.alpaca.client import AlpacaClient, AlpacaAPIError, AuthenticationError
from src.alpaca.config import AlpacaConfig


class TestAlpacaClient:
    """Test suite for AlpacaClient class."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration for testing."""
        return AlpacaConfig(api_key='test_key', secret_key='test_secret', paper_trading=True)

    @pytest.fixture
    def client(self, mock_config):
        """Create client instance for testing."""
        return AlpacaClient(mock_config)

    def test_client_initialization(self, client, mock_config):
        """Test client initialization with configuration."""
        assert client.config == mock_config
        assert client.session is not None

    def test_authentication_headers(self, client):
        """Test that authentication headers are set correctly."""
        headers = client._get_headers()
        assert 'APCA-API-KEY-ID' in headers
        assert 'APCA-API-SECRET-KEY' in headers
        assert headers['APCA-API-KEY-ID'] == 'test_key'

    @patch('requests.Session.get')
    def test_get_request_success(self, mock_get, client):
        """Test successful GET request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': 'test'}
        mock_get.return_value = mock_response

        result = client._request('GET', '/v2/account')
        assert result == {'data': 'test'}

    @patch('requests.Session.post')
    def test_post_request_success(self, mock_post, client):
        """Test successful POST request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'order_id': '123'}
        mock_post.return_value = mock_response

        result = client._request('POST', '/v2/orders', data={'symbol': 'AAPL'})
        assert result == {'order_id': '123'}

    @patch('requests.Session.get')
    def test_request_with_retry(self, mock_get, client):
        """Test request retry on temporary failure."""
        mock_response_fail = Mock()
        mock_response_fail.status_code = 429
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {'data': 'test'}

        mock_get.side_effect = [mock_response_fail, mock_response_success]

        result = client._request('GET', '/v2/account')
        assert result == {'data': 'test'}
        assert mock_get.call_count == 2

    @patch('requests.Session.get')
    def test_authentication_error(self, mock_get, client):
        """Test authentication error handling."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {'message': 'Unauthorized'}
        mock_get.return_value = mock_response

        with pytest.raises(AuthenticationError):
            client._request('GET', '/v2/account')

    @patch('requests.Session.get')
    def test_api_error(self, mock_get, client):
        """Test general API error handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {'message': 'Internal error'}
        mock_get.return_value = mock_response

        with pytest.raises(AlpacaAPIError):
            client._request('GET', '/v2/account')

    def test_get_account(self, client):
        """Test get_account method."""
        with patch.object(client, '_request') as mock_request:
            mock_request.return_value = {'account_number': '123', 'cash': '10000'}
            account = client.get_account()
            mock_request.assert_called_once_with('GET', '/v2/account')
            assert account['account_number'] == '123'

    def test_close_session(self, client):
        """Test session cleanup."""
        with patch.object(client.session, 'close') as mock_close:
            client.close()
            mock_close.assert_called_once()

    def test_context_manager(self, mock_config):
        """Test client as context manager."""
        with AlpacaClient(mock_config) as client:
            assert client.session is not None
        # Session should be closed after context

    @patch('requests.Session.get')
    def test_rate_limiting(self, mock_get, client):
        """Test rate limit handling."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '1'}
        mock_get.return_value = mock_response

        with pytest.raises(AlpacaAPIError, match="Rate limit"):
            client._request('GET', '/v2/account')

    def test_timeout_configuration(self, client):
        """Test request timeout configuration."""
        assert client.config.timeout > 0
