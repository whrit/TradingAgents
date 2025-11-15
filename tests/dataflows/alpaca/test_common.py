"""
TDD Tests for Alpaca Common Module (Authentication & Client).

SPECIFICATION (Tests Define Implementation):
============================================
The Alpaca common module MUST:
1. Provide get_alpaca_credentials() to retrieve API keys from environment
2. Raise clear errors when credentials are missing
3. Provide AlpacaDataClient class for API communication
4. Handle authentication errors (401)
5. Handle rate limiting (429) with retry logic
6. Support request retries for transient failures
7. Provide singleton client instance via get_client()
8. Clean up resources properly
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
import requests
from requests.exceptions import Timeout, ConnectionError as RequestsConnectionError


class TestAlpacaCredentials:
    """
    TDD: Test credential retrieval from environment.

    SPECIFICATION:
    - get_alpaca_credentials() returns (api_key, secret_key) tuple
    - Must read from ALPACA_API_KEY and ALPACA_SECRET_KEY env vars
    - Must raise ValueError if either is missing
    - Error messages must be clear and actionable
    """

    def test_get_credentials_function_exists(self):
        """Test that get_alpaca_credentials function exists."""
        from tradingagents.dataflows.alpaca.common import get_alpaca_credentials
        assert callable(get_alpaca_credentials)

    def test_get_credentials_returns_tuple(self):
        """Test that get_alpaca_credentials returns (api_key, secret_key) tuple."""
        from tradingagents.dataflows.alpaca.common import get_alpaca_credentials

        with patch.dict(os.environ, {
            'ALPACA_API_KEY': 'test_key_123',
            'ALPACA_SECRET_KEY': 'test_secret_456'
        }):
            result = get_alpaca_credentials()

            assert isinstance(result, tuple)
            assert len(result) == 2
            assert result[0] == 'test_key_123'
            assert result[1] == 'test_secret_456'

    def test_missing_api_key_raises_error(self):
        """Test that missing ALPACA_API_KEY raises ValueError."""
        from tradingagents.dataflows.alpaca.common import get_alpaca_credentials

        with patch.dict(os.environ, {'ALPACA_SECRET_KEY': 'secret'}, clear=True):
            with pytest.raises(ValueError, match="ALPACA_API_KEY"):
                get_alpaca_credentials()

    def test_missing_secret_key_raises_error(self):
        """Test that missing ALPACA_SECRET_KEY raises ValueError."""
        from tradingagents.dataflows.alpaca.common import get_alpaca_credentials

        with patch.dict(os.environ, {'ALPACA_API_KEY': 'key'}, clear=True):
            with pytest.raises(ValueError, match="ALPACA_SECRET_KEY"):
                get_alpaca_credentials()

    def test_falls_back_to_paper_credentials(self, monkeypatch):
        """Test fallback to ALPACA_PAPER_* environment variables."""
        from tradingagents.dataflows.alpaca.common import get_alpaca_credentials

        monkeypatch.delenv('ALPACA_API_KEY', raising=False)
        monkeypatch.delenv('ALPACA_SECRET_KEY', raising=False)
        monkeypatch.setenv('ALPACA_PAPER_API_KEY', 'paper_key')
        monkeypatch.setenv('ALPACA_PAPER_SECRET_KEY', 'paper_secret')

        api_key, secret = get_alpaca_credentials()
        assert api_key == 'paper_key'
        assert secret == 'paper_secret'

    def test_falls_back_to_config_credentials(self, monkeypatch):
        """Test fallback to config values when no environment variables set."""
        from tradingagents.dataflows.alpaca import common

        monkeypatch.delenv('ALPACA_API_KEY', raising=False)
        monkeypatch.delenv('ALPACA_SECRET_KEY', raising=False)
        monkeypatch.delenv('ALPACA_PAPER_API_KEY', raising=False)
        monkeypatch.delenv('ALPACA_PAPER_SECRET_KEY', raising=False)
        monkeypatch.delenv('ALPACA_LIVE_API_KEY', raising=False)
        monkeypatch.delenv('ALPACA_LIVE_SECRET_KEY', raising=False)

        with patch('tradingagents.dataflows.alpaca.common.get_config') as mock_config:
            mock_config.return_value = {
                "alpaca_paper_api_key": "cfg_paper",
                "alpaca_paper_secret_key": "cfg_secret",
                "alpaca_live_api_key": None,
                "alpaca_live_secret_key": None,
            }
            api_key, secret = common.get_alpaca_credentials()

        assert api_key == "cfg_paper"
        assert secret == "cfg_secret"

    def test_both_credentials_missing_raises_error(self):
        """Test that both missing credentials raises error."""
        from tradingagents.dataflows.alpaca.common import get_alpaca_credentials

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                get_alpaca_credentials()


class TestAlpacaAPIErrors:
    """
    TDD: Test custom exception classes.

    SPECIFICATION:
    - AlpacaAPIError: Base exception with status_code attribute
    - AlpacaRateLimitError: Subclass for rate limiting (429)
    - AlpacaAuthenticationError: Subclass for auth failures (401)
    """

    def test_alpaca_api_error_exists(self):
        """Test that AlpacaAPIError exception class exists."""
        from tradingagents.dataflows.alpaca.common import AlpacaAPIError
        assert issubclass(AlpacaAPIError, Exception)

    def test_alpaca_api_error_has_status_code(self):
        """Test that AlpacaAPIError stores status_code."""
        from tradingagents.dataflows.alpaca.common import AlpacaAPIError

        error = AlpacaAPIError("Test error", status_code=500)
        assert error.status_code == 500
        assert str(error) == "Test error"

    def test_rate_limit_error_exists(self):
        """Test that AlpacaRateLimitError exists and is subclass of AlpacaAPIError."""
        from tradingagents.dataflows.alpaca.common import AlpacaRateLimitError, AlpacaAPIError
        assert issubclass(AlpacaRateLimitError, AlpacaAPIError)

    def test_authentication_error_exists(self):
        """Test that AlpacaAuthenticationError exists and is subclass of AlpacaAPIError."""
        from tradingagents.dataflows.alpaca.common import AlpacaAuthenticationError, AlpacaAPIError
        assert issubclass(AlpacaAuthenticationError, AlpacaAPIError)


class TestAlpacaDataClient:
    """
    TDD: Test AlpacaDataClient initialization and configuration.

    SPECIFICATION:
    - AlpacaDataClient class for API communication
    - Constructor accepts api_key and secret_key (optional)
    - Falls back to environment variables if not provided
    - Creates requests.Session with retry configuration
    - Uses correct base URL for data API
    """

    def test_client_class_exists(self):
        """Test that AlpacaDataClient class exists."""
        from tradingagents.dataflows.alpaca.common import AlpacaDataClient
        assert isinstance(AlpacaDataClient, type)

    def test_client_initialization_with_credentials(self):
        """Test client initialization with explicit credentials."""
        from tradingagents.dataflows.alpaca.common import AlpacaDataClient

        client = AlpacaDataClient(api_key='test_key', secret_key='test_secret')

        assert client.api_key == 'test_key'
        assert client.secret_key == 'test_secret'
        assert hasattr(client, 'session')

    def test_client_initialization_from_environment(self):
        """Test client initialization from environment variables."""
        from tradingagents.dataflows.alpaca.common import AlpacaDataClient

        with patch.dict(os.environ, {
            'ALPACA_API_KEY': 'env_key',
            'ALPACA_SECRET_KEY': 'env_secret'
        }):
            client = AlpacaDataClient()

            assert client.api_key == 'env_key'
            assert client.secret_key == 'env_secret'

    def test_client_has_correct_base_url(self):
        """Test that client uses correct Alpaca data API URL."""
        from tradingagents.dataflows.alpaca.common import AlpacaDataClient

        with patch.dict(os.environ, {
            'ALPACA_API_KEY': 'key',
            'ALPACA_SECRET_KEY': 'secret'
        }):
            client = AlpacaDataClient()

            assert client.data_url == "https://data.alpaca.markets"

    def test_client_creates_session_with_retries(self):
        """Test that client creates session with retry configuration."""
        from tradingagents.dataflows.alpaca.common import AlpacaDataClient

        with patch.dict(os.environ, {
            'ALPACA_API_KEY': 'key',
            'ALPACA_SECRET_KEY': 'secret'
        }):
            client = AlpacaDataClient()

            assert isinstance(client.session, requests.Session)
            # Verify adapters are configured
            assert 'https://' in client.session.adapters


class TestAlpacaDataClientRequests:
    """
    TDD: Test AlpacaDataClient HTTP request handling.

    SPECIFICATION:
    - _request(method, endpoint, params) executes HTTP requests
    - Adds authentication headers to all requests
    - Handles 200 OK responses
    - Raises AlpacaAuthenticationError for 401
    - Raises AlpacaRateLimitError for 429
    - Raises AlpacaAPIError for other errors
    - Handles network timeouts
    """

    def test_request_method_exists(self):
        """Test that _request method exists."""
        from tradingagents.dataflows.alpaca.common import AlpacaDataClient

        with patch.dict(os.environ, {
            'ALPACA_API_KEY': 'key',
            'ALPACA_SECRET_KEY': 'secret'
        }):
            client = AlpacaDataClient()
            assert hasattr(client, '_request')
            assert callable(client._request)

    def test_request_includes_auth_headers(self):
        """Test that requests include authentication headers."""
        from tradingagents.dataflows.alpaca.common import AlpacaDataClient

        with patch.dict(os.environ, {
            'ALPACA_API_KEY': 'test_key',
            'ALPACA_SECRET_KEY': 'test_secret'
        }):
            client = AlpacaDataClient()

            with patch.object(client.session, 'request') as mock_request:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {'data': 'test'}
                mock_response.content = b'{"data": "test"}'
                mock_request.return_value = mock_response

                client._request('GET', '/test')

                # Verify auth headers were included
                call_kwargs = mock_request.call_args[1]
                headers = call_kwargs['headers']
                assert 'APCA-API-KEY-ID' in headers
                assert headers['APCA-API-KEY-ID'] == 'test_key'
                assert 'APCA-API-SECRET-KEY' in headers
                assert headers['APCA-API-SECRET-KEY'] == 'test_secret'

    def test_successful_request_returns_json(self):
        """Test that successful requests return JSON data."""
        from tradingagents.dataflows.alpaca.common import AlpacaDataClient

        with patch.dict(os.environ, {
            'ALPACA_API_KEY': 'key',
            'ALPACA_SECRET_KEY': 'secret'
        }):
            client = AlpacaDataClient()

            with patch.object(client.session, 'request') as mock_request:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {'bars': [{'t': '2025-01-14'}]}
                mock_response.content = b'{"bars": []}'
                mock_request.return_value = mock_response

                result = client._request('GET', '/v2/stocks/AAPL/bars')

                assert 'bars' in result

    def test_401_raises_authentication_error(self):
        """Test that 401 response raises AlpacaAuthenticationError."""
        from tradingagents.dataflows.alpaca.common import (
            AlpacaDataClient,
            AlpacaAuthenticationError
        )

        with patch.dict(os.environ, {
            'ALPACA_API_KEY': 'invalid_key',
            'ALPACA_SECRET_KEY': 'invalid_secret'
        }):
            client = AlpacaDataClient()

            with patch.object(client.session, 'request') as mock_request:
                mock_response = Mock()
                mock_response.status_code = 401
                mock_response.content = b'{"message": "Unauthorized"}'
                mock_response.json.return_value = {'message': 'Unauthorized'}
                mock_request.return_value = mock_response

                with pytest.raises(AlpacaAuthenticationError, match="Authentication failed"):
                    client._request('GET', '/v2/stocks/AAPL/bars')

    def test_429_raises_rate_limit_error(self):
        """Test that 429 response raises AlpacaRateLimitError."""
        from tradingagents.dataflows.alpaca.common import (
            AlpacaDataClient,
            AlpacaRateLimitError
        )

        with patch.dict(os.environ, {
            'ALPACA_API_KEY': 'key',
            'ALPACA_SECRET_KEY': 'secret'
        }):
            client = AlpacaDataClient()

            with patch.object(client.session, 'request') as mock_request:
                mock_response = Mock()
                mock_response.status_code = 429
                mock_response.headers = {'Retry-After': '60'}
                mock_response.content = b''
                mock_request.return_value = mock_response

                with pytest.raises(AlpacaRateLimitError, match="Rate limit exceeded"):
                    client._request('GET', '/v2/stocks/AAPL/bars')

    def test_timeout_raises_api_error(self):
        """Test that request timeout raises AlpacaAPIError."""
        from tradingagents.dataflows.alpaca.common import (
            AlpacaDataClient,
            AlpacaAPIError
        )

        with patch.dict(os.environ, {
            'ALPACA_API_KEY': 'key',
            'ALPACA_SECRET_KEY': 'secret'
        }):
            client = AlpacaDataClient()

            with patch.object(client.session, 'request') as mock_request:
                mock_request.side_effect = Timeout("Request timeout")

                with pytest.raises(AlpacaAPIError, match="timeout"):
                    client._request('GET', '/v2/stocks/AAPL/bars')

    def test_connection_error_raises_api_error(self):
        """Test that connection error raises AlpacaAPIError."""
        from tradingagents.dataflows.alpaca.common import (
            AlpacaDataClient,
            AlpacaAPIError
        )

        with patch.dict(os.environ, {
            'ALPACA_API_KEY': 'key',
            'ALPACA_SECRET_KEY': 'secret'
        }):
            client = AlpacaDataClient()

            with patch.object(client.session, 'request') as mock_request:
                mock_request.side_effect = RequestsConnectionError("Connection failed")

                with pytest.raises(AlpacaAPIError, match="Request failed"):
                    client._request('GET', '/v2/stocks/AAPL/bars')


class TestAlpacaClientSingleton:
    """
    TDD: Test singleton client pattern.

    SPECIFICATION:
    - get_client() returns singleton AlpacaDataClient instance
    - Multiple calls return same instance (for connection reuse)
    - Instance is created lazily on first call
    """

    def test_get_client_function_exists(self):
        """Test that get_client function exists."""
        from tradingagents.dataflows.alpaca.common import get_client
        assert callable(get_client)

    def test_get_client_returns_client_instance(self):
        """Test that get_client returns AlpacaDataClient instance."""
        from tradingagents.dataflows.alpaca.common import get_client, AlpacaDataClient

        with patch.dict(os.environ, {
            'ALPACA_API_KEY': 'key',
            'ALPACA_SECRET_KEY': 'secret'
        }):
            client = get_client()
            assert isinstance(client, AlpacaDataClient)

    def test_get_client_returns_same_instance(self):
        """Test that get_client returns singleton instance."""
        from tradingagents.dataflows.alpaca.common import get_client

        with patch.dict(os.environ, {
            'ALPACA_API_KEY': 'key',
            'ALPACA_SECRET_KEY': 'secret'
        }):
            # Reset singleton for test
            import tradingagents.dataflows.alpaca.common as common_module
            common_module._client_instance = None

            client1 = get_client()
            client2 = get_client()

            assert client1 is client2


class TestAlpacaClientCleanup:
    """
    TDD: Test resource cleanup.

    SPECIFICATION:
    - Client should have close() method
    - close() should cleanup session resources
    - Should handle cleanup gracefully even if called multiple times
    """

    def test_client_has_close_method(self):
        """Test that client has close method."""
        from tradingagents.dataflows.alpaca.common import AlpacaDataClient

        with patch.dict(os.environ, {
            'ALPACA_API_KEY': 'key',
            'ALPACA_SECRET_KEY': 'secret'
        }):
            client = AlpacaDataClient()
            assert hasattr(client, 'close')
            assert callable(client.close)

    def test_close_cleans_up_session(self):
        """Test that close method cleans up session."""
        from tradingagents.dataflows.alpaca.common import AlpacaDataClient

        with patch.dict(os.environ, {
            'ALPACA_API_KEY': 'key',
            'ALPACA_SECRET_KEY': 'secret'
        }):
            client = AlpacaDataClient()

            with patch.object(client.session, 'close') as mock_close:
                client.close()
                mock_close.assert_called_once()


# Test markers
pytestmark = [
    pytest.mark.dataflow,
    pytest.mark.alpaca,
    pytest.mark.unit
]
