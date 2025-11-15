"""
Mock credential utilities for testing.

Provides safe mock credentials for unit tests without exposing real API keys.
"""

import os
from typing import Dict


# Mock credentials for unit tests (NOT real credentials)
MOCK_CREDENTIALS = {
    "api_key": "PK1234567890ABCDEF",
    "secret_key": "SK1234567890ABCDEF1234567890ABCDEF1234567890",
}

# Mock OAuth tokens
MOCK_OAUTH_TOKEN = "Bearer mock_oauth_token_1234567890"


def get_mock_credentials() -> Dict[str, str]:
    """
    Get mock credentials for unit tests.

    Returns:
        Dictionary with mock api_key and secret_key
    """
    return MOCK_CREDENTIALS.copy()


def get_paper_credentials() -> Dict[str, str]:
    """
    Get paper trading credentials from environment.

    Returns:
        Dictionary with real paper trading credentials

    Raises:
        ValueError: If credentials not found in environment
    """
    api_key = os.getenv("ALPACA_PAPER_KEY")
    secret_key = os.getenv("ALPACA_PAPER_SECRET")

    if not api_key or not secret_key:
        raise ValueError(
            "Paper trading credentials not found. "
            "Set ALPACA_PAPER_KEY and ALPACA_PAPER_SECRET environment variables."
        )

    return {
        "api_key": api_key,
        "secret_key": secret_key,
    }


def mock_env_credentials(monkeypatch):
    """
    Mock environment variables with test credentials.

    Args:
        monkeypatch: Pytest monkeypatch fixture

    Example:
        def test_something(monkeypatch):
            mock_env_credentials(monkeypatch)
            # Now ALPACA_API_KEY and ALPACA_SECRET_KEY are set
    """
    monkeypatch.setenv("ALPACA_API_KEY", MOCK_CREDENTIALS["api_key"])
    monkeypatch.setenv("ALPACA_SECRET_KEY", MOCK_CREDENTIALS["secret_key"])
    monkeypatch.setenv("ALPACA_PAPER", "true")


def validate_credentials(api_key: str, secret_key: str) -> bool:
    """
    Validate credential format (not authenticity).

    Args:
        api_key: API key to validate
        secret_key: Secret key to validate

    Returns:
        True if credentials have valid format
    """
    # Alpaca API keys start with "PK" or "AK"
    # Secret keys start with "SK"
    if not (api_key.startswith("PK") or api_key.startswith("AK")):
        return False

    if not secret_key.startswith("SK"):
        return False

    # Check minimum length
    if len(api_key) < 10 or len(secret_key) < 20:
        return False

    return True
