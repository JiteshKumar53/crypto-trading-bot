"""
Debug strategy signals on real data.
"""

import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_fetcher import DataFetcher
from bots.mean_reversion_scalper.strategy import calculate_rsi, calculate_sma, calculate_atr

# Load env
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

fetcher = DataFetcher(paper=True)
end = datetime.now(timezone.utc)
start = end - timedelta(days=30)

bars = fetcher.fetch_bars("BTC/USD", start=start, end=end, limit=1000)
print(f"Fetched {len(bars)} bars")

if bars:
    closes = [b['close'] for b in bars]
    rsi = calculate_rsi(closes, 14)
    sma = calculate_sma(closes, 20)
    atr = calculate_atr(bars, 14)
    
    print(f"\nFirst 10 RSI values: {[round(r, 2) for r in rsi[:10]]}")
    print(f"RSI range: {min(rsi):.2f} to {max(rsi):.2f}")
    print(f"SMA range: {min(sma):.2f} to {max(sma):.2f}")
    
    # Count how many bars meet entry criteria
    long_entries = 0
    short_entries = 0
    for i in range(25, len(bars) - 1):
        if rsi[i] < 30 and closes[i] > sma[i] and rsi[i-1] < 35:
            long_entries += 1
        if rsi[i] > 70 and closes[i] < sma[i] and rsi[i-1] > 65:
            short_entries += 1
    
    print(f"\nLong entries found: {long_entries}")
    print(f"Short entries found: {short_entries}")
    
    # Check ATR
    atr_values = [a for a in atr if a > 0]
    if atr_values:
        print(f"ATR range: {min(atr_values):.2f} to {max(atr_values):.2f}")
        print(f"ATR as % of price: {min(atr_values)/closes[25]*100:.4f}% to {max(atr_values)/closes[25]*100:.4f}%")
