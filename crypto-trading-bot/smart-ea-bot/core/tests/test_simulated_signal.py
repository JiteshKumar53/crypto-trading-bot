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

    def _make_crossover_bars(self, crossover_price=200.0, flat_price=100.0):
        """Generate bars where last bar crosses above SMA50."""
        bars = []
        base = datetime(2024, 1, 1, tzinfo=timezone.utc)
        for i in range(59):
            bars.append({
                'timestamp': (base + timedelta(days=i)).isoformat(),
                'open': flat_price, 'high': flat_price + 1.0, 'low': flat_price - 1.0,
                'close': flat_price, 'volume': 1000,
            })
        bars.append({
            'timestamp': (base + timedelta(days=59)).isoformat(),
            'open': crossover_price, 'high': crossover_price + 1.0,
            'low': crossover_price - 1.0, 'close': crossover_price, 'volume': 1000,
        })
        return bars

    def _make_declining_bars(self, start_price=100.0):
        """Generate bars that stay below SMA50."""
        bars = []
        base = datetime(2024, 1, 1, tzinfo=timezone.utc)
        for i in range(60):
            p = start_price - i * 0.5
            bars.append({
                'timestamp': (base + timedelta(days=i)).isoformat(),
                'open': p, 'high': p + 1.0, 'low': p - 1.0,
                'close': p, 'volume': 1000,
            })
        return bars

    @patch('alpaca_trade_api.REST')
    @patch('paper_daemon.DataFetcher')
    def test_full_pipeline_on_crossover(self, MockFetcher, MockREST):
        """
        Simulate BTC crossing above SMA50 while ETH stays below.
        Verify end-to-end pipeline: signal -> order -> heartbeat.
        """
        from paper_daemon import PaperDaemon
        d = PaperDaemon()

        # BTC crosses, ETH declines (no cross)
        btc_bars = self._make_crossover_bars(crossover_price=200.0, flat_price=100.0)
        eth_bars = self._make_declining_bars(start_price=100.0)

        def fetch_side_effect(asset, **kwargs):
            if asset == 'BTCUSD':
                return btc_bars
            return eth_bars

        d.fetcher = MagicMock()
        d.fetcher.fetch_bars.side_effect = fetch_side_effect

        # Mock API — capture order placement
        d.api = MagicMock()
        mock_order = MagicMock()
        mock_order.id = 'test-order-123'
        d.api.submit_order.return_value = mock_order
        d.api.list_positions.return_value = []

        # Run daemon cycle
        d.run_cycle()

        # Verify 1: Order placement was attempted exactly once (BTC only)
        self.assertEqual(d.api.submit_order.call_count, 1,
                        f"Expected 1 order (BTC), got {d.api.submit_order.call_count}")

        # Verify 2: Order is for BTC
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
        self.assertEqual(hb['signal'], 'BTCUSD_LONG')
        self.assertEqual(hb['order_placed'], True)
        self.assertEqual(hb['btc_price'], 200.0)

        # Verify 5: No errors logged
        self.assertIsNone(hb.get('error_message'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
