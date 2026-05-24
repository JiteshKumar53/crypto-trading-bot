"""
EA System — Indicator Tests
Run: python3 -m pytest bots/ea_system/test_indicators.py -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from indicators import ema, sma, rsi, get_last_crossover


def test_sma_basic():
    prices = [1, 2, 3, 4, 5]
    result = sma(prices, 3)
    assert result == [2.0, 3.0, 4.0]
    assert len(result) == len(prices) - 3 + 1


def test_sma_insufficient_data():
    prices = [1, 2]
    result = sma(prices, 3)
    assert result == []


def test_ema_basic():
    prices = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
    result = ema(prices, 10)
    assert len(result) == len(prices) - 10 + 1
    # First value is SMA seed
    assert result[0] == sum(prices[:10]) / 10


def test_ema_insufficient_data():
    prices = [1, 2, 3]
    result = ema(prices, 5)
    assert result == []


def test_rsi_basic():
    # Strong uptrend
    prices = [50] + [50 + i * 2 for i in range(20)]
    result = rsi(prices, 14)
    assert len(result) == len(prices) - 14 - 1
    # In strong uptrend, RSI should be high
    assert result[-1] > 70


def test_rsi_downtrend():
    # Strong downtrend
    prices = [50] + [50 - i * 2 for i in range(20)]
    result = rsi(prices, 14)
    assert len(result) > 0
    # In strong downtrend, RSI should be low
    assert result[-1] < 30


def test_rsi_insufficient_data():
    prices = list(range(10))
    result = rsi(prices, 14)
    assert result == []


def test_get_last_crossover_up():
    ema_fast = [1, 2, 3, 4, 6]
    ema_slow = [2, 3, 4, 5, 5]
    result = get_last_crossover(ema_fast, ema_slow)
    assert result == "CROSS_UP"


def test_get_last_crossover_down():
    ema_fast = [4, 5, 6, 6, 4]
    ema_slow = [5, 5, 5, 5, 5]
    result = get_last_crossover(ema_fast, ema_slow)
    assert result == "CROSS_DOWN"


def test_get_last_crossover_none():
    ema_fast = [1, 2, 3, 4, 5]
    ema_slow = [1, 2, 3, 4, 5]
    result = get_last_crossover(ema_fast, ema_slow)
    assert result is None


def test_get_last_crossover_insufficient():
    ema_fast = [1]
    ema_slow = [1]
    result = get_last_crossover(ema_fast, ema_slow)
    assert result is None
