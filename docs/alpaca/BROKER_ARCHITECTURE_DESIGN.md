# Alpaca Broker Layer Architecture Design

**Date:** 2025-11-14
**Architect:** Code Review & Quality Assurance Specialist
**Status:** 📋 **DESIGN PROPOSAL**

---

## Overview

This document outlines the architecture for the **Alpaca Trading/Broker Layer** - the missing component required to enable actual trade execution in the TradingAgents system.

### Context

Currently implemented:
- ✅ **Data Vendor Layer** (`/tradingagents/dataflows/alpaca/`) - Retrieves market data
- ✅ **Routing System** (`/tradingagents/dataflows/interface.py`) - Routes data requests
- ✅ **Trading Agent** (`/tradingagents/agents/trader/`) - Makes BUY/HOLD/SELL decisions

**Missing:** Broker layer to **execute** the trading decisions

---

## Architecture Goals

1. **Separation of Concerns:** Keep data retrieval and trade execution separate
2. **Pattern Consistency:** Follow existing dataflow routing patterns
3. **Safety First:** Default to paper trading, require explicit live trading
4. **Extensibility:** Easy to add other brokers (Interactive Brokers, TD Ameritrade, etc.)
5. **Testability:** Full test coverage with mocking
6. **Security:** Credentials from environment, no hardcoding

---

## Proposed Directory Structure

```
tradingagents/
├── dataflows/                     # DATA VENDORS (passive - read data)
│   ├── alpaca/                   # ✅ Already implemented
│   │   ├── __init__.py
│   │   ├── common.py             # Client, auth, errors
│   │   └── data.py               # Market data functions
│   ├── y_finance.py
│   ├── alpha_vantage.py
│   └── interface.py              # Vendor routing
│
└── brokers/                       # BROKERS (active - execute trades) ⚠️ NEW
    ├── __init__.py                # Export route_to_broker()
    ├── interface.py               # Broker routing logic
    └── alpaca/                    # Alpaca broker implementation
        ├── __init__.py            # Export public API
        ├── client.py              # AlpacaTradingClient
        ├── orders.py              # Order management functions
        ├── positions.py           # Position tracking functions
        └── portfolio.py           # Account/portfolio functions
```

---

## Interface Design: Broker Routing

### `/tradingagents/brokers/interface.py`

Similar to dataflows routing, but for trading operations:

```python
"""
Broker Interface and Routing

Routes trading operations to configured broker implementations.
Follows the same pattern as dataflows/interface.py for consistency.
"""

from typing import Annotated, Any, Optional
import os

# Import broker implementations
from .alpaca import (
    place_order as alpaca_place_order,
    cancel_order as alpaca_cancel_order,
    get_order as alpaca_get_order,
    get_all_orders as alpaca_get_all_orders,
    get_positions as alpaca_get_positions,
    get_position as alpaca_get_position,
    close_position as alpaca_close_position,
    get_account as alpaca_get_account,
    get_portfolio_history as alpaca_get_portfolio_history,
)

# Configuration
from tradingagents.default_config import DEFAULT_CONFIG


# Broker methods mapping (similar to VENDOR_METHODS in dataflows)
BROKER_METHODS = {
    # Order Management
    "place_order": {
        "alpaca": alpaca_place_order,
        # Future: "interactive_brokers": ib_place_order,
        # Future: "td_ameritrade": tda_place_order,
    },
    "cancel_order": {
        "alpaca": alpaca_cancel_order,
    },
    "get_order": {
        "alpaca": alpaca_get_order,
    },
    "get_all_orders": {
        "alpaca": alpaca_get_all_orders,
    },

    # Position Management
    "get_positions": {
        "alpaca": alpaca_get_positions,
    },
    "get_position": {
        "alpaca": alpaca_get_position,
    },
    "close_position": {
        "alpaca": alpaca_close_position,
    },

    # Portfolio/Account
    "get_account": {
        "alpaca": alpaca_get_account,
    },
    "get_portfolio_history": {
        "alpaca": alpaca_get_portfolio_history,
    },
}


def get_broker() -> str:
    """Get the configured trading broker."""
    return DEFAULT_CONFIG.get("trading_broker", "alpaca")


def route_to_broker(method: str, *args, **kwargs) -> Any:
    """
    Route trading operations to configured broker.

    Args:
        method: Trading method name (e.g., "place_order", "get_positions")
        *args: Method arguments
        **kwargs: Method keyword arguments

    Returns:
        Result from broker implementation

    Raises:
        ValueError: If method not supported or broker not configured
        BrokerError: If broker operation fails

    Example:
        # Place a market buy order
        order = route_to_broker(
            "place_order",
            symbol="AAPL",
            qty=10,
            side="buy",
            type="market",
            time_in_force="day"
        )

        # Get current positions
        positions = route_to_broker("get_positions")
    """
    broker = get_broker()

    if method not in BROKER_METHODS:
        raise ValueError(f"Trading method '{method}' not supported")

    if broker not in BROKER_METHODS[method]:
        raise ValueError(
            f"Broker '{broker}' does not support method '{method}'. "
            f"Available brokers: {list(BROKER_METHODS[method].keys())}"
        )

    # Get broker implementation
    broker_func = BROKER_METHODS[method][broker]

    # Execute trading operation
    try:
        return broker_func(*args, **kwargs)
    except Exception as e:
        raise BrokerError(f"Broker operation failed: {str(e)}") from e


class BrokerError(Exception):
    """Base exception for broker errors."""
    pass
```

---

## Alpaca Broker Implementation

### `/tradingagents/brokers/alpaca/client.py`

```python
"""
Alpaca Trading Client

Handles trading operations, order management, and account tracking.
Separate from data client (dataflows/alpaca/common.py) for clean separation.
"""

import os
import logging
from typing import Optional, Dict, Any, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class AlpacaTradingError(Exception):
    """Base exception for Alpaca trading errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class OrderValidationError(AlpacaTradingError):
    """Exception raised when order validation fails."""
    pass


class InsufficientFundsError(AlpacaTradingError):
    """Exception raised when account has insufficient funds."""
    pass


def get_trading_credentials() -> tuple[str, str, str]:
    """
    Retrieve Alpaca trading credentials from environment.

    Returns:
        tuple: (api_key, secret_key, base_url)

    Raises:
        ValueError: If credentials not set or invalid mode
    """
    # Determine trading mode (paper or live)
    broker_mode = os.getenv("ALPACA_BROKER_MODE", "paper").lower()

    if broker_mode == "paper":
        api_key = os.getenv("ALPACA_API_KEY")
        secret_key = os.getenv("ALPACA_SECRET_KEY")
        base_url = "https://paper-api.alpaca.markets"
        logger.info("Using Alpaca PAPER trading mode")
    elif broker_mode == "live":
        # Extra safety: require explicit live credentials
        api_key = os.getenv("ALPACA_LIVE_API_KEY")
        secret_key = os.getenv("ALPACA_LIVE_SECRET_KEY")
        base_url = "https://api.alpaca.markets"

        # Safety warning
        logger.warning("⚠️  USING ALPACA LIVE TRADING MODE - REAL MONEY AT RISK ⚠️")

        # Require explicit confirmation
        confirm = os.getenv("ALPACA_LIVE_TRADING_CONFIRMED", "false").lower()
        if confirm != "true":
            raise ValueError(
                "Live trading requires ALPACA_LIVE_TRADING_CONFIRMED=true. "
                "This is a safety measure to prevent accidental live trading."
            )
    else:
        raise ValueError(f"Invalid broker mode: {broker_mode}. Must be 'paper' or 'live'.")

    if not api_key or not secret_key:
        raise ValueError(
            f"Alpaca {broker_mode.upper()} credentials not set. "
            f"Required: ALPACA_API_KEY and ALPACA_SECRET_KEY"
        )

    return api_key, secret_key, base_url


class AlpacaTradingClient:
    """
    Client for Alpaca trading API (orders, positions, account).

    Separate from AlpacaDataClient to maintain clean separation between
    data retrieval (passive) and trade execution (active).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize Alpaca trading client.

        Args:
            api_key: Alpaca API key (uses env var if not provided)
            secret_key: Alpaca secret key (uses env var if not provided)
            base_url: Trading API base URL (uses env var mode if not provided)
        """
        if api_key and secret_key and base_url:
            self.api_key = api_key
            self.secret_key = secret_key
            self.base_url = base_url
        else:
            self.api_key, self.secret_key, self.base_url = get_trading_credentials()

        self.session = self._create_session()
        logger.info(f"Initialized Alpaca trading client: {self.base_url}")

    def _create_session(self) -> requests.Session:
        """Create requests session with retry configuration."""
        session = requests.Session()

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "DELETE"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        return {
            'APCA-API-KEY-ID': self.api_key,
            'APCA-API-SECRET-KEY': self.secret_key,
            'Content-Type': 'application/json'
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Execute API request with error handling.

        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint path
            params: URL query parameters
            json_data: JSON body data

        Returns:
            dict: API response data

        Raises:
            AlpacaTradingError: For API errors
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        logger.debug(f"{method} {url}")

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=headers,
                timeout=30
            )

            # Handle status codes
            if response.status_code in [200, 201]:
                return response.json() if response.content else {}
            elif response.status_code == 401:
                raise AlpacaTradingError(
                    "Authentication failed. Check your API credentials.",
                    status_code=401
                )
            elif response.status_code == 403:
                raise InsufficientFundsError(
                    "Insufficient buying power or account restrictions",
                    status_code=403
                )
            elif response.status_code == 422:
                error_data = response.json() if response.content else {}
                raise OrderValidationError(
                    f"Order validation failed: {error_data.get('message', 'Invalid order')}",
                    status_code=422
                )
            else:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('message', f'API error: {response.status_code}')
                raise AlpacaTradingError(error_message, status_code=response.status_code)

        except requests.exceptions.Timeout:
            raise AlpacaTradingError("Request timeout after 30 seconds")
        except requests.exceptions.RequestException as e:
            raise AlpacaTradingError(f"Request failed: {str(e)}")

    def close(self):
        """Close session and cleanup resources."""
        if self.session:
            self.session.close()
            logger.info("Closed Alpaca trading client session")


# Singleton instance
_trading_client_instance: Optional[AlpacaTradingClient] = None


def get_trading_client() -> AlpacaTradingClient:
    """Get or create singleton trading client instance."""
    global _trading_client_instance
    if _trading_client_instance is None:
        _trading_client_instance = AlpacaTradingClient()
    return _trading_client_instance
```

### `/tradingagents/brokers/alpaca/orders.py`

```python
"""
Alpaca Order Management Functions

Functions for placing, canceling, and tracking orders.
"""

from typing import Annotated, Dict, Any, List, Optional
from datetime import datetime
import logging

from .client import get_trading_client, OrderValidationError

logger = logging.getLogger(__name__)


def place_order(
    symbol: Annotated[str, "Stock symbol (e.g., 'AAPL')"],
    qty: Annotated[int, "Number of shares to trade"],
    side: Annotated[str, "Order side: 'buy' or 'sell'"],
    type: Annotated[str, "Order type: 'market', 'limit', 'stop', 'stop_limit'"],
    time_in_force: Annotated[str, "Time in force: 'day', 'gtc', 'ioc', 'fok'"],
    limit_price: Optional[Annotated[float, "Limit price (required for limit orders)"]] = None,
    stop_price: Optional[Annotated[float, "Stop price (required for stop orders)"]] = None,
    extended_hours: Annotated[bool, "Allow trading in extended hours"] = False,
    client_order_id: Optional[Annotated[str, "Custom order ID"]] = None,
) -> Dict[str, Any]:
    """
    Place a new order with Alpaca.

    Args:
        symbol: Stock symbol to trade
        qty: Number of shares
        side: "buy" or "sell"
        type: "market", "limit", "stop", or "stop_limit"
        time_in_force: "day" (cancel at market close), "gtc" (good til canceled),
                       "ioc" (immediate or cancel), "fok" (fill or kill)
        limit_price: Required for limit and stop_limit orders
        stop_price: Required for stop and stop_limit orders
        extended_hours: Allow trading outside regular hours
        client_order_id: Custom identifier for tracking

    Returns:
        dict: Order details including order_id, status, filled_qty, etc.

    Raises:
        OrderValidationError: If order parameters are invalid
        InsufficientFundsError: If account has insufficient buying power
        AlpacaTradingError: For other API errors

    Example:
        # Market buy order
        order = place_order("AAPL", qty=10, side="buy", type="market", time_in_force="day")

        # Limit sell order
        order = place_order(
            "AAPL",
            qty=10,
            side="sell",
            type="limit",
            time_in_force="gtc",
            limit_price=150.00
        )
    """
    # Validation
    if qty <= 0:
        raise OrderValidationError("Quantity must be positive")

    if side.lower() not in ["buy", "sell"]:
        raise OrderValidationError("Side must be 'buy' or 'sell'")

    if type.lower() not in ["market", "limit", "stop", "stop_limit"]:
        raise OrderValidationError("Invalid order type")

    if type.lower() in ["limit", "stop_limit"] and limit_price is None:
        raise OrderValidationError(f"{type} orders require limit_price")

    if type.lower() in ["stop", "stop_limit"] and stop_price is None:
        raise OrderValidationError(f"{type} orders require stop_price")

    # Build order request
    order_data = {
        "symbol": symbol.upper(),
        "qty": qty,
        "side": side.lower(),
        "type": type.lower(),
        "time_in_force": time_in_force.lower(),
    }

    if limit_price is not None:
        order_data["limit_price"] = str(limit_price)

    if stop_price is not None:
        order_data["stop_price"] = str(stop_price)

    if extended_hours:
        order_data["extended_hours"] = True

    if client_order_id:
        order_data["client_order_id"] = client_order_id

    # Submit order
    client = get_trading_client()
    response = client._request("POST", "/v2/orders", json_data=order_data)

    logger.info(
        f"Order placed: {side.upper()} {qty} {symbol} @ {type.upper()} "
        f"(Order ID: {response.get('id')})"
    )

    return response


def cancel_order(
    order_id: Annotated[str, "Order ID to cancel"]
) -> Dict[str, Any]:
    """
    Cancel an existing order.

    Args:
        order_id: Alpaca order ID

    Returns:
        dict: Cancellation confirmation

    Raises:
        AlpacaTradingError: If order cannot be canceled
    """
    client = get_trading_client()
    response = client._request("DELETE", f"/v2/orders/{order_id}")

    logger.info(f"Order canceled: {order_id}")

    return response


def get_order(
    order_id: Annotated[str, "Order ID to retrieve"]
) -> Dict[str, Any]:
    """
    Get details for a specific order.

    Args:
        order_id: Alpaca order ID

    Returns:
        dict: Order details including status, fills, etc.
    """
    client = get_trading_client()
    return client._request("GET", f"/v2/orders/{order_id}")


def get_all_orders(
    status: Optional[Annotated[str, "Filter by status: 'open', 'closed', 'all'"]] = "all",
    limit: Annotated[int, "Maximum number of orders to return"] = 100,
    after: Optional[Annotated[str, "Filter orders after this date (YYYY-MM-DD)"]] = None,
    until: Optional[Annotated[str, "Filter orders until this date (YYYY-MM-DD)"]] = None,
) -> List[Dict[str, Any]]:
    """
    Get all orders for the account.

    Args:
        status: Filter by status ("open", "closed", "all")
        limit: Maximum number of orders to return (max 500)
        after: Filter orders after this date
        until: Filter orders until this date

    Returns:
        list: List of order dictionaries
    """
    params = {
        "status": status,
        "limit": min(limit, 500),
    }

    if after:
        params["after"] = after
    if until:
        params["until"] = until

    client = get_trading_client()
    return client._request("GET", "/v2/orders", params=params)
```

### `/tradingagents/brokers/alpaca/positions.py`

```python
"""
Alpaca Position Management Functions

Functions for tracking and managing open positions.
"""

from typing import Annotated, Dict, Any, List
import logging

from .client import get_trading_client

logger = logging.getLogger(__name__)


def get_positions() -> List[Dict[str, Any]]:
    """
    Get all open positions.

    Returns:
        list: List of position dictionaries with symbol, qty, market_value, etc.

    Example:
        positions = get_positions()
        for pos in positions:
            print(f"{pos['symbol']}: {pos['qty']} shares @ ${pos['avg_entry_price']}")
    """
    client = get_trading_client()
    return client._request("GET", "/v2/positions")


def get_position(
    symbol: Annotated[str, "Stock symbol"]
) -> Dict[str, Any]:
    """
    Get position for a specific symbol.

    Args:
        symbol: Stock symbol

    Returns:
        dict: Position details

    Raises:
        AlpacaTradingError: If no position exists for this symbol
    """
    client = get_trading_client()
    return client._request("GET", f"/v2/positions/{symbol.upper()}")


def close_position(
    symbol: Annotated[str, "Stock symbol"],
    qty: Optional[Annotated[int, "Quantity to close (None = close all)"]] = None,
    percentage: Optional[Annotated[float, "Percentage to close (0-100)"]] = None,
) -> Dict[str, Any]:
    """
    Close an open position (or part of it).

    Args:
        symbol: Stock symbol
        qty: Specific quantity to close (overrides percentage)
        percentage: Percentage of position to close (0-100)

    Returns:
        dict: Order details for the closing order

    Example:
        # Close entire position
        close_position("AAPL")

        # Close 50% of position
        close_position("AAPL", percentage=50)

        # Close specific quantity
        close_position("AAPL", qty=10)
    """
    params = {}
    if qty is not None:
        params["qty"] = qty
    elif percentage is not None:
        if not 0 < percentage <= 100:
            raise ValueError("Percentage must be between 0 and 100")
        params["percentage"] = str(percentage)

    client = get_trading_client()
    response = client._request("DELETE", f"/v2/positions/{symbol.upper()}", params=params)

    logger.info(f"Position closed: {symbol}")

    return response
```

### `/tradingagents/brokers/alpaca/portfolio.py`

```python
"""
Alpaca Portfolio and Account Functions

Functions for account information, buying power, and portfolio history.
"""

from typing import Annotated, Dict, Any, Optional
import logging

from .client import get_trading_client

logger = logging.getLogger(__name__)


def get_account() -> Dict[str, Any]:
    """
    Get account information including buying power, equity, and cash.

    Returns:
        dict: Account details with keys:
            - buying_power: Available buying power
            - equity: Total account equity
            - cash: Available cash
            - portfolio_value: Total portfolio value
            - pattern_day_trader: PDT status
            - daytrade_count: Number of recent day trades

    Example:
        account = get_account()
        print(f"Buying Power: ${account['buying_power']}")
        print(f"Portfolio Value: ${account['portfolio_value']}")
    """
    client = get_trading_client()
    return client._request("GET", "/v2/account")


def get_portfolio_history(
    period: Annotated[str, "Time period: '1D', '1W', '1M', '3M', '1Y', 'all'"] = "1M",
    timeframe: Annotated[str, "Bar timeframe: '1Min', '5Min', '15Min', '1H', '1D'"] = "1D",
    extended_hours: Annotated[bool, "Include extended hours"] = False,
) -> Dict[str, Any]:
    """
    Get historical portfolio values over time.

    Args:
        period: Time period to retrieve
        timeframe: Bar size for aggregation
        extended_hours: Include extended hours data

    Returns:
        dict: Portfolio history with timestamp, equity, and profit_loss arrays

    Example:
        history = get_portfolio_history(period="1M", timeframe="1D")
        timestamps = history['timestamp']
        equity = history['equity']
    """
    params = {
        "period": period,
        "timeframe": timeframe,
        "extended_hours": str(extended_hours).lower()
    }

    client = get_trading_client()
    return client._request("GET", "/v2/account/portfolio/history", params=params)
```

---

## Configuration Updates

### `/tradingagents/default_config.py`

Add these settings:

```python
import os

DEFAULT_CONFIG = {
    # ... existing config ...

    # Trading broker configuration
    "trading_broker": "alpaca",           # Default broker for trade execution
    "auto_execute_trades": False,         # Safety: require explicit enable
    "broker_mode": "paper",               # "paper" or "live" (default paper)

    # Alpaca credentials (from environment)
    "alpaca_api_key": os.getenv("ALPACA_API_KEY"),
    "alpaca_secret_key": os.getenv("ALPACA_SECRET_KEY"),

    # Live trading safety (requires explicit confirmation)
    "alpaca_live_api_key": os.getenv("ALPACA_LIVE_API_KEY"),
    "alpaca_live_secret_key": os.getenv("ALPACA_LIVE_SECRET_KEY"),
    "alpaca_live_trading_confirmed": os.getenv("ALPACA_LIVE_TRADING_CONFIRMED", "false").lower() == "true",

    # Data vendors (can now use alpaca)
    "data_vendors": {
        "core_stock_apis": "alpaca,yfinance",  # Fallback from Alpaca to yfinance
        "technical_indicators": "yfinance",
        "fundamental_data": "alpha_vantage",
        "news_data": "alpha_vantage",
    },
}
```

### `.env.example`

Already has the needed Alpaca configuration ✅

---

## Safety Features

### 1. Paper Trading Default

```python
# Always defaults to paper trading unless explicitly set to live
broker_mode = os.getenv("ALPACA_BROKER_MODE", "paper").lower()
```

### 2. Live Trading Confirmation

```python
# Requires explicit confirmation environment variable
if broker_mode == "live":
    confirm = os.getenv("ALPACA_LIVE_TRADING_CONFIRMED", "false").lower()
    if confirm != "true":
        raise ValueError("Live trading requires explicit confirmation")
```

### 3. Order Validation

```python
# Validate all order parameters before submission
if qty <= 0:
    raise OrderValidationError("Quantity must be positive")

if type == "limit" and limit_price is None:
    raise OrderValidationError("Limit orders require limit_price")
```

### 4. Comprehensive Logging

```python
logger.warning("⚠️  USING ALPACA LIVE TRADING MODE - REAL MONEY AT RISK ⚠️")
logger.info(f"Order placed: BUY 10 AAPL @ MARKET (Order ID: abc123)")
```

---

## Integration with Trader Agent

### Current Trader Agent Output

```python
# From tradingagents/agents/trader/trader.py
output = "FINAL TRANSACTION PROPOSAL: BUY 100 shares of AAPL"
```

### New Execution Layer

```python
# In tradingagents/agents/utils/trading_execution_tools.py (NEW FILE)

from langchain.tools import tool
from tradingagents.brokers.interface import route_to_broker

@tool
def execute_trade(
    symbol: str,
    qty: int,
    side: str,  # "buy" or "sell"
    type: str = "market",
    time_in_force: str = "day"
) -> str:
    """
    Execute a trade via the configured broker.

    This tool integrates with the trader agent to execute BUY/SELL decisions.

    Args:
        symbol: Stock symbol
        qty: Number of shares
        side: "buy" or "sell"
        type: Order type (default: "market")
        time_in_force: Duration (default: "day")

    Returns:
        str: Execution confirmation with order ID
    """
    # Check if auto-execution is enabled
    from tradingagents.default_config import DEFAULT_CONFIG
    if not DEFAULT_CONFIG.get("auto_execute_trades", False):
        return f"Trade NOT executed (auto_execute_trades disabled): {side.upper()} {qty} {symbol}"

    # Execute via broker routing
    try:
        order = route_to_broker(
            "place_order",
            symbol=symbol,
            qty=qty,
            side=side,
            type=type,
            time_in_force=time_in_force
        )

        return (
            f"✅ Trade executed: {side.upper()} {qty} {symbol} @ {type.upper()}\n"
            f"Order ID: {order['id']}\n"
            f"Status: {order['status']}\n"
            f"Submitted at: {order['submitted_at']}"
        )

    except Exception as e:
        return f"❌ Trade execution failed: {str(e)}"
```

---

## Testing Strategy

### Unit Tests

```python
# tests/brokers/alpaca/test_orders.py

def test_place_order_validates_quantity():
    """Test that order validation catches negative quantities."""
    with pytest.raises(OrderValidationError, match="positive"):
        place_order("AAPL", qty=-10, side="buy", type="market", time_in_force="day")

def test_place_order_requires_limit_price():
    """Test that limit orders require limit_price."""
    with pytest.raises(OrderValidationError, match="limit_price"):
        place_order("AAPL", qty=10, side="buy", type="limit", time_in_force="day")

def test_place_order_success(mock_trading_client):
    """Test successful order placement."""
    mock_trading_client._request.return_value = {
        "id": "order123",
        "status": "accepted",
        "submitted_at": "2025-01-14T12:00:00Z"
    }

    order = place_order("AAPL", qty=10, side="buy", type="market", time_in_force="day")

    assert order["id"] == "order123"
    assert order["status"] == "accepted"
```

### Integration Tests

```python
# tests/integration/test_broker_routing.py

def test_route_to_broker_alpaca():
    """Test routing to Alpaca broker."""
    with patch.dict(os.environ, {"ALPACA_API_KEY": "test", "ALPACA_SECRET_KEY": "test"}):
        result = route_to_broker("get_account")
        assert "buying_power" in result
```

### E2E Tests (Paper Trading)

```python
# tests/e2e/test_full_trading_workflow.py

@pytest.mark.skipif(not os.getenv("ALPACA_API_KEY"), reason="Requires credentials")
def test_full_workflow_paper_trading():
    """Test complete workflow with paper trading."""
    # 1. Get data
    data = route_to_vendor("get_stock_data", "AAPL", "2025-01-01", "2025-01-14")

    # 2. Make decision (mock)
    decision = "BUY"

    # 3. Execute trade
    order = route_to_broker(
        "place_order",
        symbol="AAPL",
        qty=1,
        side="buy",
        type="market",
        time_in_force="day"
    )

    # 4. Verify execution
    assert order["status"] in ["accepted", "filled", "pending_new"]

    # 5. Check position
    positions = route_to_broker("get_positions")
    assert any(pos["symbol"] == "AAPL" for pos in positions)
```

---

## Migration Path

### Phase 1: Core Implementation (4-6 hours)
1. Create `/tradingagents/brokers/` directory structure
2. Implement `client.py` (AlpacaTradingClient)
3. Implement `interface.py` (broker routing)
4. Update `default_config.py`

### Phase 2: Order Management (2-3 hours)
1. Implement `orders.py` (place, cancel, get)
2. Add order validation logic
3. Create unit tests for order functions

### Phase 3: Position & Portfolio (1-2 hours)
1. Implement `positions.py` (get, close)
2. Implement `portfolio.py` (account, history)
3. Create unit tests

### Phase 4: Integration (1-2 hours)
1. Create `trading_execution_tools.py` for agent integration
2. Add integration tests with routing
3. Test full workflow

### Phase 5: E2E Testing (1-2 hours)
1. Create E2E tests with paper trading
2. Verify complete data → decision → execution flow
3. Document usage examples

**Total Estimated Effort:** 9-15 hours

---

## Success Criteria

- ✅ Broker routing works (`route_to_broker()`)
- ✅ All order functions implemented and tested
- ✅ Position tracking works
- ✅ Account/portfolio functions work
- ✅ Paper trading is default
- ✅ Live trading requires confirmation
- ✅ Order validation catches errors
- ✅ Test coverage >90%
- ✅ Integration with trader agent
- ✅ E2E tests pass with paper trading

---

## Future Enhancements

1. **Other Brokers:**
   - Interactive Brokers integration
   - TD Ameritrade integration
   - Robinhood integration

2. **Advanced Order Types:**
   - Bracket orders (entry + stop-loss + take-profit)
   - Trailing stop orders
   - OCO (One-Cancels-Other) orders

3. **Risk Management:**
   - Position size limits
   - Max loss per trade
   - Daily loss limits
   - Automatic stop-loss placement

4. **Performance Tracking:**
   - Win/loss ratio
   - Sharpe ratio
   - Maximum drawdown
   - Trade history analysis

---

**Status:** 📋 Ready for implementation
**Next Step:** Begin Phase 1 - Core Implementation
