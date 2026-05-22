"""
Smart EA Bot Company — Trend Rider v5.2
Simple EMA cross with trend filter.
Based on v5 learnings: pullback strategies too strict, need more signals.
"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def calculate_ema(prices: List[float], period: int) -> List[float]:
    if len(prices) < period:
        return prices[:]
    emas = [sum(prices[:period]) / period]
    multiplier = 2 / (period + 1)
    for i in range(period, len(prices)):
        ema = (prices[i] * multiplier) + (emas[-1] * (1 - multiplier))
        emas.append(ema)
    return [emas[0]] * (period - 1) + emas


def calculate_atr(bars: List[Dict], period: int = 14) -> List[float]:
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


def trend_rider_v5_2_strategy(bars: List[Dict]) -> List[Dict]:
    """
    Trend Rider v5.2 — Simple EMA Cross with Trend Filter.
    
    Hypothesis: EMA crossovers capture medium-term trends in crypto.
    Filter out weak signals by requiring EMA50 alignment.
    
    Entry:
    - LONG: EMA 12 crosses above EMA 26, and EMA 26 > EMA 50
    - SHORT: EMA 12 crosses below EMA 26, and EMA 26 < EMA 50
    
    Exit:
    - Trailing stop 3 ATR
    - Or opposite crossover
    """
    if len(bars) < 100:
        return [{"action": "hold"} for _ in bars]
    
    closes = [bar["close"] for bar in bars]
    
    ema12 = calculate_ema(closes, period=12)
    ema26 = calculate_ema(closes, period=26)
    ema50 = calculate_ema(closes, period=50)
    atr = calculate_atr(bars, period=14)
    
    signals = []
    
    for i in range(len(bars)):
        signal = {"action": "hold"}
        
        if i < 50 or i >= len(bars) - 1:
            signals.append(signal)
            continue
        
        current_price = closes[i]
        current_atr = atr[i] if i < len(atr) else atr[-1]
        
        # Previous bar for crossover detection
        prev_ema12 = ema12[i-1]
        prev_ema26 = ema26[i-1]
        curr_ema12 = ema12[i]
        curr_ema26 = ema26[i]
        curr_ema50 = ema50[i]
        
        # Crossover detection
        cross_up = prev_ema12 <= prev_ema26 and curr_ema12 > curr_ema26
        cross_down = prev_ema12 >= prev_ema26 and curr_ema12 < curr_ema26
        
        # LONG: Cross up + trend filter
        if cross_up and curr_ema26 > curr_ema50:
            signal = {
                "action": "buy",
                "stop_loss": current_price - current_atr * 3.0,
                "take_profit": None,
                "trailing_stop": True,
                "trailing_distance": current_atr * 3.0,
                "max_hold_bars": 30,  # ~5 days
                "reason": "ema_cross_long",
            }
        
        # SHORT: Cross down + trend filter
        elif cross_down and curr_ema26 < curr_ema50:
            signal = {
                "action": "sell",
                "stop_loss": current_price + current_atr * 3.0,
                "take_profit": None,
                "trailing_stop": True,
                "trailing_distance": current_atr * 3.0,
                "max_hold_bars": 30,
                "reason": "ema_cross_short",
            }
        
        signals.append(signal)
    
    return signals
