"""
Alpaca Common Module

Shared utilities for Alpaca data vendor integration including authentication,
client setup, and error handling.
"""

import os
import logging
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class AlpacaAPIError(Exception):
    """Base exception for Alpaca API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class AlpacaRateLimitError(AlpacaAPIError):
    """Exception raised when Alpaca API rate limit is exceeded."""
    pass


class AlpacaAuthenticationError(AlpacaAPIError):
    """Exception raised when authentication fails."""
    pass


def get_alpaca_credentials() -> tuple[str, str]:
    """
    Retrieve Alpaca API credentials from environment variables.

    Returns:
        tuple: (api_key, secret_key)

    Raises:
        ValueError: If credentials are not set
    """
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")

    if not api_key:
        raise ValueError("ALPACA_API_KEY environment variable is not set.")
    if not secret_key:
        raise ValueError("ALPACA_SECRET_KEY environment variable is not set.")

    return api_key, secret_key


class AlpacaDataClient:
    """
    Client for Alpaca market data API.

    Handles authentication, request execution, retries, and error handling
    following the same pattern as alpha_vantage_common.

    Attributes:
        api_key: Alpaca API key
        secret_key: Alpaca secret key
        data_url: Base URL for data API
        session: Requests session with retry configuration
    """

    DATA_URL = "https://data.alpaca.markets"

    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None):
        """
        Initialize Alpaca data client.

        Args:
            api_key: Alpaca API key (uses env var if not provided)
            secret_key: Alpaca secret key (uses env var if not provided)
        """
        if api_key and secret_key:
            self.api_key = api_key
            self.secret_key = secret_key
        else:
            self.api_key, self.secret_key = get_alpaca_credentials()

        self.data_url = self.DATA_URL
        self.session = self._create_session()
        logger.info("Initialized Alpaca data client")

    def _create_session(self) -> requests.Session:
        """
        Create requests session with retry configuration.

        Returns:
            Configured requests.Session
        """
        session = requests.Session()

        # Configure retry strategy similar to AlpacaClient
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _get_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.

        Returns:
            dict: Headers with authentication credentials
        """
        return {
            'APCA-API-KEY-ID': self.api_key,
            'APCA-API-SECRET-KEY': self.secret_key,
            'Content-Type': 'application/json'
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Execute API request with error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: URL query parameters

        Returns:
            dict: API response data

        Raises:
            AlpacaAuthenticationError: If authentication fails
            AlpacaRateLimitError: If rate limit is exceeded
            AlpacaAPIError: For other API errors
        """
        url = f"{self.data_url}{endpoint}"
        headers = self._get_headers()

        logger.debug(f"{method} {url}")

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                headers=headers,
                timeout=30
            )

            # Handle different status codes
            if response.status_code == 200:
                return response.json() if response.content else {}
            elif response.status_code == 401:
                raise AlpacaAuthenticationError(
                    "Authentication failed. Check your API credentials.",
                    status_code=401
                )
            elif response.status_code == 429:
                retry_after = response.headers.get('Retry-After', '60')
                raise AlpacaRateLimitError(
                    f"Rate limit exceeded. Retry after {retry_after} seconds.",
                    status_code=429
                )
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('message', f'API error: {response.status_code}')
                raise AlpacaAPIError(
                    error_message,
                    status_code=response.status_code
                )

        except requests.exceptions.Timeout:
            raise AlpacaAPIError("Request timeout after 30 seconds")
        except requests.exceptions.RequestException as e:
            raise AlpacaAPIError(f"Request failed: {str(e)}")

    def close(self):
        """Close the session and cleanup resources."""
        if self.session:
            self.session.close()
            logger.info("Closed Alpaca data client session")


# Singleton instance for reuse across function calls
_client_instance: Optional[AlpacaDataClient] = None


def get_client() -> AlpacaDataClient:
    """
    Get or create singleton Alpaca data client instance.

    Returns:
        AlpacaDataClient: Configured client instance
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = AlpacaDataClient()
    return _client_instance
