#!/usr/bin/env python3
"""Standalone daemon integration tests — isolated process, no import contamination."""

import sys
import os
import json
import tempfile
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

# Mock alpaca_trade_api BEFORE importing anything else
sys.modules['alpaca_trade_api'] = MagicMock()
sys.modules['alpaca_trade_api.REST'] = MagicMock()

# Mock time.sleep to prevent 60-second delays in retry loops
import time
time.sleep = MagicMock()

script_dir = os.path.dirname(os.path.abspath(__file__))
core_dir = os.path.dirname(script_dir)
sys.path.insert(0, core_dir)

from paper_daemon import PaperDaemon

test_dir = tempfile.mkdtemp(prefix="daemon_test_")
os.chdir(test_dir)
os.environ['ALPACA_API_KEY'] = 'test_key'
os.environ['ALPACA_SECRET_KEY'] = 'test_secret'

def make_bars(count=60, price=100.0, trend='flat'):
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

tests_passed = 0
tests_failed = 0

# Test 1: Daily bars
print("test_01_daemon_fetches_daily_bars ... ", end="", flush=True)
try:
    d = PaperDaemon()
    d.fetcher = MagicMock()
    d.fetcher.fetch_bars.return_value = make_bars(60)
    d.api = MagicMock()
    signals, details = d.check_signals()
    tf = d.fetcher.fetch_bars.call_args[1].get('timeframe')
    assert tf == '1Day', f"Expected '1Day' but got {tf}"
    print("PASS")
    tests_passed += 1
except Exception as e:
    print(f"FAIL: {e}")
    tests_failed += 1

# Test 2: SMA match
print("test_02_daemon_sma_matches_backtest ... ", end="", flush=True)
try:
    d = PaperDaemon()
    bars = make_bars(60, trend='flat')
    for i, bar in enumerate(bars):
        bar['close'] = 100.0 + i * 0.1
    d.fetcher = MagicMock()
    d.fetcher.fetch_bars.return_value = bars
    d.api = MagicMock()
    signals, details = d.check_signals()
    daemon_sma = details.get('btc_sma50')
    closes = [b['close'] for b in bars]
    backtest_sma = sum(closes[-50:]) / 50
    assert daemon_sma is not None
    diff_pct = abs(daemon_sma - backtest_sma) / backtest_sma * 100
    assert diff_pct < 0.01, f"Daemon SMA differs by {diff_pct:.4f}%"
    print("PASS")
    tests_passed += 1
except Exception as e:
    print(f"FAIL: {e}")
    tests_failed += 1

# Test 3: No trade without signal
print("test_03_no_trade_without_signal ... ", end="", flush=True)
try:
    d = PaperDaemon()
    d.fetcher = MagicMock()
    d.fetcher.fetch_bars.return_value = make_bars(60, trend='declining')
    d.api = MagicMock()
    d.run_cycle()
    d.api.submit_order.assert_not_called()
    with open(d.heartbeat_file) as f:
        hb = json.load(f)
    assert hb['signal'] == 'NONE'
    assert hb['order_placed'] == False
    print("PASS")
    tests_passed += 1
except Exception as e:
    print(f"FAIL: {e}")
    tests_failed += 1

# Test 4: API failure recovery
print("test_04_api_failure_recovery ... ", end="", flush=True)
try:
    if os.path.exists('logs/daemon_heartbeat.json'):
        os.remove('logs/daemon_heartbeat.json')
    d = PaperDaemon()
    d.fetcher = MagicMock()
    d.fetcher.fetch_bars.side_effect = Exception("Connection timeout")
    d.api = MagicMock()
    d.run_cycle()
    with open(d.heartbeat_file) as f:
        hb = json.load(f)
    assert hb['status'] == 'ERROR'
    assert 'timeout' in hb.get('error_message', '').lower()
    print("PASS")
    tests_passed += 1
except Exception as e:
    print(f"FAIL: {e}")
    tests_failed += 1

# Test 5: Duplicate run skipped
print("test_05_duplicate_run_skipped ... ", end="", flush=True)
try:
    if os.path.exists('logs/daemon_heartbeat.json'):
        os.remove('logs/daemon_heartbeat.json')
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
    assert hb['status'] == 'SKIPPED'
    print("PASS")
    tests_passed += 1
except Exception as e:
    print(f"FAIL: {e}")
    tests_failed += 1

print(f"\n{'='*50}")
print(f"Results: {tests_passed} passed, {tests_failed} failed")
print(f"{'='*50}")

if tests_failed > 0:
    sys.exit(1)
