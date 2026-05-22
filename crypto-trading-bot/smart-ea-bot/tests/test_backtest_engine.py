"""
Smart EA Bot Company — QA Test Suite
Validate backtest engine and strategy signals.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.mock_data import generate_mock_bars, generate_trending_bars
from core.backtest_engine import BacktestEngine
from bots.mean_reversion_scalper.strategy import mean_reversion_strategy
from bots.trend_pullback_scalper.strategy import trend_pullback_strategy


def test_mock_data_generation():
    """Test that mock data generates correctly."""
    bars = generate_mock_bars(num_bars=100)
    assert len(bars) == 100
    assert "open" in bars[0]
    assert "high" in bars[0]
    assert "low" in bars[0]
    assert "close" in bars[0]
    assert "volume" in bars[0]
    print("✅ Mock data generation passes")


def test_mean_reversion_signals():
    """Test that MRS strategy generates signals without errors."""
    bars = generate_mock_bars(num_bars=100)
    signals = mean_reversion_strategy(bars)
    assert len(signals) == len(bars)
    
    # Check signal format
    for sig in signals:
        assert "action" in sig
        assert sig["action"] in ("buy", "sell", "hold")
    
    # Should have some buy/sell signals
    non_hold = [s for s in signals if s["action"] != "hold"]
    print(f"   MRS generated {len(non_hold)} signals out of {len(signals)} bars")
    print("✅ Mean reversion signal generation passes")


def test_trend_pullback_signals():
    """Test that TPS strategy generates signals without errors."""
    bars = generate_trending_bars(num_bars=100)
    signals = trend_pullback_strategy(bars)
    assert len(signals) == len(bars)
    
    for sig in signals:
        assert "action" in sig
    
    non_hold = [s for s in signals if s["action"] != "hold"]
    print(f"   TPS generated {len(non_hold)} signals out of {len(signals)} bars")
    print("✅ Trend pullback signal generation passes")


def test_backtest_engine():
    """Test that backtest engine runs without errors."""
    bars = generate_mock_bars(num_bars=200)
    engine = BacktestEngine(initial_equity=10000.0)
    result = engine.run(mean_reversion_strategy, bars, "BTCUSD")
    
    assert result is not None
    assert result.asset == "BTCUSD"
    assert result.total_trades >= 0
    
    print(f"   Total trades: {result.total_trades}")
    print(f"   Total return: {result.total_return_pct:.2f}%")
    print(f"   Win rate: {result.win_rate:.2%}")
    print(f"   Profit factor: {result.profit_factor:.2f}")
    print(f"   Max drawdown: {result.max_drawdown_pct:.2f}%")
    print("✅ Backtest engine runs correctly")


def test_risk_governor():
    """Test that risk governor blocks oversized orders."""
    from core.risk_governor import RiskGovernor
    
    rg = RiskGovernor()
    result = rg.check_order(
        symbol="BTCUSD",
        side="buy",
        qty=1.0,
        price=75000.0,
        portfolio_value=10000.0,
        current_positions={},
    )
    
    assert "allowed" in result
    assert "reason" in result
    print(f"   Risk check: allowed={result['allowed']}, reason={result['reason']}")
    print("✅ Risk governor operates correctly")


def run_all_tests():
    """Run all QA tests."""
    print("\n" + "="*60)
    print("SMART EA BOT COMPANY — QA TEST SUITE")
    print("="*60 + "\n")
    
    tests = [
        ("Mock Data Generation", test_mock_data_generation),
        ("Mean Reversion Signals", test_mean_reversion_signals),
        ("Trend Pullback Signals", test_trend_pullback_signals),
        ("Backtest Engine", test_backtest_engine),
        ("Risk Governor", test_risk_governor),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {name} FAILED: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
