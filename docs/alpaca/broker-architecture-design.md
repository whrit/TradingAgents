# Broker Layer Architecture Design
## Alpaca Trading Integration - Full Migration (Option A)

**Version:** 1.0
**Date:** 2025-11-14
**Author:** System Architecture Agent
**Status:** Design Complete - Ready for Implementation

---

## Executive Summary

This document defines the complete architecture for the broker/execution layer that enables actual trade execution through Alpaca Markets. The design follows the existing project patterns established in the data vendor abstraction layer, ensuring consistency, maintainability, and extensibility for future broker integrations.

**Key Design Principles:**
1. **Pattern Consistency**: Mirror the proven `dataflows/interface.py` routing architecture
2. **Safety First**: Default to paper trading with explicit configuration required for live trading
3. **Extensibility**: Support multiple brokers (Alpaca, Interactive Brokers, etc.)
4. **Tool Integration**: Seamless integration with existing LangChain tool system
5. **Security**: Environment-based credentials only, never hardcoded

---

## 1. Architecture Overview

### 1.1 System Context

```
┌─────────────────────────────────────────────────────────────┐
│                    Trading Agent System                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐         ┌──────────────┐                │
│  │   Trader     │────────▶│   Tools      │                │
│  │   Agent      │         │   Layer      │                │
│  └──────────────┘         └──────┬───────┘                │
│                                   │                        │
│                                   ▼                        │
│                          ┌────────────────┐                │
│                          │  Broker Layer  │◀────NEW       │
│                          │  (routing)     │                │
│                          └────────┬───────┘                │
│                                   │                        │
│                    ┌──────────────┼──────────────┐         │
│                    ▼              ▼              ▼         │
│             ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│             │  Alpaca  │   │   IB     │   │  Future  │    │
│             │  Broker  │   │  Broker  │   │ Brokers  │    │
│             └──────────┘   └──────────┘   └──────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                   External Broker APIs
```

### 1.2 High-Level Architecture

The broker layer consists of three primary components:

1. **Broker Interface** (`tradingagents/brokers/interface.py`)
   - Routing logic for broker method calls
   - Vendor configuration and fallback support
   - Integration point for tools

2. **Vendor Implementations** (`tradingagents/brokers/{vendor}/`)
   - Broker-specific API implementations
   - Authentication and client management
   - Order execution and account management

3. **Trading Tools** (`tradingagents/agents/utils/trading_execution_tools.py`)
   - LangChain tool wrappers
   - Agent-facing interface
   - Type validation and error handling

---

## 2. Directory Structure

### 2.1 New Directory Layout

```
tradingagents/
├── brokers/                          # NEW: Broker/execution layer
│   ├── __init__.py                   # Package initialization
│   ├── interface.py                  # Routing interface (mirrors dataflows/interface.py)
│   ├── config.py                     # Configuration access
│   │
│   ├── alpaca/                       # Alpaca broker implementation
│   │   ├── __init__.py               # Export public API
│   │   ├── common.py                 # Client, auth, errors (mirrors dataflows/alpaca/common.py)
│   │   ├── trading.py                # Trading operations (orders, positions)
│   │   ├── account.py                # Account management
│   │   └── portfolio.py              # Portfolio/position queries
│   │
│   └── interactive_brokers/          # FUTURE: Interactive Brokers
│       └── (similar structure)
│
├── agents/
│   └── utils/
│       ├── core_stock_tools.py       # Existing data tools
│       └── trading_execution_tools.py # NEW: Trading execution tools
│
├── default_config.py                 # UPDATED: Add broker configuration
└── dataflows/                        # Existing data vendor layer
    └── (unchanged)
```

### 2.2 File Organization Rationale

**Why separate `trading.py`, `account.py`, and `portfolio.py`?**
- **Modularity**: Each file has a single, clear responsibility
- **File Size**: Keeps files under 500 lines (project standard)
- **Testing**: Easier to write focused unit tests
- **Parallel Development**: Multiple developers can work simultaneously

---

## 3. Core Components Design

### 3.1 Broker Interface (`brokers/interface.py`)

This is the central routing mechanism that mirrors `dataflows/interface.py`.

#### 3.1.1 Tool Categories

```python
# Trading operations organized by category
BROKER_TOOL_CATEGORIES = {
    "order_execution": {
        "description": "Place, modify, and cancel orders",
        "tools": [
            "place_order",
            "cancel_order",
            "get_order_status",
            "modify_order"
        ]
    },
    "position_management": {
        "description": "Query and manage positions",
        "tools": [
            "get_positions",
            "get_position",
            "close_position",
            "close_all_positions"
        ]
    },
    "account_info": {
        "description": "Account data and buying power",
        "tools": [
            "get_account",
            "get_buying_power",
            "get_portfolio_history"
        ]
    },
    "order_history": {
        "description": "Historical order data",
        "tools": [
            "get_orders",
            "get_order"
        ]
    }
}
```

#### 3.1.2 Vendor Method Mapping

```python
# Mapping of methods to their broker-specific implementations
BROKER_METHODS = {
    # order_execution
    "place_order": {
        "alpaca": alpaca_place_order,
        # "interactive_brokers": ib_place_order,  # Future
    },
    "cancel_order": {
        "alpaca": alpaca_cancel_order,
    },
    "get_order_status": {
        "alpaca": alpaca_get_order_status,
    },

    # position_management
    "get_positions": {
        "alpaca": alpaca_get_positions,
    },
    "get_position": {
        "alpaca": alpaca_get_position,
    },
    "close_position": {
        "alpaca": alpaca_close_position,
    },

    # account_info
    "get_account": {
        "alpaca": alpaca_get_account,
    },
    "get_buying_power": {
        "alpaca": alpaca_get_buying_power,
    },

    # order_history
    "get_orders": {
        "alpaca": alpaca_get_orders,
    },
}
```

#### 3.1.3 Routing Function

```python
def route_to_broker(method: str, *args, **kwargs):
    """
    Route broker method calls to appropriate vendor implementation.

    Mirrors the pattern from dataflows/interface.py with safety checks
    for trading operations.

    Args:
        method: Broker method name (e.g., "place_order")
        *args, **kwargs: Method-specific arguments

    Returns:
        Result from broker-specific implementation

    Raises:
        ValueError: If method not supported or safety checks fail
        BrokerAPIError: If broker API call fails
    """
    # Get configuration
    config = get_config()
    broker = config.get("trading_broker", "alpaca")

    # Safety check: Prevent live trading if not explicitly enabled
    broker_mode = config.get("broker_mode", "paper")
    if broker_mode == "live":
        auto_execute = config.get("auto_execute_trades", False)
        if not auto_execute and method in ["place_order", "close_position", "close_all_positions"]:
            return {
                "status": "blocked",
                "message": "Live trading blocked. Set 'auto_execute_trades: True' to enable."
            }

    # Validate method exists
    if method not in BROKER_METHODS:
        raise ValueError(f"Method '{method}' not supported by broker interface")

    # Get vendor implementation
    if broker not in BROKER_METHODS[method]:
        raise ValueError(f"Broker '{broker}' does not support method '{method}'")

    vendor_impl = BROKER_METHODS[method][broker]

    # Execute and return
    try:
        return vendor_impl(*args, **kwargs)
    except BrokerRateLimitError:
        # Could implement fallback to alternative broker here
        raise
    except Exception as e:
        logger.error(f"Broker method '{method}' failed: {e}")
        raise
```

### 3.2 Alpaca Broker Implementation

#### 3.2.1 Common Module (`brokers/alpaca/common.py`)

Handles authentication, client creation, and error handling.

**Key Components:**
```python
class AlpacaBrokerClient:
    """
    Client for Alpaca Trading API.

    Separate from AlpacaDataClient (in dataflows/) because:
    - Different API endpoints (trading vs data)
    - Different authentication requirements
    - Different rate limits
    - Different error handling needs
    """

    PAPER_URL = "https://paper-api.alpaca.markets"
    LIVE_URL = "https://api.alpaca.markets"

    def __init__(self, mode: str = "paper"):
        """
        Initialize Alpaca broker client.

        Args:
            mode: Trading mode ("paper" or "live")
        """
        self.mode = mode
        self.api_key, self.secret_key = get_alpaca_credentials(mode)
        self.base_url = self.PAPER_URL if mode == "paper" else self.LIVE_URL
        self.session = self._create_session()

# Exception classes
class AlpacaBrokerError(Exception):
    """Base exception for Alpaca broker errors."""
    pass

class AlpacaBrokerRateLimitError(AlpacaBrokerError):
    """Rate limit exceeded."""
    pass

class AlpacaInsufficientFundsError(AlpacaBrokerError):
    """Insufficient buying power."""
    pass
```

**Credential Management:**
```python
def get_alpaca_credentials(mode: str = "paper") -> tuple[str, str]:
    """
    Get Alpaca API credentials based on trading mode.

    Environment variables:
    - Paper trading: ALPACA_PAPER_API_KEY, ALPACA_PAPER_SECRET_KEY
    - Live trading: ALPACA_LIVE_API_KEY, ALPACA_LIVE_SECRET_KEY

    Args:
        mode: Trading mode ("paper" or "live")

    Returns:
        tuple: (api_key, secret_key)

    Raises:
        ValueError: If credentials not set
    """
    if mode == "live":
        api_key = os.getenv("ALPACA_LIVE_API_KEY")
        secret_key = os.getenv("ALPACA_LIVE_SECRET_KEY")
        env_vars = "ALPACA_LIVE_API_KEY and ALPACA_LIVE_SECRET_KEY"
    else:
        api_key = os.getenv("ALPACA_PAPER_API_KEY")
        secret_key = os.getenv("ALPACA_PAPER_SECRET_KEY")
        env_vars = "ALPACA_PAPER_API_KEY and ALPACA_PAPER_SECRET_KEY"

    if not api_key or not secret_key:
        raise ValueError(f"{env_vars} environment variables must be set")

    return api_key, secret_key
```

#### 3.2.2 Trading Module (`brokers/alpaca/trading.py`)

Handles order placement and management.

**Key Functions:**

```python
def place_order(
    symbol: str,
    qty: Optional[float] = None,
    notional: Optional[float] = None,
    side: str = "buy",
    order_type: str = "market",
    time_in_force: str = "day",
    limit_price: Optional[float] = None,
    stop_price: Optional[float] = None,
    extended_hours: bool = False
) -> dict:
    """
    Place an order with Alpaca.

    Args:
        symbol: Stock ticker symbol
        qty: Number of shares (fractional allowed)
        notional: Dollar amount (alternative to qty)
        side: "buy" or "sell"
        order_type: "market", "limit", "stop", "stop_limit"
        time_in_force: "day", "gtc", "ioc", "fok"
        limit_price: Limit price (required for limit orders)
        stop_price: Stop price (required for stop orders)
        extended_hours: Allow extended hours trading

    Returns:
        dict: Order details with order_id, status, filled_qty, etc.

    Raises:
        AlpacaBrokerError: If order placement fails
        AlpacaInsufficientFundsError: If insufficient buying power
    """
    pass

def cancel_order(order_id: str) -> dict:
    """Cancel an open order."""
    pass

def get_order_status(order_id: str) -> dict:
    """Get status of a specific order."""
    pass
```

#### 3.2.3 Account Module (`brokers/alpaca/account.py`)

Manages account information and buying power.

```python
def get_account() -> dict:
    """
    Get account information.

    Returns:
        dict: Account details including:
            - buying_power: Available buying power
            - cash: Cash balance
            - portfolio_value: Total portfolio value
            - equity: Account equity
            - status: Account status
    """
    pass

def get_buying_power() -> float:
    """Get available buying power."""
    pass
```

#### 3.2.4 Portfolio Module (`brokers/alpaca/portfolio.py`)

Queries positions and portfolio data.

```python
def get_positions() -> list[dict]:
    """
    Get all open positions.

    Returns:
        list: List of position dicts with symbol, qty, market_value, etc.
    """
    pass

def get_position(symbol: str) -> dict:
    """Get position for specific symbol."""
    pass

def close_position(symbol: str) -> dict:
    """Close entire position for a symbol."""
    pass

def get_portfolio_history(
    period: str = "1M",
    timeframe: str = "1D"
) -> dict:
    """
    Get portfolio value history.

    Args:
        period: "1D", "1W", "1M", "3M", "1Y", "all"
        timeframe: "1Min", "5Min", "15Min", "1H", "1D"

    Returns:
        dict: Portfolio history with timestamps, equity, profit_loss
    """
    pass
```

### 3.3 Trading Tools (`agents/utils/trading_execution_tools.py`)

LangChain tools that agents will use for trading.

```python
from langchain_core.tools import tool
from typing import Annotated, Optional
from tradingagents.brokers.interface import route_to_broker

@tool
def execute_trade(
    symbol: Annotated[str, "Stock ticker symbol (e.g., AAPL)"],
    action: Annotated[str, "Trade action: 'buy' or 'sell'"],
    quantity: Annotated[Optional[float], "Number of shares (optional if using dollar amount)"] = None,
    dollar_amount: Annotated[Optional[float], "Dollar amount to trade (optional if using quantity)"] = None,
    order_type: Annotated[str, "Order type: 'market', 'limit', 'stop', or 'stop_limit'"] = "market",
    limit_price: Annotated[Optional[float], "Limit price for limit orders"] = None,
) -> str:
    """
    Execute a stock trade (buy or sell).

    This tool routes to the configured broker (e.g., Alpaca) and executes
    the trade based on current configuration (paper or live mode).

    Safety:
    - Defaults to paper trading mode
    - Live trading requires explicit configuration
    - Auto-execution can be disabled via config

    Args:
        symbol: Stock ticker (e.g., "AAPL", "TSLA")
        action: "buy" or "sell"
        quantity: Number of shares (supports fractional shares)
        dollar_amount: Dollar amount to invest (alternative to quantity)
        order_type: Type of order ("market", "limit", "stop", "stop_limit")
        limit_price: Price limit for limit orders

    Returns:
        str: Formatted string describing order status and details

    Examples:
        execute_trade("AAPL", "buy", quantity=10)
        execute_trade("TSLA", "buy", dollar_amount=1000)
        execute_trade("AAPL", "sell", quantity=5, order_type="limit", limit_price=150.00)
    """
    result = route_to_broker(
        "place_order",
        symbol=symbol,
        qty=quantity,
        notional=dollar_amount,
        side=action,
        order_type=order_type,
        limit_price=limit_price
    )

    # Format result for agent consumption
    return format_order_result(result)

@tool
def get_current_positions() -> str:
    """
    Get all current open positions in the portfolio.

    Returns detailed information about each position including:
    - Symbol and quantity
    - Current market value
    - Cost basis and unrealized P&L
    - Percentage of portfolio

    Returns:
        str: Formatted string with position details
    """
    positions = route_to_broker("get_positions")
    return format_positions(positions)

@tool
def get_account_status() -> str:
    """
    Get current account status and buying power.

    Returns:
        str: Account information including cash, buying power, and portfolio value
    """
    account = route_to_broker("get_account")
    return format_account(account)

@tool
def close_position(
    symbol: Annotated[str, "Stock ticker symbol to close position for"]
) -> str:
    """
    Close entire position for a specific stock.

    Args:
        symbol: Ticker symbol (e.g., "AAPL")

    Returns:
        str: Confirmation of position closure
    """
    result = route_to_broker("close_position", symbol=symbol)
    return format_close_result(result)

@tool
def check_order_status(
    order_id: Annotated[str, "Order ID to check status for"]
) -> str:
    """
    Check the status of a specific order.

    Args:
        order_id: Alpaca order ID

    Returns:
        str: Order status details
    """
    order = route_to_broker("get_order_status", order_id=order_id)
    return format_order_status(order)
```

---

## 4. Configuration Schema

### 4.1 Configuration in `default_config.py`

```python
DEFAULT_CONFIG = {
    # ... existing configuration ...

    # ========================================
    # BROKER / TRADING CONFIGURATION
    # ========================================

    # Broker selection (which broker to use for trading)
    "trading_broker": "alpaca",  # Options: "alpaca", "interactive_brokers", etc.

    # Trading mode: "paper" or "live"
    # CRITICAL: Always defaults to paper trading for safety
    "broker_mode": "paper",

    # Auto-execute trades
    # When False, trade execution is simulated/logged but not executed
    # When True, trades are actually executed (USE WITH CAUTION)
    "auto_execute_trades": False,

    # Broker-specific category configuration (optional)
    # Similar to data_vendors, allows per-category broker selection
    "broker_vendors": {
        "order_execution": "alpaca",
        "position_management": "alpaca",
        "account_info": "alpaca",
    },

    # Tool-level broker configuration (optional, overrides category)
    "broker_tool_vendors": {
        # Example: "place_order": "interactive_brokers",
    },

    # Risk management settings
    "max_position_size": 0.10,  # Max 10% of portfolio per position
    "max_order_value": 10000,   # Max $10k per order (paper trading limit)
    "require_confirmation": True,  # Require confirmation before execution
}
```

### 4.2 Environment Variables

```bash
# ========================================
# ALPACA BROKER CREDENTIALS
# ========================================

# Paper Trading (default, safe for testing)
ALPACA_PAPER_API_KEY=your_paper_api_key
ALPACA_PAPER_SECRET_KEY=your_paper_secret_key

# Live Trading (USE WITH EXTREME CAUTION)
# Only set these if you intend to trade with real money
ALPACA_LIVE_API_KEY=your_live_api_key
ALPACA_LIVE_SECRET_KEY=your_live_secret_key
```

### 4.3 Configuration Access

```python
# In brokers/config.py
from tradingagents.default_config import DEFAULT_CONFIG

_config = None

def get_config():
    """Get broker configuration (mirrors dataflows/config.py)."""
    global _config
    if _config is None:
        _config = DEFAULT_CONFIG.copy()
    return _config

def set_config(config):
    """Set custom configuration."""
    global _config
    _config = config
```

---

## 5. API Contracts

### 5.1 Order Placement Response

```python
{
    "order_id": "61e69015-8549-4bfd-b9c3-01e75843f47f",
    "status": "filled",  # or "pending", "cancelled", "rejected"
    "symbol": "AAPL",
    "side": "buy",
    "qty": 10,
    "filled_qty": 10,
    "order_type": "market",
    "filled_avg_price": 150.25,
    "time_in_force": "day",
    "submitted_at": "2025-11-14T10:30:00Z",
    "filled_at": "2025-11-14T10:30:01Z",
    "extended_hours": false
}
```

### 5.2 Position Response

```python
{
    "symbol": "AAPL",
    "qty": 10,
    "avg_entry_price": 150.00,
    "current_price": 152.50,
    "market_value": 1525.00,
    "cost_basis": 1500.00,
    "unrealized_pl": 25.00,
    "unrealized_plpc": 0.0167,  # 1.67%
    "side": "long",
    "exchange": "NASDAQ"
}
```

### 5.3 Account Response

```python
{
    "account_number": "PA2XXXXXXXX",
    "status": "ACTIVE",
    "currency": "USD",
    "buying_power": 98500.00,
    "cash": 50000.00,
    "portfolio_value": 52500.00,
    "equity": 52500.00,
    "last_equity": 52000.00,
    "long_market_value": 2500.00,
    "short_market_value": 0.00,
    "initial_margin": 0.00,
    "maintenance_margin": 0.00,
    "daytrade_count": 0,
    "daytrading_buying_power": 200000.00
}
```

### 5.4 Error Response

```python
{
    "error": "insufficient_funds",
    "message": "Insufficient buying power: need $10,000, have $5,000",
    "code": 403,
    "details": {
        "required": 10000,
        "available": 5000,
        "shortfall": 5000
    }
}
```

---

## 6. Integration Patterns

### 6.1 Integration with Trader Agent

The trader agent (`agents/trader/trader.py`) currently only makes recommendations. We'll enhance it to optionally execute trades:

```python
def create_trader(llm, memory, tools=None):
    """
    Create trader agent with optional execution tools.

    Args:
        llm: Language model
        memory: Memory system
        tools: Optional list of tools (includes trading execution tools)
    """
    def trader_node(state, name):
        # ... existing analysis logic ...

        # NEW: If tools provided and auto_execute enabled, agent can trade
        if tools and "execute_trade" in [t.name for t in tools]:
            # Agent has access to execution tools
            # It can decide to execute based on its analysis
            pass

        # ... rest of existing logic ...

    return functools.partial(trader_node, name="Trader")
```

### 6.2 Tool Registration

```python
# In agent setup/initialization
from tradingagents.agents.utils.core_stock_tools import get_stock_data, get_indicators
from tradingagents.agents.utils.trading_execution_tools import (
    execute_trade,
    get_current_positions,
    get_account_status,
    close_position
)

# Data tools (existing)
data_tools = [get_stock_data, get_indicators, ...]

# Trading tools (new)
trading_tools = [
    execute_trade,
    get_current_positions,
    get_account_status,
    close_position
]

# Conditional tool registration based on config
config = get_config()
if config.get("auto_execute_trades", False):
    all_tools = data_tools + trading_tools
else:
    all_tools = data_tools  # Read-only mode
```

### 6.3 Workflow Integration

```python
# Example: Enhanced trading workflow with execution

# 1. Analysis Phase (existing)
market_data = get_stock_data("AAPL", "2025-01-01", "2025-11-14")
fundamentals = get_balance_sheet("AAPL")
sentiment = analyze_sentiment(...)

# 2. Decision Phase (existing)
recommendation = trader_agent.decide(market_data, fundamentals, sentiment)
# Output: "BUY 10 shares of AAPL"

# 3. Execution Phase (NEW)
if config["auto_execute_trades"]:
    # Agent or system executes the trade
    result = execute_trade(
        symbol="AAPL",
        action="buy",
        quantity=10,
        order_type="market"
    )
    print(f"Trade executed: {result}")
else:
    # Log recommendation only
    print(f"Trade recommendation (not executed): {recommendation}")
```

---

## 7. Security Model

### 7.1 Credential Management

**Principles:**
1. **Never hardcode credentials** in code
2. **Environment variables only** for API keys
3. **Separate credentials** for paper and live trading
4. **Validate credentials** at startup

**Implementation:**
```python
# brokers/alpaca/common.py
def get_alpaca_credentials(mode: str = "paper") -> tuple[str, str]:
    """
    Secure credential retrieval with validation.
    """
    # Load from environment
    if mode == "live":
        api_key = os.getenv("ALPACA_LIVE_API_KEY")
        secret_key = os.getenv("ALPACA_LIVE_SECRET_KEY")
    else:
        api_key = os.getenv("ALPACA_PAPER_API_KEY")
        secret_key = os.getenv("ALPACA_PAPER_SECRET_KEY")

    # Validate
    if not api_key or not secret_key:
        raise ValueError(f"Alpaca credentials not set for {mode} mode")

    # Additional validation: Check key format
    if not api_key.startswith("PK") and not api_key.startswith("AK"):
        raise ValueError("Invalid Alpaca API key format")

    return api_key, secret_key
```

### 7.2 Safety Mechanisms

**Multi-Layer Safety:**

1. **Configuration Layer**
   ```python
   # Must explicitly enable live trading
   "broker_mode": "paper"  # Default
   "auto_execute_trades": False  # Default
   ```

2. **Routing Layer**
   ```python
   # Check mode before execution
   if broker_mode == "live" and not auto_execute_trades:
       return {"status": "blocked", "message": "Live trading disabled"}
   ```

3. **Tool Layer**
   ```python
   # Tools only registered if execution enabled
   if config.get("auto_execute_trades"):
       register_tools(trading_tools)
   ```

4. **Risk Management Layer**
   ```python
   # Pre-execution validation
   def validate_order(order):
       if order.value > config["max_order_value"]:
           raise ValueError("Order exceeds maximum value")
       if order.position_size > config["max_position_size"]:
           raise ValueError("Position size exceeds maximum")
   ```

### 7.3 Audit Trail

```python
# Log all trading activity
import logging

trade_logger = logging.getLogger("tradingagents.broker.trades")

def place_order(*args, **kwargs):
    # Log before execution
    trade_logger.info(f"Order attempt: {args}, {kwargs}")

    try:
        result = _execute_order(*args, **kwargs)
        trade_logger.info(f"Order success: {result}")
        return result
    except Exception as e:
        trade_logger.error(f"Order failed: {e}")
        raise
```

---

## 8. Error Handling Strategy

### 8.1 Error Hierarchy

```python
# Base exception
class BrokerError(Exception):
    """Base exception for all broker errors."""
    pass

# API errors
class BrokerAPIError(BrokerError):
    """API request failed."""
    pass

class BrokerRateLimitError(BrokerAPIError):
    """Rate limit exceeded."""
    pass

class BrokerAuthenticationError(BrokerAPIError):
    """Authentication failed."""
    pass

# Trading errors
class InsufficientFundsError(BrokerError):
    """Insufficient buying power."""
    pass

class InvalidOrderError(BrokerError):
    """Order parameters invalid."""
    pass

class OrderRejectedError(BrokerError):
    """Order rejected by broker."""
    pass

# System errors
class BrokerConfigurationError(BrokerError):
    """Configuration error."""
    pass
```

### 8.2 Error Handling Patterns

```python
def route_to_broker(method: str, *args, **kwargs):
    """Route with comprehensive error handling."""
    try:
        # Validate configuration
        validate_broker_config()

        # Execute method
        result = execute_broker_method(method, *args, **kwargs)

        return result

    except BrokerRateLimitError as e:
        # Could implement fallback or retry logic
        logger.warning(f"Rate limit hit: {e}")
        raise

    except BrokerAuthenticationError as e:
        # Critical: Check credentials
        logger.error(f"Authentication failed: {e}")
        raise BrokerConfigurationError("Check broker credentials")

    except InsufficientFundsError as e:
        # Return graceful error to agent
        return {
            "status": "error",
            "error": "insufficient_funds",
            "message": str(e)
        }

    except InvalidOrderError as e:
        # Validation error - fix parameters
        return {
            "status": "error",
            "error": "invalid_order",
            "message": str(e)
        }

    except Exception as e:
        # Unexpected error - log and raise
        logger.error(f"Unexpected broker error: {e}")
        raise BrokerError(f"Broker operation failed: {e}")
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

**File: `tests/test_broker_interface.py`**

```python
import pytest
from tradingagents.brokers.interface import route_to_broker
from tradingagents.brokers.config import set_config

def test_route_to_broker_alpaca():
    """Test routing to Alpaca broker."""
    config = {"trading_broker": "alpaca", "broker_mode": "paper"}
    set_config(config)

    # Mock order placement
    result = route_to_broker("place_order",
        symbol="AAPL",
        qty=10,
        side="buy"
    )

    assert result["status"] == "success"
    assert result["symbol"] == "AAPL"

def test_safety_mechanism_live_mode():
    """Test that live trading is blocked without explicit config."""
    config = {
        "trading_broker": "alpaca",
        "broker_mode": "live",
        "auto_execute_trades": False  # Not enabled
    }
    set_config(config)

    result = route_to_broker("place_order",
        symbol="AAPL",
        qty=10,
        side="buy"
    )

    assert result["status"] == "blocked"
    assert "auto_execute_trades" in result["message"]
```

**File: `tests/test_alpaca_broker.py`**

```python
import pytest
from tradingagents.brokers.alpaca.trading import place_order
from tradingagents.brokers.alpaca.common import AlpacaBrokerClient

@pytest.fixture
def paper_client():
    """Fixture for paper trading client."""
    return AlpacaBrokerClient(mode="paper")

def test_place_market_order(paper_client):
    """Test market order placement."""
    order = place_order(
        symbol="AAPL",
        qty=1,
        side="buy",
        order_type="market"
    )

    assert order["symbol"] == "AAPL"
    assert order["side"] == "buy"
    assert "order_id" in order

def test_insufficient_funds_error(paper_client):
    """Test handling of insufficient funds."""
    with pytest.raises(InsufficientFundsError):
        place_order(
            symbol="AAPL",
            qty=1000000,  # Unrealistic quantity
            side="buy"
        )
```

### 9.2 Integration Tests

**File: `tests/test_broker_integration.py`**

```python
def test_end_to_end_trade_execution():
    """Test complete trade flow from tool to broker."""
    from tradingagents.agents.utils.trading_execution_tools import execute_trade

    # Configure for paper trading
    config = {
        "trading_broker": "alpaca",
        "broker_mode": "paper",
        "auto_execute_trades": True
    }
    set_config(config)

    # Execute trade via tool
    result = execute_trade.invoke({
        "symbol": "AAPL",
        "action": "buy",
        "quantity": 1,
        "order_type": "market"
    })

    assert "order_id" in result
    assert "filled" in result.lower()
```

### 9.3 Mock Testing

```python
# For testing without actual API calls
from unittest.mock import patch, MagicMock

def test_place_order_mocked():
    """Test order placement with mocked API."""
    with patch('tradingagents.brokers.alpaca.common.AlpacaBrokerClient._request') as mock_request:
        mock_request.return_value = {
            "id": "test-order-123",
            "status": "filled",
            "symbol": "AAPL",
            "qty": 10
        }

        order = place_order("AAPL", qty=10, side="buy")

        assert order["order_id"] == "test-order-123"
        assert order["status"] == "filled"
```

---

## 10. Migration Path & Implementation Phases

### Phase 1: Foundation (Week 1)

**Deliverables:**
- [ ] Directory structure created
- [ ] `brokers/interface.py` implemented
- [ ] `brokers/config.py` implemented
- [ ] `brokers/alpaca/common.py` implemented
- [ ] Unit tests for routing and configuration
- [ ] Documentation updated

**Validation:**
- Configuration loading works
- Routing logic handles method calls correctly
- Authentication retrieves credentials properly
- Safety mechanisms block unauthorized execution

### Phase 2: Core Trading Operations (Week 2)

**Deliverables:**
- [ ] `brokers/alpaca/trading.py` implemented
  - `place_order()` - market orders
  - `cancel_order()`
  - `get_order_status()`
- [ ] `brokers/alpaca/account.py` implemented
  - `get_account()`
  - `get_buying_power()`
- [ ] Unit tests for trading operations
- [ ] Integration tests with paper trading API

**Validation:**
- Can place and cancel market orders
- Account information retrieval works
- Error handling for insufficient funds
- All operations use paper trading credentials

### Phase 3: Advanced Features (Week 3)

**Deliverables:**
- [ ] `brokers/alpaca/trading.py` - advanced orders
  - Limit orders
  - Stop orders
  - Stop-limit orders
- [ ] `brokers/alpaca/portfolio.py` implemented
  - `get_positions()`
  - `close_position()`
  - `get_portfolio_history()`
- [ ] Risk management validation
- [ ] Complete test coverage

**Validation:**
- All order types work correctly
- Position management functional
- Risk limits enforced
- Portfolio queries accurate

### Phase 4: Tool Integration (Week 4)

**Deliverables:**
- [ ] `agents/utils/trading_execution_tools.py` implemented
- [ ] Tool registration logic
- [ ] Agent integration updates
- [ ] End-to-end integration tests
- [ ] User documentation

**Validation:**
- Tools accessible to agents
- Trader agent can execute trades
- Safety mechanisms work end-to-end
- Documentation complete

### Phase 5: Production Readiness (Week 5)

**Deliverables:**
- [ ] Complete test suite (90%+ coverage)
- [ ] Security audit completed
- [ ] Performance testing
- [ ] Error handling validation
- [ ] Production deployment guide
- [ ] Rollback procedures

**Validation:**
- All tests passing
- No security vulnerabilities
- Performance acceptable
- Documentation comprehensive
- Team trained on system

---

## 11. Code Examples

### 11.1 Basic Trade Execution

```python
from tradingagents.brokers.interface import route_to_broker
from tradingagents.brokers.config import get_config

# Check configuration
config = get_config()
print(f"Broker: {config['trading_broker']}")
print(f"Mode: {config['broker_mode']}")
print(f"Auto-execute: {config['auto_execute_trades']}")

# Place a market buy order
order = route_to_broker(
    "place_order",
    symbol="AAPL",
    qty=10,
    side="buy",
    order_type="market"
)

print(f"Order placed: {order['order_id']}")
print(f"Status: {order['status']}")
```

### 11.2 Agent Using Trading Tools

```python
from langchain_openai import ChatOpenAI
from tradingagents.agents.utils.trading_execution_tools import execute_trade, get_account_status

# Initialize LLM
llm = ChatOpenAI(model="gpt-4")

# Agent decides to trade based on analysis
decision = llm.invoke([
    {"role": "system", "content": "You are a trading agent."},
    {"role": "user", "content": "Based on your analysis, should we buy AAPL?"}
])

# If decision is to buy, execute trade
if "buy" in decision.content.lower():
    result = execute_trade.invoke({
        "symbol": "AAPL",
        "action": "buy",
        "quantity": 10
    })
    print(f"Trade executed: {result}")

# Check account status
status = get_account_status.invoke({})
print(f"Account: {status}")
```

### 11.3 Position Management

```python
from tradingagents.brokers.interface import route_to_broker

# Get all positions
positions = route_to_broker("get_positions")
for pos in positions:
    print(f"{pos['symbol']}: {pos['qty']} shares @ ${pos['current_price']}")
    print(f"  P&L: ${pos['unrealized_pl']} ({pos['unrealized_plpc']:.2%})")

# Close a specific position
result = route_to_broker("close_position", symbol="AAPL")
print(f"Closed AAPL position: {result}")

# Get updated positions
positions = route_to_broker("get_positions")
print(f"Remaining positions: {len(positions)}")
```

---

## 12. Architecture Decision Records (ADRs)

### ADR-001: Separate Broker Layer from Data Layer

**Decision:** Create a separate `brokers/` directory instead of adding trading functionality to `dataflows/`.

**Rationale:**
- **Separation of Concerns**: Data retrieval and trade execution are fundamentally different operations
- **Security**: Trading operations require different security controls
- **Configuration**: Different rate limits, credentials, and endpoints
- **Testing**: Trading operations need more rigorous testing and mocking
- **Risk Management**: Easier to apply risk controls to isolated trading layer

**Alternatives Considered:**
1. Add trading to `dataflows/` - Rejected: Mixes read-only and write operations
2. Single `trading.py` file - Rejected: Would become too large and complex

### ADR-002: Mirror dataflows/interface.py Pattern

**Decision:** Use the same routing architecture as `dataflows/interface.py`.

**Rationale:**
- **Consistency**: Developers already understand this pattern
- **Proven**: Pattern works well for multiple data vendors
- **Extensibility**: Easy to add new brokers (Interactive Brokers, etc.)
- **Fallback Support**: Can implement broker fallback if needed
- **Configuration**: Reuse existing configuration patterns

**Alternatives Considered:**
1. Direct broker SDK usage - Rejected: No abstraction for multi-broker support
2. Factory pattern - Rejected: Overly complex for our needs

### ADR-003: Separate Paper and Live Credentials

**Decision:** Use different environment variables for paper and live trading.

**Rationale:**
- **Safety**: Prevents accidental live trading with wrong credentials
- **Clarity**: Explicit about which mode is being used
- **Testing**: Can test without risk of live API calls
- **Audit**: Clear separation in logs and monitoring

**Environment Variables:**
- Paper: `ALPACA_PAPER_API_KEY`, `ALPACA_PAPER_SECRET_KEY`
- Live: `ALPACA_LIVE_API_KEY`, `ALPACA_LIVE_SECRET_KEY`

### ADR-004: Default to Paper Trading

**Decision:** System defaults to paper trading mode; live trading requires explicit configuration.

**Rationale:**
- **Safety First**: Never risk real money by default
- **Development**: Developers can test freely in paper mode
- **Education**: New users learn with paper trading
- **Risk Management**: Requires conscious decision to enable live trading

**Configuration:**
```python
"broker_mode": "paper",  # Default
"auto_execute_trades": False,  # Default
```

### ADR-005: Three-Module Structure for Alpaca

**Decision:** Split Alpaca implementation into `trading.py`, `account.py`, and `portfolio.py`.

**Rationale:**
- **File Size**: Keeps each file under 500 lines
- **Modularity**: Clear separation of responsibilities
- **Testing**: Easier to write focused tests
- **Maintenance**: Changes to one area don't affect others

**Alternative Considered:**
- Single `broker.py` file - Rejected: Would exceed 500 line limit

---

## 13. Future Enhancements

### 13.1 Additional Brokers

**Interactive Brokers Integration:**
```
brokers/
├── interactive_brokers/
│   ├── __init__.py
│   ├── common.py
│   ├── trading.py
│   ├── account.py
│   └── portfolio.py
```

**Configuration:**
```python
"trading_broker": "interactive_brokers",
```

### 13.2 Advanced Order Types

- Bracket orders (take-profit + stop-loss)
- Trailing stops
- One-cancels-other (OCO)
- Good-til-date (GTD)

### 13.3 Risk Management

- Real-time position size validation
- Portfolio-level risk limits
- Automatic stop-loss placement
- Volatility-based position sizing

### 13.4 Analytics

- Trade performance tracking
- Strategy backtesting integration
- Portfolio analytics dashboard
- Risk metrics calculation

### 13.5 Multi-Account Support

```python
"broker_accounts": {
    "conservative": {
        "broker": "alpaca",
        "mode": "paper",
        "account_id": "account1"
    },
    "aggressive": {
        "broker": "alpaca",
        "mode": "paper",
        "account_id": "account2"
    }
}
```

---

## 14. Documentation Requirements

### 14.1 User Documentation

**File: `docs/alpaca/user-guide.md`**
- Getting started with paper trading
- Environment variable setup
- Configuration options
- Trading tool usage examples
- Safety best practices
- Troubleshooting guide

**File: `docs/alpaca/api-reference.md`**
- Complete function reference
- Parameter descriptions
- Return value specifications
- Error codes and handling
- Code examples

### 14.2 Developer Documentation

**File: `docs/alpaca/developer-guide.md`**
- Architecture overview
- Adding new brokers
- Extending functionality
- Testing guidelines
- Contributing guide

**File: `docs/alpaca/security-guide.md`**
- Credential management
- Safety mechanisms
- Audit trail
- Risk management
- Compliance considerations

---

## 15. Success Criteria

The broker layer implementation will be considered successful when:

### Functional Requirements
- ✅ Can place market, limit, and stop orders via Alpaca API
- ✅ Can retrieve account information and buying power
- ✅ Can query and manage positions
- ✅ Can check order status and history
- ✅ Works in both paper and live modes
- ✅ Integrates with existing trader agent
- ✅ Tools accessible to LangChain agents

### Non-Functional Requirements
- ✅ 90%+ test coverage
- ✅ All operations complete in < 5 seconds
- ✅ No hardcoded credentials
- ✅ Paper trading is the default mode
- ✅ Live trading requires explicit configuration
- ✅ Comprehensive error handling
- ✅ Complete documentation
- ✅ Code follows project patterns
- ✅ Files under 500 lines
- ✅ Passes security review

### Safety Requirements
- ✅ Default configuration prevents live trading
- ✅ Auto-execution disabled by default
- ✅ Separate credentials for paper/live
- ✅ Risk limits enforced
- ✅ All trades logged
- ✅ No accidental execution possible

---

## 16. Risk Assessment

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| API rate limiting | Medium | High | Implement rate limit handling, retry logic |
| Authentication failure | High | Low | Comprehensive credential validation, clear error messages |
| Order execution failure | High | Medium | Robust error handling, fallback mechanisms |
| Network issues | Medium | Medium | Timeout handling, retry logic, circuit breaker |
| Data consistency | Medium | Low | Atomic operations, transaction logging |

### Business Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Accidental live trading | Critical | Low | Multiple safety layers, default to paper mode |
| Incorrect order execution | High | Low | Input validation, confirmation step |
| Insufficient testing | High | Medium | Comprehensive test suite, manual QA |
| Poor documentation | Medium | Medium | Documentation as deliverable, peer review |
| User error | High | Medium | Clear UI/UX, safety warnings, education |

### Mitigation Strategies

1. **Accidental Live Trading Prevention:**
   - Default to paper mode
   - Require explicit `auto_execute_trades: True`
   - Separate live credentials
   - Warning messages in logs
   - Confirmation prompts

2. **Comprehensive Testing:**
   - Unit tests for all functions
   - Integration tests with paper API
   - Mock tests for edge cases
   - Manual QA before production
   - Staged rollout

3. **Documentation:**
   - Code comments
   - API documentation
   - User guides
   - Security guidelines
   - Deployment procedures

---

## 17. Conclusion

This architecture provides a robust, safe, and extensible foundation for integrating Alpaca trading capabilities into the TradingAgents system. By following the established patterns from the data vendor layer, we ensure consistency and maintainability while adding powerful new execution capabilities.

**Key Achievements:**
- ✅ Mirrors proven dataflows architecture
- ✅ Multiple safety layers prevent accidental trading
- ✅ Extensible for future brokers
- ✅ Comprehensive error handling
- ✅ Well-defined API contracts
- ✅ Clear migration path

**Next Steps:**
1. **Coder Agent**: Implement the architecture as specified
2. **Tester Agent**: Create comprehensive test suite
3. **Reviewer Agent**: Code review and security audit
4. **Documentation Agent**: User and developer guides

**Ready for Implementation:** This design is complete and ready for the development team to begin implementation. All architectural decisions are documented, patterns are established, and success criteria are defined.

---

## Appendix A: File Checklist

**New Files to Create:**

```
tradingagents/brokers/
├── __init__.py                       # Package exports
├── interface.py                      # Routing interface (300-400 lines)
├── config.py                         # Configuration access (50-100 lines)
│
├── alpaca/
│   ├── __init__.py                   # Alpaca exports
│   ├── common.py                     # Client, auth, errors (200-250 lines)
│   ├── trading.py                    # Order operations (250-350 lines)
│   ├── account.py                    # Account info (100-150 lines)
│   └── portfolio.py                  # Position queries (150-200 lines)

tradingagents/agents/utils/
└── trading_execution_tools.py        # LangChain tools (200-300 lines)

tests/
├── test_broker_interface.py          # Interface tests (150-200 lines)
├── test_alpaca_broker.py              # Alpaca tests (200-300 lines)
└── test_broker_integration.py        # Integration tests (100-150 lines)

docs/alpaca/
├── user-guide.md                     # User documentation
├── api-reference.md                  # API docs
├── developer-guide.md                # Developer docs
└── security-guide.md                 # Security docs
```

**Files to Update:**

```
tradingagents/default_config.py       # Add broker configuration
tradingagents/agents/trader/trader.py # Optional: Enhanced execution
```

**Total Estimated Lines of Code:** ~2,000-2,800 lines (excluding tests and docs)

---

## Appendix B: Glossary

- **Broker**: A platform that executes trades on behalf of users (e.g., Alpaca, Interactive Brokers)
- **Paper Trading**: Simulated trading with fake money for testing and learning
- **Live Trading**: Real trading with actual money
- **Order Type**: Type of trade order (market, limit, stop, etc.)
- **Position**: Current holding of a stock (quantity owned)
- **Buying Power**: Available cash for purchasing stocks
- **Time in Force**: How long an order remains active (day, GTC, IOC, etc.)
- **Fill**: Completed execution of an order
- **Routing**: Directing method calls to appropriate broker implementation
- **Vendor**: Another term for broker or data provider

---

**Document End**

*This architecture design is ready for implementation by the coding agent. All patterns, contracts, and specifications are clearly defined and follow project standards.*
