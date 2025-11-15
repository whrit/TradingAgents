"""
End-to-end tests for complete trading workflows.

Tests realistic trading scenarios from data retrieval through order execution
and position management using Alpaca paper trading.
"""

import pytest
import time
from datetime import datetime, timedelta
from tests.alpaca.utils import (
    wait_for_order_fill,
    calculate_expected_pnl,
    assert_valid_order,
    assert_valid_position,
)


@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteTradingCycle:
    """Test complete trading cycle from start to finish."""

    def test_buy_hold_sell_workflow(
        self,
        paper_trading_client,
        cleanup_test_positions
    ):
        """
        Should complete full trading cycle: buy -> hold -> sell.

        Workflow:
        1. Check account balance
        2. Place market buy order
        3. Verify order fills
        4. Check position created
        5. Hold position briefly
        6. Place market sell order
        7. Verify position closed
        """
        # 1. Check initial account state
        initial_account = paper_trading_client.get_account()
        initial_cash = float(initial_account.cash)

        # 2. Place buy order
        buy_order = paper_trading_client.submit_order(
            symbol="AAPL",
            qty=1,
            side="buy",
            type="market",
            time_in_force="day"
        )

        assert_valid_order(buy_order, expected_symbol="AAPL")
        assert buy_order.side == "buy"

        # 3. Wait for order to fill
        filled_order = wait_for_order_fill(
            paper_trading_client,
            buy_order.id,
            timeout=30
        )

        assert filled_order.status == "filled"
        entry_price = float(filled_order.filled_avg_price)

        # 4. Verify position created
        position = paper_trading_client.get_position("AAPL")
        assert_valid_position(position, expected_symbol="AAPL")
        assert float(position.qty) == 1.0

        # 5. Hold position briefly (simulate holding period)
        time.sleep(2)

        # 6. Place sell order to close position
        sell_order = paper_trading_client.submit_order(
            symbol="AAPL",
            qty=1,
            side="sell",
            type="market",
            time_in_force="day"
        )

        # 7. Wait for sell to fill
        filled_sell = wait_for_order_fill(
            paper_trading_client,
            sell_order.id,
            timeout=30
        )

        assert filled_sell.status == "filled"
        exit_price = float(filled_sell.filled_avg_price)

        # 8. Verify position closed
        positions = paper_trading_client.get_all_positions()
        aapl_positions = [p for p in positions if p.symbol == "AAPL"]
        assert len(aapl_positions) == 0

        # 9. Verify P&L calculation
        expected_pnl = calculate_expected_pnl(
            qty=1,
            entry_price=entry_price,
            exit_price=exit_price,
            side="long"
        )

        # Account for commissions (Alpaca paper trading has no commissions)
        final_account = paper_trading_client.get_account()
        final_cash = float(final_account.cash)

        # Cash should change by approximately the P&L
        cash_change = final_cash - initial_cash
        assert abs(cash_change - expected_pnl) < 0.01  # Allow small rounding


@pytest.mark.e2e
@pytest.mark.slow
class TestLimitOrderWorkflow:
    """Test workflow with limit orders."""

    def test_limit_order_execution(
        self,
        paper_trading_client,
        paper_stock_client,
        cleanup_test_positions
    ):
        """
        Should execute limit order workflow.

        Workflow:
        1. Get current market price
        2. Place limit buy order below market
        3. Monitor order status
        4. Cancel if not filled within timeout
        """
        pytest.skip("Limit order testing requires market conditions - implement as needed")


@pytest.mark.e2e
@pytest.mark.slow
class TestDataTradingIntegration:
    """Test integration between data retrieval and trading."""

    def test_fetch_data_and_trade(
        self,
        paper_trading_client,
        paper_stock_client,
        cleanup_test_positions
    ):
        """
        Should fetch market data and execute trade based on data.

        Workflow:
        1. Fetch recent market data
        2. Calculate simple indicator (e.g., recent price change)
        3. Place order based on indicator
        4. Verify order execution
        """
        pytest.skip("Data-driven trading test - implement with actual strategy")


@pytest.mark.e2e
@pytest.mark.slow
class TestErrorRecovery:
    """Test error recovery in trading workflows."""

    def test_recover_from_failed_order(
        self,
        paper_trading_client,
        cleanup_test_positions
    ):
        """
        Should recover from failed order submission.

        Workflow:
        1. Attempt order with invalid parameters
        2. Catch error
        3. Submit corrected order
        4. Verify success
        """
        # 1. Try to submit invalid order (e.g., invalid symbol)
        with pytest.raises(Exception):
            paper_trading_client.submit_order(
                symbol="INVALID_SYMBOL_12345",
                qty=1,
                side="buy",
                type="market"
            )

        # 2. Submit valid order after error
        valid_order = paper_trading_client.submit_order(
            symbol="AAPL",
            qty=1,
            side="buy",
            type="market"
        )

        assert_valid_order(valid_order, expected_symbol="AAPL")

        # Cleanup
        if valid_order.status in ["accepted", "pending_new", "new"]:
            paper_trading_client.cancel_order(valid_order.id)


@pytest.mark.e2e
@pytest.mark.slow
class TestPositionManagement:
    """Test position management workflows."""

    def test_scale_in_position(
        self,
        paper_trading_client,
        cleanup_test_positions
    ):
        """
        Should scale into a position with multiple orders.

        Workflow:
        1. Place initial small order
        2. Wait for fill
        3. Place additional order to increase position
        4. Verify total position size
        5. Close entire position
        """
        pytest.skip("Position scaling test - implement as needed")

    def test_partial_position_close(
        self,
        paper_trading_client,
        cleanup_test_positions
    ):
        """
        Should partially close a position.

        Workflow:
        1. Open position with multiple shares
        2. Close partial position
        3. Verify remaining position
        4. Close remaining position
        """
        pytest.skip("Partial close test - implement as needed")


# Template for additional E2E tests:
#
# @pytest.mark.e2e
# @pytest.mark.slow
# class TestMultiSymbolTrading:
#     """Test trading workflows with multiple symbols."""
#
#     def test_portfolio_rebalancing(
#         self,
#         paper_trading_client,
#         cleanup_test_positions
#     ):
#         """
#         Should rebalance portfolio across multiple symbols.
#
#         Workflow:
#         1. Define target allocation (e.g., 50% AAPL, 50% MSFT)
#         2. Calculate required orders
#         3. Execute orders
#         4. Verify portfolio matches target
#         """
#         # Implementation here
#         pass
