"""
Integration tests for paper_daemon.py (v3.0 hardened)

These tests verify the daemon handles real-world failure modes.
Run with: cd smart-ea-bot/core/tests && python3 test_paper_daemon.py

NOTE: Each test patches alpaca_trade_api.REST and paper_daemon.DataFetcher
BEFORE importing paper_daemon to prevent real network connections.
"""

import os
import sys
import json
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPaperDaemon(unittest.TestCase):
    """Hardened daemon integration tests."""

    def setUp(self):
        os.environ['ALPACA_API_KEY'] = 'test_key'
        os.environ['ALPACA_SECRET_KEY'] = 'test_secret'
        self.test_dir = tempfile.mkdtemp(prefix="daemon_test_")
        self.orig_dir = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        os.chdir(self.orig_dir)

    def _make_bars(self, count=60, price=100.0, trend='flat'):
        """Generate mock daily bars."""
        bars = []
        base = datetime(2024, 1, 1, tzinfo=timezone.utc)
        for i in range(count):
            if trend == 'flat':
                p = price
            elif trend == 'declining':
                p = price - i * 0.5
            elif trend == 'crossover':
                p = price if i < count - 1 else price * 2.0
            bars.append({
                'timestamp': (base + timedelta(days=i)).isoformat(),
                'open': p, 'high': p + 1.0, 'low': p - 1.0,
                'close': p, 'volume': 1000,
            })
        return bars

    def test_01_daemon_fetches_daily_bars(self):
        """Assert daemon fetch returns daily bars."""
        with patch('alpaca_trade_api.REST'):
            with patch('paper_daemon.DataFetcher') as MockFetcher:
                from paper_daemon import PaperDaemon
                d = PaperDaemon()
                d.fetcher = MagicMock()
                d.fetcher.fetch_bars.return_value = self._make_bars(60)
                d.api = MagicMock()

                signals, details = d.check_signals()
                tf = d.fetcher.fetch_bars.call_args[1].get('timeframe')
                self.assertEqual(tf, '1Day', f"Expected '1Day' but got {tf}")

    def test_02_daemon_sma_matches_backtest(self):
        """Daemon SMA must match backtest SMA within 0.01%."""
        with patch('alpaca_trade_api.REST'):
            with patch('paper_daemon.DataFetcher'):
                from paper_daemon import PaperDaemon
                d = PaperDaemon()

                bars = self._make_bars(60, trend='flat')
                for i, bar in enumerate(bars):
                    bar['close'] = 100.0 + i * 0.1

                d.fetcher = MagicMock()
                d.fetcher.fetch_bars.return_value = bars
                d.api = MagicMock()

                signals, details = d.check_signals()
                daemon_sma = details.get('btc_sma50')

                closes = [b['close'] for b in bars]
                backtest_sma = sum(closes[-50:]) / 50

                self.assertIsNotNone(daemon_sma)
                diff_pct = abs(daemon_sma - backtest_sma) / backtest_sma * 100
                self.assertLess(diff_pct, 0.01,
                                f"Daemon SMA differs by {diff_pct:.4f}%")

    def test_03_no_trade_without_signal(self):
        """Declining price (no cross) -> no order, heartbeat=NONE."""
        with patch('alpaca_trade_api.REST'):
            with patch('paper_daemon.DataFetcher'):
                from paper_daemon import PaperDaemon
                d = PaperDaemon()
                d.fetcher = MagicMock()
                d.fetcher.fetch_bars.return_value = self._make_bars(60, trend='declining')
                d.api = MagicMock()

                d.run_cycle()

                d.api.submit_order.assert_not_called()

                with open(d.heartbeat_file) as f:
                    hb = json.load(f)
                self.assertEqual(hb['signal'], 'NONE')
                self.assertEqual(hb['order_placed'], False)

    def test_04_api_failure_recovery(self):
        """API failure -> no crash, heartbeat=ERROR."""
        with patch('alpaca_trade_api.REST'):
            with patch('paper_daemon.DataFetcher'):
                from paper_daemon import PaperDaemon
                d = PaperDaemon()
                d.fetcher = MagicMock()
                d.fetcher.fetch_bars.side_effect = Exception("Connection timeout")
                d.api = MagicMock()

                try:
                    d.run_cycle()
                except Exception:
                    self.fail("Daemon crashed on API failure")

                with open(d.heartbeat_file) as f:
                    hb = json.load(f)
                self.assertEqual(hb['status'], 'ERROR')
                self.assertIn('timeout', hb.get('error_message', '').lower())

    def test_05_duplicate_run_skipped(self):
        """Same-day heartbeat -> SKIPPED, no order."""
        with patch('alpaca_trade_api.REST'):
            with patch('paper_daemon.DataFetcher'):
                from paper_daemon import PaperDaemon
                d = PaperDaemon()

                recent = {
                    'last_check_utc': datetime.now(timezone.utc).isoformat(),
                    'status': 'OK', 'signal': 'NONE', 'order_placed': False,
                }
                os.makedirs('logs', exist_ok=True)
                with open(d.heartbeat_file, 'w') as f:
                    json.dump(recent, f)

                d.fetcher = MagicMock()
                d.api = MagicMock()

                d.run_cycle()

                d.api.submit_order.assert_not_called()

                with open(d.heartbeat_file) as f:
                    hb = json.load(f)
                self.assertEqual(hb['status'], 'SKIPPED')


if __name__ == '__main__':
    unittest.main(verbosity=2)
