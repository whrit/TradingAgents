# Alpaca Integration - Cleanup Checklist

**Generated:** 2025-11-14
**Based on:** CODE_AUDIT_REPORT.md

---

## ✅ Quick Action Items

### 1. Remove Unused Imports from `data.py`

**File:** `/tradingagents/dataflows/alpaca/data.py`

**Lines to modify:**

```diff
- from typing import Annotated, Optional
+ from typing import Annotated

- from datetime import datetime
- import pandas as pd
- from io import StringIO  # ← REMOVE THIS LINE

from datetime import datetime
import pandas as pd

- from .common import get_client, AlpacaAPIError, AlpacaRateLimitError
+ from .common import get_client, AlpacaRateLimitError
```

**Summary:** Remove 3 unused imports
- `Optional` from typing
- `StringIO` from io
- `AlpacaAPIError` from .common

---

### 2. Add Documentation to `__init__.py`

**File:** `/tradingagents/dataflows/alpaca/__init__.py`

**Add this docstring:**

```python
"""
Alpaca data vendor module.

Provides market data retrieval following the project's data vendor pattern.

Integrated Functions (available via VENDOR_METHODS routing):
    - get_stock_data: Historical OHLCV data (production ready)

Available Functions (tested but not yet routed):
    - get_latest_quote: Real-time bid/ask quotes
    - get_bars: Intraday bar data with custom timeframes

To integrate additional functions:
    1. Add to VENDOR_METHODS in tradingagents/dataflows/interface.py
    2. Add appropriate tool category in TOOLS_CATEGORIES
    3. Create LangChain tool wrapper if needed for agents

Example:
    >>> from tradingagents.dataflows.alpaca import get_stock_data
    >>> data = get_stock_data('AAPL', '2025-01-01', '2025-01-14')
"""
```

---

## 📋 Verification Steps

After making changes, run these checks:

### 1. Verify Imports Still Work
```bash
/Users/beckett/Projects/TradingAgents/.venv/bin/python -c "
from tradingagents.dataflows.alpaca import get_stock_data
from tradingagents.dataflows.alpaca.data import get_latest_quote, get_bars
print('✅ All imports successful')
"
```

### 2. Verify No Unused Imports Remain
```bash
/Users/beckett/Projects/TradingAgents/.venv/bin/python -c "
import ast
with open('tradingagents/dataflows/alpaca/data.py') as f:
    tree = ast.parse(f.read())

imports = []
used_names = set()

for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        for alias in node.names:
            imports.append(alias.asname if alias.asname else alias.name)
    elif isinstance(node, ast.ImportFrom):
        for alias in node.names:
            imports.append(alias.asname if alias.asname else alias.name)
    elif isinstance(node, ast.Name):
        used_names.add(node.id)

unused = [imp for imp in imports if imp not in used_names]
if unused:
    print(f'⚠️ Still unused: {unused}')
else:
    print('✅ No unused imports!')
"
```

### 3. Run Tests
```bash
cd /Users/beckett/Projects/TradingAgents
/Users/beckett/Projects/TradingAgents/.venv/bin/python -m pytest tests/dataflows/test_alpaca_data.py -v
/Users/beckett/Projects/TradingAgents/.venv/bin/python -m pytest tests/dataflows/alpaca/ -v
```

---

## 🎯 Expected Results

After cleanup:

**Before:**
```
tradingagents/dataflows/alpaca/data.py:
  UNUSED: Optional (from typing.Optional)
  UNUSED: StringIO (from io.StringIO)
  UNUSED: AlpacaAPIError (from common.AlpacaAPIError)
```

**After:**
```
tradingagents/dataflows/alpaca/data.py: All imports used ✓
```

---

## 📝 Commit Message Template

```
chore(alpaca): cleanup unused imports and add module documentation

- Remove unused imports from dataflows/alpaca/data.py
  - Remove Optional from typing (not used in type hints)
  - Remove StringIO from io (pandas handles CSV conversion)
  - Remove AlpacaAPIError from common (only AlpacaRateLimitError is used)

- Add comprehensive docstring to dataflows/alpaca/__init__.py
  - Document integrated vs. available functions
  - Clarify which functions are production-ready
  - Add usage examples and integration instructions

Based on code audit: docs/alpaca/CODE_AUDIT_REPORT.md
```

---

## 🔮 Optional Future Enhancements

These are NOT required now but could be added later:

### 1. Integrate `get_latest_quote()`
**When:** If real-time quote data is needed by agents

**Changes needed:**
```python
# In tradingagents/dataflows/interface.py
VENDOR_METHODS = {
    "get_quote": {
        "alpaca": get_latest_quote,
    },
}

TOOLS_CATEGORIES = {
    "real_time_quotes": {
        "description": "Real-time bid/ask quotes",
        "tools": ["get_quote"]
    }
}
```

### 2. Integrate `get_bars()`
**When:** If intraday data (1Min, 5Min, 1Hour) is needed

**Changes needed:**
```python
# In tradingagents/dataflows/interface.py
VENDOR_METHODS = {
    "get_intraday_data": {
        "alpaca": get_bars,
    },
}

TOOLS_CATEGORIES = {
    "intraday_data": {
        "description": "Intraday bar data for technical analysis",
        "tools": ["get_intraday_data"]
    }
}
```

### 3. Add `cancel_order` Tool
**When:** If agents need to cancel orders

**Changes needed:**
```python
# In tradingagents/agents/utils/trading_execution_tools.py
@tool
def cancel_trade_order(
    order_id: Annotated[str, "Order ID to cancel"]
) -> str:
    """Cancel a pending order by ID."""
    from tradingagents.brokers.interface import route_to_broker
    return route_to_broker("cancel_order", order_id)
```

---

## Summary

**Total changes required:** 2 files to edit
**Estimated time:** 15 minutes
**Risk level:** Very low (only removing unused code and adding comments)
**Tests affected:** None (no functional changes)

**Priority:** Medium (cleanup is good practice but not urgent)
