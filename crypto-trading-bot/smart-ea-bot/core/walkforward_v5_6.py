"""
Walk-forward validation for Trend Rider v5.6
70% training, 30% OOS test
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.yahoo_data_fetcher import fetch_yahoo_bars
from core.backtest_engine import BacktestEngine
from bots.trend_rider_v5_6.strategy import trend_rider_v5_6_strategy

print("Walk-Forward Validation — Trend Rider v5.6")
print("=" * 60)

for asset in ["BTCUSD", "ETHUSD"]:
    print(f"\n{asset}:")
    bars = fetch_yahoo_bars(asset, interval="1d", period="5y")
    
    if len(bars) < 100:
        print(f"  Insufficient data: {len(bars)} bars")
        continue
    
    # Split: 70% design, 30% OOS
    split_idx = int(len(bars) * 0.7)
    design_bars = bars[:split_idx]
    oos_bars = bars[split_idx:]
    
    print(f"  Total: {len(bars)} bars")
    print(f"  Design: {len(design_bars)} bars ({design_bars[0]['timestamp'][:10]} → {design_bars[-1]['timestamp'][:10]})")
    print(f"  OOS: {len(oos_bars)} bars ({oos_bars[0]['timestamp'][:10]} → {oos_bars[-1]['timestamp'][:10]})")
    
    # Test on OOS only (strategy is already "designed" — simple SMA cross)
    engine = BacktestEngine(10000.0)
    result = engine.run(trend_rider_v5_6_strategy, oos_bars, asset, fee_pct=0.10, slippage_pct=0.05)
    
    status = "✅ PASS" if result.passes_thresholds else "❌ FAIL"
    print(f"  OOS: Trades={result.total_trades}, Return={result.total_return_pct:.2f}%, PF={result.profit_factor:.2f}, DD={result.max_drawdown_pct:.2f}% {status}")
