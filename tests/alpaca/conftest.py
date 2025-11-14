"""
Pytest configuration and shared fixtures for Alpaca integration tests.

This module provides shared fixtures, test utilities, and configuration
for all Alpaca-related tests (unit, integration, and E2E).
"""

import pytest
import os
import json
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta

# Test data directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"
API_RESPONSES_DIR = FIXTURES_DIR / "api_responses"
MOCK_DATA_DIR = FIXTURES_DIR / "mock_data"


# ============================================================================
# Session-level fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Provide test configuration."""
    return {
        "alpaca": {
            "base_url": "https://paper-api.alpaca.markets",
            "data_url": "https://data.alpaca.markets",
            "stream_url": "wss://stream.data.alpaca.markets",
            "api_version": "v2",
            "timeout": 30,
            "max_retries": 3,
        },
        "testing": {
            "default_symbol": "AAPL",
            "test_quantity": 1,
            "max_test_duration": 300,
        }
    }


@pytest.fixture(scope="session")
def fixtures_path() -> Path:
    """Provide path to test fixtures directory."""
    return FIXTURES_DIR


# ============================================================================
# Mock Alpaca Client fixtures
# ============================================================================

@pytest.fixture
def mock_alpaca_client():
    """Provide a mock Alpaca REST client for unit tests."""
    from tests.alpaca.utils.mock_alpaca import MockAlpacaClient
    return MockAlpacaClient()


@pytest.fixture
def mock_trading_client():
    """Provide a mock Alpaca TradingClient for unit tests."""
    client = MagicMock()

    # Mock account methods
    client.get_account.return_value = Mock(
        id="test-account-id",
        account_number="PA123456789",
        status="ACTIVE",
        currency="USD",
        buying_power="100000.00",
        cash="100000.00",
        portfolio_value="100000.00",
        pattern_day_trader=False,
        trading_blocked=False,
        transfers_blocked=False,
        account_blocked=False,
    )

    # Mock order methods
    client.submit_order.return_value = Mock(
        id="test-order-id",
        client_order_id="test-client-order-id",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        submitted_at=datetime.now(),
        filled_at=None,
        expired_at=None,
        canceled_at=None,
        failed_at=None,
        replaced_at=None,
        asset_id="test-asset-id",
        symbol="AAPL",
        asset_class="us_equity",
        qty="10",
        filled_qty="0",
        type="market",
        side="buy",
        time_in_force="day",
        limit_price=None,
        stop_price=None,
        status="accepted",
    )

    # Mock position methods
    client.get_all_positions.return_value = []
    client.close_position.return_value = Mock(status="filled")

    return client


@pytest.fixture
def mock_stock_client():
    """Provide a mock Alpaca StockHistoricalDataClient for unit tests."""
    client = MagicMock()

    # Mock bar data
    from tests.alpaca.utils.mock_alpaca import create_mock_bars
    client.get_stock_bars.return_value = create_mock_bars("AAPL", 100)

    return client


# ============================================================================
# Paper Trading fixtures (for integration tests)
# ============================================================================

@pytest.fixture
def paper_trading_credentials() -> Dict[str, str]:
    """
    Provide paper trading credentials from environment.

    Requires ALPACA_PAPER_KEY and ALPACA_PAPER_SECRET environment variables.
    """
    api_key = os.getenv("ALPACA_PAPER_KEY")
    secret_key = os.getenv("ALPACA_PAPER_SECRET")

    if not api_key or not secret_key:
        pytest.skip("Paper trading credentials not available")

    return {
        "api_key": api_key,
        "secret_key": secret_key,
    }


@pytest.fixture
def paper_trading_client(paper_trading_credentials):
    """
    Provide real Alpaca TradingClient connected to paper trading.

    Only available for integration tests when credentials are set.
    """
    try:
        from alpaca.trading.client import TradingClient

        client = TradingClient(
            api_key=paper_trading_credentials["api_key"],
            secret_key=paper_trading_credentials["secret_key"],
            paper=True,
        )

        # Verify connection
        client.get_account()

        return client
    except ImportError:
        pytest.skip("alpaca-py package not installed")
    except Exception as e:
        pytest.skip(f"Failed to connect to paper trading: {e}")


@pytest.fixture
def paper_stock_client(paper_trading_credentials):
    """
    Provide real Alpaca StockHistoricalDataClient for integration tests.

    Only available when credentials are set.
    """
    try:
        from alpaca.data.historical import StockHistoricalDataClient

        client = StockHistoricalDataClient(
            api_key=paper_trading_credentials["api_key"],
            secret_key=paper_trading_credentials["secret_key"],
        )

        return client
    except ImportError:
        pytest.skip("alpaca-py package not installed")


# ============================================================================
# Test data fixtures
# ============================================================================

@pytest.fixture
def sample_account_data() -> Dict[str, Any]:
    """Load sample account data from fixtures."""
    file_path = API_RESPONSES_DIR / "account.json"
    if file_path.exists():
        with open(file_path) as f:
            return json.load(f)

    # Fallback to inline data
    return {
        "id": "test-account-id",
        "account_number": "PA123456789",
        "status": "ACTIVE",
        "currency": "USD",
        "buying_power": "100000.00",
        "cash": "100000.00",
        "portfolio_value": "100000.00",
    }


@pytest.fixture
def sample_order_data() -> Dict[str, Any]:
    """Load sample order data from fixtures."""
    file_path = API_RESPONSES_DIR / "orders.json"
    if file_path.exists():
        with open(file_path) as f:
            return json.load(f)

    # Fallback to inline data
    return {
        "id": "test-order-id",
        "symbol": "AAPL",
        "qty": "10",
        "side": "buy",
        "type": "market",
        "status": "filled",
    }


@pytest.fixture
def sample_position_data() -> List[Dict[str, Any]]:
    """Load sample position data from fixtures."""
    file_path = API_RESPONSES_DIR / "positions.json"
    if file_path.exists():
        with open(file_path) as f:
            return json.load(f)

    # Fallback to inline data
    return [
        {
            "symbol": "AAPL",
            "qty": "10",
            "avg_entry_price": "150.00",
            "current_price": "155.00",
            "market_value": "1550.00",
            "unrealized_pl": "50.00",
        }
    ]


@pytest.fixture
def sample_bars_data() -> Dict[str, Any]:
    """Load sample bar data from fixtures."""
    file_path = API_RESPONSES_DIR / "bars.json"
    if file_path.exists():
        with open(file_path) as f:
            return json.load(f)

    # Fallback to inline data
    return {
        "bars": [
            {
                "t": "2024-11-14T09:30:00Z",
                "o": 150.0,
                "h": 151.0,
                "l": 149.5,
                "c": 150.5,
                "v": 1000000,
            }
        ]
    }


# ============================================================================
# Cleanup fixtures
# ============================================================================

@pytest.fixture
def cleanup_test_orders(paper_trading_client):
    """
    Cleanup fixture that cancels all open test orders after integration tests.
    """
    yield

    if paper_trading_client:
        try:
            # Cancel all open orders
            orders = paper_trading_client.get_orders(status="open")
            for order in orders:
                if order.client_order_id and "test" in order.client_order_id.lower():
                    paper_trading_client.cancel_order(order.id)
        except Exception as e:
            print(f"Warning: Failed to cleanup test orders: {e}")


@pytest.fixture
def cleanup_test_positions(paper_trading_client):
    """
    Cleanup fixture that closes all test positions after integration tests.
    """
    yield

    if paper_trading_client:
        try:
            # Close all positions (in paper trading only)
            paper_trading_client.close_all_positions(cancel_orders=True)
        except Exception as e:
            print(f"Warning: Failed to cleanup test positions: {e}")


# ============================================================================
# Helper fixtures
# ============================================================================

@pytest.fixture
def mock_datetime():
    """Provide a freezegun mock for datetime manipulation."""
    try:
        from freezegun import freeze_time
        return freeze_time
    except ImportError:
        pytest.skip("freezegun not installed")


@pytest.fixture
def http_mock():
    """Provide responses mock for HTTP requests."""
    try:
        import responses
        with responses.RequestsMock() as rsps:
            yield rsps
    except ImportError:
        pytest.skip("responses package not installed")


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary configuration file for testing."""
    config_file = tmp_path / "test_config.json"
    config_data = {
        "alpaca": {
            "api_key": "test_key",
            "secret_key": "test_secret",
            "paper": True,
        }
    }
    with open(config_file, "w") as f:
        json.dump(config_data, f)

    return config_file


# ============================================================================
# Pytest hooks
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Register custom markers
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (requires API)"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests (complete workflows)"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Auto-mark tests based on path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
