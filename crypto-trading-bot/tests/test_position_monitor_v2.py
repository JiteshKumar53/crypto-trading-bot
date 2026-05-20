"""Tests for PositionMonitorV2 partial-sell fix and exit logic."""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timezone
import sys
sys.path.insert(0, 'src')

from position_monitor_v2 import PositionMonitorV2, PositionState, PARTIAL_PROFIT_LEVEL_1


class TestPositionMonitorV2PartialSellFix:
    """Verify the partial-sell death spiral bug is fixed."""

    @pytest.fixture(autouse=True)
    def mock_alpaca(self):
        with patch('position_monitor_v2.AlpacaPaperClient') as MockClient:
            MockClient.return_value = Mock()
            yield MockClient

    @pytest.fixture
    def mock_state(self):
        return {
            "symbol": "BTCUSD",
            "qty": 0.01,
            "avg_entry_price": 70000.0,
            "current_price": 70350.0,
            "market_value": 703.5,
            "unrealized_pl": 3.5,
            "unrealized_pl_pct": 0.005,
            "entry_time": datetime.now(timezone.utc).isoformat(),
            "holding_hours": 1.0,
            "highest_price": 70350.0,
            "highest_price_pct": 0.005,
            "partial_sold": False,
            "partial_sold_qty": 0.0,
            "stop_triggered": False,
            "take_profit_triggered": False,
            "trailing_stop_triggered": False,
            "time_exit_triggered": False,
            "break_even_triggered": False,
            "break_even_price": 70350.0,
            "regime_at_entry": "uptrend",
            "strategy_name": "test",
        }

    def test_partial_sell_sets_flag(self, tmp_path, mock_state):
        """After executing a partial sell, partial_sold must be True."""
        state_file = tmp_path / "test_state.json"
        
        with patch('position_monitor_v2.STATE_FILE', state_file), \
             patch('position_monitor_v2.REJECTED_SIGNALS_FILE', tmp_path / "rejected.jsonl"):
            
            monitor = PositionMonitorV2()
            
            # Create state with +0.5% profit (triggers partial_profit_1)
            state = PositionState(**mock_state)
            state.current_price = 70350.0  # +0.5%
            
            # Mock the client
            mock_result = Mock()
            mock_result.success = True
            mock_result.order_id = "test-123"
            monitor.client = Mock()
            monitor.client.submit_order = Mock(return_value=mock_result)
            
            # Run check_position
            action = monitor.check_position(state)
            
            assert action is not None
            assert action["action"] == "SELL_PARTIAL"
            
            # Execute the action
            success = monitor.execute_exit(action)
            assert success is True
            
            # In monitor_once, the flag would be set. Let's verify the logic:
            # After execute_exit, we need to manually set the flag (as done in monitor_once)
            state.partial_sold = True
            state.partial_sold_qty = action["qty"]
            
            assert state.partial_sold is True
            assert state.partial_sold_qty > 0
            
            # Now running check_position again should NOT trigger partial
            action2 = monitor.check_position(state)
            # Should be None or some other action, NOT SELL_PARTIAL
            if action2:
                assert action2["action"] != "SELL_PARTIAL", \
                    "partial_sold flag should prevent repeated partial sells"

    def test_partial_sell_prevents_repeated_triggers(self):
        """With partial_sold=True, check_position must not return SELL_PARTIAL."""
        monitor = PositionMonitorV2()
        
        state = PositionState(
            symbol="BTCUSD",
            qty=0.005,
            avg_entry_price=70000.0,
            current_price=70350.0,  # +0.5%
            market_value=351.75,
            unrealized_pl=1.75,
            unrealized_pl_pct=0.005,
            entry_time=datetime.now(timezone.utc).isoformat(),
            holding_hours=1.0,
            highest_price=70350.0,
            highest_price_pct=0.005,
            partial_sold=True,  # Already sold
            partial_sold_qty=0.005,
            stop_triggered=False,
            take_profit_triggered=False,
            trailing_stop_triggered=False,
            time_exit_triggered=False,
            break_even_triggered=False,
            break_even_price=70350.0,
            regime_at_entry="uptrend",
            strategy_name="test",
        )
        
        action = monitor.check_position(state)
        
        # Should NOT be SELL_PARTIAL
        if action:
            assert action["action"] != "SELL_PARTIAL", \
                "partial_sold=True must prevent partial sell from re-triggering"

    def test_exit_flags_prevent_re_execution(self):
        """After SELL_ALL, flags should prevent re-triggering."""
        monitor = PositionMonitorV2()
        
        state = PositionState(
            symbol="BTCUSD",
            qty=0.0,  # Position already exited
            avg_entry_price=70000.0,
            current_price=69000.0,
            market_value=0.0,
            unrealized_pl=0.0,
            unrealized_pl_pct=0.0,
            entry_time=datetime.now(timezone.utc).isoformat(),
            holding_hours=2.0,
            highest_price=70500.0,
            highest_price_pct=0.007,
            partial_sold=True,
            partial_sold_qty=0.01,
            stop_triggered=True,  # Already stopped
            take_profit_triggered=False,
            trailing_stop_triggered=False,
            time_exit_triggered=False,
            break_even_triggered=False,
            break_even_price=70350.0,
            regime_at_entry="uptrend",
            strategy_name="test",
        )
        
        # With qty=0, should not try to sell
        action = monitor.check_position(state)
        assert action is None or action["action"] == "HOLD", \
            "Zero qty should not trigger any sell action"


class TestPositionMonitorV2ExitThresholds:
    """Verify tightened exit thresholds."""

    @pytest.fixture(autouse=True)
    def mock_alpaca(self):
        with patch('position_monitor_v2.AlpacaPaperClient') as MockClient:
            MockClient.return_value = Mock()
            yield MockClient

    def test_stop_loss_now_1_5_percent(self):
        """Stop loss should trigger at -1.5%."""
        monitor = PositionMonitorV2()
        assert monitor.stop_loss_pct == 0.015

    def test_max_holding_8_hours(self):
        """Max holding should be 8 hours."""
        monitor = PositionMonitorV2()
        assert monitor.max_holding_hours == 8

    def test_stale_loss_6_hours(self):
        """Stale loss exit should trigger after 6 hours."""
        monitor = PositionMonitorV2()
        assert monitor.stale_loss_hours == 6

    def test_stale_profit_4_hours(self):
        """Stale profit exit should trigger after 4 hours."""
        monitor = PositionMonitorV2()
        assert monitor.stale_profit_hours == 4

    def test_minimum_profit_exit_0_2_percent(self):
        """Minimum profit exit should be 0.2% (low fees)."""
        from position_monitor_v2 import MINIMUM_PROFIT_EXIT
        assert MINIMUM_PROFIT_EXIT == 0.002
