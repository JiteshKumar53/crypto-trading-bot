"""
Smart EA Bot Company — Mean Reversion Scalper v2
RSI + Bollinger Bands — Range-Only Mean Reversion
Pure function: bars in → signals out.
"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
    """Calculate RSI for a list of prices."""
    if len(prices) < period + 1:
        return [50.0] * len(prices)
    rsis = [50.0] * period
    for i in range(period, len(prices)):
        gains = [max(0, prices[j] - prices[j - 1]) for j in range(i - period + 1, i + 1)]
        losses = [abs(min(0, prices[j] - prices[j - 1])) for j in range(i - period + 1, i + 1)]
        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 0
        rsis.append(100 - (100 / (1 + avg_gain / avg_loss)) if avg_loss else 100)
    return rsis


def calculate_bollinger_bands(prices: List[float], period: int = 20, num_std: float = 2.0) -> tuple:
    """Calculate Bollinger Bands. Returns (upper, middle, lower)."""
    upper = []
    middle = []
    lower = []
    for i in range(len(prices)):
        if i < period - 1:
            window = prices[:i + 1]
        else:
            window = prices[i - period + 1:i + 1]
        sma = sum(window) / len(window)
        variance = sum((p - sma) ** 2 for p in window) / len(window)
        std = variance ** 0.5
        upper.append(sma + std * num_std)
        middle.append(sma)
        lower.append(sma - std * num_std)
    return upper, middle, lower


def calculate_atr(bars: List[Dict], period: int = 14) -> List[float]:
    """Calculate ATR for a list of bars."""
    atrs = [0.0] * period
    for i in range(period, len(bars)):
        trs = []
        for j in range(i - period + 1, i + 1):
            bar = bars[j]
            tr = max(
                bar["high"] - bar["low"],
                abs(bar["high"] - bars[j - 1]["close"]),
                abs(bar["low"] - bars[j - 1]["close"])
            )
            trs.append(tr)
        atrs.append(sum(trs) / period)
    return atrs


def calculate_adx(bars: List[Dict], period: int = 14) -> List[float]:
    """Calculate ADX. Returns values 0-100."""
    n = len(bars)
    if n < period * 3:
        return [20.0] * n

    plus_dm = [0.0] * n
    minus_dm = [0.0] * n
    tr_values = [0.0] * n

    for i in range(1, n):
        high = bars[i]["high"]
        low = bars[i]["low"]
        prev_high = bars[i - 1]["high"]
        prev_low = bars[i - 1]["low"]
        prev_close = bars[i - 1]["close"]

        up_move = high - prev_high
        down_move = prev_low - low

        plus_dm[i] = up_move if up_move > down_move and up_move > 0 else 0.0
        minus_dm[i] = down_move if down_move > up_move and down_move > 0 else 0.0
        tr_values[i] = max(high - low, abs(high - prev_close), abs(low - prev_close))

    # Wilder's smoothing
    tr_smooth = [0.0] * n
    plus_smooth = [0.0] * n
    minus_smooth = [0.0] * n

    tr_smooth[period] = sum(tr_values[1:period + 1])
    plus_smooth[period] = sum(plus_dm[1:period + 1])
    minus_smooth[period] = sum(minus_dm[1:period + 1])

    for i in range(period + 1, n):
        tr_smooth[i] = tr_smooth[i - 1] - tr_smooth[i - 1] / period + tr_values[i]
        plus_smooth[i] = plus_smooth[i - 1] - plus_smooth[i - 1] / period + plus_dm[i]
        minus_smooth[i] = minus_smooth[i - 1] - minus_smooth[i - 1] / period + minus_dm[i]

    # DX
    dx = [0.0] * n
    for i in range(period, n):
        if tr_smooth[i] == 0:
            dx[i] = 0.0
        else:
            plus_di = 100.0 * plus_smooth[i] / tr_smooth[i]
            minus_di = 100.0 * minus_smooth[i] / tr_smooth[i]
            dx[i] = 100.0 * abs(plus_di - minus_di) / (plus_di + minus_di) if (plus_di + minus_di) > 0 else 0.0

    # ADX
    adx = [20.0] * n
    adx[period * 2] = sum(dx[period + 1:period * 2 + 1]) / period

    for i in range(period * 2 + 1, n):
        adx[i] = (adx[i - 1] * (period - 1) + dx[i]) / period

    return adx


def calculate_rolling_vwap(bars: List[Dict], window: int = 288) -> List[float]:
    """Calculate rolling VWAP (288 bars = 1 day for 5-min candles)."""
    vwaps = []
    for i in range(len(bars)):
        start = max(0, i - window + 1)
        cumulative_tp_vol = 0.0
        cumulative_vol = 0.0
        for j in range(start, i + 1):
            tp = (bars[j]["high"] + bars[j]["low"] + bars[j]["close"]) / 3
            vol = bars[j].get("volume", 1.0)
            cumulative_tp_vol += tp * vol
            cumulative_vol += vol
        vwaps.append(cumulative_tp_vol / cumulative_vol if cumulative_vol > 0 else bars[i]["close"])
    return vwaps


def mean_reversion_v2_strategy(bars: List[Dict]) -> List[Dict]:
    """
    Mean Reversion Scalper v2 — Range-Only Strategy.
    Uses RSI + BB + rolling VWAP with ADX regime filter.
    """
    if len(bars) < 55:
        return [{"action": "hold"} for _ in bars]

    closes = [bar["close"] for bar in bars]
    rsi = calculate_rsi(closes, 14)
    bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(closes, 20, 2.0)
    atr = calculate_atr(bars, 14)
    adx = calculate_adx(bars, 14)
    vwap = calculate_rolling_vwap(bars, 288)

    signals = []

    for i in range(len(bars)):
        signal = {"action": "hold"}

        if i < 55 or i >= len(bars) - 1:
            signals.append(signal)
            continue

        current_price = closes[i]
        current_rsi = rsi[i]
        prev_rsi = rsi[i - 1]
        current_atr = atr[i]
        current_adx = adx[i]
        current_vwap = vwap[i]

        # Regime: not strongly trending (ADX < 30 is acceptable for mean reversion)
        is_ranging = current_adx < 30

        # ATR check — avoid dead markets
        atr_pct = current_atr / current_price if current_price > 0 else 0
        atr_ok = atr_pct >= 0.002

        if not is_ranging or not atr_ok:
            signals.append(signal)
            continue

        # VWAP distance check — price must be near VWAP (not in a strong trend away from mean)
        vwap_dist = abs(current_price - current_vwap) / current_vwap if current_vwap > 0 else 0
        vwap_ok = vwap_dist < 0.02  # Within 2% of rolling VWAP

        if not vwap_ok:
            signals.append(signal)
            continue

        # Long entry: deeply oversold, below lower BB, near VWAP
        if (current_rsi < 25 and
            current_price < bb_lower[i] and
            prev_rsi < 30 and
            current_price > current_vwap * 0.985):
            signal = {
                "action": "buy",
                "stop_loss": current_price * 0.997,
                "take_profit": current_price * 1.006,
                "max_hold_bars": 4,
                "reason": "mrs_v2_oversold",
            }

        # Short entry: deeply overbought, above upper BB, near VWAP
        elif (current_rsi > 75 and
              current_price > bb_upper[i] and
              prev_rsi > 70 and
              current_price < current_vwap * 1.015):
            signal = {
                "action": "sell",
                "stop_loss": current_price * 1.003,
                "take_profit": current_price * 0.994,
                "max_hold_bars": 4,
                "reason": "mrs_v2_overbought",
            }

        signals.append(signal)

    return signals
