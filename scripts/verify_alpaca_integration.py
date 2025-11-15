#!/usr/bin/env python3
"""
Verification script for Alpaca data vendor integration.

This script verifies that:
1. Alpaca module structure is correct
2. Functions are properly exported
3. Integration with routing system works
4. All expected features are available
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)


def check_module_structure():
    """Verify module structure and imports."""
    print_section("1. Module Structure Verification")

    try:
        # Check main module imports
        from tradingagents.dataflows import alpaca
        print("✅ Main module 'tradingagents.dataflows.alpaca' imports successfully")

        # Check submodules
        from tradingagents.dataflows.alpaca import common, data
        print("✅ Submodules 'common' and 'data' import successfully")

        # Check exported functions
        from tradingagents.dataflows.alpaca import get_stock_data, get_latest_quote, get_bars
        print("✅ All main functions exported correctly")

        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def check_common_module():
    """Verify common module components."""
    print_section("2. Common Module (Error Classes & Client)")

    try:
        from tradingagents.dataflows.alpaca.common import (
            AlpacaAPIError,
            AlpacaRateLimitError,
            AlpacaAuthenticationError,
            AlpacaDataClient,
            get_alpaca_credentials,
            get_client
        )
        print("✅ AlpacaAPIError class available")
        print("✅ AlpacaRateLimitError class available")
        print("✅ AlpacaAuthenticationError class available")
        print("✅ AlpacaDataClient class available")
        print("✅ get_alpaca_credentials function available")
        print("✅ get_client function available")

        # Check error hierarchy
        assert issubclass(AlpacaRateLimitError, AlpacaAPIError)
        assert issubclass(AlpacaAuthenticationError, AlpacaAPIError)
        print("✅ Error class hierarchy correct")

        return True
    except (ImportError, AssertionError) as e:
        print(f"❌ Error: {e}")
        return False


def check_data_module():
    """Verify data module functions."""
    print_section("3. Data Module (Core Functions)")

    try:
        from tradingagents.dataflows.alpaca.data import (
            get_stock_data,
            get_latest_quote,
            get_bars
        )
        print("✅ get_stock_data function available")
        print("✅ get_latest_quote function available")
        print("✅ get_bars function available")

        # Check function signatures
        import inspect

        sig = inspect.signature(get_stock_data)
        params = list(sig.parameters.keys())
        assert params == ['symbol', 'start_date', 'end_date']
        print("✅ get_stock_data has correct signature")

        sig = inspect.signature(get_latest_quote)
        params = list(sig.parameters.keys())
        assert params == ['symbol']
        print("✅ get_latest_quote has correct signature")

        sig = inspect.signature(get_bars)
        params = list(sig.parameters.keys())
        assert params == ['symbol', 'timeframe', 'start', 'end']
        print("✅ get_bars has correct signature")

        return True
    except (ImportError, AssertionError) as e:
        print(f"❌ Error: {e}")
        return False


def check_interface_integration():
    """Verify integration with interface.py routing."""
    print_section("4. Interface Integration (Vendor Routing)")

    try:
        from tradingagents.dataflows.interface import (
            VENDOR_METHODS,
            VENDOR_LIST,
            route_to_vendor
        )

        # Check Alpaca in VENDOR_LIST
        if 'alpaca' in VENDOR_LIST:
            print("✅ 'alpaca' in VENDOR_LIST")
        else:
            print("⚠️  'alpaca' not in VENDOR_LIST (but may work via VENDOR_METHODS)")

        # Check Alpaca in VENDOR_METHODS
        assert 'get_stock_data' in VENDOR_METHODS
        assert 'alpaca' in VENDOR_METHODS['get_stock_data']
        print("✅ Alpaca registered in VENDOR_METHODS['get_stock_data']")

        # Check function is callable
        alpaca_func = VENDOR_METHODS['get_stock_data']['alpaca']
        assert callable(alpaca_func)
        print("✅ Alpaca get_stock_data function is callable")

        # Check function name
        from tradingagents.dataflows.alpaca import get_stock_data
        assert VENDOR_METHODS['get_stock_data']['alpaca'] == get_stock_data
        print("✅ Registered function matches alpaca.get_stock_data")

        return True
    except (ImportError, AssertionError) as e:
        print(f"❌ Error: {e}")
        return False


def check_error_handling():
    """Verify error handling in interface."""
    print_section("5. Error Handling Integration")

    try:
        from tradingagents.dataflows.interface import route_to_vendor
        from tradingagents.dataflows.alpaca.common import AlpacaRateLimitError

        # Check that AlpacaRateLimitError is imported in interface
        import tradingagents.dataflows.interface as interface_module
        assert hasattr(interface_module, 'AlpacaRateLimitError')
        print("✅ AlpacaRateLimitError imported in interface.py")

        # Verify it's the same class
        assert interface_module.AlpacaRateLimitError is AlpacaRateLimitError
        print("✅ Error class reference is correct")

        return True
    except (ImportError, AssertionError, AttributeError) as e:
        print(f"❌ Error: {e}")
        return False


def check_documentation():
    """Verify documentation files exist."""
    print_section("6. Documentation")

    docs_exist = True

    # Check for summary document
    summary_path = "docs/alpaca-implementation-summary.md"
    if os.path.exists(summary_path):
        print(f"✅ Implementation summary exists: {summary_path}")
    else:
        print(f"⚠️  Missing: {summary_path}")
        docs_exist = False

    # Check for usage guide
    guide_path = "docs/alpaca-usage-guide.md"
    if os.path.exists(guide_path):
        print(f"✅ Usage guide exists: {guide_path}")
    else:
        print(f"⚠️  Missing: {guide_path}")
        docs_exist = False

    return docs_exist


def check_test_files():
    """Verify test files exist."""
    print_section("7. Test Files")

    tests_exist = True
    test_files = [
        "tests/dataflows/test_alpaca_data.py",
        "tests/dataflows/test_alpaca_integration.py",
        "tests/dataflows/test_alpaca_e2e.py"
    ]

    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"✅ {test_file}")
        else:
            print(f"❌ Missing: {test_file}")
            tests_exist = False

    return tests_exist


def run_sample_test():
    """Run a simple mock test to verify functionality."""
    print_section("8. Functional Test (Mocked)")

    try:
        from unittest.mock import Mock, patch
        from tradingagents.dataflows.alpaca.data import get_stock_data

        # Mock the client
        mock_response = {
            'bars': [
                {
                    't': '2025-01-10T05:00:00Z',
                    'o': 150.00,
                    'h': 152.00,
                    'l': 149.50,
                    'c': 151.50,
                    'v': 1000000,
                }
            ]
        }

        with patch('tradingagents.dataflows.alpaca.data.get_client') as mock_get_client:
            mock_client = Mock()
            mock_client._request.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = get_stock_data('AAPL', '2025-01-10', '2025-01-10')

            # Verify result structure
            assert isinstance(result, str)
            assert '# Stock data for AAPL' in result
            assert 'Alpaca Markets' in result
            assert '150.0' in result or '150.00' in result

            print("✅ Mock test passed")
            print(f"   Result preview: {result[:100]}...")

            return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def main():
    """Run all verification checks."""
    print("\n" + "="*70)
    print("  ALPACA DATA VENDOR INTEGRATION VERIFICATION")
    print("="*70)

    checks = [
        ("Module Structure", check_module_structure),
        ("Common Module", check_common_module),
        ("Data Module", check_data_module),
        ("Interface Integration", check_interface_integration),
        ("Error Handling", check_error_handling),
        ("Documentation", check_documentation),
        ("Test Files", check_test_files),
        ("Functional Test", run_sample_test),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Unexpected error in {name}: {e}")
            results.append((name, False))

    # Summary
    print_section("VERIFICATION SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:>12} - {name}")

    print(f"\n{'='*70}")
    print(f"  Results: {passed}/{total} checks passed")
    print('='*70)

    if passed == total:
        print("\n🎉 All verification checks passed!")
        print("   Alpaca integration is complete and working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} check(s) failed.")
        print("   Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
