# Alpaca Trading Integration - Test Suite

Comprehensive test-driven development (TDD) framework for Alpaca trading API integration.

## Quick Start

### 1. Install Dependencies

```bash
# Install testing dependencies
pip install pytest pytest-cov pytest-mock pytest-asyncio pytest-timeout responses faker
```

### 2. Configure Paper Trading Credentials

```bash
# Copy environment template
cp tests/alpaca/.env.test.example tests/alpaca/.env.test

# Edit .env.test and add your Alpaca paper trading credentials
# Get credentials from: https://app.alpaca.markets/paper/dashboard/overview
```

### 3. Run Tests

```bash
# Run all unit tests (fast, no credentials needed)
pytest tests/alpaca/unit/ -m unit

# Run integration tests (requires paper trading credentials)
pytest tests/alpaca/integration/ -m integration

# Run all tests with coverage
./tests/alpaca/run_tests.sh --all

# Run specific test file
pytest tests/alpaca/unit/test_auth_example.py -v
```

## Test Structure

```
tests/alpaca/
├── unit/                          # Unit tests (60% of tests)
│   ├── test_auth_example.py      # Authentication tests
│   ├── test_orders_example.py    # Order management tests
│   └── ...                        # Add more as implementation grows
├── integration/                   # Integration tests (30% of tests)
│   ├── test_api_connection_example.py
│   └── ...
├── e2e/                           # End-to-end tests (10% of tests)
│   ├── test_trading_workflow_example.py
│   └── ...
├── fixtures/                      # Test data and mocks
│   ├── api_responses/            # Sample API responses
│   │   ├── account.json
│   │   ├── orders.json
│   │   ├── positions.json
│   │   └── bars.json
│   └── credentials.py            # Mock credential utilities
├── utils/                         # Test utilities
│   ├── mock_alpaca.py            # Mock Alpaca client
│   ├── assertions.py             # Custom assertions
│   └── helpers.py                # Test helpers
├── conftest.py                    # Shared fixtures
├── pytest.ini                     # Pytest configuration
├── run_tests.sh                   # Test runner script
└── README.md                      # This file
```

## Test Categories

### Unit Tests (Fast, Isolated)
- **Purpose**: Test individual functions in isolation
- **Speed**: <100ms per test
- **Dependencies**: Mocked
- **Coverage Target**: >95%
- **Run**: `pytest tests/alpaca/unit/ -m unit`

### Integration Tests (API Communication)
- **Purpose**: Test integration with Alpaca API
- **Speed**: <5 seconds per test
- **Dependencies**: Alpaca paper trading API
- **Coverage Target**: >80%
- **Run**: `pytest tests/alpaca/integration/ -m integration`

### E2E Tests (Complete Workflows)
- **Purpose**: Test realistic user workflows
- **Speed**: <30 seconds per test
- **Dependencies**: Alpaca paper trading API
- **Coverage Target**: >70%
- **Run**: `pytest tests/alpaca/e2e/ -m e2e`

## Test Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only e2e tests
pytest -m e2e

# Run slow tests
pytest -m slow

# Exclude slow tests
pytest -m "not slow"
```

## Coverage Requirements

- **Overall Target**: >90% code coverage
- **Unit Tests**: >95% coverage
- **Integration Tests**: >80% coverage
- **Critical Components**: 100% coverage
  - Authentication logic
  - Order validation
  - Error handling
  - Configuration parsing

## Using Test Utilities

### Mock Alpaca Client

```python
from tests.alpaca.utils import MockAlpacaClient

def test_order_submission():
    client = MockAlpacaClient()
    order = client.submit_order(
        symbol="AAPL",
        qty=10,
        side="buy"
    )
    assert order["symbol"] == "AAPL"
```

### Custom Assertions

```python
from tests.alpaca.utils import assert_valid_order, assert_valid_position

def test_order_structure(mock_alpaca_client):
    order = mock_alpaca_client.submit_order(symbol="AAPL", qty=10, side="buy")
    assert_valid_order(order, expected_symbol="AAPL")
```

### Test Helpers

```python
from tests.alpaca.utils import wait_for_order_fill, calculate_expected_pnl

def test_trade_execution(paper_trading_client):
    order = paper_trading_client.submit_order(symbol="AAPL", qty=1, side="buy")
    filled_order = wait_for_order_fill(paper_trading_client, order.id, timeout=30)
    assert filled_order.status == "filled"
```

## Writing New Tests

### Unit Test Template

```python
import pytest
from tests.alpaca.utils import MockAlpacaClient, assert_valid_order

@pytest.mark.unit
class TestYourFeature:
    """Test your feature description."""

    def test_feature_success(self, mock_alpaca_client):
        """Should succeed with valid input."""
        # Arrange
        client = mock_alpaca_client

        # Act
        result = client.your_method()

        # Assert
        assert result is not None
```

### Integration Test Template

```python
import pytest

@pytest.mark.integration
class TestYourAPIIntegration:
    """Test your API integration."""

    def test_api_call_success(self, paper_trading_client):
        """Should successfully call API."""
        result = paper_trading_client.your_api_call()
        assert result is not None
```

### E2E Test Template

```python
import pytest

@pytest.mark.e2e
@pytest.mark.slow
class TestYourWorkflow:
    """Test complete workflow."""

    def test_complete_workflow(self, paper_trading_client, cleanup_test_positions):
        """Should complete workflow successfully."""
        # Step 1
        # Step 2
        # Step 3
        pass
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Alpaca Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run unit tests
        run: pytest tests/alpaca/unit/ -m unit --cov=src/alpaca --cov-fail-under=95
      - name: Run integration tests
        env:
          ALPACA_PAPER_KEY: ${{ secrets.ALPACA_PAPER_KEY }}
          ALPACA_PAPER_SECRET: ${{ secrets.ALPACA_PAPER_SECRET }}
        run: pytest tests/alpaca/integration/ -m integration
```

## Best Practices

1. **Test First**: Write tests before implementation (TDD)
2. **One Assertion**: Each test should verify one behavior
3. **Descriptive Names**: Test names should explain what and why
4. **Arrange-Act-Assert**: Structure tests clearly
5. **Mock External Dependencies**: Keep tests fast and reliable
6. **Use Fixtures**: Share setup code via pytest fixtures
7. **Document Complex Tests**: Add docstrings explaining scenarios
8. **Keep Tests DRY**: Use helper functions for common operations

## Common Issues

### Issue: Integration tests fail with authentication error
**Solution**: Ensure `ALPACA_PAPER_KEY` and `ALPACA_PAPER_SECRET` are set in `.env.test`

### Issue: Tests are too slow
**Solution**: Run only unit tests during development: `pytest tests/alpaca/unit/ -m unit`

### Issue: Coverage is below target
**Solution**: Check coverage report: `pytest --cov=src/alpaca --cov-report=html` then open `htmlcov/index.html`

### Issue: Test fixtures not found
**Solution**: Ensure you're running pytest from the project root directory

## Resources

- [Test Strategy Document](../../docs/alpaca/test-strategy.md) - Comprehensive test strategy
- [Alpaca API Documentation](https://alpaca.markets/docs/) - Official API docs
- [Pytest Documentation](https://docs.pytest.org/) - Pytest framework docs
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/) - General testing guide

## Coverage Reports

After running tests with coverage:

```bash
# Generate HTML coverage report
pytest tests/alpaca/ --cov=src/alpaca --cov-report=html

# Open in browser
open tests/alpaca/htmlcov/index.html
```

## Support

For issues or questions:
1. Check the [Test Strategy Document](../../docs/alpaca/test-strategy.md)
2. Review example test files in each category
3. Contact the testing team via coordination hooks

---

**Version**: 1.0.0
**Last Updated**: 2025-11-14
**Maintainer**: Testing Agent
**Status**: Active
