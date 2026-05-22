"""
Check Alpaca data availability across timeframes.
"""

import os
import sys
from datetime import datetime, timezone, timedelta

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

from core.data_fetcher import DataFetcher

fetcher = DataFetcher(paper=True)
assets = ["BTC/USD", "ETH/USD"]
timeframes = ["5Min", "15Min", "1Hour", "4Hour", "1Day"]

print("=" * 60)
print("ALPACA DATA AVAILABILITY CHECK")
print("=" * 60)

end = datetime.now(timezone.utc)

for asset in assets:
    print(f"\n📊 {asset}:")
    for tf in timeframes:
        # Try to fetch as much as possible
        start = end - timedelta(days=365*3)
        try:
            bars = fetcher.fetch_bars(symbol=asset, timeframe=tf, start=start, end=end, limit=10000)
            if bars:
                first_date = bars[0]['timestamp']
                last_date = bars[-1]['timestamp']
                print(f"   {tf:6s}: {len(bars):5d} bars | {first_date} → {last_date}")
            else:
                print(f"   {tf:6s}: NO DATA")
        except Exception as e:
            print(f"   {tf:6s}: ERROR - {str(e)[:50]}")

print("\n" + "=" * 60)
