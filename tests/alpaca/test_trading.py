"""
Unit tests for Alpaca trading module.

Tests order placement, position management, and portfolio tracking.
"""

import pytest
from unittest.mock import Mock, patch
from decimal import Decimal
from src.alpaca.trading import AlpacaTradingClient, OrderValidationError, TradingError
from src.alpaca.config import AlpacaConfig


class TestAlpacaTradingClient:
    """Test suite for AlpacaTradingClient class."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration for testing."""
        return AlpacaConfig(api_key='test_key', secret_key='test_secret', paper_trading=True)

    @pytest.fixture
    def trading_client(self, mock_config):
        """Create trading client instance for testing."""
        return AlpacaTradingClient(mock_config)

    def test_client_initialization(self, trading_client, mock_config):
        """Test trading client initialization."""
        assert trading_client.client is not None
        assert trading_client.config == mock_config

    def test_submit_market_order(self, trading_client):
        """Test submitting a market order."""
        with patch.object(trading_client.client, '_request') as mock_request:
            mock_request.return_value = {
                'id': 'order123',
                'symbol': 'AAPL',
                'qty': '10',
                'side': 'buy',
                'type': 'market',
                'status': 'pending_new'
            }
            order = trading_client.submit_order(
                symbol='AAPL',
                qty=10,
                side='buy',
                order_type='market'
            )
            assert order['id'] == 'order123'
            assert order['type'] == 'market'

    def test_submit_limit_order(self, trading_client):
        """Test submitting a limit order."""
        with patch.object(trading_client.client, '_request') as mock_request:
            mock_request.return_value = {
                'id': 'order456',
                'symbol': 'GOOGL',
                'qty': '5',
                'side': 'sell',
                'type': 'limit',
                'limit_price': '150.00',
                'status': 'pending_new'
            }
            order = trading_client.submit_order(
                symbol='GOOGL',
                qty=5,
                side='sell',
                order_type='limit',
                limit_price=150.00
            )
            assert order['type'] == 'limit'
            assert order['limit_price'] == '150.00'

    def test_submit_stop_order(self, trading_client):
        """Test submitting a stop order."""
        with patch.object(trading_client.client, '_request') as mock_request:
            mock_request.return_value = {
                'id': 'order789',
                'symbol': 'MSFT',
                'qty': '20',
                'side': 'buy',
                'type': 'stop',
                'stop_price': '300.00',
                'status': 'pending_new'
            }
            order = trading_client.submit_order(
                symbol='MSFT',
                qty=20,
                side='buy',
                order_type='stop',
                stop_price=300.00
            )
            assert order['type'] == 'stop'

    def test_limit_order_requires_limit_price(self, trading_client):
        """Test that limit orders require limit_price."""
        with pytest.raises(OrderValidationError, match="limit_price"):
            trading_client.submit_order(
                symbol='AAPL',
                qty=10,
                side='buy',
                order_type='limit'
            )

    def test_stop_order_requires_stop_price(self, trading_client):
        """Test that stop orders require stop_price."""
        with pytest.raises(OrderValidationError, match="stop_price"):
            trading_client.submit_order(
                symbol='AAPL',
                qty=10,
                side='buy',
                order_type='stop'
            )

    def test_invalid_side_raises_error(self, trading_client):
        """Test that invalid order side raises error."""
        with pytest.raises(OrderValidationError, match="side"):
            trading_client.submit_order(
                symbol='AAPL',
                qty=10,
                side='invalid',
                order_type='market'
            )

    def test_get_orders(self, trading_client):
        """Test getting all orders."""
        with patch.object(trading_client.client, '_request') as mock_request:
            mock_request.return_value = [
                {'id': 'order1', 'symbol': 'AAPL'},
                {'id': 'order2', 'symbol': 'GOOGL'}
            ]
            orders = trading_client.get_orders()
            assert len(orders) == 2

    def test_get_order_by_id(self, trading_client):
        """Test getting specific order by ID."""
        with patch.object(trading_client.client, '_request') as mock_request:
            mock_request.return_value = {
                'id': 'order123',
                'symbol': 'AAPL',
                'status': 'filled'
            }
            order = trading_client.get_order('order123')
            assert order['id'] == 'order123'

    def test_cancel_order(self, trading_client):
        """Test canceling an order."""
        with patch.object(trading_client.client, '_request') as mock_request:
            mock_request.return_value = {'id': 'order123', 'status': 'canceled'}
            result = trading_client.cancel_order('order123')
            assert result['status'] == 'canceled'

    def test_cancel_all_orders(self, trading_client):
        """Test canceling all orders."""
        with patch.object(trading_client.client, '_request') as mock_request:
            mock_request.return_value = [
                {'id': 'order1', 'status': 'canceled'},
                {'id': 'order2', 'status': 'canceled'}
            ]
            results = trading_client.cancel_all_orders()
            assert len(results) == 2

    def test_get_positions(self, trading_client):
        """Test getting all positions."""
        with patch.object(trading_client.client, '_request') as mock_request:
            mock_request.return_value = [
                {
                    'symbol': 'AAPL',
                    'qty': '10',
                    'avg_entry_price': '150.00',
                    'market_value': '1550.00'
                }
            ]
            positions = trading_client.get_positions()
            assert len(positions) == 1
            assert positions[0]['symbol'] == 'AAPL'

    def test_get_position(self, trading_client):
        """Test getting specific position."""
        with patch.object(trading_client.client, '_request') as mock_request:
            mock_request.return_value = {
                'symbol': 'AAPL',
                'qty': '10',
                'avg_entry_price': '150.00'
            }
            position = trading_client.get_position('AAPL')
            assert position['symbol'] == 'AAPL'

    def test_close_position(self, trading_client):
        """Test closing a position."""
        with patch.object(trading_client.client, '_request') as mock_request:
            mock_request.return_value = {
                'id': 'order123',
                'symbol': 'AAPL',
                'status': 'filled'
            }
            result = trading_client.close_position('AAPL')
            assert result['symbol'] == 'AAPL'

    def test_close_all_positions(self, trading_client):
        """Test closing all positions."""
        with patch.object(trading_client.client, '_request') as mock_request:
            mock_request.return_value = [
                {'symbol': 'AAPL', 'status': 'closed'},
                {'symbol': 'GOOGL', 'status': 'closed'}
            ]
            results = trading_client.close_all_positions()
            assert len(results) == 2

    def test_get_portfolio_value(self, trading_client):
        """Test getting portfolio value."""
        with patch.object(trading_client.client, 'get_account') as mock_account:
            mock_account.return_value = {
                'portfolio_value': '50000.00',
                'cash': '10000.00',
                'equity': '50000.00'
            }
            portfolio = trading_client.get_account()
            assert float(portfolio['portfolio_value']) == 50000.00

    def test_validate_quantity(self, trading_client):
        """Test quantity validation."""
        assert trading_client._validate_quantity(10) is True
        assert trading_client._validate_quantity(0.5) is True
        with pytest.raises(OrderValidationError):
            trading_client._validate_quantity(0)
        with pytest.raises(OrderValidationError):
            trading_client._validate_quantity(-5)

    def test_paper_trading_mode_indicator(self, trading_client):
        """Test that paper trading mode is correctly indicated."""
        assert trading_client.is_paper_trading() is True

    def test_fractional_shares(self, trading_client):
        """Test fractional share orders."""
        with patch.object(trading_client.client, '_request') as mock_request:
            mock_request.return_value = {
                'id': 'order999',
                'symbol': 'AAPL',
                'qty': '0.5',
                'side': 'buy',
                'type': 'market'
            }
            order = trading_client.submit_order(
                symbol='AAPL',
                qty=0.5,
                side='buy',
                order_type='market'
            )
            assert order['qty'] == '0.5'

    def test_time_in_force_options(self, trading_client):
        """Test different time-in-force options."""
        tif_options = ['day', 'gtc', 'ioc', 'fok']
        for tif in tif_options:
            with patch.object(trading_client.client, '_request') as mock_request:
                mock_request.return_value = {
                    'id': f'order_{tif}',
                    'time_in_force': tif
                }
                order = trading_client.submit_order(
                    symbol='AAPL',
                    qty=10,
                    side='buy',
                    order_type='market',
                    time_in_force=tif
                )
                assert order['time_in_force'] == tif
