"""
EA System — Strategy Signal Tests
Run: python3 -m pytest bots/ea_system/test_strategy_signals.py -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from strategy_ema_rsi import EmaRsiStrategy
from strategy_bollinger import BollingerStrategy


def make_bars(closes):
    """Helper: create minimal bar dicts from close prices."""
    return [{'close': c, 'open': c, 'high': c, 'low': c, 'volume': 1} for c in closes]


def test_ema_rsi_entry_no_crossover():
    """Flat prices — no signal expected."""
    closes = [100] * 30
    bars = make_bars(closes)
    strategy = EmaRsiStrategy()
    signal = strategy.check_entry(bars)
    assert signal is None



def test_ema_rsi_entry_crossover_low_rsi():
    """Crossover happens but RSI too low — no signal."""
    # Downtrend then tiny bounce (crossover but RSI still low)
    closes = [150] * 22
    closes += [150, 145, 140, 138, 136, 135, 134, 133, 132, 131]
    bars = make_bars(closes)
    strategy = EmaRsiStrategy()
    signal = strategy.check_entry(bars)
    assert signal is None


def test_ema_rsi_exit_stop_loss():
    """Price drops 2% below entry — stop loss fires."""
    closes = [100] * 30
    bars = make_bars(closes)
    strategy = EmaRsiStrategy()
    exit_signal = strategy.check_exit(bars, entry_price=102.1, current_price=100)
    assert exit_signal is not None
    assert exit_signal['reason'] == 'stop_loss_2pct'


def test_ema_rsi_exit_take_profit():
    """Price rises 3% above entry — take profit fires."""
    closes = [100] * 30
    bars = make_bars(closes)
    strategy = EmaRsiStrategy()
    exit_signal = strategy.check_exit(bars, entry_price=96.15, current_price=100)
    assert exit_signal is not None
    assert exit_signal['reason'] == 'take_profit_3pct'


def test_bollinger_entry_lower_band():
    """Price at lower band, RSI oversold — signal."""
    # Flat around 100 then sharp drop
    closes = [100] * 25
    closes += [100, 98, 96, 94, 92, 90, 88, 86, 84, 82]
    bars = make_bars(closes)
    strategy = BollingerStrategy()
    signal = strategy.check_entry(bars)
    assert signal is not None
    assert signal['signal'] == 'LONG'
    assert signal['reason'] == 'bb_lower_touch_rsi_oversold'


def test_bollinger_entry_no_touch():
    """Price above lower band — no signal."""
    closes = [100] * 30
    bars = make_bars(closes)
    strategy = BollingerStrategy()
    signal = strategy.check_entry(bars)
    assert signal is None


def test_bollinger_exit_middle_band():
    """Price reaches middle band — exit signal fires (could also be take profit)."""
    # Flat at 100, drop to 80, then rise back
    closes = [100] * 20 + [80] * 5 + [90, 95, 100, 105, 110]
    bars = make_bars(closes)
    strategy = BollingerStrategy()
    exit_signal = strategy.check_exit(bars, entry_price=80, current_price=105)
    assert exit_signal is not None
    # Middle band reached AND 2% TP both fire — either is valid
    assert exit_signal['reason'] in ('bb_middle_band_reached', 'bb_take_profit_2pct')
