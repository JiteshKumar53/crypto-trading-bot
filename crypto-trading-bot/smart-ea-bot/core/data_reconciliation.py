"""
Data Source Reconciliation: Yahoo Finance vs Alpaca
Verifies daily close prices match between sources.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

from core.yahoo_data_fetcher import fetch_yahoo_bars
from core.data_fetcher import DataFetcher
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 70)
print("DATA SOURCE RECONCILIATION: Yahoo Finance vs Alpaca")
print("=" * 70)

# Fetch from both sources
fetcher = DataFetcher(paper=True)

for asset in ["BTCUSD", "ETHUSD"]:
    print(f"\n📊 {asset}:")
    
    # Yahoo Finance (2 years daily)
    yahoo_bars = fetch_yahoo_bars(asset, interval="1d", period="2y")
    print(f"   Yahoo Finance: {len(yahoo_bars)} daily bars")
    
    # Alpaca (2 years daily - if available)
    alpaca_bars = fetcher.fetch_bars(asset, timeframe="1Day", 
                                     start=datetime(2024, 5, 22, tzinfo=timezone.utc),
                                     end=datetime(2026, 5, 22, tzinfo=timezone.utc),
                                     limit=10000)
    print(f"   Alpaca: {len(alpaca_bars)} daily bars")
    
    if len(yahoo_bars) == 0 or len(alpaca_bars) == 0:
        print("   ⚠️ Insufficient data from one source")
        continue
    
    # Compare last 30 overlapping days
    mismatch_count = 0
    max_mismatch = 0
    
    for i in range(min(30, len(yahoo_bars), len(alpaca_bars))):
        yahoo_close = yahoo_bars[-(i+1)]["close"]
        alpaca_close = alpaca_bars[-(i+1)]["close"]
        
        # Calculate percentage difference
        pct_diff = abs(yahoo_close - alpaca_close) / ((yahoo_close + alpaca_close) / 2) * 100
        
        if pct_diff > max_mismatch:
            max_mismatch = pct_diff
        
        if pct_diff > 0.1:  # 0.1% threshold
            mismatch_count += 1
            print(f"   ⚠️ Day {i+1}: Yahoo ${yahoo_close:.2f} vs Alpaca ${alpaca_close:.2f} ({pct_diff:.4f}% diff)")
    
    if mismatch_count == 0:
        print(f"   ✅ PASS: All {min(30, len(yahoo_bars), len(alpaca_bars))} days within 0.1%")
        print(f"   Max mismatch: {max_mismatch:.6f}%")
    else:
        print(f"   ❌ FAIL: {mismatch_count} days exceeded 0.1% threshold")
        print(f"   Max mismatch: {max_mismatch:.4f}%")

print("\n" + "=" * 70)
print("RECONCILIATION COMPLETE")
print("=" * 70)
