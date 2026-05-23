"""
Standalone daemon tests - run each in subprocess to avoid import hang.

Usage: python3 test_paper_daemon_standalone.py
"""
import os
import sys
import json
import subprocess

os.environ['ALPACA_API_KEY'] = 'test'
os.environ['ALPACA_SECRET_KEY'] = 'test'

def run(script, timeout=20):
    return subprocess.run([sys.executable, '-c', script],
                         capture_output=True, text=True, timeout=timeout)

tests = {
    'TEST_01_daily_bars': r'''
import os, sys
os.environ['ALPACA_API_KEY'] = 'test'
os.environ['ALPACA_SECRET_KEY'] = 'test'
sys.path.insert(0, '/data/.openclaw/workspace/crypto-trading-bot/smart-ea-bot/core')
from unittest.mock import MagicMock, patch
with patch('alpaca_trade_api.REST'):
    import paper_daemon
    d = paper_daemon.PaperDaemon()
    d.fetcher = MagicMock()
    d.fetcher.fetch_bars.return_value = []
    d.check_signals()
    assert d.fetcher.fetch_bars.call_args[1].get('timeframe') == '1Day'
print("PASS")
''',
    'TEST_02_sma_match': r'''
import os, sys
os.environ['ALPACA_API_KEY'] = 'test'
os.environ['ALPACA_SECRET_KEY'] = 'test'
sys.path.insert(0, '/data/.openclaw/workspace/crypto-trading-bot/smart-ea-bot/core')
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
with patch('alpaca_trade_api.REST'):
    import paper_daemon
    d = paper_daemon.PaperDaemon()
    bars = []
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    for i in range(60):
        bars.append({'timestamp': (base + timedelta(days=i)).isoformat(), 'open': 100.0, 'high': 101.0, 'low': 99.0, 'close': 100.0 + i * 0.1, 'volume': 1000})
    d.fetcher = MagicMock()
    d.fetcher.fetch_bars.return_value = bars
    signals, details = d.check_signals()
    daemon_sma = details.get('btc_sma50')
    closes = [b['close'] for b in bars]
    backtest_sma = sum(closes[-50:]) / 50
    assert daemon_sma is not None
    assert abs(daemon_sma - backtest_sma) / backtest_sma * 100 < 0.01
print("PASS")
''',
    'TEST_03_no_signal': r'''
import os, sys
os.environ['ALPACA_API_KEY'] = 'test'
os.environ['ALPACA_SECRET_KEY'] = 'test'
sys.path.insert(0, '/data/.openclaw/workspace/crypto-trading-bot/smart-ea-bot/core')
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
with patch('alpaca_trade_api.REST'):
    import paper_daemon
    d = paper_daemon.PaperDaemon()
    mock_bars = []
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    for i in range(60):
        price = 100.0 - i * 0.5
        mock_bars.append({'timestamp': (base + timedelta(days=i)).isoformat(), 'open': price, 'high': price + 1.0, 'low': price - 1.0, 'close': price, 'volume': 1000})
    d.fetcher = MagicMock()
    d.fetcher.fetch_bars.return_value = mock_bars
    d.api = MagicMock()
    d.run_cycle()
    assert not d.api.submit_order.called
    with open(d.heartbeat_file) as f:
        hb = json.load(f)
    assert hb['signal'] == 'NONE' and hb['order_placed'] == False
print("PASS")
''',
    'TEST_04_crossover': r'''
import os, sys
os.environ['ALPACA_API_KEY'] = 'test'
os.environ['ALPACA_SECRET_KEY'] = 'test'
sys.path.insert(0, '/data/.openclaw/workspace/crypto-trading-bot/smart-ea-bot/core')
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
with patch('alpaca_trade_api.REST'):
    import paper_daemon
    d = paper_daemon.PaperDaemon()
    mock_bars = []
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    for i in range(59):
        mock_bars.append({'timestamp': (base + timedelta(days=i)).isoformat(), 'open': 100.0, 'high': 101.0, 'low': 99.0, 'close': 100.0, 'volume': 1000})
    mock_bars.append({'timestamp': (base + timedelta(days=59)).isoformat(), 'open': 200.0, 'high': 201.0, 'low': 199.0, 'close': 200.0, 'volume': 1000})
    d.fetcher = MagicMock()
    d.fetcher.fetch_bars.return_value = mock_bars
    d.api = MagicMock()
    d.run_cycle()
    with open(d.heartbeat_file) as f:
        hb = json.load(f)
    assert 'LONG' in hb.get('signal', ''), f"Got: {hb.get('signal')}"
print("PASS")
''',
    'TEST_05_api_failure': r'''
import os, sys
os.environ['ALPACA_API_KEY'] = 'test'
os.environ['ALPACA_SECRET_KEY'] = 'test'
sys.path.insert(0, '/data/.openclaw/workspace/crypto-trading-bot/smart-ea-bot/core')
from unittest.mock import MagicMock, patch
with patch('alpaca_trade_api.REST'):
    import paper_daemon
    d = paper_daemon.PaperDaemon()
    d.api = MagicMock()
    d.api.list_positions.side_effect = Exception("Connection timeout")
    d.fetcher = MagicMock()
    d.fetcher.fetch_bars.side_effect = Exception("API timeout")
    d.run_cycle()
    with open(d.heartbeat_file) as f:
        hb = json.load(f)
    assert hb['status'] == 'ERROR', f"Got: {hb['status']}"
print("PASS")
''',
    'TEST_06_duplicate': r'''
import os, sys, json
os.environ['ALPACA_API_KEY'] = 'test'
os.environ['ALPACA_SECRET_KEY'] = 'test'
sys.path.insert(0, '/data/.openclaw/workspace/crypto-trading-bot/smart-ea-bot/core')
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
with patch('alpaca_trade_api.REST'):
    import paper_daemon
    d = paper_daemon.PaperDaemon()
    recent = {'last_check_utc': datetime.now(timezone.utc).isoformat(), 'status': 'OK', 'signal': 'NONE', 'order_placed': False}
    os.makedirs('logs', exist_ok=True)
    with open(d.heartbeat_file, 'w') as f:
        json.dump(recent, f)
    d.fetcher = MagicMock()
    d.api = MagicMock()
    d.run_cycle()
    assert not d.api.submit_order.called
    with open(d.heartbeat_file) as f:
        hb = json.load(f)
    assert hb['status'] == 'SKIPPED'
print("PASS")
''',
}

if __name__ == '__main__':
    passed = 0
    failed = 0
    
    for name, script in tests.items():
        r = run(script)
        if r.returncode == 0 and 'PASS' in r.stdout:
            print(f"{name}: PASS")
            passed += 1
        else:
            print(f"{name}: FAIL")
            print("STDOUT:", r.stdout[:500])
            print("STDERR:", r.stderr[:500])
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Total: {len(tests)} | Passed: {passed} | Failed: {failed}")
    print(f"{'='*60}")
    
    sys.exit(0 if failed == 0 else 1)
