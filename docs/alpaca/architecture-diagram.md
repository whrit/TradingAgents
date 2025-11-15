# Broker Architecture Diagram

## System Overview

```
┌───────────────────────────────────────────────────────────────────┐
│                      Trading Agent System                         │
└───────────────────────────────────────────────────────────────────┘
                                │
                                │
┌───────────────────────────────▼───────────────────────────────────┐
│                         Agent Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │   Market     │  │ Fundamental  │  │   Trader     │            │
│  │  Researcher  │  │   Analyst    │  │    Agent     │            │
│  └──────────────┘  └──────────────┘  └──────┬───────┘            │
└────────────────────────────────────────────────┼──────────────────┘
                                                 │
                                                 │
┌────────────────────────────────────────────────▼──────────────────┐
│                         Tools Layer                               │
│  ┌─────────────────────┐         ┌─────────────────────┐          │
│  │   Data Tools        │         │  Trading Tools      │          │
│  │  (existing)         │         │  (NEW)              │          │
│  ├─────────────────────┤         ├─────────────────────┤          │
│  │ • get_stock_data    │         │ • execute_trade     │          │
│  │ • get_indicators    │         │ • get_positions     │          │
│  │ • get_fundamentals  │         │ • get_account       │          │
│  │ • get_news          │         │ • close_position    │          │
│  └──────────┬──────────┘         └──────────┬──────────┘          │
└─────────────┼──────────────────────────────┼────────────────────┘
              │                              │
              │                              │
┌─────────────▼──────────────────┐  ┌────────▼───────────────────┐
│   Data Vendor Layer            │  │  Broker Layer (NEW)        │
│   (existing)                   │  │                            │
│  ┌──────────────────────────┐  │  │  ┌──────────────────────┐  │
│  │  dataflows/interface.py  │  │  │  │ brokers/interface.py │  │
│  │  route_to_vendor()       │  │  │  │ route_to_broker()    │  │
│  └────────────┬─────────────┘  │  │  └──────────┬───────────┘  │
│               │                │  │             │              │
│     ┌─────────┼─────────┐      │  │  ┌──────────┼──────────┐   │
│     ▼         ▼         ▼      │  │  ▼          ▼          ▼   │
│  ┌────┐   ┌────┐   ┌────┐     │  │ ┌────┐   ┌────┐   ┌────┐  │
│  │YFIN│   │ AV │   │ALP │     │  │ │ALP │   │ IB │   │... │  │
│  └────┘   └────┘   └────┘     │  │ └────┘   └────┘   └────┘  │
└────────────────────────────────┘  └────────────────────────────┘
     │         │         │               │        │        │
     ▼         ▼         ▼               ▼        ▼        ▼
  External Data APIs              External Broker APIs
```

## Broker Layer Internal Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    brokers/interface.py                         │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              route_to_broker(method, *args, **kwargs)     │ │
│  │                                                           │ │
│  │  1. Get broker from config ("alpaca", "ib", etc.)        │ │
│  │  2. Safety check (paper mode? auto_execute enabled?)     │ │
│  │  3. Route to vendor implementation                       │ │
│  └───────────────────────────┬───────────────────────────────┘ │
│                              │                                 │
│              ┌───────────────┼───────────────┐                 │
│              ▼               ▼               ▼                 │
│      ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│      │   Alpaca     │ │     IB       │ │   Future     │       │
│      │   Broker     │ │   Broker     │ │   Brokers    │       │
│      └──────┬───────┘ └──────────────┘ └──────────────┘       │
└─────────────┼──────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    brokers/alpaca/                              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  common.py - Client, Authentication, Errors             │   │
│  │                                                         │   │
│  │  • AlpacaBrokerClient                                   │   │
│  │  • get_alpaca_credentials()                             │   │
│  │  • AlpacaBrokerError, AlpacaRateLimitError, etc.        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  trading.py - Order Execution                           │   │
│  │                                                         │   │
│  │  • place_order()     - Market, limit, stop orders       │   │
│  │  • cancel_order()    - Cancel pending orders            │   │
│  │  • get_order_status()- Check order status               │   │
│  │  • modify_order()    - Update order parameters          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  account.py - Account Management                        │   │
│  │                                                         │   │
│  │  • get_account()     - Account info, balances           │   │
│  │  • get_buying_power()- Available buying power           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  portfolio.py - Position Management                     │   │
│  │                                                         │   │
│  │  • get_positions()   - All positions                    │   │
│  │  • get_position()    - Single position                  │   │
│  │  • close_position()  - Close position                   │   │
│  │  • get_portfolio_history() - Historical performance     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow: Trade Execution

```
1. Agent Decision
   ┌──────────────┐
   │ Trader Agent │ "Buy 10 AAPL based on analysis"
   └──────┬───────┘
          │
          ▼
2. Tool Invocation
   ┌────────────────────────┐
   │ execute_trade()        │
   │ symbol="AAPL"          │
   │ action="buy"           │
   │ quantity=10            │
   └──────┬─────────────────┘
          │
          ▼
3. Routing Layer
   ┌──────────────────────────────────┐
   │ route_to_broker("place_order")   │
   │                                  │
   │ ✓ Check config: broker="alpaca" │
   │ ✓ Safety: mode="paper"          │
   │ ✓ Safety: auto_execute=True     │
   └──────┬───────────────────────────┘
          │
          ▼
4. Vendor Implementation
   ┌──────────────────────────────┐
   │ alpaca/trading.py            │
   │ place_order()                │
   │                              │
   │ • Validate parameters        │
   │ • Get client from common.py  │
   │ • Make API request           │
   │ • Handle response/errors     │
   └──────┬───────────────────────┘
          │
          ▼
5. Broker API
   ┌──────────────────────────────┐
   │ POST https://paper-api.      │
   │ alpaca.markets/v2/orders     │
   │                              │
   │ Headers: API-KEY, SECRET     │
   │ Body: {symbol, qty, side...} │
   └──────┬───────────────────────┘
          │
          ▼
6. Response
   ┌──────────────────────────────┐
   │ Order Confirmation           │
   │                              │
   │ {                            │
   │   order_id: "abc123"         │
   │   status: "filled"           │
   │   symbol: "AAPL"             │
   │   filled_qty: 10             │
   │   filled_avg_price: 150.25   │
   │ }                            │
   └──────┬───────────────────────┘
          │
          ▼
7. Formatted Result
   ┌──────────────────────────────┐
   │ "Order executed successfully:│
   │ Bought 10 shares of AAPL at  │
   │ $150.25 per share.           │
   │ Order ID: abc123"            │
   └──────────────────────────────┘
```

## Configuration Flow

```
┌─────────────────────────────────┐
│  default_config.py              │
│                                 │
│  DEFAULT_CONFIG = {             │
│    "trading_broker": "alpaca",  │
│    "broker_mode": "paper",      │
│    "auto_execute_trades": False │
│  }                              │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  brokers/config.py              │
│                                 │
│  def get_config():              │
│    return DEFAULT_CONFIG        │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  brokers/interface.py           │
│                                 │
│  config = get_config()          │
│  broker = config["trading_broker"]│
│  mode = config["broker_mode"]   │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  brokers/alpaca/common.py       │
│                                 │
│  if mode == "paper":            │
│    api_key = ALPACA_PAPER_API_KEY│
│  else:                          │
│    api_key = ALPACA_LIVE_API_KEY│
└─────────────────────────────────┘
```

## Safety Mechanism Layers

```
┌──────────────────────────────────────────────────────────┐
│  Layer 1: Configuration Defaults                         │
│  ────────────────────────────────────────────────────    │
│  • broker_mode = "paper" (NOT "live")                    │
│  • auto_execute_trades = False (NOT True)                │
└──────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────┐
│  Layer 2: Environment Variables                          │
│  ────────────────────────────────────────────────────    │
│  • Separate PAPER and LIVE credentials                   │
│  • Live credentials optional                             │
│  • Must explicitly set to enable live trading            │
└──────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────┐
│  Layer 3: Routing Safety Checks                          │
│  ────────────────────────────────────────────────────    │
│  if broker_mode == "live" and not auto_execute:          │
│    return "blocked"                                      │
└──────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────┐
│  Layer 4: Tool Registration                              │
│  ────────────────────────────────────────────────────    │
│  if not auto_execute_trades:                             │
│    # Don't register trading tools                        │
│    tools = data_tools_only                               │
└──────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────┐
│  Layer 5: Risk Management                                │
│  ────────────────────────────────────────────────────    │
│  • Validate order size < max_order_value                 │
│  • Validate position < max_position_size                 │
│  • Require confirmation if enabled                       │
└──────────────────────────────────────────────────────────┘
```

## Comparison: Data Layer vs Broker Layer

```
┌─────────────────────────────┬─────────────────────────────┐
│      Data Layer             │      Broker Layer           │
│   (dataflows/)              │      (brokers/)             │
├─────────────────────────────┼─────────────────────────────┤
│ Purpose:                    │ Purpose:                    │
│   Read market data          │   Execute trades            │
│                             │                             │
│ Operations:                 │ Operations:                 │
│   • Get stock prices        │   • Place orders            │
│   • Get indicators          │   • Cancel orders           │
│   • Get fundamentals        │   • Manage positions        │
│   • Get news                │   • Query account           │
│                             │                             │
│ Characteristics:            │ Characteristics:            │
│   ✓ Read-only               │   ✓ Read and Write          │
│   ✓ No financial risk       │   ✓ Financial risk!         │
│   ✓ Can retry freely        │   ✓ Retry carefully         │
│   ✓ Fallback to other vendors│  ✓ Single broker per order │
│   ✓ Caching possible        │   ✗ No caching (real-time)  │
│                             │                             │
│ Safety:                     │ Safety:                     │
│   Low priority              │   CRITICAL priority         │
│   (worst case: stale data)  │   (worst case: lost money)  │
│                             │                             │
│ Credentials:                │ Credentials:                │
│   ALPACA_API_KEY (shared)   │   ALPACA_PAPER_API_KEY      │
│   ALPACA_SECRET_KEY         │   ALPACA_LIVE_API_KEY       │
│                             │   (separate for safety)     │
└─────────────────────────────┴─────────────────────────────┘
```

## File Organization Rationale

```
Why split alpaca/ into trading.py, account.py, portfolio.py?

┌─────────────────────────────────────────────────────────┐
│  Single broker.py file (❌ Rejected)                    │
│                                                         │
│  Cons:                                                  │
│    • Would be 600-800 lines (exceeds 500 limit)        │
│    • Mixing different concerns                         │
│    • Harder to test                                    │
│    • Harder to maintain                                │
│    • Harder for parallel development                   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Three separate modules (✅ Chosen)                     │
│                                                         │
│  trading.py (250-350 lines)                            │
│    • place_order, cancel_order, modify_order           │
│    • All order execution logic                         │
│    • Single responsibility: trading operations         │
│                                                         │
│  account.py (100-150 lines)                            │
│    • get_account, get_buying_power                     │
│    • Account information queries                       │
│    • Single responsibility: account data               │
│                                                         │
│  portfolio.py (150-200 lines)                          │
│    • get_positions, close_position                     │
│    • Portfolio queries and management                  │
│    • Single responsibility: position data              │
│                                                         │
│  Pros:                                                  │
│    ✓ Each file under 500 lines                         │
│    ✓ Clear separation of concerns                      │
│    ✓ Easy to test independently                        │
│    ✓ Easy to maintain                                  │
│    ✓ Parallel development possible                     │
│    ✓ Follows project patterns                          │
└─────────────────────────────────────────────────────────┘
```

## Legend

- **Solid lines** (─│): Component relationships
- **Arrows** (▼ ►): Data/control flow
- **Boxes** (┌─┐): Components/modules
- **✓**: Requirement met
- **✗**: Requirement not met
- **❌**: Rejected approach
- **✅**: Chosen approach
