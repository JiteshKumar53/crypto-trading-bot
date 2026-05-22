"""
3-fold walk-forward validation for Trend Rider v5.6
Tests consistency across multiple OOS windows.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.yahoo_data_fetcher import fetch_yahoo_bars
from core.backtest_engine import BacktestEngine
from bots.trend_rider_v5_6.strategy import trend_rider_v5_6_strategy

print("3-Fold Walk-Forward — Trend Rider v5.6")
print("=" * 70)

for asset in ["BTCUSD", "ETHUSD"]:
    print(f"\n{asset}:")
    bars = fetch_yahoo_bars(asset, interval="1d", period="5y")
    
    if len(bars) < 100:
        continue
    
    # 3-fold split
    n = len(bars)
    fold_size = n // 3
    
    windows = [
        ("Fold 1 (2021-2022)", bars[:fold_size]),
        ("Fold 2 (2022-2023)", bars[fold_size:2*fold_size]),
        ("Fold 3 (2023-2024)", bars[2*fold_size:3*fold_size]),
    ]
    
    positive_windows = 0
    total_windows = 0
    
    for name, window_bars in windows:
        if len(window_bars) < 50:
            continue
        
        engine = BacktestEngine(10000.0)
        result = engine.run(trend_rider_v5_6_strategy, window_bars, asset, fee_pct=0.10, slippage_pct=0.05)
        
        status = "✅" if result.total_return_pct > 0 and result.profit_factor > 1.0 else "❌"
        if result.total_return_pct > 0 and result.profit_factor > 1.0:
            positive_windows += 1
        total_windows += 1
        
        print(f"  {name}: Trades={result.total_trades}, Return={result.total_return_pct:.2f}%, PF={result.profit_factor:.2f}, DD={result.max_drawdown_pct:.2f}% {status}")
    
    print(f"  Positive windows: {positive_windows}/{total_windows}")
