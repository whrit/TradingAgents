# Broker Architecture - Quick Reference

**Full Design:** See [broker-architecture-design.md](./broker-architecture-design.md)

## Directory Structure

```
tradingagents/brokers/
├── interface.py          # Routing (mirrors dataflows/interface.py)
├── config.py            # Configuration access
└── alpaca/              # Alpaca implementation
    ├── common.py        # Client, auth, errors
    ├── trading.py       # Order execution
    ├── account.py       # Account info
    └── portfolio.py     # Position management
```

## Core Patterns

### 1. Routing Pattern (same as dataflows)
```python
from tradingagents.brokers.interface import route_to_broker

result = route_to_broker("place_order", symbol="AAPL", qty=10, side="buy")
```

### 2. Tool Pattern
```python
from langchain_core.tools import tool
from tradingagents.brokers.interface import route_to_broker

@tool
def execute_trade(symbol: str, action: str, quantity: float) -> str:
    return route_to_broker("place_order", symbol=symbol, qty=quantity, side=action)
```

### 3. Configuration
```python
DEFAULT_CONFIG = {
    "trading_broker": "alpaca",
    "broker_mode": "paper",  # NEVER "live" by default
    "auto_execute_trades": False,  # Safety first!
}
```

## Key Design Decisions

1. **Separate from dataflows/** - Trading is write operations, data is read-only
2. **Mirror dataflows pattern** - Consistency across codebase
3. **Paper trading default** - Safety first, always
4. **Multi-broker ready** - Easy to add Interactive Brokers, etc.
5. **Three-module split** - trading.py, account.py, portfolio.py (keep files < 500 lines)

## Environment Variables

```bash
# Paper Trading (default)
ALPACA_PAPER_API_KEY=...
ALPACA_PAPER_SECRET_KEY=...

# Live Trading (requires explicit config)
ALPACA_LIVE_API_KEY=...
ALPACA_LIVE_SECRET_KEY=...
```

## Safety Mechanisms

1. **Config Layer**: Default to paper mode
2. **Routing Layer**: Block execution if `auto_execute_trades: False`
3. **Tool Layer**: Only register tools if execution enabled
4. **Risk Layer**: Validate order size and position limits

## Implementation Phases

1. **Week 1**: Foundation (interface.py, config.py, common.py)
2. **Week 2**: Trading operations (place_order, cancel_order)
3. **Week 3**: Advanced features (limit orders, positions)
4. **Week 4**: Tool integration (LangChain tools)
5. **Week 5**: Production readiness (tests, security)

## API Contracts

### Order Response
```python
{
    "order_id": "...",
    "status": "filled",
    "symbol": "AAPL",
    "qty": 10,
    "filled_avg_price": 150.25
}
```

### Position Response
```python
{
    "symbol": "AAPL",
    "qty": 10,
    "market_value": 1525.00,
    "unrealized_pl": 25.00
}
```

## Testing Strategy

- **Unit Tests**: Each function independently
- **Integration Tests**: With paper trading API
- **Mock Tests**: No actual API calls
- **90%+ Coverage**: Required for production

## Success Criteria

✅ Place orders via Alpaca API
✅ Query account and positions
✅ Work in paper and live modes
✅ Integrate with trader agent
✅ 90%+ test coverage
✅ Default to paper trading
✅ Comprehensive documentation

## Next Steps

1. **Coder**: Implement architecture
2. **Tester**: Create test suite
3. **Reviewer**: Security audit
4. **Documentation**: User guides
