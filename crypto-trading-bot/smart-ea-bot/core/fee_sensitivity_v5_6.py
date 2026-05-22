"""
Fee sensitivity test for Trend Rider v5.6
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.yahoo_data_fetcher import fetch_yahoo_bars
from core.backtest_engine import BacktestEngine
from bots.trend_rider_v5_6.strategy import trend_rider_v5_6_strategy

print("Fee Sensitivity — Trend Rider v5.6")
print("=" * 60)

for asset in ["BTCUSD", "ETHUSD"]:
    print(f"\n{asset}:")
    bars = fetch_yahoo_bars(asset, interval="1d", period="5y")
    
    for fee_label, fee, slippage in [
        ("Normal", 0.10, 0.05),
        ("1.5x", 0.15, 0.075),
        ("2x", 0.20, 0.10),
        ("3x", 0.30, 0.15),
    ]:
        result = BacktestEngine(10000.0).run(
            trend_rider_v5_6_strategy, bars, asset, 
            fee_pct=fee, slippage_pct=slippage
        )
        status = "✅" if result.profit_factor > 1.3 else "❌"
        print(f"  {fee_label}: Trades={result.total_trades}, PF={result.profit_factor:.2f}, Return={result.total_return_pct:.2f}% {status}")
