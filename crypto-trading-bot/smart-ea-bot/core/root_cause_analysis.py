"""
Root Cause Analysis: Alpaca vs Yahoo Finance Data Mismatch
Step-by-step investigation of why prices differ by 25-46%
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
import logging

logging.basicConfig(level=logging.WARNING)

print("=" * 70)
print("ROOT CAUSE ANALYSIS: Alpaca vs Yahoo Finance")
print("=" * 70)

# Step 1: Check symbol formats
print("\n📋 Step 1: Symbol Format Check")
print("   Yahoo Finance symbols: BTC-USD, ETH-USD")
print("   Alpaca symbols: BTCUSD, ETHUSD")
print("   Are they the same instrument? Need to verify...")

# Step 2: Fetch detailed comparison
fetcher = DataFetcher(paper=True)

for asset in ["BTCUSD", "ETHUSD"]:
    print(f"\n📊 {asset} Deep Dive:")
    
    # Yahoo Finance
    yahoo_bars = fetch_yahoo_bars(asset, interval="1d", period="1mo")
    print(f"   Yahoo Finance: {len(yahoo_bars)} bars")
    
    # Alpaca (latest month)
    from datetime import datetime, timezone
    end = datetime.now(timezone.utc)
    start = end.replace(day=1)
    alpaca_bars = fetcher.fetch_bars(asset, timeframe="1Day", start=start, end=end, limit=100)
    print(f"   Alpaca: {len(alpaca_bars)} bars")
    
    if len(yahoo_bars) == 0 or len(alpaca_bars) == 0:
        print("   ⚠️ Insufficient data")
        continue
    
    # Compare latest 5 days side by side
    print(f"\n   Side-by-side comparison (latest 5 days):")
    print(f"   {'Date':<12} {'Yahoo Close':>12} {'Alpaca Close':>13} {'Diff %':>8} {'Yahoo ATR%':>10}")
    print(f"   {'-'*60}")
    
    for i in range(min(5, len(yahoo_bars), len(alpaca_bars))):
        yahoo = yahoo_bars[-(i+1)]
        alpaca = alpaca_bars[-(i+1)]
        
        yahoo_close = yahoo["close"]
        alpaca_close = alpaca["close"]
        
        # Calculate ATR as % of price
        if len(yahoo_bars) > i+2:
            yahoo_high = yahoo["high"]
            yahoo_low = yahoo["low"]
            yahoo_atr_pct = (yahoo_high - yahoo_low) / yahoo_close * 100
        else:
            yahoo_atr_pct = 0
        
        diff_pct = abs(yahoo_close - alpaca_close) / ((yahoo_close + alpaca_close) / 2) * 100
        
        yahoo_date = yahoo["timestamp"][:10] if isinstance(yahoo["timestamp"], str) else str(yahoo["timestamp"])[:10]
        
        print(f"   {yahoo_date:<12} ${yahoo_close:>10,.2f} ${alpaca_close:>11,.2f} {diff_pct:>7.2f}% {yahoo_atr_pct:>9.2f}%")
    
    # Check if shapes are similar (same trend direction)
    print(f"\n   Trend comparison (last 5 days):")
    yahoo_changes = []
    alpaca_changes = []
    
    for i in range(min(5, len(yahoo_bars)-1, len(alpaca_bars)-1)):
        yahoo_change = (yahoo_bars[-(i+1)]["close"] - yahoo_bars[-(i+2)]["close"]) / yahoo_bars[-(i+2)]["close"] * 100
        alpaca_change = (alpaca_bars[-(i+1)]["close"] - alpaca_bars[-(i+2)]["close"]) / alpaca_bars[-(i+2)]["close"] * 100
        yahoo_changes.append(yahoo_change)
        alpaca_changes.append(alpaca_change)
    
    same_direction = sum(1 for y, a in zip(yahoo_changes, alpaca_changes) if (y > 0) == (a > 0))
    print(f"   Same trend direction: {same_direction}/{len(yahoo_changes)} days")
    
    if same_direction >= 3:
        print(f"   ✅ Shape is SIMILAR — prices move in same direction")
        print(f"   Hypothesis: Different base prices (e.g., different exchanges)")
    else:
        print(f"   ❌ Shape is DIFFERENT — prices move independently")
        print(f"   Hypothesis: Completely different instruments or data feeds")

print("\n" + "=" * 70)
print("ROOT CAUSE ANALYSIS COMPLETE")
print("=" * 70)
