"""
Check Alpaca daily data availability and date range
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

from core.data_fetcher import DataFetcher
from datetime import datetime, timezone, timedelta
import logging

logging.basicConfig(level=logging.INFO)

fetcher = DataFetcher(paper=True)

print("=" * 70)
print("ALPACA DAILY DATA AVAILABILITY CHECK")
print("=" * 70)

for asset in ["BTCUSD", "ETHUSD"]:
    print(f"\n📊 {asset}:")
    
    # Fetch maximum available daily data
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=365*5)
    
    bars = fetcher.fetch_bars(asset, timeframe="1Day", start=start, end=end, limit=10000)
    
    if bars:
        print(f"   Total bars: {len(bars)}")
        print(f"   Date range: {bars[0]['timestamp']} → {bars[-1]['timestamp']}")
        print(f"   First close: ${bars[0]['close']:,.2f}")
        print(f"   Last close: ${bars[-1]['close']:,.2f}")
        
        # Calculate how many years
        from datetime import datetime as dt
        first_date = dt.fromisoformat(bars[0]['timestamp'].replace('Z', '+00:00'))
        last_date = dt.fromisoformat(bars[-1]['timestamp'].replace('Z', '+00:00'))
        days = (last_date - first_date).days
        print(f"   Duration: {days} days (~{days/365:.1f} years)")
    else:
        print("   No data returned")

print("\n" + "=" * 70)
