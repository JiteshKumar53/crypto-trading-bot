"""
Quick test runner for Trend Rider v5.1
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.yahoo_data_fetcher import fetch_4h_bars
from core.backtest_engine import BacktestEngine
from bots.trend_rider_v5_1.strategy import trend_rider_v5_1_strategy

print("Testing Trend Rider v5.1...")

for asset in ["BTCUSD", "ETHUSD"]:
    print(f"\n{asset}:")
    bars = fetch_4h_bars(asset, period="1y")
    
    engine = BacktestEngine(initial_equity=10000.0)
    result = engine.run(trend_rider_v5_1_strategy, bars, asset, fee_pct=0.10, slippage_pct=0.05)
    
    status = "✅ PASS" if result.passes_thresholds else "❌ FAIL"
    print(f"  Trades: {result.total_trades}, Return: {result.total_return_pct:.2f}%, PF: {result.profit_factor:.2f}, DD: {result.max_drawdown_pct:.2f}% {status}")
