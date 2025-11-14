# Alpaca Trading Integration - Comprehensive Test Strategy

## Overview

This document outlines the comprehensive test-driven development (TDD) strategy for integrating Alpaca trading APIs into the TradingAgents platform. The strategy follows industry best practices with a focus on reliability, maintainability, and comprehensive coverage.

## Testing Philosophy

- **Test-First Development**: Write tests before implementation
- **Comprehensive Coverage**: Target >90% code coverage
- **Isolated Tests**: Each test should be independent and repeatable
- **Fast Feedback**: Unit tests should run in <100ms each
- **Real-World Scenarios**: Integration tests use Alpaca paper trading
- **Security First**: Never expose real credentials in tests

## Test Pyramid Structure

```
         /\
        /E2E\      <- 10% - Complete workflows (slow, high value)
       /------\
      /Integr. \   <- 30% - API communication (moderate speed)
     /----------\
    /   Unit     \ <- 60% - Function-level (fast, focused)
   /--------------\
```

## Directory Structure

```
tests/alpaca/
├── unit/                   # Unit tests (60% of tests)
│   ├── test_auth.py       # Authentication logic
│   ├── test_market_data.py # Market data functions
│   ├── test_orders.py      # Order management
│   ├── test_positions.py   # Position tracking
│   ├── test_account.py     # Account operations
│   └── test_config.py      # Configuration validation
├── integration/            # Integration tests (30% of tests)
│   ├── test_api_auth.py   # API authentication flow
│   ├── test_data_retrieval.py # Data fetching from API
│   ├── test_order_lifecycle.py # Order CRUD operations
│   ├── test_streaming.py   # Real-time data streaming
│   └── test_error_handling.py # API error scenarios
├── e2e/                    # End-to-end tests (10% of tests)
│   ├── test_trading_workflow.py # Complete trading flow
│   ├── test_data_pipeline.py    # Data fetch -> process -> store
│   └── test_recovery.py         # Error recovery scenarios
├── fixtures/               # Test data and mocks
│   ├── api_responses/     # Sample API responses
│   ├── mock_data/         # Test datasets
│   └── credentials.py     # Mock credential helpers
├── utils/                  # Test utilities
│   ├── __init__.py
│   ├── mock_alpaca.py     # Alpaca API mocking
│   ├── assertions.py      # Custom assertions
│   └── helpers.py         # Test helper functions
├── pytest.ini             # Pytest configuration
├── conftest.py            # Shared fixtures
└── run_tests.sh           # CI/CD test runner
```

## Test Categories

### 1. Unit Tests (60% - Fast, Focused)

**Scope**: Test individual functions in isolation with mocked dependencies.

**Categories**:
- **Authentication**: API key validation, token generation, credential management
- **Market Data**: Price parsing, historical data formatting, indicator calculations
- **Orders**: Order validation, parameter sanitization, type conversion
- **Positions**: Position calculations, PnL computation, portfolio aggregation
- **Account**: Balance checks, buying power calculations, status parsing
- **Configuration**: Environment validation, settings parsing, defaults

**Requirements**:
- Run in <100ms each
- No external API calls
- Mock all dependencies
- Test edge cases and error conditions
- Achieve >95% code coverage

**Example Test Structure**:
```python
# tests/alpaca/unit/test_orders.py
import pytest
from unittest.mock import Mock, patch
from alpaca.orders import create_market_order, validate_order_params

class TestCreateMarketOrder:
    def test_valid_market_order(self):
        """Should create valid market order with required params"""
        order = create_market_order(
            symbol="AAPL",
            qty=10,
            side="buy"
        )
        assert order["symbol"] == "AAPL"
        assert order["qty"] == 10
        assert order["side"] == "buy"
        assert order["type"] == "market"

    def test_invalid_quantity_raises_error(self):
        """Should raise ValueError for negative quantity"""
        with pytest.raises(ValueError, match="Quantity must be positive"):
            create_market_order("AAPL", -10, "buy")

    def test_invalid_side_raises_error(self):
        """Should raise ValueError for invalid side"""
        with pytest.raises(ValueError, match="Side must be 'buy' or 'sell'"):
            create_market_order("AAPL", 10, "invalid")
```

### 2. Integration Tests (30% - API Communication)

**Scope**: Test integration with Alpaca API using paper trading environment.

**Categories**:
- **API Authentication**: Real credential validation, token refresh, session management
- **Data Retrieval**: Market data API calls, historical data fetching, rate limiting
- **Order Lifecycle**: Create, modify, cancel orders via API
- **Streaming**: WebSocket connections, real-time data handling
- **Error Handling**: Network errors, API errors, rate limits, timeouts

**Requirements**:
- Use Alpaca paper trading environment
- Test real API communication
- Handle rate limits gracefully
- Test retry logic and timeouts
- Run in <5 seconds each

**Example Test Structure**:
```python
# tests/alpaca/integration/test_order_lifecycle.py
import pytest
from alpaca.client import AlpacaClient

@pytest.fixture
def paper_client():
    """Create client connected to paper trading"""
    return AlpacaClient(
        api_key=os.getenv("ALPACA_PAPER_KEY"),
        secret_key=os.getenv("ALPACA_PAPER_SECRET"),
        paper=True
    )

class TestOrderLifecycle:
    def test_create_modify_cancel_order(self, paper_client):
        """Should complete full order lifecycle"""
        # Create order
        order = paper_client.submit_order(
            symbol="AAPL",
            qty=1,
            side="buy",
            type="limit",
            limit_price=150.00
        )
        assert order.status == "accepted"

        # Modify order
        modified = paper_client.replace_order(
            order.id,
            limit_price=145.00
        )
        assert modified.limit_price == 145.00

        # Cancel order
        cancelled = paper_client.cancel_order(order.id)
        assert cancelled.status == "canceled"
```

### 3. End-to-End Tests (10% - Complete Workflows)

**Scope**: Test complete user workflows from start to finish.

**Scenarios**:
- **Trading Workflow**: Fetch data → Analyze → Place order → Monitor → Close position
- **Data Pipeline**: Stream market data → Process → Store → Retrieve
- **Recovery Scenarios**: Connection loss → Reconnect → Resume → Verify state

**Requirements**:
- Test realistic user scenarios
- Use paper trading exclusively
- Verify system state consistency
- Test error recovery mechanisms
- Can run up to 30 seconds each

**Example Test Structure**:
```python
# tests/alpaca/e2e/test_trading_workflow.py
class TestCompleteTradingWorkflow:
    def test_intraday_trading_cycle(self, paper_client, data_processor):
        """Should complete full intraday trading cycle"""
        # 1. Fetch market data
        bars = paper_client.get_bars("AAPL", "1Min", limit=100)
        assert len(bars) > 0

        # 2. Process data and generate signal
        signal = data_processor.analyze(bars)

        # 3. Place order based on signal
        if signal == "BUY":
            order = paper_client.submit_order(
                symbol="AAPL",
                qty=10,
                side="buy",
                type="market"
            )
            assert order.status in ["filled", "accepted"]

        # 4. Monitor position
        position = paper_client.get_position("AAPL")
        assert position.qty == 10

        # 5. Close position
        close_order = paper_client.close_position("AAPL")
        assert close_order.status in ["filled", "accepted"]
```

## Test Fixtures and Mocks

### API Response Fixtures

Located in `tests/alpaca/fixtures/api_responses/`:

- `account.json` - Sample account data
- `positions.json` - Sample position data
- `orders.json` - Sample order responses
- `bars.json` - Sample market data bars
- `quotes.json` - Sample quote data
- `trades.json` - Sample trade data
- `errors.json` - Sample error responses

### Mock Utilities

```python
# tests/alpaca/utils/mock_alpaca.py
class MockAlpacaClient:
    """Mock Alpaca client for unit tests"""

    def __init__(self, responses=None):
        self.responses = responses or {}
        self.calls = []

    def submit_order(self, **kwargs):
        self.calls.append(("submit_order", kwargs))
        return self.responses.get("submit_order", self._default_order())

    def get_bars(self, symbol, timeframe, **kwargs):
        self.calls.append(("get_bars", {"symbol": symbol, **kwargs}))
        return self.responses.get("get_bars", self._default_bars())
```

## Configuration and Setup

### Pytest Configuration (`pytest.ini`)

```ini
[pytest]
testpaths = tests/alpaca
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --cov=src/alpaca
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=90
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (requires API access)
    e2e: End-to-end tests (complete workflows)
    slow: Tests that take >1 second
env_files =
    .env.test
```

### Shared Fixtures (`conftest.py`)

```python
import pytest
import os
from tests.alpaca.utils.mock_alpaca import MockAlpacaClient

@pytest.fixture
def mock_client():
    """Provide mock Alpaca client for unit tests"""
    return MockAlpacaClient()

@pytest.fixture
def paper_client():
    """Provide real client for paper trading (integration tests)"""
    return AlpacaClient(
        api_key=os.getenv("ALPACA_PAPER_KEY"),
        secret_key=os.getenv("ALPACA_PAPER_SECRET"),
        paper=True
    )

@pytest.fixture
def sample_bars():
    """Load sample bar data from fixtures"""
    import json
    with open("tests/alpaca/fixtures/api_responses/bars.json") as f:
        return json.load(f)
```

## Test Execution Strategy

### Local Development

```bash
# Run all tests
pytest tests/alpaca/

# Run only unit tests (fast)
pytest tests/alpaca/unit/ -m unit

# Run with coverage
pytest tests/alpaca/ --cov=src/alpaca --cov-report=html

# Run specific test file
pytest tests/alpaca/unit/test_orders.py

# Run tests matching pattern
pytest tests/alpaca/ -k "test_order"
```

### CI/CD Pipeline

```bash
# tests/alpaca/run_tests.sh
#!/bin/bash
set -e

echo "Running Alpaca integration tests..."

# Run unit tests (must pass)
echo "→ Unit tests..."
pytest tests/alpaca/unit/ -m unit --cov=src/alpaca --cov-fail-under=95

# Run integration tests (requires paper trading credentials)
if [ -n "$ALPACA_PAPER_KEY" ]; then
    echo "→ Integration tests..."
    pytest tests/alpaca/integration/ -m integration --maxfail=3
else
    echo "⚠️  Skipping integration tests (no credentials)"
fi

# Run E2E tests (only on main branch)
if [ "$CI_BRANCH" = "main" ]; then
    echo "→ E2E tests..."
    pytest tests/alpaca/e2e/ -m e2e --maxfail=1
fi

echo "✅ All tests passed!"
```

## Coverage Requirements

### Overall Target: >90%

- **Unit Tests**: >95% coverage
- **Integration Tests**: >80% coverage (focus on critical paths)
- **E2E Tests**: >70% coverage (focus on user workflows)

### Critical Components (100% Coverage Required)

- Authentication logic
- Order validation
- Error handling
- Configuration parsing
- Security-sensitive code

## Testing Tools and Dependencies

### Core Testing Framework

```python
# Add to requirements.txt or pyproject.toml
pytest>=8.0.0                 # Test framework
pytest-cov>=4.1.0            # Coverage reporting
pytest-mock>=3.12.0          # Mocking utilities
pytest-asyncio>=0.23.0       # Async test support
pytest-timeout>=2.2.0        # Test timeouts
pytest-xdist>=3.5.0          # Parallel execution
```

### Additional Testing Tools

```python
responses>=0.24.0            # HTTP mocking
faker>=22.0.0               # Test data generation
freezegun>=1.4.0            # Time mocking
hypothesis>=6.95.0          # Property-based testing
```

## Edge Cases and Error Scenarios

### Authentication Errors
- Invalid API keys
- Expired credentials
- Rate limit exceeded
- Network timeouts

### Order Errors
- Insufficient buying power
- Invalid symbols
- Market closed
- Order rejected

### Data Errors
- Missing data points
- Malformed responses
- Rate limit exceeded
- Streaming disconnections

### System Errors
- Database connection failures
- Configuration errors
- Memory constraints
- Concurrent access issues

## Security Testing

### Credential Management
- Test credential validation without exposing real keys
- Verify secure storage mechanisms
- Test credential rotation
- Verify no credentials in logs

### API Security
- Test SSL/TLS connections
- Verify signature validation
- Test injection attacks
- Verify input sanitization

## Performance Testing

### Benchmarks
- Order submission: <100ms
- Market data fetch: <500ms
- Historical data query: <2s
- Position updates: <50ms

### Load Testing
- Multiple concurrent orders
- High-frequency data streaming
- Large historical queries
- Bulk position updates

## Monitoring and Reporting

### Test Metrics
- Pass/fail rates
- Code coverage percentage
- Test execution time
- Flaky test detection

### Continuous Monitoring
- Daily test runs
- Coverage trend tracking
- Performance regression detection
- Error pattern analysis

## Best Practices

1. **Test Naming**: Use descriptive names that explain what and why
   - Format: `test_<what>_<condition>_<expected>`
   - Example: `test_order_submission_invalid_symbol_raises_error`

2. **Arrange-Act-Assert**: Structure all tests clearly
   ```python
   # Arrange
   client = MockAlpacaClient()

   # Act
   result = client.submit_order(symbol="AAPL", qty=10, side="buy")

   # Assert
   assert result.symbol == "AAPL"
   ```

3. **One Assertion Per Test**: Focus each test on a single behavior

4. **Test Independence**: Each test should be able to run alone

5. **Mock External Dependencies**: Keep tests fast and reliable

6. **Use Fixtures**: Share setup code via pytest fixtures

7. **Document Complex Tests**: Add docstrings explaining the scenario

8. **Keep Tests DRY**: Use helper functions for common operations

## Coordination with Development

### Test-First Workflow

1. Tester designs tests based on requirements
2. Coder implements features to pass tests
3. Tests validate implementation
4. Refactor with confidence

### Communication Protocol

```bash
# Store test requirements for coder
npx claude-flow@alpha hooks post-edit \
  --file "docs/alpaca/test-strategy.md" \
  --memory-key "hive/testing/strategy"

# Notify team of test completion
npx claude-flow@alpha hooks notify \
  --message "Test strategy complete: 90% coverage target, TDD workflow ready"
```

## Success Criteria

- [ ] Test strategy document complete
- [ ] Pytest configuration set up
- [ ] Test directory structure created
- [ ] Fixture files created
- [ ] Mock utilities implemented
- [ ] Sample tests written for each category
- [ ] CI/CD scripts configured
- [ ] Coverage reporting enabled
- [ ] >90% code coverage achieved
- [ ] All tests passing in CI/CD

## References

- [Alpaca API Documentation](https://alpaca.markets/docs/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Test-Driven Development Guide](https://testdriven.io/blog/modern-tdd/)

---

**Version**: 1.0.0
**Last Updated**: 2025-11-14
**Owner**: Testing Agent
**Status**: Active
