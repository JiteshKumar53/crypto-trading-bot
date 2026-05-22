"""
Smart EA Bot Company — Tournament v4
Tests v4 candidates on available Alpaca data.
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_fetcher import DataFetcher
from core.backtest_engine import BacktestEngine
from bots.v4_multi_timeframe_momentum.strategy import multi_timeframe_momentum
from bots.v4_vwap_reversion.strategy import vwap_reversion_strategy
from bots.v4_overnight_momentum.strategy import overnight_momentum_strategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_REGISTRY = {
    "v4_multi_timeframe_momentum": {
        "strategy": multi_timeframe_momentum,
        "hypothesis": "Crypto trends on 1h; enter on 15m pullback",
    },
    "v4_vwap_reversion": {
        "strategy": vwap_reversion_strategy,
        "hypothesis": "Price reverts to VWAP after 1.5 ATR deviation",
    },
    "v4_overnight_momentum": {
        "strategy": overnight_momentum_strategy,
        "hypothesis": "Crypto has overnight momentum breakout",
    },
}


def run_tournament_v4():
    """Run v4 tournament on full available data."""
    
    print("=" * 80)
    print("🏆 TOURNAMENT v4 — New Strategy Class")
    print("=" * 80)
    print("Data: Full available Alpaca crypto history (~35 days)")
    print("Bots: Multi-Timeframe Momentum, VWAP Reversion, Overnight Momentum")
    print("=" * 80)
    
    fetcher = DataFetcher(paper=True)
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=365)
    
    assets = ["BTCUSD", "ETHUSD"]
    all_results = []
    
    for asset in assets:
        print(f"\n📊 Fetching {asset}...")
        bars = fetcher.fetch_bars(symbol=asset, timeframe="5Min", start=start, end=end, limit=10000)
        
        if len(bars) < 100:
            print(f"   ⚠️ Insufficient data: {len(bars)} bars")
            continue
        
        print(f"   Loaded {len(bars)} bars ({bars[0]['timestamp']} → {bars[-1]['timestamp']})")
        
        for bot_name, bot_config in BOT_REGISTRY.items():
            print(f"\n   🤖 Testing {bot_name}...")
            
            # Test normal fees
            engine = BacktestEngine(initial_equity=10000.0)
            result = engine.run(
                bot_config["strategy"], bars, asset,
                fee_pct=0.10, slippage_pct=0.05
            )
            
            result_dict = {
                "bot": bot_name,
                "asset": asset,
                "hypothesis": bot_config["hypothesis"],
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
    passing = [r for r in all_results if r["passes"]]
    failing = [r for r in all_results if not r["passes"]]
    
    all_sorted = sorted(all_results, key=lambda x: x["profit_factor"], reverse=True)
    
    print("\n" + "=" * 80)
    print("📊 FINAL RANKING")
    print("=" * 80)
    
    for i, r in enumerate(all_sorted, 1):
        status = "✅ PASS" if r["passes"] else "❌ FAIL"
        print(f"   {i}. {r['bot']} on {r['asset']}: PF={r['profit_factor']:.2f}, Return={r['return_pct']:.2f}%, Trades={r['trades']}, DD={r['max_dd']:.2f}% {status}")
    
    # Save report
    report_dir = "reports/backtests"
    os.makedirs(report_dir, exist_ok=True)
    report_path = f"{report_dir}/tournament_v4_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(report_path, "w") as f:
        f.write("# Tournament v4 Report\n\n")
        f.write(f"**Date:** {datetime.now().isoformat()}\n\n")
        f.write("| Rank | Bot | Asset | Trades | Return | PF | Max DD | Status |\n")
        f.write("|------|-----|-------|--------|--------|----|--------|--------|\n")
        for i, r in enumerate(all_sorted, 1):
            status = "✅ PASS" if r["passes"] else "❌ FAIL"
            f.write(f"| {i} | {r['bot']} | {r['asset']} | {r['trades']} | {r['return_pct']}% | {r['profit_factor']} | {r['max_dd']}% | {status} |\n")
        
        if passing:
            f.write(f"\n✅ **{len(passing)} bot(s) passed!**\n")
        else:
            f.write(f"\n❌ **No bots passed.**\n")
    
    print(f"\n📝 Report saved: {report_path}")
    return all_results


if __name__ == "__main__":
    run_tournament_v4()
