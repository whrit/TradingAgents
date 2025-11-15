"""
Integration tests for Alpaca modules.

Tests end-to-end workflows combining multiple modules.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.alpaca import (
    AlpacaConfig,
    AlpacaClient,
    AlpacaDataClient,
    AlpacaTradingClient,
    ConfigurationError,
    AlpacaAPIError
)


class TestAlpacaIntegration:
    """Integration tests for Alpaca modules."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AlpacaConfig(
            api_key='test_key',
            secret_key='test_secret',
            paper_trading=True
        )

    def test_config_to_client_integration(self, config):
        """Test configuration flows to client correctly."""
        client = AlpacaClient(config)
        assert client.config == config
        assert client.session is not None
        client.close()

    def test_data_client_full_workflow(self, config):
        """Test complete data retrieval workflow."""
        data_client = AlpacaDataClient(config)

        with patch.object(data_client.client, '_request') as mock_request:
            # Mock quote data
            mock_request.return_value = {
                'symbol': 'AAPL',
                'bid': 150.00,
                'ask': 150.10
            }

            # Get quote
            quote = data_client.get_latest_quote('AAPL')
            assert quote['symbol'] == 'AAPL'

            # Mock bar data
            mock_request.return_value = {
                'bars': [{
                    'timestamp': '2025-01-14T10:00:00Z',
                    'open': 150.00,
                    'close': 150.50
                }]
            }

            # Get bars
            bars = data_client.get_bars('AAPL', timeframe='1Day')
            assert len(bars['bars']) == 1

        data_client.close()

    def test_trading_client_full_workflow(self, config):
        """Test complete trading workflow."""
        trading_client = AlpacaTradingClient(config)

        with patch.object(trading_client.client, '_request') as mock_request:
            # Submit order
            mock_request.return_value = {
                'id': 'order123',
                'symbol': 'AAPL',
                'qty': '10',
                'status': 'pending_new'
            }

            order = trading_client.submit_order(
                symbol='AAPL',
                qty=10,
                side='buy',
                order_type='market'
            )
            assert order['id'] == 'order123'

            # Get order status
            mock_request.return_value = {
                'id': 'order123',
                'status': 'filled'
            }

            order_status = trading_client.get_order('order123')
            assert order_status['status'] == 'filled'

            # Get positions
            mock_request.return_value = [{
                'symbol': 'AAPL',
                'qty': '10',
                'avg_entry_price': '150.00'
            }]

            positions = trading_client.get_positions()
            assert len(positions) == 1

        trading_client.close()

    def test_context_manager_workflow(self, config):
        """Test context manager usage."""
        with AlpacaTradingClient(config) as client:
            with patch.object(client.client, 'get_account') as mock_account:
                mock_account.return_value = {
                    'portfolio_value': '50000.00',
                    'cash': '10000.00'
                }
                account = client.get_account()
                assert float(account['portfolio_value']) == 50000.00

    def test_data_to_trading_workflow(self, config):
        """Test workflow using both data and trading clients."""
        data_client = AlpacaDataClient(config)
        trading_client = AlpacaTradingClient(config)

        with patch.object(data_client.client, '_request') as mock_data_request:
            with patch.object(trading_client.client, '_request') as mock_trading_request:
                # Get current price
                mock_data_request.return_value = {
                    'symbol': 'AAPL',
                    'price': 150.00
                }
                trade = data_client.get_latest_trade('AAPL')
                current_price = trade['price']

                # Place order based on price
                mock_trading_request.return_value = {
                    'id': 'order123',
                    'symbol': 'AAPL',
                    'type': 'limit',
                    'limit_price': str(current_price * 0.99)
                }

                order = trading_client.submit_order(
                    symbol='AAPL',
                    qty=10,
                    side='buy',
                    order_type='limit',
                    limit_price=current_price * 0.99
                )
                assert order['id'] == 'order123'

        data_client.close()
        trading_client.close()

    def test_error_propagation(self, config):
        """Test error propagation through integration."""
        trading_client = AlpacaTradingClient(config)

        with patch.object(trading_client.client, '_request') as mock_request:
            # Simulate authentication error
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.json.return_value = {'message': 'Unauthorized'}

            from src.alpaca.client import AuthenticationError

            with pytest.raises((AuthenticationError, AlpacaAPIError)):
                mock_request.side_effect = AuthenticationError(
                    "Authentication failed",
                    status_code=401
                )
                trading_client.submit_order(
                    symbol='AAPL',
                    qty=10,
                    side='buy',
                    order_type='market'
                )

        trading_client.close()

    def test_configuration_validation_workflow(self):
        """Test configuration validation in workflow."""
        # Missing credentials should raise error
        with pytest.raises(ConfigurationError):
            with patch.dict('os.environ', {}, clear=True):
                AlpacaConfig()

    def test_paper_vs_live_trading_urls(self):
        """Test URL selection for paper vs live trading."""
        paper_config = AlpacaConfig(
            api_key='key',
            secret_key='secret',
            paper_trading=True
        )
        assert 'paper' in paper_config.base_url

        live_config = AlpacaConfig(
            api_key='key',
            secret_key='secret',
            paper_trading=False
        )
        assert 'paper' not in live_config.base_url

    def test_retry_mechanism_integration(self, config):
        """Test retry mechanism in integrated workflow."""
        client = AlpacaClient(config)

        with patch.object(client.session, 'request') as mock_request:
            # First call fails, second succeeds
            mock_fail = Mock()
            mock_fail.status_code = 500
            mock_fail.json.return_value = {'message': 'Server error'}

            mock_success = Mock()
            mock_success.status_code = 200
            mock_success.json.return_value = {'data': 'success'}
            mock_success.content = b'{"data": "success"}'

            mock_request.side_effect = [mock_fail, mock_success]

            # Should succeed after retry
            result = client._request('GET', '/v2/account')
            assert result['data'] == 'success'

        client.close()

    def test_multiple_symbol_operations(self, config):
        """Test operations on multiple symbols."""
        data_client = AlpacaDataClient(config)
        symbols = ['AAPL', 'GOOGL', 'MSFT']

        with patch.object(data_client.client, '_request') as mock_request:
            mock_request.return_value = {
                symbol: {
                    'symbol': symbol,
                    'latestTrade': {'price': 100.0}
                }
                for symbol in symbols
            }

            snapshots = data_client.get_snapshots(symbols)
            assert len(snapshots) == len(symbols)

        data_client.close()

    def test_position_management_workflow(self, config):
        """Test complete position management workflow."""
        trading_client = AlpacaTradingClient(config)

        with patch.object(trading_client.client, '_request') as mock_request:
            # Open position with order
            mock_request.return_value = {
                'id': 'order123',
                'symbol': 'AAPL',
                'qty': '10',
                'status': 'filled'
            }
            order = trading_client.submit_order(
                symbol='AAPL',
                qty=10,
                side='buy',
                order_type='market'
            )

            # Check position
            mock_request.return_value = {
                'symbol': 'AAPL',
                'qty': '10',
                'avg_entry_price': '150.00',
                'market_value': '1550.00'
            }
            position = trading_client.get_position('AAPL')
            assert position['qty'] == '10'

            # Close position
            mock_request.return_value = {
                'id': 'order124',
                'symbol': 'AAPL',
                'status': 'filled'
            }
            close_result = trading_client.close_position('AAPL')
            assert close_result['status'] == 'filled'

        trading_client.close()


class TestAlpacaEdgeCases:
    """Test edge cases and error scenarios."""

    def test_empty_symbol_validation(self):
        """Test empty symbol handling."""
        config = AlpacaConfig(api_key='key', secret_key='secret')
        data_client = AlpacaDataClient(config)

        from src.alpaca.data import DataValidationError
        with pytest.raises(DataValidationError):
            data_client._validate_symbol('')

        data_client.close()

    def test_negative_quantity_validation(self):
        """Test negative quantity handling."""
        config = AlpacaConfig(api_key='key', secret_key='secret')
        trading_client = AlpacaTradingClient(config)

        from src.alpaca.trading import OrderValidationError
        with pytest.raises(OrderValidationError):
            trading_client._validate_quantity(-10)

        trading_client.close()

    def test_invalid_timeframe(self):
        """Test invalid timeframe handling."""
        config = AlpacaConfig(api_key='key', secret_key='secret')
        data_client = AlpacaDataClient(config)

        from src.alpaca.data import DataValidationError
        with pytest.raises(DataValidationError):
            data_client._validate_timeframe('InvalidTimeframe')

        data_client.close()

    def test_concurrent_client_operations(self):
        """Test multiple clients operating concurrently."""
        config = AlpacaConfig(api_key='key', secret_key='secret')

        data_client = AlpacaDataClient(config)
        trading_client = AlpacaTradingClient(config)

        # Both clients should be able to operate independently
        assert data_client.client is not None
        assert trading_client.client is not None

        data_client.close()
        trading_client.close()
