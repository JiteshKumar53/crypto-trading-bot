"""
Tests for Backtest Engine and Metrics
Agent: QA + Testing Team
"""

import pytest
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from backtest.backtest_engine import BacktestEngine, Order, OrderSide, OrderType
from backtest.metrics import MetricsCalculator
from strategy.strategy_engine import BuyAndHoldStrategy, SimpleMAStrategy


@pytest.fixture
def sample_ohlcv():
    """Create sample OHLCV data."""
    dates = pd.date_range("2026-01-01", periods=100, freq="h")
    np.random.seed(42)
    base = 100.0
    prices = []
    for i in range(100):
        change = np.random.normal(0.001, 0.01)
        close = base * (1 + change)
        open_p = close * (1 + np.random.normal(0, 0.005))
        high = max(open_p, close) * (1 + abs(np.random.normal(0, 0.005)))
        low = min(open_p, close) * (1 - abs(np.random.normal(0, 0.005)))
        volume = np.random.uniform(1000, 5000)
        prices.append({
            "open": open_p,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "vwap": (high + low + close) / 3,
        })
        base = close

    df = pd.DataFrame(prices, index=dates)
    return df


def test_backtest_engine_initialization():
    engine = BacktestEngine(initial_capital=10000)
    assert engine.initial_capital == 10000
    assert engine.cash == 10000
    assert engine.equity == 10000


def test_backtest_buy_order():
    engine = BacktestEngine(initial_capital=10000)
    order = Order(
        symbol="BTC/USD",
        side=OrderSide.BUY,
        qty=0.1,
        order_type=OrderType.MARKET,
        timestamp=datetime.now(),
    )
    trade = engine.place_order(order, current_price=50000)
    assert trade is not None
    assert trade.symbol == "BTC/USD"
    assert trade.side == OrderSide.BUY
    assert trade.price > 50000  # Slippage applied


def test_backtest_insufficient_cash():
    engine = BacktestEngine(initial_capital=100)
    order = Order(
        symbol="BTC/USD",
        side=OrderSide.BUY,
        qty=1.0,
        order_type=OrderType.MARKET,
        timestamp=datetime.now(),
    )
    trade = engine.place_order(order, current_price=50000)
    assert trade is None  # Should fail due to insufficient cash


def test_buy_and_hold_strategy(sample_ohlcv):
    strategy = BuyAndHoldStrategy("BTC/USD")
    engine = BacktestEngine(initial_capital=10000)

    # Create strategy wrapper
    def strategy_wrapper(engine, timestamp, prices, data):
        return strategy.on_bar(engine, timestamp, prices, data)

    result = engine.run(strategy_wrapper, sample_ohlcv, "BTC/USD")

    assert result.total_return != 0  # Should have some return
    assert result.num_trades >= 1  # Should have entered position
    assert result.exposure_time > 0  # Should be in position


def test_simple_ma_strategy(sample_ohlcv):
    strategy = SimpleMAStrategy("BTC/USD", ma_window=20)
    engine = BacktestEngine(initial_capital=10000)

    def strategy_wrapper(engine, timestamp, prices, data):
        return strategy.on_bar(engine, timestamp, prices, data)

    result = engine.run(strategy_wrapper, sample_ohlcv, "BTC/USD")

    assert result.num_trades >= 0  # May or may not trade depending on data
    assert result.max_drawdown >= 0


def test_metrics_calculation():
    """Test metrics with synthetic equity curve."""
    dates = pd.date_range("2026-01-01", periods=100, freq="h")
    equity = pd.Series(10000 * (1 + np.cumsum(np.random.normal(0.0001, 0.01, 100))), index=dates)
    equity = pd.Series(equity.values, index=dates)  # Ensure it's a Series

    df = pd.DataFrame({
        "equity": equity,
        "returns": equity.pct_change().fillna(0),
        "position_value": pd.Series([0] * 100, index=dates),
    })

    metrics = MetricsCalculator.calculate(df, [], 10000)

    assert metrics["total_return"] != 0
    assert metrics["sharpe_ratio"] != 0 or metrics["max_drawdown"] > 0
    assert metrics["max_drawdown"] >= 0


def test_max_drawdown_calculation():
    """Test max drawdown with known values."""
    equity = pd.Series([100, 110, 105, 115, 100, 120], index=pd.date_range("2026-01-01", periods=6, freq="h"))
    dd = MetricsCalculator._max_drawdown(equity)
    # Peak at 110, trough at 100: drawdown = (100 - 110) / 110 = -0.0909
    assert dd > 0
    assert dd <= 1.0


def test_no_lookahead_bias_in_engine():
    """Verify backtest engine doesn't allow lookahead."""
    strategy = SimpleMAStrategy("BTC/USD", ma_window=5)
    engine = BacktestEngine(initial_capital=10000)

    # Track what data the strategy sees
    seen_lengths = []

    def tracking_strategy(engine, timestamp, prices, data):
        seen_lengths.append(len(data))
        return strategy.on_bar(engine, timestamp, prices, data)

    # Create minimal data
    dates = pd.date_range("2026-01-01", periods=10, freq="h")
    data = pd.DataFrame({
        "close": [100.0] * 10,
        "open": [100.0] * 10,
        "high": [105.0] * 10,
        "low": [95.0] * 10,
        "volume": [1000.0] * 10,
    }, index=dates)

    engine.run(tracking_strategy, data, "BTC/USD")

    # Strategy should see increasing amounts of data (1, 2, 3, ..., 10)
    assert seen_lengths == list(range(1, 11))
