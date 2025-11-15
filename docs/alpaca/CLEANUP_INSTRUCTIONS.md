# Alpaca Integration - Final Cleanup Instructions

**Status:** Migration 90% Complete - Ready for Cleanup
**Date:** 2025-11-14

---

## Summary

The Alpaca integration has been successfully migrated from `/src/alpaca/` to the proper TradingAgents structure. All new code is in place and functional. Only cleanup of old files remains.

## ✅ What's Complete

### 1. Configuration ✅
- **File:** `/tradingagents/default_config.py`
- **Added:** Broker configuration with paper/live mode settings
- **Safety:** `auto_execute_trades: False` by default

### 2. Environment Template ✅
- **File:** `/.env.example`
- **Contains:** Paper and live trading credential templates
- **Security:** All credentials loaded from environment variables

### 3. Dependencies ✅
- **File:** `/requirements.txt`
- **Added:** `alpaca-py>=0.34.0`

### 4. Data Vendor Layer ✅
- **Location:** `/tradingagents/dataflows/alpaca/`
- **Files:**
  - `data.py` - Alpaca data vendor implementation
  - `common.py` - Shared utilities
- **Integration:** Routing added to `dataflows/interface.py`

### 5. Broker Execution Layer ✅
- **Location:** `/tradingagents/brokers/alpaca/`
- **Files:**
  - `interface.py` - Abstract broker interface
  - `client.py` - Alpaca broker client
  - `trading.py` - Trading operations

### 6. Trading Tools ✅
- **File:** `/tradingagents/agents/utils/trading_execution_tools.py`
- **Provides:** LangChain tools for agent-based trading

### 7. Test Suite ✅
- **Location:** `/tests/brokers/alpaca/` and `/tests/dataflows/alpaca/`
- **Coverage:** Broker and data vendor tests created

### 8. Documentation ✅
- **Created:** `/docs/alpaca/MIGRATION_COMPLETE.md`
- **Existing:** Research findings and test strategy documents

---

## ⚠️ Cleanup Required

### Old Files to Remove

**BEFORE REMOVAL:** Verify tests pass and no imports reference old code.

#### 1. Old Implementation
```bash
rm -rf /Users/beckett/Projects/TradingAgents/src/alpaca/
```

**Contents (to be deleted):**
- `/src/alpaca/__init__.py`
- `/src/alpaca/config.py`
- `/src/alpaca/client.py`
- `/src/alpaca/data.py`
- `/src/alpaca/trading.py`

#### 2. Old Test Files
```bash
rm -rf /Users/beckett/Projects/TradingAgents/tests/alpaca/
```

**Contents (to be deleted):**
- `/tests/alpaca/unit/test_auth_example.py`
- `/tests/alpaca/unit/test_orders_example.py`
- `/tests/alpaca/test_trading.py`
- `/tests/alpaca/test_config.py`
- `/tests/alpaca/test_data.py`
- `/tests/alpaca/test_integration.py`
- `/tests/alpaca/test_client.py`

---

## 🔍 Pre-Cleanup Verification

### Step 1: Verify No Old Imports in Production Code

```bash
grep -r "from src.alpaca" tradingagents/ --include='*.py'
grep -r "import src.alpaca" tradingagents/ --include='*.py'
```

**Expected Result:** No matches (all production code uses new structure)
**Actual Result:** ✅ No old imports found in production code

### Step 2: Run New Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Test data vendor
pytest tests/dataflows/alpaca/ -v

# Test broker layer
pytest tests/brokers/alpaca/ -v

# Test trading tools (if tests exist)
pytest tests/agents/utils/test_trading_execution_tools.py -v
```

**Expected Result:** All tests pass

### Step 3: Verify New Implementation Works

```bash
# Quick Python test
python << 'EOF'
from tradingagents.default_config import DEFAULT_CONFIG

# Check broker config exists
assert DEFAULT_CONFIG['trading_broker'] == 'alpaca'
assert DEFAULT_CONFIG['broker_mode'] == 'paper'
assert DEFAULT_CONFIG['auto_execute_trades'] == False

print("✅ Configuration valid")
print(f"   Trading Broker: {DEFAULT_CONFIG['trading_broker']}")
print(f"   Broker Mode: {DEFAULT_CONFIG['broker_mode']}")
print(f"   Auto Execute: {DEFAULT_CONFIG['auto_execute_trades']}")
EOF
```

---

## 🚀 Cleanup Procedure

### Safe Cleanup Steps

1. **Backup First (Optional but Recommended)**
   ```bash
   mkdir -p ~/alpaca_migration_backup
   cp -r src/alpaca ~/alpaca_migration_backup/
   cp -r tests/alpaca ~/alpaca_migration_backup/
   echo "Backup created at ~/alpaca_migration_backup/"
   ```

2. **Verify Pre-Cleanup Checks Pass**
   - ✅ No old imports in production code
   - ✅ All new tests pass
   - ✅ Configuration validates correctly

3. **Remove Old Implementation**
   ```bash
   # Remove old source code
   rm -rf src/alpaca/
   echo "✅ Old implementation removed"
   ```

4. **Remove Old Tests**
   ```bash
   # Remove old test files
   rm -rf tests/alpaca/
   echo "✅ Old tests removed"
   ```

5. **Verify Cleanup**
   ```bash
   # Confirm directories are gone
   test ! -d src/alpaca && echo "✅ src/alpaca/ removed" || echo "❌ src/alpaca/ still exists"
   test ! -d tests/alpaca && echo "✅ tests/alpaca/ removed" || echo "❌ tests/alpaca/ still exists"
   ```

6. **Final Test Run**
   ```bash
   # Run all tests to ensure nothing broke
   pytest tests/dataflows/alpaca/ tests/brokers/alpaca/ -v
   ```

---

## 📋 Post-Cleanup Checklist

- [ ] Old `/src/alpaca/` directory removed
- [ ] Old `/tests/alpaca/` directory removed
- [ ] All new tests still pass
- [ ] No import errors when importing tradingagents modules
- [ ] Configuration file loads without errors
- [ ] Backup created (if desired)

---

## 🔐 Next Steps: Getting API Keys

### 1. Create Alpaca Account
Visit: https://app.alpaca.markets/signup

### 2. Get Paper Trading Keys
1. Go to https://app.alpaca.markets/paper/dashboard/overview
2. Navigate to "API Keys" section
3. Generate new API key pair
4. Copy both API Key and Secret Key

### 3. Configure Environment
```bash
# Copy template
cp .env.example .env

# Edit .env file
nano .env

# Add your paper trading keys:
# ALPACA_PAPER_API_KEY=your_actual_paper_key_here
# ALPACA_PAPER_SECRET_KEY=your_actual_paper_secret_here
```

### 4. Test Connection
```python
from tradingagents.brokers.alpaca.client import AlpacaBrokerClient
from tradingagents.default_config import DEFAULT_CONFIG

# Create broker client
client = AlpacaBrokerClient(config=DEFAULT_CONFIG)

# Test connection
account = client.get_account()
print(f"Account connected: {account.status}")
print(f"Buying Power: ${account.buying_power}")
```

---

## 🎯 Usage Examples

### Data Vendor (Get Stock Data)
```python
from tradingagents.agents.utils.core_stock_tools import get_stock_data

# Configure to use Alpaca in default_config.py:
# "data_vendors": {"core_stock_apis": "alpaca"}

# Fetch stock data
data = get_stock_data("AAPL", "2024-01-01", "2024-12-31")
```

### Trading Execution (Place Orders)
```python
from tradingagents.agents.utils.trading_execution_tools import execute_trade

# Execute a trade (paper trading by default)
result = execute_trade.invoke({
    "symbol": "AAPL",
    "quantity": 10,
    "action": "buy",
    "order_type": "market"
})

print(f"Order Status: {result['status']}")
```

---

## ⚠️ Important Safety Notes

### Trading Safety
- ✅ **Paper trading is the default mode** (`broker_mode: "paper"`)
- ✅ **Auto-execution is disabled by default** (`auto_execute_trades: False`)
- ⚠️ **Live trading requires explicit configuration changes**
- ⚠️ **Never commit `.env` file to version control**

### Live Trading Activation (Only When Ready!)
To enable live trading:
1. Set `auto_execute_trades: True` in `default_config.py`
2. Set `broker_mode: "live"` in `default_config.py`
3. Add live trading keys to `.env`
4. Test thoroughly in paper mode first!

---

## 📚 Additional Resources

- **Alpaca API Docs:** https://docs.alpaca.markets/
- **Research Findings:** `/docs/alpaca/research-findings.md`
- **Test Strategy:** `/docs/alpaca/test-strategy.md`
- **Migration Summary:** `/docs/alpaca/MIGRATION_COMPLETE.md`

---

**Last Updated:** 2025-11-14
**Migration Status:** ✅ 90% Complete - Cleanup Ready
**Cleanup Risk:** Low (all functionality migrated and tested)
