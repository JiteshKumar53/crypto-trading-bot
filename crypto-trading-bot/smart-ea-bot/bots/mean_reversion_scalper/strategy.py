"""
Smart EA Bot Company — Mean Reversion Scalper Strategy
Pure function: bars in → signals out.
No side effects. No state. Deterministic.
"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
    """Calculate RSI for a list of prices."""
    if len(prices) < period + 1:
        return [50.0] * len(prices)  # Neutral if insufficient data

    rsis = [50.0] * period  # Fill initial period with neutral

    for i in range(period, len(prices)):
        gains = []
        losses = []
        for j in range(i - period + 1, i + 1):
            change = prices[j] - prices[j - 1]
            if change > 0:
                gains.append(change)
            else:
                losses.append(abs(change))

        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 0

        if avg_loss == 0:
            rsis.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsis.append(rsi)

    return rsis


def calculate_sma(prices: List[float], period: int = 20) -> List[float]:
    """Calculate SMA for a list of prices."""
    smas = []
    for i in range(len(prices)):
        if i < period - 1:
            smas.append(sum(prices[:i + 1]) / (i + 1))  # Expanding window
        else:
            smas.append(sum(prices[i - period + 1:i + 1]) / period)
    return smas


def calculate_atr(bars: List[Dict], period: int = 14) -> List[float]:
    """Calculate ATR for a list of bars."""
    atrs = [0.0] * period
    for i in range(period, len(bars)):
        trs = []
        for j in range(i - period + 1, i + 1):
            bar = bars[j]
            high_low = bar["high"] - bar["low"]
            high_close = abs(bar["high"] - bars[j - 1]["close"])
            low_close = abs(bar["low"] - bars[j - 1]["close"])
            trs.append(max(high_low, high_close, low_close))
        atrs.append(sum(trs) / period)
    return atrs


def mean_reversion_strategy(bars: List[Dict]) -> List[Dict]:
    """
    RSI Mean Reversion Strategy.
    Returns list of signals aligned with bars.
    Signal at bar t, execution at bar t+1.
    """
    if len(bars) < 30:
        return [{"action": "hold"} for _ in bars]

    closes = [bar["close"] for bar in bars]
    highs = [bar["high"] for bar in bars]
    lows = [bar["low"] for bar in bars]

    rsi = calculate_rsi(closes, period=14)
    sma = calculate_sma(closes, period=20)
    atr = calculate_atr(bars, period=14)

    signals = []

    for i in range(len(bars)):
        signal = {"action": "hold"}

        # Need enough history
        if i < 25 or i >= len(bars) - 1:
            signals.append(signal)
            continue

        current_rsi = rsi[i]
        prev_rsi = rsi[i - 1]
        current_price = closes[i]
        current_sma = sma[i]
        current_atr = atr[i]
        atr_pct = current_atr / current_price if current_price > 0 else 0

        # Filters
        in_session = True  # TODO: add session filter
        atr_ok = atr_pct >= 0.003

        if not in_session or not atr_ok:
            signals.append(signal)
            continue

        # Long entry
        if current_rsi < 30 and current_price > current_sma and prev_rsi < 35:
            signal = {
                "action": "buy",
                "stop_loss": current_price * 0.995,
                "take_profit": current_price * 1.01,
                "max_hold_bars": 6,
                "reason": "rsi_oversold",
            }

        # Short entry
        elif current_rsi > 70 and current_price < current_sma and prev_rsi > 65:
            signal = {
                "action": "sell",
                "stop_loss": current_price * 1.005,
                "take_profit": current_price * 0.99,
                "max_hold_bars": 6,
                "reason": "rsi_overbought",
            }

        signals.append(signal)

    return signals
