"""
QA tests for Trend Rider v5.6
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.yahoo_data_fetcher import fetch_yahoo_bars
from core.backtest_engine import BacktestEngine
from bots.trend_rider_v5_6.strategy import trend_rider_v5_6_strategy

print("QA TESTS — Trend Rider v5.6")
print("=" * 60)

# Test 1: Deterministic replay
print("\n[Test 1] Deterministic replay...")
bars = fetch_yahoo_bars("ETHUSD", interval="1d", period="1y")
engine1 = BacktestEngine(10000.0)
result1 = engine1.run(trend_rider_v5_6_strategy, bars, "ETHUSD", fee_pct=0.10, slippage_pct=0.05)

engine2 = BacktestEngine(10000.0)
result2 = engine2.run(trend_rider_v5_6_strategy, bars, "ETHUSD", fee_pct=0.10, slippage_pct=0.05)

if (result1.total_return_pct == result2.total_return_pct and 
    result1.total_trades == result2.total_trades and
    result1.profit_factor == result2.profit_factor):
    print("  ✅ PASS — Results are identical on replay")
else:
    print("  ❌ FAIL — Results differ on replay")
    print(f"    Run 1: {result1.total_trades} trades, {result1.total_return_pct}% return")
    print(f"    Run 2: {result2.total_trades} trades, {result2.total_return_pct}% return")

# Test 2: No lookahead bias
print("\n[Test 2] No lookahead bias check...")
# If strategy uses future data, it would show PF > 10 with few trades
if result1.profit_factor < 20:  # Reasonable PF means no obvious lookahead
    print(f"  ✅ PASS — PF {result1.profit_factor} is reasonable (no obvious lookahead)")
else:
    print(f"  ⚠️ WARNING — PF {result1.profit_factor} suspiciously high")

# Test 3: Fee impact realism
print("\n[Test 3] Fee impact...")
engine_nofees = BacktestEngine(10000.0)
result_nofees = engine_nofees.run(trend_rider_v5_6_strategy, bars, "ETHUSD", fee_pct=0.0, slippage_pct=0.0)

fee_impact = result_nofees.total_return_pct - result1.total_return_pct
print(f"  Without fees: {result_nofees.total_return_pct:.2f}%")
print(f"  With fees: {result1.total_return_pct:.2f}%")
print(f"  Fee drag: {fee_impact:.2f}%")
if fee_impact < 2.0:  # Less than 2% drag
    print("  ✅ PASS — Fee drag is reasonable")
else:
    print("  ⚠️ WARNING — High fee drag")

# Test 4: Risk Governor
print("\n[Test 4] Risk Governor check...")
from core.risk_governor import RiskGovernor
governor = RiskGovernor()
result = governor.check_order("BTCUSD", "buy", 0.5, 70000, 10000, {})
if result["allowed"]:
    print(f"  ❌ FAIL — Risk Governor approved oversized order")
else:
    print(f"  ✅ PASS — Risk Governor blocked order: {result['reason']}")

print("\n" + "=" * 60)
print("QA TESTS COMPLETE")
print("=" * 60)
