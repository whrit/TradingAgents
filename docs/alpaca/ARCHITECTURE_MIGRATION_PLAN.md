# Alpaca Integration Architecture Migration Plan

## 🚨 Critical Issue Identified

The Hive Mind created the Alpaca integration in `/src/alpaca/` but the project uses `/tradingagents/` as the main source directory. This document outlines the correct architecture and migration plan.

---

## 📁 Current Project Architecture

```
TradingAgents/
├── tradingagents/              # Main source directory
│   ├── agents/                 # Agent implementations
│   │   ├── analysts/          # Market analysts
│   │   ├── researchers/       # Bull/bear researchers
│   │   ├── risk_mgmt/         # Risk management debators
│   │   ├── managers/          # Research & risk managers
│   │   ├── trader/            # Trading decision agent
│   │   └── utils/             # LangChain tools
│   │       ├── core_stock_tools.py
│   │       ├── fundamental_data_tools.py
│   │       ├── news_data_tools.py
│   │       └── technical_indicators_tools.py
│   ├── dataflows/             # DATA VENDORS (passive - read data)
│   │   ├── alpaca/           # ⚠️ EMPTY - needs implementation
│   │   ├── y_finance.py      # Yahoo Finance integration
│   │   ├── alpha_vantage*.py # Alpha Vantage integration
│   │   ├── local.py          # Local data sources
│   │   ├── openai.py         # OpenAI data processing
│   │   ├── google.py         # Google News
│   │   ├── interface.py      # Vendor routing logic
│   │   └── config.py         # Vendor configuration
│   ├── graph/                 # LangGraph workflow
│   └── default_config.py      # Global configuration
└── tests/                     # Test suite
```

### Key Patterns Observed:

1. **Dataflows = Data Vendors Only**
   - Purpose: Retrieve market data, news, fundamentals
   - Pattern: Each vendor has its own file/directory
   - Examples: `y_finance.py`, `alpha_vantage*.py`, `local.py`

2. **Routing via interface.py**
   - `route_to_vendor()` function routes tool calls to configured vendor
   - Configuration in `default_config.py` under `data_vendors`
   - Tools use `route_to_vendor("get_stock_data", ...)` pattern

3. **LangChain Tools in agents/utils/**
   - Tools decorated with `@tool`
   - Call `route_to_vendor()` internally
   - Examples: `get_stock_data()`, `get_fundamentals()`, `get_news()`

4. **Trader Agent = Decision Making Only**
   - Located in `agents/trader/trader.py`
   - Returns: "FINAL TRANSACTION PROPOSAL: BUY/HOLD/SELL"
   - **Does NOT execute trades** - only makes recommendations

5. **No Trading Execution Layer Exists!**
   - No `place_order()`, `execute_trade()`, or broker integration
   - This is the MISSING piece for Alpaca

---

## 🎯 Where Alpaca Fits

Alpaca provides **TWO distinct capabilities:**

### 1. Market Data (Data Vendor) ✅
- Historical stock/crypto/options data
- Real-time quotes and trades
- Market status and calendar
- **Fits in:** `/tradingagents/dataflows/alpaca/`

### 2. Trading Execution (NEW Layer) ⚠️
- Order placement and management
- Position tracking
- Portfolio management
- Paper vs Live trading
- **Needs NEW directory:** `/tradingagents/brokers/` or `/tradingagents/execution/`

---

## 📋 Proposed Architecture

### Option 1: Separate Data & Execution (Recommended)

```
tradingagents/
├── dataflows/
│   └── alpaca/
│       ├── __init__.py
│       ├── data.py              # Market data only (stocks, crypto, options)
│       └── common.py            # Shared utilities (auth, rate limiting)
│
└── brokers/                      # NEW - Trading execution layer
    ├── __init__.py
    ├── interface.py              # Broker routing logic
    └── alpaca/
        ├── __init__.py
        ├── client.py             # Trading client (paper/live)
        ├── orders.py             # Order management
        ├── positions.py          # Position tracking
        └── portfolio.py          # Account management
```

### Option 2: Unified Alpaca Directory (Simpler)

```
tradingagents/
├── dataflows/
│   └── alpaca/
│       ├── __init__.py
│       ├── data.py              # Market data
│       ├── trading.py           # Trading execution
│       ├── client.py            # Shared client
│       └── config.py            # Configuration
│
└── agents/
    └── trader/
        └── executor.py          # NEW - Executes trader decisions
```

**Recommendation:** **Option 1** - Cleaner separation of concerns, follows existing pattern.

---

## 🔄 Migration Steps

### Phase 1: Create Broker Layer Architecture

1. **Create brokers directory:**
   ```bash
   mkdir -p tradingagents/brokers/alpaca
   ```

2. **Move trading-specific code from `/src/alpaca/`:**
   - `client.py` → `tradingagents/brokers/alpaca/client.py`
   - `trading.py` → `tradingagents/brokers/alpaca/trading.py`
   - `config.py` → `tradingagents/brokers/alpaca/config.py`

3. **Create broker routing interface:**
   ```python
   # tradingagents/brokers/interface.py
   def route_to_broker(action, *args, **kwargs):
       """Route trading actions to configured broker."""
       broker = get_config().get("trading_broker", "alpaca")
       # Similar to dataflows/interface.py pattern
   ```

### Phase 2: Implement Alpaca Data Vendor

1. **Implement data vendor in `/tradingagents/dataflows/alpaca/`:**
   - Extract market data functions from `/src/alpaca/data.py`
   - Follow pattern from `y_finance.py` and `alpha_vantage_stock.py`
   - Implement: `get_stock_data()`, `get_quotes()`, `get_bars()`

2. **Update `dataflows/interface.py`:**
   ```python
   # Add to VENDOR_METHODS
   "get_stock_data": {
       "alpha_vantage": get_alpha_vantage_stock,
       "yfinance": get_YFin_data_online,
       "alpaca": get_alpaca_stock_data,  # NEW
       "local": get_YFin_data,
   }
   ```

3. **Update `default_config.py`:**
   ```python
   "data_vendors": {
       "core_stock_apis": "alpaca",  # Can now select Alpaca for data
       ...
   }
   ```

### Phase 3: Integrate Trading Execution

1. **Create trading tools in `agents/utils/`:**
   ```python
   # tradingagents/agents/utils/trading_execution_tools.py

   @tool
   def execute_trade(
       symbol: str,
       action: str,  # "buy" or "sell"
       quantity: float,
       order_type: str = "market"
   ) -> str:
       """Execute a trade via configured broker."""
       from tradingagents.brokers.interface import route_to_broker
       return route_to_broker("place_order", symbol, action, quantity, order_type)

   @tool
   def get_positions() -> str:
       """Get current portfolio positions."""
       from tradingagents.brokers.interface import route_to_broker
       return route_to_broker("get_positions")

   @tool
   def get_account_balance() -> str:
       """Get account balance and buying power."""
       from tradingagents.brokers.interface import route_to_broker
       return route_to_broker("get_account")
   ```

2. **Extend trader agent to execute trades:**
   ```python
   # tradingagents/agents/trader/executor.py

   def create_trade_executor(trader_agent):
       """Wrapper that executes trader's decisions."""
       def execute_decision(state):
           # Get trader's decision
           decision = trader_agent(state)

           # Parse "BUY/HOLD/SELL" from decision
           action = parse_decision(decision)

           if action in ["BUY", "SELL"]:
               # Execute via broker
               result = execute_trade(
                   symbol=state["company_of_interest"],
                   action=action.lower(),
                   quantity=calculate_position_size(state),
                   order_type="market"
               )
               return {**decision, "execution_result": result}

           return decision

       return execute_decision
   ```

### Phase 4: Update Tests

1. **Move tests to correct locations:**
   ```
   tests/
   ├── dataflows/
   │   └── test_alpaca_data.py      # Data vendor tests
   └── brokers/
       └── alpaca/
           ├── test_client.py
           ├── test_trading.py
           └── test_integration.py
   ```

2. **Update test fixtures to match project patterns**

### Phase 5: Update Configuration

1. **Add broker configuration to `default_config.py`:**
   ```python
   DEFAULT_CONFIG = {
       ...
       # Trading broker configuration
       "trading_broker": "alpaca",           # Active broker
       "broker_mode": "paper",               # paper or live
       "alpaca_paper_api_key": os.getenv("ALPACA_PAPER_API_KEY"),
       "alpaca_paper_secret_key": os.getenv("ALPACA_PAPER_SECRET_KEY"),
       "alpaca_live_api_key": os.getenv("ALPACA_LIVE_API_KEY"),
       "alpaca_live_secret_key": os.getenv("ALPACA_LIVE_SECRET_KEY"),

       # Data vendor configuration (existing)
       "data_vendors": {
           "core_stock_apis": "alpaca",      # Can use Alpaca for data
           ...
       },
   }
   ```

2. **Create `.env.example`:**
   ```bash
   # Alpaca Paper Trading (Safe for testing)
   ALPACA_PAPER_API_KEY=your_paper_key
   ALPACA_PAPER_SECRET_KEY=your_paper_secret

   # Alpaca Live Trading (Production - use with caution)
   # ALPACA_LIVE_API_KEY=your_live_key
   # ALPACA_LIVE_SECRET_KEY=your_live_secret
   ```

### Phase 6: Clean Up

1. **Remove incorrect `/src/alpaca/` directory**
2. **Update all documentation paths**
3. **Verify all imports point to correct locations**

---

## 🔧 Implementation Checklist

- [ ] Create `/tradingagents/brokers/` directory structure
- [ ] Implement Alpaca data vendor in `/tradingagents/dataflows/alpaca/`
- [ ] Implement Alpaca broker in `/tradingagents/brokers/alpaca/`
- [ ] Create broker routing interface (`brokers/interface.py`)
- [ ] Update dataflows routing (`dataflows/interface.py`)
- [ ] Create trading execution tools (`agents/utils/trading_execution_tools.py`)
- [ ] Extend trader agent with execution capability
- [ ] Update `default_config.py` with broker configuration
- [ ] Migrate tests to correct locations
- [ ] Update documentation
- [ ] Remove `/src/alpaca/` directory
- [ ] Create `.env.example` in project root
- [ ] Add Alpaca to requirements.txt (if not already there)

---

## 📊 File Migration Map

| Current Location (WRONG) | Correct Location | Purpose |
|--------------------------|------------------|---------|
| `/src/alpaca/data.py` | `/tradingagents/dataflows/alpaca/data.py` | Market data retrieval |
| `/src/alpaca/client.py` | `/tradingagents/brokers/alpaca/client.py` | Trading client base |
| `/src/alpaca/trading.py` | `/tradingagents/brokers/alpaca/trading.py` | Order/position management |
| `/src/alpaca/config.py` | Merge into `default_config.py` | Configuration |
| `/tests/alpaca/*` | Split into `tests/dataflows/` and `tests/brokers/` | Tests |
| `/docs/alpaca/*` | `/docs/alpaca/` (keep, but update paths) | Documentation |

---

## 🎯 Integration with Existing Trader Agent

The trader agent currently returns text decisions. We need to:

1. **Parse decisions** from trader output:
   ```python
   if "BUY" in trader_output:
       action = "buy"
   elif "SELL" in trader_output:
       action = "sell"
   else:
       action = "hold"
   ```

2. **Execute via new tools:**
   ```python
   if action in ["buy", "sell"]:
       result = execute_trade(symbol, action, quantity)
   ```

3. **Optional: Add to LangGraph workflow:**
   ```python
   # In graph/trading_graph.py
   workflow.add_node("trade_executor", create_trade_executor(trader))
   workflow.add_edge("Trader", "trade_executor")
   ```

---

## 🔒 Security Considerations

1. **Default to paper trading** - Never default to live
2. **Explicit live trading enable** - Require `ENABLE_LIVE_TRADING=true`
3. **Environment-based credentials** - Never hardcode
4. **Position size limits** - Max $10k per position recommended
5. **Pre-trade validation** - Check buying power, validate symbols

---

## ⚡ Next Steps

1. **Review this plan** with team/project owner
2. **Get approval** for architecture decisions
3. **Execute migration** in phases
4. **Test thoroughly** in paper trading mode
5. **Document** new patterns for future integrations

---

## 📝 Questions to Resolve

1. **Should we create a `brokers/` directory or integrate into existing structure?**
   - Recommendation: Create `brokers/` for cleaner separation

2. **Should the trader agent automatically execute or require manual approval?**
   - Recommendation: Add configuration flag `auto_execute_trades: bool`

3. **How do we handle broker failures?**
   - Recommendation: Add retry logic and fallback to different broker

4. **Should we support multiple brokers (Alpaca, Interactive Brokers, etc.)?**
   - Recommendation: Yes - follow same pattern as data vendors

---

**Status:** Architecture analysis complete, awaiting approval to proceed with migration.
