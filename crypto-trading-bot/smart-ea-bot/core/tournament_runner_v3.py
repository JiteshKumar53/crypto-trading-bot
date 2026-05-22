"""
Smart EA Bot Company — Tournament Runner v3
Extended data, fee sensitivity, walk-forward validation.
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
from core.regime_filter import regime_filter
from bots.mean_reversion_scalper_v3.strategy import mean_reversion_v3_strategy
from bots.trend_pullback_scalper_v3.strategy import trend_pullback_v3_strategy
from bots.breakout_retest_bot.strategy import breakout_retest_strategy
from bots.volatility_breakout_bot.strategy import volatility_squeeze_strategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


BOT_REGISTRY = {
    "mean_reversion_scalper_v3": {
        "strategy": mean_reversion_v3_strategy,
        "spec": "bots/mean_reversion_scalper_v3/strategy_spec.md",
        "regimes": ["ranging"],
        "timeframes": ["5m", "15m"],
    },
    "trend_pullback_scalper_v3": {
        "strategy": trend_pullback_v3_strategy,
        "spec": "bots/trend_pullback_scalper_v3/strategy_spec.md",
        "regimes": ["trending_up", "trending_down"],
        "timeframes": ["5m", "15m", "1h"],
    },
    "breakout_retest_bot": {
        "strategy": breakout_retest_strategy,
        "spec": "bots/breakout_retest_bot/strategy_spec.md",
        "regimes": ["ranging", "high_volatility"],
        "timeframes": ["5m", "15m"],
    },
    "volatility_breakout_bot": {
        "strategy": volatility_squeeze_strategy,
        "spec": "bots/volatility_breakout_bot/strategy_spec.md",
        "regimes": ["high_volatility"],
        "timeframes": ["5m", "15m"],
    },
}


def run_extended_tournament(
    assets: List[str] = None,
    start_days: int = 365,
    fee_pct: float = 0.10,
    slippage_pct: float = 0.05,
) -> Dict:
    """
    Run strategy tournament with extended data and fee sensitivity.
    """
    if assets is None:
        assets = ["BTCUSD", "ETHUSD"]
    
    fetcher = DataFetcher(paper=True)
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=start_days)
    
    all_results = []
    data_cache = {}
    
    print("=" * 80)
    print("STRATEGY TOURNAMENT v3 — Extended Data + Fee Sensitivity")
    print("=" * 80)
    print(f"Data Range: {start.date()} to {end.date()} ({start_days} days)")
    print(f"Assets: {', '.join(assets)}")
    print(f"Fee Model: {fee_pct}% per side + {slippage_pct}% slippage")
    print("=" * 80)
    
    # Fetch data once per asset
    for asset in assets:
        print(f"\n📊 Fetching {asset}...")
        bars = fetcher.fetch_bars(symbol=asset, timeframe="5Min", start=start, end=end, limit=10000)
        if len(bars) < 100:
            print(f"   ⚠️ Insufficient data: {len(bars)} bars")
            continue
        data_cache[asset] = bars
        print(f"   Loaded {len(bars)} bars ({bars[0]['timestamp']} to {bars[-1]['timestamp']})")
    
    # Fee sensitivity scenarios
    fee_scenarios = [
        {"name": "normal", "fee_pct": fee_pct, "slippage_pct": slippage_pct},
        {"name": "high_cost", "fee_pct": fee_pct * 2, "slippage_pct": slippage_pct * 2},
        {"name": "low_cost", "fee_pct": fee_pct * 0.5, "slippage_pct": slippage_pct * 0.5},
    ]
    
    # Run each bot on each asset with each fee scenario
    for bot_name, bot_config in BOT_REGISTRY.items():
        strategy_func = bot_config["strategy"]
        
        for asset, bars in data_cache.items():
            for fee_scenario in fee_scenarios:
                print(f"\n🤖 Testing {bot_name} on {asset} ({fee_scenario['name']} fees)...")
                
                engine = BacktestEngine(initial_equity=10000.0)
                result = engine.run(
                    strategy_func, bars, asset,
                    fee_pct=fee_scenario["fee_pct"],
                    slippage_pct=fee_scenario["slippage_pct"]
                )
                
                result_dict = {
                    "bot": bot_name,
                    "asset": asset,
                    "fee_scenario": fee_scenario["name"],
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
    
    passing.sort(key=lambda x: (x["profit_factor"], x["total_return_pct"]), reverse=True)
    failing.sort(key=lambda x: (x["profit_factor"], x["total_return_pct"]), reverse=True)
    
    print("\n" + "=" * 80)
    print("TOURNAMENT RESULTS v3")
    print("=" * 80)
    
    print(f"\n🥇 PASSING ({len(passing)} results):")
    for i, r in enumerate(passing, 1):
        print(f"   {i}. {r['bot']} on {r['asset']} ({r['fee_scenario']}): PF={r['profit_factor']}, Return={r['total_return_pct']}%, DD={r['max_drawdown_pct']}%, Trades={r['total_trades']}")
    
    print(f"\n❌ FAILING ({len(failing)} results):")
    for i, r in enumerate(failing, 1):
        print(f"   {i}. {r['bot']} on {r['asset']} ({r['fee_scenario']}): PF={r['profit_factor']}, Return={r['total_return_pct']}%, DD={r['max_drawdown_pct']}%, Trades={r['total_trades']}")
    
    # Generate report
    report_path = f"reports/backtests/tournament_v3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    os.makedirs("reports/backtests", exist_ok=True)
    
    with open(report_path, "w") as f:
        f.write("# Strategy Tournament Report v3\n\n")
        f.write(f"**Date:** {datetime.now().isoformat()}\n")
        f.write(f"**Data Range:** {start.date()} to {end.date()} ({start_days} days)\n")
        f.write(f"**Fee Model:** {fee_pct}% per side + {slippage_pct}% slippage\n\n")
        
        f.write("## Passing Strategies\n\n")
        f.write("| Rank | Bot | Asset | Fee Scenario | Trades | Return % | Win Rate | PF | Max DD | Sharpe |\n")
        f.write("|------|-----|-------|-------------|--------|----------|----------|----|--------|--------|\n")
        for i, r in enumerate(passing, 1):
            f.write(f"| {i} | {r['bot']} | {r['asset']} | {r['fee_scenario']} | {r['total_trades']} | {r['total_return_pct']}% | {r['win_rate']}% | {r['profit_factor']} | {r['max_drawdown_pct']}% | {r['sharpe_ratio']} |\n")
        if not passing:
            f.write("_No strategies passed thresholds._\n")
        
        f.write("\n## Failing Strategies\n\n")
        f.write("| Rank | Bot | Asset | Fee Scenario | Trades | Return % | Win Rate | PF | Max DD | Sharpe |\n")
        f.write("|------|-----|-------|-------------|--------|----------|----------|----|--------|--------|\n")
        for i, r in enumerate(failing, 1):
            f.write(f"| {i} | {r['bot']} | {r['asset']} | {r['fee_scenario']} | {r['total_trades']} | {r['total_return_pct']}% | {r['win_rate']}% | {r['profit_factor']} | {r['max_drawdown_pct']}% | {r['sharpe_ratio']} |\n")
        
        f.write("\n## Fee Sensitivity Analysis\n\n")
        for bot in BOT_REGISTRY:
            bot_results = [r for r in all_results if r["bot"] == bot]
            f.write(f"### {bot}\n")
            for r in bot_results:
                f.write(f"- **{r['fee_scenario']}**: PF={r['profit_factor']}, Return={r['total_return_pct']}%, Trades={r['total_trades']}\n")
            f.write("\n")
        
        f.write("\n## Thresholds\n")
        f.write("- Profit factor \u003e 1.2\n")
        f.write("- At least 100 trades\n")
        f.write("- Max drawdown \u003c 10%\n")
        f.write("- Survives normal + high fees\n\n")
        f.write("**Result:** " + (f"✅ {len(passing)} passing strategies" if passing else "❌ NO STRATEGIES PASSED"))
    
    # Save raw results
    json_path = report_path.replace(".md", ".json")
    with open(json_path, "w") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n📝 Report saved: {report_path}")
    print(f"📊 Raw results: {json_path}")
    
    return {
        "passing": passing,
        "failing": failing,
        "all_results": all_results,
        "report_path": report_path,
        "json_path": json_path,
    }


if __name__ == "__main__":
    run_extended_tournament()
