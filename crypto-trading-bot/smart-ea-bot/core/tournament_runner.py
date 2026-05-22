"""
Smart EA Bot Company — Strategy Tournament Runner
Backtest all bot candidates on same data, rank, produce report.
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict

# Load .env file before importing modules that need API keys
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
from core.regime_filter import regime_filter as classify_regime
from bots.mean_reversion_scalper_v2.strategy import mean_reversion_v2_strategy
from bots.trend_pullback_scalper_v2.strategy import trend_pullback_v2_strategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Map bot names to strategy functions and spec paths
BOT_REGISTRY = {
    "mean_reversion_scalper_v2": {
        "strategy": mean_reversion_v2_strategy,
        "spec": "bots/mean_reversion_scalper_v2/strategy_spec.md",
        "regimes": ["ranging", "choppy"],
    },
    "trend_pullback_scalper_v2": {
        "strategy": trend_pullback_v2_strategy,
        "spec": "bots/trend_pullback_scalper_v2/strategy_spec.md",
        "regimes": ["trending_up", "trending_down"],
    },
    # Placeholder for future bots
    "breakout_retest_bot": {
        "strategy": None,
        "spec": "bots/breakout_retest_bot/strategy_spec.md",
        "regimes": ["ranging", "high_volatility"],
    },
    "volatility_breakout_bot": {
        "strategy": None,
        "spec": "bots/volatility_breakout_bot/strategy_spec.md",
        "regimes": ["high_volatility"],
    },
}


def run_tournament(
    assets: List[str] = None,
    start_days: int = 90,
    fee_pct: float = 0.10,
    slippage_pct: float = 0.05,
) -> Dict:
    """
    Run strategy tournament on all registered bots.
    Returns results and ranking.
    """
    if assets is None:
        assets = ["BTCUSD", "ETHUSD"]
    
    fetcher = DataFetcher(paper=True)
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=start_days)
    
    all_results = []
    data_cache = {}
    
    print("=" * 70)
    print("STRATEGY TOURNAMENT — Multi-Bot Research")
    print("=" * 70)
    
    # Fetch data once
    for asset in assets:
        print(f"\n📊 Fetching {asset}...")
        bars = fetcher.fetch_bars(symbol=asset, timeframe="5Min", start=start, end=end, limit=10000)
        if len(bars) < 100:
            print(f"   ⚠️ Insufficient data: {len(bars)} bars")
            continue
        data_cache[asset] = bars
        print(f"   Loaded {len(bars)} bars ({bars[0]['timestamp']} to {bars[-1]['timestamp']})")
    
    # Run each bot on each asset
    for bot_name, bot_config in BOT_REGISTRY.items():
        strategy_func = bot_config["strategy"]
        if strategy_func is None:
            print(f"\n⏭️  {bot_name}: STRATEGY NOT YET IMPLEMENTED — skipping")
            continue
        
        for asset, bars in data_cache.items():
            print(f"\n🤖 Testing {bot_name} on {asset}...")
            
            engine = BacktestEngine(initial_equity=10000.0)
            result = engine.run(strategy_func, bars, asset, fee_pct=fee_pct, slippage_pct=slippage_pct)
            
            # Get regime distribution
            regimes = classify_regime(bars)
            regime_counts = {}
            for r in regimes:
                regime_counts[r["regime"]] = regime_counts.get(r["regime"], 0) + 1
            
            result_dict = {
                "bot": bot_name,
                "asset": asset,
                "total_return_pct": round(result.total_return_pct, 2),
                "win_rate": round(result.win_rate, 2),
                "profit_factor": round(result.profit_factor, 2),
                "max_drawdown_pct": round(result.max_drawdown_pct, 2),
                "sharpe_ratio": round(result.sharpe_ratio, 2),
                "total_trades": result.total_trades,
                "avg_win_pct": round(result.avg_win_pct, 2),
                "avg_loss_pct": round(result.avg_loss_pct, 2),
                "worst_streak": result.worst_streak,
                "fees_pct": round(result.fees_pct, 2),
                "net_profit_pct": round(result.net_profit_pct, 2),
                "passes_thresholds": result.passes_thresholds,
                "regime_distribution": regime_counts,
                "exit_reasons": {},
            }
            
            if result.trades:
                reasons = {}
                for t in result.trades:
                    reasons[t["reason"]] = reasons.get(t["reason"], 0) + 1
                result_dict["exit_reasons"] = reasons
            
            all_results.append(result_dict)
            
            status = "✅ PASS" if result.passes_thresholds else "❌ FAIL"
            print(f"   Trades: {result.total_trades}, Return: {result.total_return_pct}%, PF: {result.profit_factor}, DD: {result.max_drawdown_pct}% {status}")
    
    # Rank results
    passing = [r for r in all_results if r["passes_thresholds"]]
    failing = [r for r in all_results if not r["passes_thresholds"]]
    
    # Sort by profit factor desc, then by return desc
    passing.sort(key=lambda x: (x["profit_factor"], x["total_return_pct"]), reverse=True)
    failing.sort(key=lambda x: (x["profit_factor"], x["total_return_pct"]), reverse=True)
    
    print("\n" + "=" * 70)
    print("TOURNAMENT RESULTS")
    print("=" * 70)
    
    print(f"\n🥇 PASSING ({len(passing)} bots):")
    for i, r in enumerate(passing, 1):
        print(f"   {i}. {r['bot']} on {r['asset']}: PF={r['profit_factor']}, Return={r['total_return_pct']}%, DD={r['max_drawdown_pct']}%, Trades={r['total_trades']}")
    
    print(f"\n❌ FAILING ({len(failing)} bots):")
    for i, r in enumerate(failing, 1):
        print(f"   {i}. {r['bot']} on {r['asset']}: PF={r['profit_factor']}, Return={r['total_return_pct']}%, DD={r['max_drawdown_pct']}%, Trades={r['total_trades']}")
    
    # Generate report
    report_path = f"reports/backtests/tournament_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    os.makedirs("reports/backtests", exist_ok=True)
    
    with open(report_path, "w") as f:
        f.write("# Strategy Tournament Report\n\n")
        f.write(f"**Date:** {datetime.now().isoformat()}\n")
        f.write(f"**Data Range:** Last {start_days} days\n")
        f.write(f"**Fee Model:** {fee_pct}% per side + {slippage_pct}% slippage\n\n")
        
        f.write("## Passing Strategies\n\n")
        f.write("| Rank | Bot | Asset | Trades | Return % | Win Rate | PF | Max DD | Sharpe |\n")
        f.write("|------|-----|-------|--------|----------|----------|----|--------|--------|\n")
        for i, r in enumerate(passing, 1):
            f.write(f"| {i} | {r['bot']} | {r['asset']} | {r['total_trades']} | {r['total_return_pct']}% | {r['win_rate']}% | {r['profit_factor']} | {r['max_drawdown_pct']}% | {r['sharpe_ratio']} |\n")
        if not passing:
            f.write("_No strategies passed thresholds._\n")
        
        f.write("\n## Failing Strategies\n\n")
        f.write("| Rank | Bot | Asset | Trades | Return % | Win Rate | PF | Max DD | Sharpe |\n")
        f.write("|------|-----|-------|--------|----------|----------|----|--------|--------|\n")
        for i, r in enumerate(failing, 1):
            f.write(f"| {i} | {r['bot']} | {r['asset']} | {r['total_trades']} | {r['total_return_pct']}% | {r['win_rate']}% | {r['profit_factor']} | {r['max_drawdown_pct']}% | {r['sharpe_ratio']} |\n")
        
        f.write("\n## Thresholds\n")
        f.write("- Profit factor > 1.2\n")
        f.write("- Max drawdown < 10%\n")
        f.write("- At least 100 trades\n\n")
        
        f.write("## Regime Distribution (BTC/USD sample)\n")
        if data_cache:
            first_asset = list(data_cache.keys())[0]
            regimes = classify_regime(data_cache[first_asset])
            counts = {}
            for r in regimes:
                counts[r["regime"]] = counts.get(r["regime"], 0) + 1
            for regime, count in sorted(counts.items(), key=lambda x: -x[1]):
                pct = count / len(regimes) * 100
                f.write(f"- {regime}: {count} bars ({pct:.1f}%)\n")
    
    print(f"\n📝 Report saved: {report_path}")
    
    # Save raw JSON
    json_path = f"reports/backtests/tournament_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_path, "w") as f:
        json.dump(all_results, f, indent=2)
    
    return {
        "results": all_results,
        "passing": passing,
        "failing": failing,
        "report_path": report_path,
        "json_path": json_path,
    }


if __name__ == "__main__":
    run_tournament()
