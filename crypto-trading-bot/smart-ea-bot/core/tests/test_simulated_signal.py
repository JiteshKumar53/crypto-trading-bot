"""
Simulated Signal Test — End-to-End Pipeline Verification
Tests what happens when the daemon detects a crossover and places an order.
Uses mocked data — no real orders placed.
"""

import os
import sys
import json
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSimulatedSignal(unittest.TestCase):
    """End-to-end test: crossover signal -> order placement -> heartbeat."""

    def setUp(self):
        os.environ['ALPACA_API_KEY'] = 'test_key'
        os.environ['ALPACA_SECRET_KEY'] = 'test_secret'
        self.test_dir = tempfile.mkdtemp(prefix="signal_test_")
        self.orig_dir = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        os.chdir(self.orig_dir)

    @patch('alpaca_trade_api.REST')
    @patch('paper_daemon.DataFetcher')
    def test_full_pipeline_on_crossover(self, MockFetcher, MockREST):
        """
        Simulate BTC crossing above SMA50.
        Verify:
        1. Crossover detected
        2. Order placement attempted
        3. Heartbeat written with signal and order_placed=true
        """
        from paper_daemon import PaperDaemon
        d = PaperDaemon()

        # Create bars where price crosses above SMA on last bar
        mock_bars = []
        base = datetime(2024, 1, 1, tzinfo=timezone.utc)
        for i in range(59):
            mock_bars.append({
                'timestamp': (base + timedelta(days=i)).isoformat(),
                'open': 100.0, 'high': 101.0, 'low': 99.0,
                'close': 100.0, 'volume': 1000,
            })
        # Last bar: price jumps to 200 (well above SMA50 ~100)
        mock_bars.append({
            'timestamp': (base + timedelta(days=59)).isoformat(),
            'open': 200.0, 'high': 201.0, 'low': 199.0,
            'close': 200.0, 'volume': 1000,
        })

        d.fetcher = MagicMock()
        d.fetcher.fetch_bars.return_value = mock_bars

        # Mock API — capture order placement
        d.api = MagicMock()
        mock_order = MagicMock()
        mock_order.id = 'test-order-123'
        d.api.submit_order.return_value = mock_order
        d.api.list_positions.return_value = []

        # Run daemon cycle
        d.run_cycle()

        # Verify 1: Order placement was attempted
        self.assertTrue(d.api.submit_order.called,
                        "submit_order was not called — signal may not have been detected")

        # Verify 2: Order parameters are correct
        call_args = d.api.submit_order.call_args[1]
        self.assertEqual(call_args.get('side'), 'buy')
        self.assertEqual(call_args.get('symbol'), 'BTC/USD')
        self.assertEqual(call_args.get('type'), 'market')

        # Verify 3: Order size ≤ $100
        qty = call_args.get('qty')
        self.assertIsNotNone(qty)
        self.assertGreater(qty, 0)
        self.assertLessEqual(qty * 200.0, 101.0,
                            f"Order value ${qty*200.0} exceeds $100 max")

        # Verify 4: Heartbeat written with signal details
        with open(d.heartbeat_file) as f:
            hb = json.load(f)

        self.assertEqual(hb['status'], 'SIGNAL_FIRED')
        self.assertIn('LONG', hb.get('signal', ''))
        self.assertEqual(hb['order_placed'], True)
        self.assertEqual(hb['btc_price'], 200.0)

        # Verify 5: No errors logged
        self.assertIsNone(hb.get('error_message'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
