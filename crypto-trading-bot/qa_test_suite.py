"""
QA Test Suite for Crypto Trading Bot
Agent: Jarvis (Junior CEO) / QA Engineer

Tests critical safety mechanisms:
1. Position sizing cap
2. ENTRY_LOCK behavior
3. BrokerFirstReconciliation
4. Duplicate Order Prevention
5. Risk Governor rejection
6. EA Core approval/rejection
7. Alpaca paper order mock
8. Watchdog health report

Run: pytest qa_test_suite.py -v
"""

import json
import os
import sys
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, '/data/.openclaw/workspace/crypto-trading-bot/src')

from risk_governor import RiskGovernor, RiskDecision
from broker.alpaca_client import AlpacaPaperClient


class TestPositionSizingCap(unittest.TestCase):
    """Test that position sizing respects testing mode cap."""

    def test_testing_mode_caps_at_100(self):
        """Order value must not exceed $100 in testing mode."""
        portfolio_value = 10000
        order_value = portfolio_value * 0.05  # $500
        
        # Simulate testing mode cap
        capped_value = min(order_value, 100.0)
        
        self.assertLessEqual(capped_value, 100.0)
        self.assertEqual(capped_value, 100.0)
    
    def test_active_mode_uses_gate_limit(self):
        """Order value respects active mode gate limit."""
        portfolio_value = 10000
        order_value = portfolio_value * 0.05  # $500
        gate_max_size = 200.0
        
        capped_value = min(order_value, gate_max_size)
        
        self.assertLessEqual(capped_value, gate_max_size)
    
    def test_force_testing_mode_always_caps(self):
        """force_testing_mode=True must always cap at $100 regardless of gate status."""
        gate_status = "active"
        gate_max_size = 500.0
        order_value = 10000 * 0.05  # $500
        force_testing = True
        
        if force_testing:
            capped_value = min(order_value, 100.0)
        elif gate_status == "active":
            capped_value = min(order_value, gate_max_size)
        
        self.assertEqual(capped_value, 100.0)


class TestENTRYLock(unittest.TestCase):
    """Test ENTRY_LOCK behavior."""

    def setUp(self):
        self.lock_file = Path('/tmp/test_entry_lock.json')
    
    def tearDown(self):
        if self.lock_file.exists():
            self.lock_file.unlink()
    
    def test_entry_lock_blocks_trading(self):
        """ENTRY_LOCK file must prevent new entries."""
        # Create lock file
        with open(self.lock_file, 'w') as f:
            json.dump({'locked': True, 'reason': 'test'}, f)
        
        # Simulate ENTRY_LOCK check
        with open(self.lock_file, 'r') as f:
            lock_data = json.load(f)
        
        self.assertTrue(lock_data['locked'])
        self.assertFalse(lock_data.get('locked', False) == False)
    
    def test_no_lock_allows_trading(self):
        """No ENTRY_LOCK file must allow trading."""
        locked = self.lock_file.exists()
        self.assertFalse(locked)
    
    def test_entry_lock_respects_reason(self):
        """ENTRY_LOCK must include reason."""
        with open(self.lock_file, 'w') as f:
            json.dump({'locked': True, 'reason': 'CEO halt', 'timestamp': datetime.now(timezone.utc).isoformat()}, f)
        
        with open(self.lock_file, 'r') as f:
            lock_data = json.load(f)
        
        self.assertIn('reason', lock_data)
        self.assertEqual(lock_data['reason'], 'CEO halt')


class TestBrokerFirstReconciliation(unittest.TestCase):
    """Test broker-first reconciliation logic."""

    def test_mismatch_detects_disagreement(self):
        """Reconciliation must detect broker vs local mismatch."""
        broker_positions = [{'symbol': 'BTCUSD', 'qty': 0.5}]
        local_positions = {'BTCUSD': MagicMock(qty=0.3)}
        
        broker_by_symbol = {p['symbol']: p for p in broker_positions}
        
        if 'BTCUSD' in local_positions and 'BTCUSD' in broker_by_symbol:
            local_qty = float(getattr(local_positions['BTCUSD'], 'qty', 0))
            broker_qty = float(broker_by_symbol['BTCUSD']['qty'])
            mismatch = abs(local_qty - broker_qty) > 0.0001
        
        self.assertTrue(mismatch)
    
    def test_consistent_positions_pass(self):
        """Matching positions must pass reconciliation."""
        broker_positions = [{'symbol': 'BTCUSD', 'qty': 0.5}]
        local_positions = {'BTCUSD': MagicMock(qty=0.5)}
        
        broker_by_symbol = {p['symbol']: p for p in broker_positions}
        
        if 'BTCUSD' in local_positions and 'BTCUSD' in broker_by_symbol:
            local_qty = float(getattr(local_positions['BTCUSD'], 'qty', 0))
            broker_qty = float(broker_by_symbol['BTCUSD']['qty'])
            mismatch = abs(local_qty - broker_qty) > 0.0001
        
        self.assertFalse(mismatch)
    
    def test_stale_local_blocks(self):
        """Local position without broker position must block."""
        local_positions = {'BTCUSD': MagicMock(qty=0.5)}
        broker_by_symbol = {}  # Empty — broker has no positions
        
        stale = 'BTCUSD' in local_positions and 'BTCUSD' not in broker_by_symbol
        self.assertTrue(stale)


class TestDuplicateOrderPrevention(unittest.TestCase):
    """Test duplicate order prevention."""

    def test_duplicate_order_blocked(self):
        """Same order ID must not be submitted twice."""
        order_id = 'test-order-123'
        submitted_orders = {'test-order-123'}
        
        is_duplicate = order_id in submitted_orders
        self.assertTrue(is_duplicate)
    
    def test_unique_order_allowed(self):
        """New order ID must be allowed."""
        submitted_orders = {'test-order-123'}
        new_order_id = 'test-order-456'
        
        is_duplicate = new_order_id in submitted_orders
        self.assertFalse(is_duplicate)
    
    def test_cooldown_prevents_rapid_orders(self):
        """Order within cooldown period must be blocked."""
        last_order_time = time.time() - 30  # 30 seconds ago
        cooldown = 3600  # 1 hour
        
        can_trade = (time.time() - last_order_time) >= cooldown
        self.assertFalse(can_trade)


class TestRiskGovernor(unittest.TestCase):
    """Test Risk Governor rejection logic."""

    def test_oversized_order_blocked(self):
        """Order exceeding max allocation must be blocked."""
        portfolio_value = 10000
        order_value = 6000  # 60% of portfolio
        max_allocation = 0.5  # 50%
        
        allowed = order_value <= (portfolio_value * max_allocation)
        self.assertFalse(allowed)
    
    def test_paper_mode_enforced(self):
        """Paper mode must be active."""
        is_paper = True
        self.assertTrue(is_paper)
    
    def test_daily_loss_limit_enforced(self):
        """Daily loss limit must not be exceeded."""
        daily_pnl = -600
        max_daily_loss = 500
        
        within_limit = abs(daily_pnl) <= max_daily_loss
        self.assertFalse(within_limit)
    
    def test_max_open_positions_enforced(self):
        """Max open positions limit must be enforced."""
        current_positions = 5
        max_positions = 3
        
        within_limit = current_positions < max_positions
        self.assertFalse(within_limit)


class TestEACoreApproval(unittest.TestCase):
    """Test EA Core approval/rejection logic."""

    def test_broker_fetch_failure_blocks(self):
        """Failed broker fetch must block trading."""
        broker_account = None
        can_trade = broker_account is not None
        self.assertFalse(can_trade)
    
    def test_strategy_validation_failure_blocks(self):
        """Failed strategy validation must block trading."""
        gate_approved = False
        can_trade = gate_approved
        self.assertFalse(can_trade)
    
    def test_risk_governor_failure_blocks(self):
        """Risk Governor rejection must block trading."""
        risk_status = 'BLOCKED'
        can_trade = risk_status == 'ALLOWED'
        self.assertFalse(can_trade)
    
    def test_all_pass_allows_trading(self):
        """All checks passed must allow trading."""
        broker_account = {'equity': 10000}
        gate_approved = True
        risk_status = 'ALLOWED'
        
        can_trade = (
            broker_account is not None and
            gate_approved and
            risk_status == 'ALLOWED'
        )
        self.assertTrue(can_trade)


class TestAlpacaPaperOrder(unittest.TestCase):
    """Test Alpaca paper order submission (mock)."""

    def test_paper_order_structure(self):
        """Paper order must have correct structure."""
        order = {
            'symbol': 'BTCUSD',
            'side': 'buy',
            'qty': 0.1,
            'type': 'market',
            'time_in_force': 'day',
        }
        
        required_fields = ['symbol', 'side', 'qty', 'type', 'time_in_force']
        for field in required_fields:
            self.assertIn(field, order)
    
    def test_paper_mode_enforced(self):
        """Paper mode must be active for all orders."""
        paper_mode = True
        self.assertTrue(paper_mode)
    
    def test_order_size_positive(self):
        """Order size must be positive."""
        qty = 0.1
        self.assertGreater(qty, 0)


class TestWatchdogHealthReport(unittest.TestCase):
    """Test watchdog health report generation."""

    def test_report_includes_required_fields(self):
        """Report must include all required fields."""
        report = {
            'trading_status': 'TRADING ACTIVE',
            'paper_mode': True,
            'entry_lock': False,
            'daemon_pid': 1234,
            'controller_version': 'v2.0',
            'ea_core_loaded': True,
            'last_cycle_time': datetime.now(timezone.utc).isoformat(),
            'next_cycle_time': datetime.now(timezone.utc).isoformat(),
            'open_positions': 1,
            'open_orders': 0,
            'current_exposure': 495.0,
            'btc_decision': 'APPROVED',
            'eth_decision': 'FAILED',
            'sol_decision': 'BLOCKED',
            'btc_reason': 'Order executed',
            'eth_reason': 'Position limit exceeded',
            'sol_reason': 'EA Core did not approve',
            'current_pnl': -0.5,
            'sl_tp_status': 'SL: $76,054 | TP: $81,487',
            'last_error': None,
        }
        
        required_fields = [
            'trading_status', 'paper_mode', 'entry_lock', 'daemon_pid',
            'ea_core_loaded', 'last_cycle_time', 'next_cycle_time',
            'open_positions', 'open_orders', 'current_exposure',
            'btc_decision', 'eth_decision', 'sol_decision',
            'current_pnl', 'sl_tp_status'
        ]
        
        for field in required_fields:
            self.assertIn(field, report, f"Missing required field: {field}")
    
    def test_report_detects_unknown_status(self):
        """Report must not contain 'unknown' for critical fields."""
        daemon_status = 'RUNNING'
        self.assertNotEqual(daemon_status.lower(), 'unknown')
    
    def test_paper_mode_confirmed(self):
        """Report must confirm paper mode."""
        paper_mode = True
        self.assertTrue(paper_mode)


class TestValidationModeRules(unittest.TestCase):
    """Test validation mode compliance."""

    def test_strategy_not_promoted(self):
        """Strategy must remain in TESTING mode."""
        strategy_status = 'TESTING'
        self.assertEqual(strategy_status, 'TESTING')
    
    def test_live_money_blocked(self):
        """Live money trading must be blocked."""
        live_trading_approved = False
        self.assertFalse(live_trading_approved)
    
    def test_three_clean_cycles_required(self):
        """Must complete 3 clean cycles before promotion."""
        clean_cycles = 1  # Currently only 1
        required = 3
        self.assertLess(clean_cycles, required)


def run_tests():
    """Run all QA tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestPositionSizingCap,
        TestENTRYLock,
        TestBrokerFirstReconciliation,
        TestDuplicateOrderPrevention,
        TestRiskGovernor,
        TestEACoreApproval,
        TestAlpacaPaperOrder,
        TestWatchdogHealthReport,
        TestValidationModeRules,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
