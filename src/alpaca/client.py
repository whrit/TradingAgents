"""
Alpaca API Client Module

Provides base client for API communication with authentication and error handling.
"""

import time
import logging
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import AlpacaConfig


# Set up logging
logger = logging.getLogger(__name__)


class AlpacaAPIError(Exception):
    """Base exception for Alpaca API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class AuthenticationError(AlpacaAPIError):
    """Raised when authentication fails."""
    pass


class RateLimitError(AlpacaAPIError):
    """Raised when rate limit is exceeded."""
    pass


class AlpacaClient:
    """
    Base client for Alpaca API communication.

    Handles authentication, request execution, retries, and error handling.

    Attributes:
        config: AlpacaConfig instance with API credentials
        session: Requests session with retry configuration
    """

    def __init__(self, config: AlpacaConfig):
        """
        Initialize Alpaca client.

        Args:
            config: AlpacaConfig instance
        """
        self.config = config
        self.session = self._create_session()
        logger.info(f"Initialized Alpaca client (paper_trading={config.is_paper_trading})")

    def _create_session(self) -> requests.Session:
        """
        Create requests session with retry configuration.

        Returns:
            Configured requests.Session
        """
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "DELETE", "PUT"]
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
            'APCA-API-KEY-ID': self.config.api_key,
            'APCA-API-SECRET-KEY': self.config.secret_key,
            'Content-Type': 'application/json'
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        base_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute API request with error handling.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: URL query parameters
            base_url: Override base URL

        Returns:
            dict: API response data

        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit is exceeded
            AlpacaAPIError: For other API errors
        """
        url = f"{base_url or self.config.base_url}{endpoint}"
        headers = self._get_headers()

        logger.debug(f"{method} {url}")

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=self.config.timeout
            )

            # Handle different status codes
            if response.status_code == 200:
                return response.json() if response.content else {}
            elif response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed. Check your API credentials.",
                    status_code=401,
                    response_data=response.json() if response.content else None
                )
            elif response.status_code == 429:
                retry_after = response.headers.get('Retry-After', '60')
                raise RateLimitError(
                    f"Rate limit exceeded. Retry after {retry_after} seconds.",
                    status_code=429,
                    response_data={'retry_after': retry_after}
                )
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('message', f'API error: {response.status_code}')
                raise AlpacaAPIError(
                    error_message,
                    status_code=response.status_code,
                    response_data=error_data
                )

        except requests.exceptions.Timeout:
            raise AlpacaAPIError(f"Request timeout after {self.config.timeout} seconds")
        except requests.exceptions.RequestException as e:
            raise AlpacaAPIError(f"Request failed: {str(e)}")

    def get_account(self) -> Dict[str, Any]:
        """
        Get account information.

        Returns:
            dict: Account information
        """
        return self._request('GET', '/v2/account')

    def close(self):
        """Close the session and cleanup resources."""
        if self.session:
            self.session.close()
            logger.info("Closed Alpaca client session")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
