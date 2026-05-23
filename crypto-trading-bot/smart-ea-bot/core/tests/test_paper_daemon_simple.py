"""
Standalone daemon tests (avoids import hang via subprocess approach).
"""

import os
import sys
import json
import tempfile
import subprocess
from datetime import datetime, timezone, timedelta

def run_daemon_test(name, test_code):
    """Run a single daemon test in subprocess to avoid import hang."""
    full_code = f'''
import os, sys, json, tempfile
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
os.environ['ALPACA_API_KEY'] = 'test'
os.environ['ALPACA_SECRET_KEY'] = 'test'

# Change to temp dir to isolate file writes
os.chdir(tempfile.mkdtemp(prefix="daemon_test_"))

# Patch REST before importing daemon
with patch('alpaca_trade_api.REST') as mock_rest:
    sys.path.insert(0, '/data/.openclaw/workspace/crypto-trading-bot/smart-ea-bot/core')
    import paper_daemon
    {test_code}
'''
    result = subprocess.run([sys.executable, '-c', full_code],
                          capture_output=True, text=True, timeout=15)
    return result


def test_daemon_fetches_daily_bars():
    code = '''
d = paper_daemon.PaperDaemon()
mock_bars = []
base = datetime(2024, 1, 1, tzinfo=timezone.utc)
for i in range(60):
    mock_bars.append({
        'timestamp': (base + timedelta(days=i)).isoformat(),
        'open': 100.0, 'high': 101.0, 'low': 99.0,
        'close': 100.0 + i, 'volume': 1000,
    })
d.fetcher = MagicMock()
d.fetcher.fetch_bars.return_value = mock_bars
signals, details = d.check_signals()
assert d.fetcher.fetch_bars.call_args[1].get('timeframe') == '1Day', "Must fetch daily bars"
print("TEST_01: PASS")
'''
    return run_daemon_test("daily_bars", code)


def test_daemon_sma_matches_backtest():
    code = '''
d = paper_daemon.PaperDaemon()
bars = []
base = datetime(2024, 1, 1, tzinfo=timezone.utc)
for i in range(60):
    bars.append({
        'timestamp': (base + timedelta(days=i)).isoformat(),
        'open': 100.0, 'high': 101.0, 'low': 99.0,
        'close': 100.0 + i * 0.1, 'volume': 1000,
    })
d.fetcher = MagicMock()
d.fetcher.fetch_bars.return_value = bars
signals, details = d.check_signals()
daemon_sma = details.get('btc_sma50')
closes = [b['close'] for b in bars]
backtest_sma = sum(closes[-50:]) / 50
assert daemon_sma is not None
assert abs(daemon_sma - backtest_sma) / backtest_sma * 100 < 0.01
print("TEST_02: PASS")
'''
    return run_daemon_test("sma_match", code)


def test_no_trade_without_signal():
    code = '''
d = paper_daemon.PaperDaemon()
mock_bars = []
base = datetime(2024, 1, 1, tzinfo=timezone.utc)
for i in range(60):
    price = 100.0 - i * 0.5
    mock_bars.append({
        'timestamp': (base + timedelta(days=i)).isoformat(),
        'open': price, 'high': price + 1.0, 'low': price - 1.0,
        'close': price, 'volume': 1000,
    })
d.fetcher = MagicMock()
d.fetcher.fetch_bars.return_value = mock_bars
d.api = MagicMock()
d.run_cycle()
d.api.submit_order.assert_not_called()
with open(d.heartbeat_file) as f:
    hb = json.load(f)
assert hb['signal'] == 'NONE'
assert hb['order_placed'] == False
print("TEST_03: PASS")
'''
    return run_daemon_test("no_signal", code)


def test_places_order_on_crossover():
    code = '''
d = paper_daemon.PaperDaemon()
mock_bars = []
base = datetime(2024, 1, 1, tzinfo=timezone.utc)
for i in range(59):
    mock_bars.append({
        'timestamp': (base + timedelta(days=i)).isoformat(),
        'open': 100.0, 'high': 101.0, 'low': 99.0,
        'close': 100.0, 'volume': 1000,
    })
mock_bars.append({
    'timestamp': (base + timedelta(days=59)).isoformat(),
    'open': 200.0, 'high': 201.0, 'low': 199.0,
    'close': 200.0, 'volume': 1000,
})
d.fetcher = MagicMock()
d.fetcher.fetch_bars.return_value = mock_bars
d.api = MagicMock()
d.run_cycle()
d.api.submit_order.assert_called_once()
qty = d.api.submit_order.call_args[1].get('qty')
assert qty * 200.0 <= 101.0
with open(d.heartbeat_file) as f:
    hb = json.load(f)
assert hb['order_placed'] == True
print("TEST_04: PASS")
'''
    return run_daemon_test("crossover", code)


def test_handles_api_failure():
    code = '''
d = paper_daemon.PaperDaemon()
d.fetcher = MagicMock()
d.fetcher.fetch_bars.side_effect = Exception("API timeout")
d.api = MagicMock()
try:
    d.run_cycle()
except Exception:
    print("TEST_05: FAIL - daemon crashed")
    sys.exit(1)
with open(d.heartbeat_file) as f:
    hb = json.load(f)
assert hb['status'] == 'ERROR'
assert 'API timeout' in hb.get('error_message', '')
print("TEST_05: PASS")
'''
    return run_daemon_test("api_failure", code)


def test_prevents_duplicate_run():
    code = '''
d = paper_daemon.PaperDaemon()
recent = {
    'last_check_utc': datetime.now(timezone.utc).isoformat(),
    'status': 'OK', 'signal': 'NONE', 'order_placed': False,
}
import os
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
print("TEST_06: PASS")
'''
    return run_daemon_test("duplicate", code)


if __name__ == '__main__':
    tests = [
        test_daemon_fetches_daily_bars,
        test_daemon_sma_matches_backtest,
        test_no_trade_without_signal,
        test_places_order_on_crossover,
        test_handles_api_failure,
        test_prevents_duplicate_run,
    ]
    
    passed = 0
    failed = 0
    
    for test_fn in tests:
        result = test_fn()
        if result.returncode == 0:
            print(result.stdout.strip())
            passed += 1
        else:
            print(f"FAIL: {test_fn.__name__}")
            print(result.stderr)
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Total: {len(tests)} | Passed: {passed} | Failed: {failed}")
    print(f"{'='*60}")
    sys.exit(0 if failed == 0 else 1)
