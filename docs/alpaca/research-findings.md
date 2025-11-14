# Alpaca API Research Findings - TDD Implementation Guide

**Research Date:** 2025-11-14
**Researcher:** Hive Mind Research Agent
**Document Version:** 1.0
**Purpose:** Comprehensive analysis of Alpaca Python API for TDD-based trading system implementation

---

## Executive Summary

The Alpaca Python API (`alpaca-py`) provides a comprehensive interface for trading US equities and cryptocurrencies with both paper and live trading capabilities. This research identifies key integration points, authentication patterns, data models, and TDD strategies for building a robust trading system.

**Key Findings:**
- Three primary client classes: `TradingClient`, `StockHistoricalDataClient`, and `BrokerClient`
- Dual-mode authentication: Paper trading (testing) and Live trading (production)
- Rich data models with Pydantic validation for type safety
- Built-in error handling and retry mechanisms
- No explicit rate limits documented, but throttling is recommended
- WebSocket streaming support for real-time data

---

## 1. API Client Classes & Integration Points

### 1.1 TradingClient - Core Trading Operations

**Purpose:** Submit and manage orders, retrieve account information, handle positions

**Initialization:**
```python
from alpaca.trading.client import TradingClient

# Paper Trading (recommended for development/testing)
client = TradingClient(
    api_key="YOUR_API_KEY",
    secret_key="YOUR_SECRET_KEY",
    paper=True  # CRITICAL: Set to False for live trading
)

# Live Trading
client = TradingClient(
    api_key="YOUR_LIVE_API_KEY",
    secret_key="YOUR_LIVE_SECRET_KEY",
    paper=False
)
```

**Key Methods:**
- `submit_order(order_data)` - Submit buy/sell orders
- `get_all_orders()` - Retrieve all orders
- `get_order_by_id(order_id)` - Get specific order
- `cancel_order_by_id(order_id)` - Cancel an order
- `get_all_positions()` - Get current positions
- `close_position(symbol)` - Close a position
- `get_account()` - Get account information (buying power, equity, cash)

### 1.2 StockHistoricalDataClient - Market Data Retrieval

**Purpose:** Fetch historical bars, quotes, trades, and snapshots

**Initialization:**
```python
from alpaca.data.historical.stock import StockHistoricalDataClient

# Authentication optional but recommended for higher rate limits
client = StockHistoricalDataClient(
    api_key="YOUR_API_KEY",
    secret_key="YOUR_SECRET_KEY",
    # Can also work without authentication (lower limits)
)
```

**Key Methods:**
- `get_stock_bars(request_params)` - OHLCV bar data
- `get_stock_quotes(request_params)` - Bid/ask quote data
- `get_stock_trades(request_params)` - Trade tick data
- `get_stock_latest_quote(request_params)` - Most recent quote
- `get_stock_latest_trade(request_params)` - Most recent trade
- `get_stock_snapshot(request_params)` - Combined latest data

### 1.3 BrokerClient - Account Management (For Broker Applications)

**Purpose:** Create and manage brokerage accounts (primarily for broker applications, not typical traders)

**Key Methods:**
- `create_account(account_data)` - Create new account
- `get_account_by_id(account_id)` - Retrieve account details
- `get_all_positions_for_account(account_id)` - Get positions
- `submit_order_for_account(account_id, order_data)` - Submit order on behalf of account

**Note:** Most individual traders will use `TradingClient`, not `BrokerClient`

---

## 2. Authentication & Configuration

### 2.1 API Keys & Security

**Key Types:**
- **Paper Trading Keys** - For testing/development (https://paper-api.alpaca.markets)
- **Live Trading Keys** - For production trading (https://api.alpaca.markets)

**Environment Variables (Recommended Pattern):**
```python
import os

API_KEY = os.getenv('ALPACA_API_KEY')
SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
IS_PAPER = os.getenv('ALPACA_PAPER', 'true').lower() == 'true'
```

**Security Best Practices:**
1. Never hardcode credentials in source code
2. Use environment variables or secret management systems
3. Separate paper and live credentials
4. Rotate keys periodically
5. Use `.env` files locally (excluded from git)

### 2.2 Base URLs

```python
from alpaca.common.enums import BaseURL

# Paper Trading
BaseURL.TRADING_PAPER = 'https://paper-api.alpaca.markets'

# Live Trading
BaseURL.TRADING_LIVE = 'https://api.alpaca.markets'

# Market Data
BaseURL.DATA = 'https://data.alpaca.markets'

# WebSocket Streams
BaseURL.TRADING_STREAM_PAPER = 'wss://paper-api.alpaca.markets/stream'
BaseURL.TRADING_STREAM_LIVE = 'wss://api.alpaca.markets/stream'
```

---

## 3. Data Models & Schemas

### 3.1 Order Models

**Order Request Types:**
```python
from alpaca.trading.requests import (
    MarketOrderRequest,    # Execute at current market price
    LimitOrderRequest,     # Execute at specified price or better
    StopOrderRequest,      # Trigger when price reaches stop price
    StopLimitOrderRequest, # Combo of stop and limit
    TrailingStopOrderRequest # Dynamic stop based on price movement
)
from alpaca.trading.enums import OrderSide, TimeInForce

# Market Order Example
market_order = MarketOrderRequest(
    symbol="AAPL",
    qty=10,
    side=OrderSide.BUY,
    time_in_force=TimeInForce.DAY
)

# Limit Order Example
limit_order = LimitOrderRequest(
    symbol="TSLA",
    qty=5,
    side=OrderSide.SELL,
    time_in_force=TimeInForce.GTC,  # Good til cancelled
    limit_price=250.00
)
```

**Key Order Attributes:**
- `symbol` (str) - Ticker symbol
- `qty` (float) - Quantity of shares
- `notional` (float) - Dollar amount (alternative to qty)
- `side` (OrderSide) - BUY or SELL
- `type` (OrderType) - MARKET, LIMIT, STOP, STOP_LIMIT, TRAILING_STOP
- `time_in_force` (TimeInForce) - DAY, GTC, IOC, FOK, OPG, CLS
- `extended_hours` (bool) - Allow extended hours trading
- `client_order_id` (str) - Custom tracking ID

### 3.2 Account Model

```python
from alpaca.trading.models import Account

# Account attributes (after client.get_account())
account.buying_power         # Available buying power
account.cash                 # Cash balance
account.portfolio_value      # Total portfolio value
account.equity               # Current equity
account.last_equity          # Previous day's equity
account.long_market_value    # Value of long positions
account.short_market_value   # Value of short positions
account.daytrading_buying_power  # Day trading buying power
account.pattern_day_trader   # PDT status
account.trading_blocked      # Account restrictions
account.account_blocked      # Account status
```

### 3.3 Position Model

```python
from alpaca.trading.models import Position

# Position attributes
position.symbol              # Stock symbol
position.qty                 # Number of shares
position.avg_entry_price     # Average purchase price
position.current_price       # Current market price
position.market_value        # Current position value
position.cost_basis          # Total cost of position
position.unrealized_pl       # Unrealized profit/loss
position.unrealized_plpc     # Unrealized P/L percentage
position.side                # long or short
```

### 3.4 Bar (OHLCV) Model

```python
from alpaca.data.models import Bar

# Bar attributes (candle stick data)
bar.symbol                   # Ticker symbol
bar.timestamp                # Bar timestamp
bar.open                     # Opening price
bar.high                     # High price
bar.low                      # Low price
bar.close                    # Closing price
bar.volume                   # Trading volume
bar.trade_count              # Number of trades (optional)
bar.vwap                     # Volume-weighted average price (optional)
```

---

## 4. Market Data Requests

### 4.1 Historical Bar Data

```python
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime

# Request bars (OHLCV candles)
request = StockBarsRequest(
    symbol_or_symbols=["AAPL", "TSLA"],  # Single symbol or list
    timeframe=TimeFrame.Minute,  # Minute, Hour, Day, Week, Month
    start=datetime(2025, 1, 1),
    end=datetime(2025, 11, 14),
    limit=1000,  # Optional max results
    adjustment="split"  # Handle stock splits: "raw", "split", "dividend", "all"
)

bars = client.get_stock_bars(request)
# Returns BarSet - Dict[symbol, List[Bar]]
```

**Available Timeframes:**
- `TimeFrame.Minute` - 1 minute bars
- `TimeFrame.Hour` - 1 hour bars
- `TimeFrame.Day` - Daily bars
- `TimeFrame.Week` - Weekly bars
- `TimeFrame.Month` - Monthly bars
- Custom: `TimeFrame(amount, unit)` e.g., `TimeFrame(5, TimeFrameUnit.Minute)`

### 4.2 Quote Data

```python
from alpaca.data.requests import StockQuotesRequest

request = StockQuotesRequest(
    symbol_or_symbols="AAPL",
    start=datetime(2025, 11, 14, 9, 30),
    end=datetime(2025, 11, 14, 16, 0)
)

quotes = client.get_stock_quotes(request)
# Returns QuoteSet with bid/ask data
```

### 4.3 Latest Data (Snapshot)

```python
from alpaca.data.requests import StockLatestQuoteRequest

# Get most recent quote
latest_quote = client.get_stock_latest_quote(
    StockLatestQuoteRequest(symbol_or_symbols="AAPL")
)

# Get latest trade
latest_trade = client.get_stock_latest_trade(
    StockLatestTradeRequest(symbol_or_symbols="AAPL")
)

# Get comprehensive snapshot
snapshot = client.get_stock_snapshot(
    StockSnapshotRequest(symbol_or_symbols=["AAPL", "MSFT"])
)
# Includes latest trade, quote, minute bar, daily bar, previous daily bar
```

---

## 5. Real-Time Streaming (WebSocket)

### 5.1 Stock Data Stream

```python
from alpaca.data.live import StockDataStream

# Initialize stream
stream = StockDataStream(
    api_key=API_KEY,
    secret_key=SECRET_KEY,
    feed=DataFeed.IEX  # or DataFeed.SIP for premium data
)

# Define handlers
async def trade_handler(trade):
    print(f"Trade: {trade.symbol} @ ${trade.price}")

async def quote_handler(quote):
    print(f"Quote: {quote.symbol} Bid: ${quote.bid_price} Ask: ${quote.ask_price}")

# Subscribe to symbols
stream.subscribe_trades(trade_handler, "AAPL", "TSLA")
stream.subscribe_quotes(quote_handler, "AAPL")

# Run stream
stream.run()
```

### 5.2 Trading Event Stream

```python
from alpaca.trading.stream import TradingStream

stream = TradingStream(
    api_key=API_KEY,
    secret_key=SECRET_KEY,
    paper=True
)

async def trade_updates_handler(update):
    print(f"Order update: {update.event} for {update.order.symbol}")

stream.subscribe_trade_updates(trade_updates_handler)
stream.run()
```

---

## 6. Error Handling & Edge Cases

### 6.1 Common Exceptions

```python
from alpaca.common.exceptions import APIError

try:
    order = client.submit_order(order_request)
except APIError as e:
    print(f"API Error: {e.status_code} - {e}")
    # e.status_code contains HTTP status code
    # Common codes:
    # 400 - Bad Request (invalid parameters)
    # 401 - Unauthorized (invalid API keys)
    # 403 - Forbidden (account restrictions)
    # 404 - Not Found
    # 422 - Unprocessable Entity (business logic error)
    # 429 - Too Many Requests (rate limit)
    # 500 - Internal Server Error
```

### 6.2 Edge Cases to Handle

**Market Hours:**
- Regular hours: 9:30 AM - 4:00 PM ET
- Extended hours: 4:00 AM - 9:30 AM (pre-market), 4:00 PM - 8:00 PM (after-hours)
- Orders during closed hours are queued for next open
- Check market status with `client.get_clock()`

**Insufficient Buying Power:**
```python
account = client.get_account()
if float(account.buying_power) < order_cost:
    raise ValueError("Insufficient buying power")
```

**Pattern Day Trading (PDT):**
```python
account = client.get_account()
if account.pattern_day_trader:
    # Account flagged as PDT, restricted to 4 day trades per 5 days
    # Must maintain $25,000 minimum equity
    pass
```

**Symbol Not Found:**
```python
try:
    asset = client.get_asset("INVALID_SYMBOL")
except APIError as e:
    if e.status_code == 404:
        print("Symbol not found")
```

**Fractional Shares:**
- Supported for many stocks
- Use `qty` as float (e.g., 0.5 shares)
- Not all stocks support fractional trading

**Order Rejection Scenarios:**
- Insufficient funds
- Symbol not tradable
- Market closed (for DAY orders)
- Invalid price (limit price outside reasonable range)
- Position size limits exceeded
- Account restrictions (PDT, trading_blocked)

---

## 7. Rate Limits & Constraints

### 7.1 API Rate Limits

**Note:** Alpaca does not publicly document explicit rate limits in the Python SDK documentation, but general guidance:

1. **REST API:**
   - Conservative estimate: ~200 requests per minute
   - Burst allowances may apply
   - Monitor HTTP 429 responses

2. **WebSocket Streams:**
   - No hard limits documented
   - Designed for high-frequency data
   - Connection limits per account

3. **Market Data:**
   - Free tier: IEX data feed (delayed)
   - Paid tier: SIP data feed (real-time, higher limits)

### 7.2 Best Practices

```python
import time
from functools import wraps

def rate_limited(max_per_second):
    """Decorator to rate limit function calls"""
    min_interval = 1.0 / max_per_second
    last_called = [0.0]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator

@rate_limited(3)  # Max 3 calls per second
def fetch_data(symbol):
    return client.get_stock_latest_quote(symbol)
```

---

## 8. TDD Strategy Recommendations

### 8.1 Test Structure

```
tests/
├── unit/
│   ├── test_models.py          # Data model validation
│   ├── test_order_builders.py  # Order construction logic
│   └── test_calculations.py    # P/L, position sizing
├── integration/
│   ├── test_api_client.py      # API client integration (mocked)
│   ├── test_data_fetching.py   # Data retrieval patterns
│   └── test_order_placement.py # Order submission flows
└── e2e/
    ├── test_paper_trading.py   # End-to-end with paper API
    └── test_strategies.py      # Full strategy execution
```

### 8.2 Mocking Strategy

**Use `unittest.mock` or `pytest-mock`:**

```python
from unittest.mock import Mock, patch
import pytest
from alpaca.trading.client import TradingClient
from alpaca.trading.models import Account

@pytest.fixture
def mock_trading_client():
    """Mock TradingClient for testing"""
    client = Mock(spec=TradingClient)

    # Mock account data
    mock_account = Mock(spec=Account)
    mock_account.buying_power = "10000.00"
    mock_account.cash = "5000.00"
    mock_account.portfolio_value = "15000.00"

    client.get_account.return_value = mock_account
    return client

def test_check_buying_power(mock_trading_client):
    """Test buying power validation"""
    account = mock_trading_client.get_account()
    assert float(account.buying_power) >= 1000
```

### 8.3 Paper Trading Tests

```python
import os
import pytest

@pytest.fixture
def paper_client():
    """Real paper trading client for integration tests"""
    return TradingClient(
        api_key=os.getenv('ALPACA_PAPER_API_KEY'),
        secret_key=os.getenv('ALPACA_PAPER_SECRET_KEY'),
        paper=True
    )

@pytest.mark.integration
def test_submit_paper_order(paper_client):
    """Test order submission in paper trading"""
    order = MarketOrderRequest(
        symbol="AAPL",
        qty=1,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY
    )

    result = paper_client.submit_order(order)
    assert result.symbol == "AAPL"
    assert result.status in ["new", "accepted", "pending_new"]

    # Cleanup - cancel order
    paper_client.cancel_order_by_id(result.id)
```

### 8.4 Data Validation Tests

```python
from pydantic import ValidationError

def test_order_validation():
    """Test order data validation"""

    # Valid order
    order = MarketOrderRequest(
        symbol="AAPL",
        qty=10,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY
    )
    assert order.symbol == "AAPL"

    # Invalid order - should raise validation error
    with pytest.raises(ValidationError):
        invalid_order = MarketOrderRequest(
            symbol="",  # Empty symbol
            qty=-10,    # Negative quantity
            side="INVALID"  # Invalid side
        )
```

### 8.5 Test Coverage Goals

**Minimum Coverage Targets:**
- Data models: 100% (critical for data integrity)
- Order logic: 95%
- API integration: 80% (mock-based)
- Error handling: 90%
- Strategy logic: 95%

**Critical Test Cases:**
1. ✅ Order validation (valid/invalid parameters)
2. ✅ Buying power checks
3. ✅ Position sizing calculations
4. ✅ Error handling (network, API errors)
5. ✅ Market hours handling
6. ✅ PDT compliance
7. ✅ Data parsing and transformation
8. ✅ WebSocket reconnection logic
9. ✅ Rate limiting behavior
10. ✅ Credential management

---

## 9. Security Considerations

### 9.1 Credential Management

**DO:**
- ✅ Use environment variables
- ✅ Use secret management services (AWS Secrets Manager, HashiCorp Vault)
- ✅ Separate paper and live credentials
- ✅ Add `.env` to `.gitignore`
- ✅ Rotate keys periodically
- ✅ Use least privilege access

**DON'T:**
- ❌ Hardcode credentials in source code
- ❌ Commit credentials to version control
- ❌ Share credentials in plain text
- ❌ Use production keys for testing
- ❌ Log full API responses containing sensitive data

### 9.2 Example `.env` File

```bash
# .env (DO NOT COMMIT)
# Paper Trading Credentials
ALPACA_PAPER_API_KEY=PK...
ALPACA_PAPER_SECRET_KEY=...
ALPACA_PAPER=true

# Live Trading Credentials (separate environment)
ALPACA_LIVE_API_KEY=AK...
ALPACA_LIVE_SECRET_KEY=...
ALPACA_LIVE_PAPER=false
```

### 9.3 Loading Credentials

```python
from dotenv import load_dotenv
import os

load_dotenv()  # Load from .env file

class AlpacaConfig:
    """Configuration management for Alpaca API"""

    def __init__(self, environment='paper'):
        if environment == 'paper':
            self.api_key = os.getenv('ALPACA_PAPER_API_KEY')
            self.secret_key = os.getenv('ALPACA_PAPER_SECRET_KEY')
            self.is_paper = True
        elif environment == 'live':
            self.api_key = os.getenv('ALPACA_LIVE_API_KEY')
            self.secret_key = os.getenv('ALPACA_LIVE_SECRET_KEY')
            self.is_paper = False
        else:
            raise ValueError("Environment must be 'paper' or 'live'")

        # Validate credentials loaded
        if not self.api_key or not self.secret_key:
            raise ValueError(f"Missing credentials for {environment} environment")

    def get_client(self):
        """Get authenticated TradingClient"""
        return TradingClient(
            api_key=self.api_key,
            secret_key=self.secret_key,
            paper=self.is_paper
        )
```

---

## 10. Recommended Project Structure

```
trading_system/
├── src/
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── trading_client.py      # TradingClient wrapper
│   │   └── data_client.py         # DataClient wrapper
│   ├── models/
│   │   ├── __init__.py
│   │   ├── order.py               # Order models/builders
│   │   ├── position.py            # Position management
│   │   └── account.py             # Account models
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── base_strategy.py       # Abstract base class
│   │   └── example_strategy.py    # Concrete strategy
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py              # Configuration management
│   │   ├── validators.py          # Input validation
│   │   └── helpers.py             # Utility functions
│   └── main.py                    # Entry point
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── config/
│   ├── .env.example               # Example credentials
│   └── logging_config.yaml        # Logging configuration
├── docs/
│   └── alpaca/
│       └── research-findings.md   # This document
├── requirements.txt
├── setup.py
└── README.md
```

---

## 11. Next Steps for Implementation

### Phase 1: Foundation (Week 1)
1. ✅ Set up project structure
2. ✅ Configure authentication (paper trading)
3. ✅ Write unit tests for data models
4. ✅ Implement configuration management
5. ✅ Set up logging framework

### Phase 2: Core Functionality (Week 2)
1. ✅ Implement TradingClient wrapper with error handling
2. ✅ Create order builders with validation
3. ✅ Write integration tests (mocked)
4. ✅ Implement position tracking
5. ✅ Add account monitoring

### Phase 3: Data Integration (Week 3)
1. ✅ Implement DataClient wrapper
2. ✅ Create bar data fetching utilities
3. ✅ Add data caching layer
4. ✅ Write data validation tests
5. ✅ Implement WebSocket stream handlers

### Phase 4: Strategy Development (Week 4)
1. ✅ Design base strategy interface
2. ✅ Implement example strategy
3. ✅ Add backtesting framework
4. ✅ Create strategy unit tests
5. ✅ Test end-to-end with paper trading

### Phase 5: Production Readiness (Week 5)
1. ✅ Performance optimization
2. ✅ Comprehensive error handling
3. ✅ Production logging and monitoring
4. ✅ Security audit
5. ✅ Live trading preparation (review only, don't enable)

---

## 12. Critical Warnings & Gotchas

⚠️ **CRITICAL WARNINGS:**

1. **Paper vs Live Flag:**
   - ALWAYS verify `paper=True` in development
   - Double-check before any production deployment
   - Use environment-based configuration to prevent mistakes

2. **Pattern Day Trading Rules:**
   - Accounts < $25,000 limited to 3 day trades per 5 business days
   - Exceeding limits can freeze account for 90 days
   - Monitor `account.pattern_day_trader` status

3. **Market Hours:**
   - Orders submitted outside hours are queued
   - Extended hours have lower liquidity
   - Use `client.get_clock()` to check market status

4. **Error Handling:**
   - ALWAYS wrap API calls in try/except
   - Handle network failures gracefully
   - Implement retry logic for transient errors

5. **Data Latency:**
   - IEX data is real-time but may have slight delays
   - SIP data (premium) is consolidated and faster
   - WebSocket streams are near real-time

6. **Order Fill Guarantees:**
   - Market orders are NOT guaranteed to fill at last price
   - Slippage can occur, especially for large orders
   - Use limit orders for price control

---

## 13. Additional Resources

**Official Documentation:**
- Alpaca API Docs: https://docs.alpaca.markets/
- Python SDK GitHub: https://github.com/alpacahq/alpaca-py
- Trading API Reference: https://docs.alpaca.markets/reference/trading-api
- Market Data API: https://docs.alpaca.markets/reference/market-data-api

**Community Resources:**
- Alpaca Community Forum: https://forum.alpaca.markets/
- Discord Server: https://alpaca.markets/discord
- YouTube Channel: https://www.youtube.com/alpacamarkets

**Testing:**
- Paper Trading Dashboard: https://app.alpaca.markets/paper/dashboard
- API Keys Management: https://app.alpaca.markets/account/keys

---

## 14. Summary of Key API Endpoints

| Endpoint Category | Key Methods | Purpose |
|-------------------|-------------|---------|
| **Account** | `get_account()` | Get account info (buying power, equity) |
| **Orders** | `submit_order()`, `get_all_orders()`, `cancel_order_by_id()` | Order management |
| **Positions** | `get_all_positions()`, `close_position()` | Position tracking |
| **Market Data (Bars)** | `get_stock_bars()` | Historical OHLCV data |
| **Market Data (Latest)** | `get_stock_latest_quote()`, `get_stock_latest_trade()` | Real-time quotes/trades |
| **Streaming** | `StockDataStream`, `TradingStream` | WebSocket real-time data |
| **Assets** | `get_all_assets()`, `get_asset()` | Asset information |
| **Clock** | `get_clock()` | Market hours/status |
| **Calendar** | `get_calendar()` | Trading calendar (holidays) |

---

## 15. Appendix: Code Examples

### Example: Complete Trading Workflow

```python
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.common.exceptions import APIError
import os

# Initialize client
client = TradingClient(
    api_key=os.getenv('ALPACA_API_KEY'),
    secret_key=os.getenv('ALPACA_SECRET_KEY'),
    paper=True
)

def execute_trade_workflow(symbol, quantity):
    """Complete trade execution with validation"""

    try:
        # 1. Check market status
        clock = client.get_clock()
        if not clock.is_open:
            print("Market is closed. Order will be queued.")

        # 2. Check account buying power
        account = client.get_account()
        print(f"Buying Power: ${account.buying_power}")

        # 3. Get current price estimate
        from alpaca.data.historical import StockHistoricalDataClient
        data_client = StockHistoricalDataClient(
            api_key=os.getenv('ALPACA_API_KEY'),
            secret_key=os.getenv('ALPACA_SECRET_KEY')
        )

        snapshot = data_client.get_stock_snapshot(
            StockSnapshotRequest(symbol_or_symbols=symbol)
        )
        latest_price = snapshot[symbol].latest_trade.price
        estimated_cost = latest_price * quantity

        print(f"Latest Price: ${latest_price}")
        print(f"Estimated Cost: ${estimated_cost}")

        # 4. Validate buying power
        if float(account.buying_power) < estimated_cost:
            raise ValueError("Insufficient buying power")

        # 5. Submit order
        order = MarketOrderRequest(
            symbol=symbol,
            qty=quantity,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY
        )

        submitted_order = client.submit_order(order)
        print(f"Order submitted: {submitted_order.id}")
        print(f"Status: {submitted_order.status}")

        # 6. Monitor order status
        import time
        for _ in range(10):  # Check for up to 10 seconds
            order_status = client.get_order_by_id(submitted_order.id)
            print(f"Order status: {order_status.status}")

            if order_status.status in ['filled', 'cancelled', 'rejected']:
                break

            time.sleep(1)

        if order_status.status == 'filled':
            print(f"Order filled at ${order_status.filled_avg_price}")

        return order_status

    except APIError as e:
        print(f"API Error: {e.status_code} - {e}")
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise

# Execute
if __name__ == "__main__":
    execute_trade_workflow("AAPL", 1)
```

---

**Document compiled by:** Hive Mind Research Agent
**Last Updated:** 2025-11-14
**Status:** ✅ Complete - Ready for TDD Implementation
**Next Review:** Before live trading deployment
