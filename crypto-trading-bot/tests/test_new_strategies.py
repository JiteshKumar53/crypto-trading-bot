import sys
sys.path.insert(0, 'src')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backtest.backtest_engine import BacktestEngine
from strategy.strategy_engine import RSIStrategy, MACDStrategy, BollingerBandsStrategy


def create_test_data(n_bars=50, trend='up'):
    """Create synthetic test data for strategies."""
    dates = [datetime(2026, 1, 1) + timedelta(hours=i) for i in range(n_bars)]
    
    if trend == 'up':
        closes = np.linspace(100, 200, n_bars) + np.random.randn(n_bars) * 5
    elif trend == 'down':
        closes = np.linspace(200, 100, n_bars) + np.random.randn(n_bars) * 5
    else:  # sideways
        closes = 150 + np.random.randn(n_bars) * 10
    
    # Ensure no negative prices
    closes = np.maximum(closes, 1.0)
    
    highs = closes + np.random.rand(n_bars) * 5
    lows = closes - np.random.rand(n_bars) * 5
    opens = closes + np.random.randn(n_bars) * 2
    volumes = np.random.rand(n_bars) * 1000
    
    return pd.DataFrame({
        'timestamp': dates,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes,
    })


class TestRSIStrategy:
    def test_rsi_strategy_initialization(self):
        strat = RSIStrategy('BTC/USD')
        assert strat.name == 'rsi_14_30_70'
        assert strat.period == 14
        assert strat.oversold == 30
        assert strat.overbought == 70
        assert not strat.in_position

    def test_rsi_strategy_needs_data(self):
        strat = RSIStrategy('BTC/USD')
        engine = BacktestEngine(initial_capital=10000)
        data = create_test_data(n_bars=10)
        result = strat.on_bar(engine, data['timestamp'].iloc[-1], {'BTC/USD': 150}, data)
        assert result is None  # Not enough data for RSI

    def test_rsi_strategy_runs_on_sufficient_data(self):
        strat = RSIStrategy('BTC/USD')
        engine = BacktestEngine(initial_capital=10000)
        data = create_test_data(n_bars=50)
        
        # Run on a bar to get some action
        result = strat.on_bar(engine, data['timestamp'].iloc[-1], {'BTC/USD': 150}, data)
        # RSI might or might not generate a signal on first bar
        assert result is None or len(result) <= 1

    def test_rsi_strategy_buy_signal(self):
        """Create data where RSI drops below 30 to trigger buy."""
        strat = RSIStrategy('BTC/USD', period=5, oversold=30, overbought=70)
        engine = BacktestEngine(initial_capital=10000)
        
        # Create data with a sharp drop then flat (to get RSI low)
        dates = [datetime(2026, 1, 1) + timedelta(hours=i) for i in range(20)]
        closes = [100] * 10 + [90, 85, 80, 75, 70, 65, 60, 55, 50, 45]  # Sharp drop
        data = pd.DataFrame({
            'timestamp': dates,
            'open': closes,
            'high': [c + 1 for c in closes],
            'low': [c - 1 for c in closes],
            'close': closes,
            'volume': [100] * 20,
        })
        
        # First bar - may not trigger
        result = strat.on_bar(engine, dates[-2], {'BTC/USD': 50}, data.iloc[:-1])
        
        # Force RSI to be very low on next bar
        strat.prev_rsi = 35  # Was above oversold
        result = strat.on_bar(engine, dates[-1], {'BTC/USD': 45}, data)
        assert result is not None
        assert len(result) == 1
        assert result[0].side.value == 'buy'

    def test_rsi_strategy_reset(self):
        strat = RSIStrategy('BTC/USD')
        strat.in_position = True
        strat.prev_rsi = 50
        strat.reset()
        assert not strat.in_position
        assert strat.prev_rsi is None


class TestMACDStrategy:
    def test_macd_strategy_initialization(self):
        strat = MACDStrategy('BTC/USD')
        assert strat.name == 'macd_12_26_9'
        assert strat.fast == 12
        assert strat.slow == 26
        assert strat.signal == 9

    def test_macd_strategy_needs_data(self):
        strat = MACDStrategy('BTC/USD')
        engine = BacktestEngine(initial_capital=10000)
        data = create_test_data(n_bars=30)
        result = strat.on_bar(engine, data['timestamp'].iloc[-1], {'BTC/USD': 150}, data)
        assert result is None  # Not enough data (needs 26+9=35)

    def test_macd_strategy_runs_on_sufficient_data(self):
        strat = MACDStrategy('BTC/USD')
        engine = BacktestEngine(initial_capital=10000)
        data = create_test_data(n_bars=50)
        result = strat.on_bar(engine, data['timestamp'].iloc[-1], {'BTC/USD': 150}, data)
        assert result is None or len(result) <= 1

    def test_macd_strategy_reset(self):
        strat = MACDStrategy('BTC/USD')
        strat.in_position = True
        strat.prev_macd = 1.0
        strat.prev_signal = 0.5
        strat.reset()
        assert not strat.in_position
        assert strat.prev_macd is None
        assert strat.prev_signal is None


class TestBollingerBandsStrategy:
    def test_bb_strategy_initialization(self):
        strat = BollingerBandsStrategy('BTC/USD')
        assert strat.name == 'bb_20_2.0'
        assert strat.period == 20
        assert strat.std_dev == 2.0

    def test_bb_strategy_needs_data(self):
        strat = BollingerBandsStrategy('BTC/USD')
        engine = BacktestEngine(initial_capital=10000)
        data = create_test_data(n_bars=15)
        result = strat.on_bar(engine, data['timestamp'].iloc[-1], {'BTC/USD': 150}, data)
        assert result is None  # Not enough data for 20-period BB

    def test_bb_strategy_buy_signal(self):
        """Create data where price drops below lower band."""
        strat = BollingerBandsStrategy('BTC/USD', period=5, std_dev=2.0)
        engine = BacktestEngine(initial_capital=10000)
        
        dates = [datetime(2026, 1, 1) + timedelta(hours=i) for i in range(15)]
        # Flat then volatile last 5 bars, then extreme price
        closes = [100]*10 + [10, 20, 10, 20, 10]
        data = pd.DataFrame({
            'timestamp': dates,
            'open': closes,
            'high': [c + 5 for c in closes],
            'low': [c - 5 for c in closes],
            'close': closes,
            'volume': [100] * 15,
        })
        
        # Mean=14, std≈5.48, lower=14-10.96=3.04, so 1 <= 3.04
        result = strat.on_bar(engine, dates[-1], {'BTC/USD': 1}, data)
        assert result is not None
        assert len(result) == 1
        assert result[0].side.value == 'buy'

    def test_bb_strategy_sell_signal(self):
        """Create data where price rises above upper band."""
        strat = BollingerBandsStrategy('BTC/USD', period=5, std_dev=2.0)
        engine = BacktestEngine(initial_capital=10000)
        engine.positions['BTC/USD'] = type('Pos', (), {'qty': 0.1})()
        strat.in_position = True
        
        dates = [datetime(2026, 1, 1) + timedelta(hours=i) for i in range(15)]
        closes = [100]*10 + [10, 20, 10, 20, 10]
        data = pd.DataFrame({
            'timestamp': dates,
            'open': closes,
            'high': [c + 5 for c in closes],
            'low': [c - 5 for c in closes],
            'close': closes,
            'volume': [100] * 15,
        })
        
        # Mean=14, std≈5.48, upper=14+10.96=24.96, so 30 >= 24.96
        result = strat.on_bar(engine, dates[-1], {'BTC/USD': 30}, data)
        assert result is not None
        assert len(result) == 1
        assert result[0].side.value == 'sell'

    def test_bb_strategy_reset(self):
        strat = BollingerBandsStrategy('BTC/USD')
        strat.in_position = True
        strat.reset()
        assert not strat.in_position
