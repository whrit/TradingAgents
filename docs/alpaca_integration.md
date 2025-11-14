# Alpaca Trading Integration

Comprehensive integration with Alpaca Markets API for trading operations.

## Overview

The Alpaca integration provides a complete, production-ready solution for:
- Market data retrieval
- Order placement and management
- Position tracking
- Portfolio management
- Paper and live trading support

## Installation

Add required dependencies to your environment:

```bash
pip install requests python-dotenv urllib3
```

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```bash
# Paper Trading (recommended for testing)
ALPACA_API_KEY=your_paper_api_key
ALPACA_SECRET_KEY=your_paper_secret_key
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Live Trading (use with caution)
# ALPACA_API_KEY=your_live_api_key
# ALPACA_SECRET_KEY=your_live_secret_key
# ALPACA_BASE_URL=https://api.alpaca.markets
```

### Configuration Options

```python
from src.alpaca import AlpacaConfig

# Load from environment
config = AlpacaConfig.from_env_file('.env')

# Or configure explicitly
config = AlpacaConfig(
    api_key='your_key',
    secret_key='your_secret',
    paper_trading=True,
    timeout=30,
    max_retries=3
)
```

## Usage Examples

### Market Data

```python
from src.alpaca import AlpacaDataClient, AlpacaConfig

config = AlpacaConfig.from_env_file('.env')

with AlpacaDataClient(config) as data_client:
    # Get latest quote
    quote = data_client.get_latest_quote('AAPL')
    print(f"Bid: {quote['bid']}, Ask: {quote['ask']}")

    # Get historical bars
    bars = data_client.get_bars(
        'AAPL',
        timeframe='1Day',
        start='2025-01-01',
        limit=100
    )

    # Get market snapshot
    snapshot = data_client.get_snapshot('AAPL')
    print(f"Latest price: {snapshot['latestTrade']['price']}")

    # Get multiple snapshots
    snapshots = data_client.get_snapshots(['AAPL', 'GOOGL', 'MSFT'])
```

### Trading Operations

```python
from src.alpaca import AlpacaTradingClient, AlpacaConfig

config = AlpacaConfig.from_env_file('.env')

with AlpacaTradingClient(config) as trading_client:
    # Submit market order
    order = trading_client.submit_order(
        symbol='AAPL',
        qty=10,
        side='buy',
        order_type='market'
    )

    # Submit limit order
    limit_order = trading_client.submit_order(
        symbol='GOOGL',
        qty=5,
        side='sell',
        order_type='limit',
        limit_price=150.00,
        time_in_force='gtc'
    )

    # Submit stop order
    stop_order = trading_client.submit_order(
        symbol='MSFT',
        qty=20,
        side='buy',
        order_type='stop',
        stop_price=300.00
    )

    # Fractional shares
    fractional_order = trading_client.submit_order(
        symbol='AAPL',
        qty=0.5,
        side='buy',
        order_type='market'
    )
```

### Position Management

```python
from src.alpaca import AlpacaTradingClient, AlpacaConfig

config = AlpacaConfig.from_env_file('.env')

with AlpacaTradingClient(config) as trading_client:
    # Get all positions
    positions = trading_client.get_positions()
    for position in positions:
        print(f"{position['symbol']}: {position['qty']} shares")

    # Get specific position
    aapl_position = trading_client.get_position('AAPL')
    print(f"AAPL average entry: ${aapl_position['avg_entry_price']}")

    # Close position partially
    trading_client.close_position('AAPL', qty=5)

    # Close position completely
    trading_client.close_position('GOOGL')

    # Close all positions
    trading_client.close_all_positions()
```

### Account Information

```python
from src.alpaca import AlpacaTradingClient, AlpacaConfig

config = AlpacaConfig.from_env_file('.env')

with AlpacaTradingClient(config) as trading_client:
    account = trading_client.get_account()

    print(f"Portfolio value: ${account['portfolio_value']}")
    print(f"Cash: ${account['cash']}")
    print(f"Buying power: ${account['buying_power']}")
    print(f"Pattern day trader: {account['pattern_day_trader']}")
```

### Order Management

```python
from src.alpaca import AlpacaTradingClient, AlpacaConfig

config = AlpacaConfig.from_env_file('.env')

with AlpacaTradingClient(config) as trading_client:
    # Get all orders
    orders = trading_client.get_orders(status='open')

    # Get specific order
    order = trading_client.get_order('order_id_here')

    # Cancel order
    trading_client.cancel_order('order_id_here')

    # Cancel all orders
    trading_client.cancel_all_orders()
```

## Error Handling

```python
from src.alpaca import (
    AlpacaTradingClient,
    AlpacaConfig,
    OrderValidationError,
    AuthenticationError,
    AlpacaAPIError
)

config = AlpacaConfig.from_env_file('.env')

try:
    with AlpacaTradingClient(config) as client:
        order = client.submit_order(
            symbol='AAPL',
            qty=10,
            side='buy',
            order_type='market'
        )
except OrderValidationError as e:
    print(f"Invalid order parameters: {e}")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except AlpacaAPIError as e:
    print(f"API error: {e} (status: {e.status_code})")
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest tests/alpaca/

# Run specific test module
pytest tests/alpaca/test_trading.py

# Run with coverage
pytest tests/alpaca/ --cov=src/alpaca --cov-report=html
```

## Security Best Practices

1. **Never hardcode credentials** - Always use environment variables
2. **Use paper trading** for testing - Switch to live only when ready
3. **Validate all inputs** - The modules include comprehensive validation
4. **Monitor your positions** - Regularly check account status
5. **Set appropriate timeouts** - Prevent hanging requests
6. **Implement proper logging** - Track all trading operations

## API Rate Limits

Alpaca enforces rate limits:
- 200 requests per minute per API key
- The client includes automatic retry logic with exponential backoff

## Module Architecture

```
src/alpaca/
├── __init__.py       # Package exports
├── config.py         # Configuration management
├── client.py         # Base API client
├── data.py          # Market data operations
└── trading.py       # Trading operations

tests/alpaca/
├── __init__.py
├── test_config.py    # Configuration tests
├── test_client.py    # Client tests
├── test_data.py      # Data module tests
└── test_trading.py   # Trading module tests
```

## Support

- Alpaca Documentation: https://alpaca.markets/docs/
- API Reference: https://alpaca.markets/docs/api-references/
- Community Forum: https://forum.alpaca.markets/

## License

This integration follows the same license as the main TradingAgents project.
