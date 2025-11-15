"""
Pytest configuration and shared fixtures for TradingAgents tests.

This file provides:
- Common fixtures for mocking API clients
- Test data fixtures
- Configuration helpers
- Markers for test organization
"""

import pytest
import os
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock
from typing import Dict, Any


# ============================================================================
# Test Markers
# ============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests that don't require external services"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests that may require external services"
    )
    config.addinivalue_line(
        "markers", "dataflow: Tests for data vendor layer"
    )
    config.addinivalue_line(
        "markers", "broker: Tests for broker layer"
    )
    config.addinivalue_line(
        "markers", "alpaca: Tests specific to Alpaca integration"
    )
    config.addinivalue_line(
        "markers", "agents: Tests for agent tools and utilities"
    )
    config.addinivalue_line(
        "markers", "tools: Tests for LangChain tool implementations"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take more than 1 second"
    )


# ============================================================================
# Environment Fixtures
# ============================================================================

@pytest.fixture
def mock_alpaca_credentials(monkeypatch):
    """Provide mock Alpaca credentials in environment."""
    monkeypatch.setenv('ALPACA_API_KEY', 'test_api_key_123')
    monkeypatch.setenv('ALPACA_SECRET_KEY', 'test_secret_key_456')
    yield {
        'api_key': 'test_api_key_123',
        'secret_key': 'test_secret_key_456'
    }


@pytest.fixture
def mock_env_clean(monkeypatch):
    """Provide clean environment without credentials."""
    # Remove all Alpaca-related env vars
    for key in list(os.environ.keys()):
        if key.startswith('ALPACA_'):
            monkeypatch.delenv(key, raising=False)
    yield


# ============================================================================
# Data Fixtures
# ============================================================================

@pytest.fixture
def fixture_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "dataflows" / "alpaca" / "fixtures"


@pytest.fixture
def sample_order_data(fixture_dir):
    """Load sample order JSON fixture."""
    with open(fixture_dir / "sample_order.json") as f:
        return json.load(f)


@pytest.fixture
def sample_positions_data(fixture_dir):
    """Load sample positions JSON fixture."""
    with open(fixture_dir / "sample_positions.json") as f:
        return json.load(f)


@pytest.fixture
def sample_account_data(fixture_dir):
    """Load sample account JSON fixture."""
    with open(fixture_dir / "sample_account.json") as f:
        return json.load(f)


# ============================================================================
# Mock Client Fixtures
# ============================================================================

@pytest.fixture
def mock_alpaca_data_client():
    """Provide mock AlpacaDataClient."""
    client = MagicMock()
    client.api_key = 'test_api_key'
    client.secret_key = 'test_secret_key'
    client.data_url = 'https://data.alpaca.markets'

    # Mock successful response
    def mock_request(method, endpoint, params=None):
        return {
            'bars': [
                {
                    't': '2025-01-14T09:30:00Z',
                    'o': 150.00,
                    'h': 152.00,
                    'l': 149.00,
                    'c': 151.00,
                    'v': 1000000
                }
            ]
        }

    client._request = Mock(side_effect=mock_request)
    client.close = Mock()

    return client


@pytest.fixture
def mock_trading_client():
    """Provide mock Alpaca TradingClient."""
    client = MagicMock()

    # Mock order submission
    def mock_submit_order(*args, **kwargs):
        order = MagicMock()
        order.id = 'test-order-123'
        order.symbol = kwargs.get('symbol', 'AAPL')
        order.qty = kwargs.get('qty', 10)
        order.side = kwargs.get('side', 'buy')
        order.type = kwargs.get('order_type', 'market')
        order.status = 'accepted'
        return order

    client.submit_order = Mock(side_effect=mock_submit_order)

    # Mock get positions
    def mock_get_positions():
        position = MagicMock()
        position.symbol = 'AAPL'
        position.qty = 10
        position.current_price = 150.00
        position.market_value = 1500.00
        position.avg_entry_price = 145.00
        position.unrealized_pl = 50.00
        return [position]

    client.get_all_positions = Mock(side_effect=mock_get_positions)

    # Mock get account
    def mock_get_account():
        account = MagicMock()
        account.cash = '10000.00'
        account.portfolio_value = '12750.00'
        account.buying_power = '20000.00'
        account.equity = '12750.00'
        account.status = 'ACTIVE'
        return account

    client.get_account = Mock(side_effect=mock_get_account)

    # Mock cancel order
    client.cancel_order_by_id = Mock(return_value=None)

    return client


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def mock_config():
    """Provide mock configuration."""
    return {
        'trading_broker': 'alpaca',
        'broker_mode': 'paper',
        'auto_execute_trades': False,
        'alpaca_paper_api_key': 'test_paper_key',
        'alpaca_paper_secret_key': 'test_paper_secret',
        'alpaca_live_api_key': 'test_live_key',
        'alpaca_live_secret_key': 'test_live_secret'
    }


# ============================================================================
# Pandas DataFrame Fixtures
# ============================================================================

@pytest.fixture
def sample_stock_dataframe():
    """Provide sample stock data DataFrame."""
    import pandas as pd
    from datetime import datetime, timedelta

    dates = pd.date_range(start='2025-01-10', end='2025-01-14', freq='D')
    data = {
        'Open': [148.50, 149.00, 150.50, 151.00, 150.00],
        'High': [150.00, 151.00, 152.50, 153.00, 152.00],
        'Low': [147.50, 148.00, 149.50, 150.00, 149.00],
        'Close': [149.50, 150.00, 151.50, 152.00, 151.00],
        'Volume': [1000000, 1100000, 1050000, 1200000, 1150000]
    }

    return pd.DataFrame(data, index=dates)


# ============================================================================
# Cleanup
# ============================================================================

@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests."""
    # Reset Alpaca data client singleton
    try:
        import tradingagents.dataflows.alpaca.common as alpaca_common
        alpaca_common._client_instance = None
    except ImportError:
        pass

    # Reset trading client singleton
    try:
        import tradingagents.brokers.alpaca.client as alpaca_client
        if hasattr(alpaca_client, '_trading_client_instance'):
            alpaca_client._trading_client_instance = None
    except ImportError:
        pass

    yield

    # Cleanup after test
    pass
