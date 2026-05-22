"""
Smart EA Bot Company — Tournament v5 Runner
Tests Trend Rider v5 on Yahoo Finance 4h data.
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.yahoo_data_fetcher import fetch_4h_bars
from core.backtest_engine import BacktestEngine
from bots.trend_rider_v5.strategy import trend_rider_v5_strategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_tournament_v5():
    """Run Trend Rider v5 on 1 year of 4h Yahoo Finance data."""
    
    print("=" * 80)
    print("🏆 TOURNAMENT v5 — Trend Rider on 4h Data")
    print("=" * 80)
    print("Data: Yahoo Finance (1 year, 4h bars)")
    print("Bot: Trend Rider v5 (trend following)")
    print("=" * 80)
    
    assets = ["BTCUSD", "ETHUSD"]
    all_results = []
    
    for asset in assets:
        print(f"\n📊 Fetching {asset} from Yahoo Finance...")
        bars = fetch_4h_bars(asset, period="1y")
        
        if len(bars) < 100:
            print(f"   ⚠️ Insufficient data: {len(bars)} bars")
            continue
        
        print(f"   Loaded {len(bars)} 4h bars")
        print(f"   Range: {bars[0]['timestamp'][:10]} → {bars[-1]['timestamp'][:10]}")
        
        # Test normal fees
        print(f"\n   🤖 Testing Trend Rider v5...")
        engine = BacktestEngine(initial_equity=10000.0)
        result = engine.run(
            trend_rider_v5_strategy, bars, asset,
            fee_pct=0.10, slippage_pct=0.05
        )
        
        result_dict = {
            "bot": "trend_rider_v5",
            "asset": asset,
            "trades": result.total_trades,
            "return_pct": round(result.total_return_pct, 2),
            "win_rate": round(result.win_rate, 2),
            "profit_factor": round(result.profit_factor, 2),
            "max_dd": round(result.max_drawdown_pct, 2),
            "sharpe": round(result.sharpe_ratio, 2),
            "avg_win": round(result.avg_win_pct, 2),
            "avg_loss": round(result.avg_loss_pct, 2),
            "worst_streak": result.worst_streak,
            "fees_pct": round(result.fees_pct, 2),
            "passes": result.passes_thresholds,
        }
        
        all_results.append(result_dict)
        
        status = "✅ PASS" if result.passes_thresholds else "❌ FAIL"
        print(f"      Trades: {result.total_trades}, Return: {result.total_return_pct:.2f}%, PF: {result.profit_factor:.2f}, DD: {result.max_drawdown_pct:.2f}% {status}")
    
    # Rank
    print("\n" + "=" * 80)
    print("📊 FINAL RANKING — Tournament v5")
    print("=" * 80)
    
    for i, r in enumerate(sorted(all_results, key=lambda x: x["profit_factor"], reverse=True), 1):
        status = "✅ PASS" if r["passes"] else "❌ FAIL"
        print(f"   {i}. {r['bot']} on {r['asset']}: PF={r['profit_factor']:.2f}, Return={r['return_pct']:.2f}%, Trades={r['trades']}, DD={r['max_dd']:.2f}% {status}")
    
    passing = [r for r in all_results if r["passes"]]
    
    print(f"\n{'='*80}")
    if passing:
        print(f"✅ {len(passing)} RESULT(S) PASSED!")
    else:
        print(f"❌ NO RESULTS PASSED")
        print(f"   Paper trading remains BLOCKED.")
    print(f"{'='*80}")
    
    # Save report
    report_dir = "reports/backtests"
    os.makedirs(report_dir, exist_ok=True)
    report_path = f"{report_dir}/tournament_v5_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(report_path, "w") as f:
        f.write("# Tournament v5 Report — Trend Rider\n\n")
        f.write(f"**Date:** {datetime.now().isoformat()}\n")
        f.write(f"**Data:** Yahoo Finance 4h bars (1 year)\n\n")
        f.write("| Rank | Asset | Trades | Return | PF | Max DD | Status |\n")
        f.write("|------|-------|--------|--------|----|--------|--------|\n")
        for i, r in enumerate(sorted(all_results, key=lambda x: x["profit_factor"], reverse=True), 1):
            status = "✅ PASS" if r["passes"] else "❌ FAIL"
            f.write(f"| {i} | {r['asset']} | {r['trades']} | {r['return_pct']}% | {r['profit_factor']} | {r['max_dd']}% | {status} |\n")
        
        f.write(f"\n## Conclusion\n")
        if passing:
            f.write(f"✅ **{len(passing)} result(s) passed!** Ready for paper trading preparation.\n")
        else:
            f.write(f"❌ **No results passed.** Paper trading blocked.\n")
    
    print(f"\n📝 Report saved: {report_path}")
    return all_results


if __name__ == "__main__":
    run_tournament_v5()
