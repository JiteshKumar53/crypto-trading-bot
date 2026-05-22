"""Quick test v5.4"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.yahoo_data_fetcher import fetch_yahoo_bars
from core.backtest_engine import BacktestEngine
from bots.trend_rider_v5_4.strategy import trend_rider_v5_4_strategy

print("Testing Trend Rider v5.4 (Daily Fast EMA)...")
for asset in ["BTCUSD", "ETHUSD"]:
    bars = fetch_yahoo_bars(asset, interval="1d", period="2y")
    result = BacktestEngine(10000.0).run(trend_rider_v5_4_strategy, bars, asset, fee_pct=0.10, slippage_pct=0.05)
    status = "✅ PASS" if result.passes_thresholds else "❌ FAIL"
    print(f"{asset}: Trades={result.total_trades}, Return={result.total_return_pct:.2f}%, PF={result.profit_factor:.2f}, DD={result.max_drawdown_pct:.2f}% {status}")
