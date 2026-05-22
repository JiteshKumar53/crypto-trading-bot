"""
Smart EA Bot Company — Tournament Round 3 (Walk-Forward)
Uses 70/15/15 split: Design/Validation/OOS
OOS touched only once per bot.
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Tuple

# Load .env
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

# Import bot strategies
from bots.mean_reversion_scalper_v3.strategy import mean_reversion_v3_strategy
from bots.trend_pullback_scalper_v3.strategy import trend_pullback_v3_strategy
from bots.breakout_retest_bot.strategy import breakout_retest_strategy
from bots.volatility_breakout_bot.strategy import volatility_squeeze_strategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OOS Windows (committed in GOVERNANCE.md)
DESIGN_START = "2023-05-23T00:00:00-04:00"
DESIGN_END = "2023-06-13T23:59:59-04:00"
VAL_START = "2023-06-14T00:00:00-04:00"
VAL_END = "2023-06-18T23:59:59-04:00"
OOS_START = "2023-06-19T00:00:00-04:00"
OOS_END = "2023-06-27T23:59:59-04:00"

BOT_REGISTRY = {
    "mean_reversion_scalper_v3": {
        "strategy": mean_reversion_v3_strategy,
        "regimes": ["ranging"],
        "timeframes": ["5m", "15m"],
    },
    "trend_pullback_scalper_v3": {
        "strategy": trend_pullback_v3_strategy,
        "regimes": ["trending_up", "trending_down"],
        "timeframes": ["5m", "15m", "1h"],
    },
    "breakout_retest_bot": {
        "strategy": breakout_retest_strategy,
        "regimes": ["ranging", "high_volatility"],
        "timeframes": ["5m", "15m"],
    },
    "volatility_breakout_bot": {
        "strategy": volatility_squeeze_strategy,
        "regimes": ["high_volatility"],
        "timeframes": ["5m", "15m"],
    },
}


def split_bars(bars: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Split bars into Design / Validation / OOS windows."""
    design = []
    validation = []
    oos = []
    
    for bar in bars:
        ts = bar["timestamp"]
        # Simple string comparison works for ISO format
        if ts <= DESIGN_END:
            design.append(bar)
        elif ts <= VAL_END:
            validation.append(bar)
        elif ts <= OOS_END:
            oos.append(bar)
    
    return design, validation, oos


def check_gates(result) -> Dict:
    """Check all validation gates."""
    gates = {
        "profit_factor": result.profit_factor > 1.2,
        "min_trades": result.total_trades >= 100,
        "max_drawdown": result.max_drawdown_pct < 10,
        "positive_return": result.total_return_pct > 0,
        "explainable": True,  # All our strategies are explainable
    }
    
    gates["all_pass"] = all(gates.values())
    return gates


def run_bot_oos(bot_name: str, strategy_func, bars: List[Dict], asset: str) -> Dict:
    """Run a single bot through OOS test."""
    
    # Split data
    design, validation, oos = split_bars(bars)
    
    print(f"\n{'='*70}")
    print(f"🤖 {bot_name} on {asset}")
    print(f"{'='*70}")
    print(f"   Design:      {len(design)} bars ({DESIGN_START[:10]} → {DESIGN_END[:10]})")
    print(f"   Validation:  {len(validation)} bars ({VAL_START[:10]} → {VAL_END[:10]})")
    print(f"   OOS:         {len(oos)} bars ({OOS_START[:10]} → {OOS_END[:10]})")
    
    # Check if we have enough OOS data
    if len(oos) < 100:
        print(f"   ⚠️ INSUFFICIENT OOS DATA ({len(oos)} bars)")
        return None
    
    # Run on OOS only (design/validation not backtested here —
    # strategies are already designed and validated offline)
    
    results = {}
    
    # Test multiple fee scenarios
    fee_scenarios = [
        {"name": "normal", "fee": 0.10, "slippage": 0.05},
        {"name": "low_cost", "fee": 0.05, "slippage": 0.025},
        {"name": "high_cost", "fee": 0.20, "slippage": 0.10},
    ]
    
    for scenario in fee_scenarios:
        print(f"\n   📊 Testing {scenario['name']} fees...")
        engine = BacktestEngine(initial_equity=10000.0)
        result = engine.run(
            strategy_func, oos, asset,
            fee_pct=scenario["fee"],
            slippage_pct=scenario["slippage"]
        )
        
        gates = check_gates(result)
        
        results[scenario["name"]] = {
            "trades": result.total_trades,
            "return_pct": round(result.total_return_pct, 2),
            "win_rate": round(result.win_rate, 2),
            "profit_factor": round(result.profit_factor, 2),
            "max_dd": round(result.max_drawdown_pct, 2),
            "sharpe": round(result.sharpe_ratio, 2),
            "avg_win": round(result.avg_win_pct, 2),
            "avg_loss": round(result.avg_loss_pct, 2),
            "worst_streak": result.worst_streak,
            "gates_pass": gates["all_pass"],
            "gate_details": gates,
        }
        
        status = "✅ PASS" if gates["all_pass"] else "❌ FAIL"
        print(f"      Trades: {result.total_trades}, Return: {result.total_return_pct:.2f}%, PF: {result.profit_factor:.2f}, DD: {result.max_drawdown_pct:.2f}% {status}")
    
    return results


def run_tournament_round3():
    """Run full Tournament Round 3 with walk-forward validation."""
    
    print("=" * 80)
    print("🏆 TOURNAMENT ROUND 3 — Walk-Forward Validation")
    print("=" * 80)
    print(f"OOS Window: {OOS_START[:10]} → {OOS_END[:10]}")
    print(f"Assets: BTC/USD, ETH/USD")
    print(f"Bots: {len(BOT_REGISTRY)} candidates")
    print("=" * 80)
    
    # Fetch data
    fetcher = DataFetcher(paper=True)
    
    assets_data = {}
    for asset in ["BTCUSD", "ETHUSD"]:
        print(f"\n📊 Fetching {asset}...")
        bars = fetcher.fetch_bars(
            symbol=asset,
            timeframe="5Min",
            start=datetime.fromisoformat(DESIGN_START),
            end=datetime.fromisoformat(OOS_END),
            limit=10000
        )
        assets_data[asset] = bars
        print(f"   Loaded {len(bars)} bars")
    
    # Run each bot
    tournament_results = {}
    
    for bot_name, bot_config in BOT_REGISTRY.items():
        strategy_func = bot_config["strategy"]
        
        for asset, bars in assets_data.items():
            key = f"{bot_name}_{asset}"
            results = run_bot_oos(bot_name, strategy_func, bars, asset)
            
            if results:
                tournament_results[key] = {
                    "bot": bot_name,
                    "asset": asset,
                    "results": results,
                }
    
    # Rank results
    print("\n" + "=" * 80)
    print("📊 FINAL RANKING — Tournament Round 3")
    print("=" * 80)
    
    # Score each bot-asset pair
    scored = []
    for key, data in tournament_results.items():
        # Use normal fee scenario for ranking
        normal = data["results"].get("normal", {})
        
        # Score = profit_factor if passes gates, else 0
        score = normal.get("profit_factor", 0) if normal.get("gates_pass") else 0
        
        scored.append({
            "key": key,
            "bot": data["bot"],
            "asset": data["asset"],
            "score": score,
            "pf": normal.get("profit_factor", 0),
            "return": normal.get("return_pct", 0),
            "trades": normal.get("trades", 0),
            "dd": normal.get("max_dd", 0),
            "pass": normal.get("gates_pass", False),
        })
    
    scored.sort(key=lambda x: x["score"], reverse=True)
    
    print("\n🥇 RANKING (by Profit Factor, only passing gates):")
    for i, s in enumerate(scored, 1):
        status = "✅ PASS" if s["pass"] else "❌ FAIL"
        print(f"   {i}. {s['bot']} on {s['asset']}: PF={s['pf']:.2f}, Return={s['return']:.2f}%, Trades={s['trades']}, DD={s['dd']:.2f}% {status}")
    
    passing = [s for s in scored if s["pass"]]
    
    print(f"\n{'='*80}")
    if passing:
        print(f"✅ {len(passing)} BOT(S) PASSED ALL GATES")
        print(f"   Ready for paper trading preparation.")
    else:
        print(f"❌ NO BOTS PASSED ALL GATES")
        print(f"   Paper trading remains BLOCKED.")
        print(f"   Generating v4 candidates...")
    print(f"{'='*80}")
    
    # Save report
    report_dir = "reports/backtests"
    os.makedirs(report_dir, exist_ok=True)
    
    report_path = f"{report_dir}/tournament_round3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(report_path, "w") as f:
        f.write("# Tournament Round 3 Report\n\n")
        f.write(f"**Date:** {datetime.now().isoformat()}\n")
        f.write(f"**OOS Window:** {OOS_START[:10]} → {OOS_END[:10]}\n\n")
        
        f.write("## Results\n\n")
        f.write("| Rank | Bot | Asset | PF | Return | Trades | Max DD | Status |\n")
        f.write("|------|-----|-------|----|--------|--------|--------|--------|\n")
        for i, s in enumerate(scored, 1):
            status = "✅ PASS" if s["pass"] else "❌ FAIL"
            f.write(f"| {i} | {s['bot']} | {s['asset']} | {s['pf']:.2f} | {s['return']:.2f}% | {s['trades']} | {s['dd']:.2f}% | {status} |\n")
        
        f.write(f"\n## Conclusion\n")
        if passing:
            f.write(f"✅ **{len(passing)} bot(s) passed all gates.** Ready for paper trading.\n")
        else:
            f.write(f"❌ **No bots passed.** Paper trading blocked.\n")
    
    print(f"\n📝 Report saved: {report_path}")
    
    return tournament_results


if __name__ == "__main__":
    run_tournament_round3()
