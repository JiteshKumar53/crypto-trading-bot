"""
Smart EA Bot Company — Historical Backtest Runner
Fetch real Alpaca data, validate quality, run backtests, generate reports.
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta, timezone
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
from bots.mean_reversion_scalper.strategy import mean_reversion_strategy
from bots.trend_pullback_scalper.strategy import trend_pullback_strategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_data_quality(bars: List[Dict]) -> Dict:
    """Check data quality issues."""
    issues = []
    
    if not bars:
        return {"valid": False, "issues": ["No data returned"], "candles": 0}
    
    # Check for zero or negative prices
    for i, bar in enumerate(bars):
        for field in ["open", "high", "low", "close"]:
            if bar[field] <= 0:
                issues.append(f"Bar {i}: {field} <= 0 ({bar[field]})")
    
    # Check OHLC consistency
    for i, bar in enumerate(bars):
        if bar["high"] < bar["low"]:
            issues.append(f"Bar {i}: high < low")
        if bar["high"] < max(bar["open"], bar["close"]):
            issues.append(f"Bar {i}: high < max(open,close)")
        if bar["low"] > min(bar["open"], bar["close"]):
            issues.append(f"Bar {i}: low > min(open,close)")
    
    # Check for gaps > 180 minutes (crypto maintenance windows)
    for i in range(1, len(bars)):
        t1 = datetime.fromisoformat(bars[i-1]["timestamp"])
        t2 = datetime.fromisoformat(bars[i]["timestamp"])
        gap = (t2 - t1).total_seconds() / 60
        if gap > 180:
            issues.append(f"Gap at bar {i}: {gap:.0f} minutes")
    
    # Check for duplicate timestamps
    timestamps = [bar["timestamp"] for bar in bars]
    if len(timestamps) != len(set(timestamps)):
        issues.append("Duplicate timestamps detected")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "candles": len(bars),
        "start": bars[0]["timestamp"] if bars else None,
        "end": bars[-1]["timestamp"] if bars else None,
    }


def run_backtest_for_bot(strategy_func, bars: List[Dict], asset: str, bot_name: str) -> Dict:
    """Run backtest for a single bot/asset combination."""
    logger.info(f"Running backtest: {bot_name} on {asset}")
    
    engine = BacktestEngine(initial_equity=10000.0)
    result = engine.run(strategy_func, bars, asset, fee_pct=0.10, slippage_pct=0.05)
    
    return {
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
    }


def main():
    """Main backtest execution."""
    print("="*70)
    print("SMART EA BOT COMPANY — HISTORICAL BACKTEST RUNNER")
    print("="*70)
    
    # Initialize data fetcher
    fetcher = DataFetcher(paper=True)
    
    # Define parameters
    assets = ["BTCUSD", "ETHUSD"]
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=90)  # 3 months (Alpaca crypto limit)
    
    results = []
    data_quality_reports = {}
    
    for asset in assets:
        print(f"\n📊 Fetching data for {asset}...")
        bars = fetcher.fetch_bars(
            symbol=asset,
            timeframe="5Min",
            start=start_date,
            end=end_date,
            limit=10000,
        )
        
        # Validate data
        quality = validate_data_quality(bars)
        data_quality_reports[asset] = quality
        
        print(f"   Candles: {quality['candles']}")
        print(f"   Range: {quality['start']} to {quality['end']}")
        print(f"   Valid: {quality['valid']}")
        if quality['issues']:
            print(f"   Issues: {len(quality['issues'])}")
            for issue in quality['issues'][:5]:
                print(f"      - {issue}")
        
        if not quality['valid'] or quality['candles'] < 100:
            print(f"   ⚠️ Skipping {asset} due to data quality issues")
            continue
        
        # Run MRS backtest
        print(f"\n   🤖 Mean Reversion Scalper...")
        mrs_result = run_backtest_for_bot(mean_reversion_strategy, bars, asset, "Mean Reversion Scalper")
        results.append(mrs_result)
        print(f"      Trades: {mrs_result['total_trades']}, Return: {mrs_result['total_return_pct']}%, PF: {mrs_result['profit_factor']}, DD: {mrs_result['max_drawdown_pct']}%")
        
        # Run TPS backtest
        print(f"   🤖 Trend Pullback Scalper...")
        tps_result = run_backtest_for_bot(trend_pullback_strategy, bars, asset, "Trend Pullback Scalper")
        results.append(tps_result)
        print(f"      Trades: {tps_result['total_trades']}, Return: {tps_result['total_return_pct']}%, PF: {tps_result['profit_factor']}, DD: {tps_result['max_drawdown_pct']}%")
    
    # Generate reports
    print("\n" + "="*70)
    print("GENERATING REPORTS...")
    print("="*70)
    
    # Data quality report
    os.makedirs("reports/qa", exist_ok=True)
    with open("reports/qa/data_quality_report.md", "w") as f:
        f.write("# Data Quality Report\n\n")
        for asset, report in data_quality_reports.items():
            f.write(f"## {asset}\n")
            f.write(f"- Candles: {report['candles']}\n")
            f.write(f"- Valid: {report['valid']}\n")
            f.write(f"- Issues: {len(report['issues'])}\n")
            for issue in report['issues']:
                f.write(f"  - {issue}\n")
            f.write("\n")
    
    # Backtest comparison report
    os.makedirs("reports/backtests", exist_ok=True)
    with open("reports/backtests/bot_comparison_report.md", "w") as f:
        f.write("# Bot Comparison Report\n\n")
        f.write("| Bot | Asset | Trades | Return % | Win Rate | Profit Factor | Max DD % | Pass |\n")
        f.write("|-----|-------|--------|----------|----------|---------------|----------|------|\n")
        
        for r in results:
            pass_mark = "✅" if r['passes_thresholds'] else "❌"
            f.write(f"| {r['bot']} | {r['asset']} | {r['total_trades']} | {r['total_return_pct']}% | {r['win_rate']}% | {r['profit_factor']} | {r['max_drawdown_pct']}% | {pass_mark} |\n")
        
        f.write("\n## Pass Criteria\n")
        f.write("- Profit factor > 1.2\n")
        f.write("- At least 100 trades\n")
        f.write("- Max drawdown < 10%\n")
        
        # Determine best performer
        passing = [r for r in results if r['passes_thresholds']]
        if passing:
            best = max(passing, key=lambda x: x['profit_factor'])
            f.write(f"\n## Best Performer: {best['bot']} on {best['asset']}\n")
            f.write(f"Profit Factor: {best['profit_factor']}\n")
            f.write(f"Return: {best['total_return_pct']}%\n")
        else:
            f.write("\n## Result: NO BOT PASSED MINIMUM CRITERIA\n")
            f.write("All bots failed backtest thresholds. Paper trading BLOCKED.\n")
    
    print("\n✅ Reports generated:")
    print("   - reports/qa/data_quality_report.md")
    print("   - reports/backtests/bot_comparison_report.md")
    
    return results


if __name__ == "__main__":
    results = main()
    
    # Save raw results
    with open("reports/backtests/raw_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n✅ Raw results saved to reports/backtests/raw_results.json")
