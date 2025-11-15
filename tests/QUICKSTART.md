# TDD Test Suite - Quick Start Guide

## 🚀 Quick Start

### 1. Activate Virtual Environment

```bash
source /Users/beckett/Projects/TradingAgents/.venv/bin/activate
```

### 2. Run All Tests

```bash
# Run everything
pytest tests/ -v

# Run only Alpaca tests
pytest tests/dataflows/alpaca/ tests/brokers/ -v

# Run with coverage
pytest tests/dataflows/alpaca/ --cov=tradingagents/dataflows/alpaca --cov-report=term-missing
```

### 3. Run Specific Test Suites

```bash
# Data vendor authentication & client (26 tests) ✅
pytest tests/dataflows/alpaca/test_common.py -v

# Data vendor interface (25 tests)
pytest tests/dataflows/alpaca/test_data.py -v

# Broker interface (6 tests)
pytest tests/brokers/test_interface.py -v

# Alpaca trading client (4 tests)
pytest tests/brokers/alpaca/test_client.py -v

# Trading operations (10 tests)
pytest tests/brokers/alpaca/test_trading.py -v

# Agent tools (1+ tests)
pytest tests/agents/utils/test_trading_execution_tools.py -v
```

### 4. Run by Marker

```bash
# Only unit tests
pytest -m unit -v

# Only Alpaca-specific
pytest -m alpaca -v

# Only data vendor layer
pytest -m dataflow -v

# Only broker layer
pytest -m broker -v
```

## 📊 Current Status

```
Total Tests:     71
✅ Passing:      36 (data vendor common module)
⚠️  Failing:      10 (expected - TDD in progress)
⏭️  Skipped:      1 (TDD placeholder)
```

## 🎯 Test Coverage by Layer

### Data Vendor (51 tests)
- ✅ `test_common.py` - 26/26 passing (100%)
- 🔄 `test_data.py` - Needs implementation updates

### Broker (20 tests)
- 🔄 `test_interface.py` - 1/6 passing
- 🔄 `test_client.py` - 1/4 passing  
- 🔄 `test_trading.py` - 8/10 passing

### Agent Tools
- ⏳ `test_trading_execution_tools.py` - Not yet implemented

## 🔧 Common Test Commands

### Development Workflow

```bash
# Watch mode (requires pytest-watch)
ptw tests/dataflows/alpaca/

# Run failed tests only
pytest --lf -v

# Run with detailed output
pytest tests/dataflows/alpaca/ -vv

# Stop on first failure
pytest -x tests/

# Show print statements
pytest -s tests/
```

### Coverage Commands

```bash
# HTML coverage report
pytest tests/dataflows/alpaca/ --cov=tradingagents/dataflows/alpaca --cov-report=html
open htmlcov/index.html

# Terminal coverage with missing lines
pytest tests/dataflows/alpaca/ --cov=tradingagents/dataflows/alpaca --cov-report=term-missing

# Fail if coverage below 90%
pytest tests/dataflows/alpaca/ --cov=tradingagents/dataflows/alpaca --cov-fail-under=90
```

## 📝 Test Organization

```
tests/
├── conftest.py              # Shared fixtures & config
├── pytest.ini               # Pytest configuration
├── TEST_SUMMARY.md          # Detailed test documentation
├── QUICKSTART.md            # This file
│
├── dataflows/alpaca/        # Data vendor tests
│   ├── test_common.py       # ✅ Auth & client (26 tests)
│   ├── test_data.py         # Interface tests (25 tests)
│   └── fixtures/            # Mock JSON data
│       ├── sample_order.json
│       ├── sample_positions.json
│       └── sample_account.json
│
├── brokers/                 # Broker layer tests
│   ├── test_interface.py    # Routing tests (6 tests)
│   └── alpaca/
│       ├── test_client.py   # Client tests (4 tests)
│       └── test_trading.py  # Trading tests (10 tests)
│
└── agents/utils/            # Agent tools tests
    └── test_trading_execution_tools.py  # Tool tests
```

## 🎨 Available Fixtures

### From `conftest.py`

```python
# Environment
mock_alpaca_credentials   # Mock API credentials
mock_env_clean           # Clean environment

# Data
sample_order_data        # Order JSON fixture
sample_positions_data    # Positions JSON fixture
sample_account_data      # Account JSON fixture
sample_stock_dataframe   # Sample stock DataFrame

# Mocks
mock_alpaca_data_client  # Mock data client
mock_trading_client      # Mock trading client
mock_config             # Mock configuration
```

### Usage Example

```python
def test_with_fixtures(mock_alpaca_credentials, mock_trading_client):
    """Test using fixtures."""
    assert mock_alpaca_credentials['api_key'] == 'test_api_key_123'
    order = mock_trading_client.submit_order(symbol='AAPL', qty=10)
    assert order.id == 'test-order-123'
```

## 🐛 Debugging Tests

### Verbose Output

```bash
# Show all test details
pytest tests/dataflows/alpaca/test_common.py -vv

# Show local variables on failure
pytest tests/dataflows/alpaca/test_common.py -l

# Show print/log output
pytest tests/dataflows/alpaca/test_common.py -s
```

### Run Single Test

```bash
# By test name
pytest tests/dataflows/alpaca/test_common.py::TestAlpacaCredentials::test_get_credentials_returns_tuple -v

# By keyword match
pytest tests/ -k "credentials" -v
```

### Debug with PDB

```python
def test_something():
    import pdb; pdb.set_trace()  # Debugger breakpoint
    result = some_function()
    assert result == expected
```

```bash
pytest tests/ -s  # Run with -s to see pdb
```

## 📈 TDD Workflow

### The Red-Green-Refactor Cycle

1. **RED** - Write a failing test
```bash
pytest tests/dataflows/alpaca/test_common.py::test_new_feature -v
# Should fail - feature not implemented
```

2. **GREEN** - Write minimal code to pass
```python
# In tradingagents/dataflows/alpaca/common.py
def new_feature():
    return "implemented"
```

```bash
pytest tests/dataflows/alpaca/test_common.py::test_new_feature -v
# Should pass now
```

3. **REFACTOR** - Improve while keeping tests green
```bash
# Make changes
pytest tests/dataflows/alpaca/test_common.py -v
# All tests still pass
```

## 🔍 Test Markers

### Custom Markers

```bash
# List all markers
pytest --markers

# Run specific marker
pytest -m unit -v          # Unit tests only
pytest -m integration -v   # Integration tests
pytest -m alpaca -v        # Alpaca-specific
pytest -m slow -v          # Slow tests
pytest -m "not slow" -v    # Exclude slow tests
```

### Combining Markers

```bash
# Unit tests for Alpaca data vendor
pytest -m "unit and dataflow and alpaca" -v

# Broker tests excluding slow ones
pytest -m "broker and not slow" -v
```

## 📚 Helpful pytest Flags

```bash
-v          # Verbose output
-vv         # Very verbose output
-s          # Show print statements
-x          # Stop on first failure
--lf        # Run last failed tests
--ff        # Run failures first, then rest
--tb=short  # Shorter traceback format
--tb=line   # One-line traceback
-q          # Quiet output
-k EXPR     # Run tests matching expression
-m MARKER   # Run tests with marker
--collect-only  # Show what would be collected
--markers   # Show available markers
```

## 🎯 Next Steps

1. **Review failing tests** to understand requirements
2. **Implement features** guided by test specifications
3. **Run tests frequently** during development
4. **Achieve >90% coverage** for production readiness
5. **Add integration tests** for end-to-end validation

## 📞 Getting Help

- **Test fails?** Read the test docstring for specification
- **Need fixture?** Check `conftest.py` for available fixtures
- **Mock not working?** See examples in existing test files
- **Coverage issues?** Run with `--cov-report=term-missing` to see gaps

## 🔗 Resources

- **Main Documentation:** `/Users/beckett/Projects/TradingAgents/tests/TEST_SUMMARY.md`
- **Pytest Docs:** https://docs.pytest.org/
- **Coverage Docs:** https://coverage.readthedocs.io/
- **Mock Docs:** https://docs.python.org/3/library/unittest.mock.html

---

**Happy Testing! 🧪**
