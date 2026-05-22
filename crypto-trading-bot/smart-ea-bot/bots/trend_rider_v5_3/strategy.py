"""
Smart EA Bot Company — Trend Rider v5.3
Daily timeframe EMA cross — bigger moves, fees matter less.
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


def trend_rider_v5_3_strategy(bars: List[Dict]) -> List[Dict]:
    """
    Trend Rider v5.3 — Daily EMA Cross.
    
    Hypothesis: Daily EMA crosses capture crypto's multi-day trends.
    Bigger moves mean fees are smaller % of target.
    
    Entry: EMA 9 crosses EMA 21 on daily
    Filter: EMA 21 > EMA 50 (long) or < (short)
    Exit: Trailing stop 2.5 ATR or opposite cross
    """
    if len(bars) < 100:
        return [{"action": "hold"} for _ in bars]
    
    closes = [bar["close"] for bar in bars]
    
    ema9 = calculate_ema(closes, period=9)
    ema21 = calculate_ema(closes, period=21)
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
        
        prev_ema9 = ema9[i-1]
        prev_ema21 = ema21[i-1]
        curr_ema9 = ema9[i]
        curr_ema21 = ema21[i]
        curr_ema50 = ema50[i]
        
        cross_up = prev_ema9 <= prev_ema21 and curr_ema9 > curr_ema21
        cross_down = prev_ema9 >= prev_ema21 and curr_ema9 < curr_ema21
        
        # LONG
        if cross_up and curr_ema21 > curr_ema50:
            signal = {
                "action": "buy",
                "stop_loss": current_price - current_atr * 2.5,
                "take_profit": None,
                "trailing_stop": True,
                "trailing_distance": current_atr * 2.5,
                "max_hold_bars": 20,  # ~20 days
                "reason": "daily_ema_cross_long",
            }
        
        # SHORT
        elif cross_down and curr_ema21 < curr_ema50:
            signal = {
                "action": "sell",
                "stop_loss": current_price + current_atr * 2.5,
                "take_profit": None,
                "trailing_stop": True,
                "trailing_distance": current_atr * 2.5,
                "max_hold_bars": 20,
                "reason": "daily_ema_cross_short",
            }
        
        signals.append(signal)
    
    return signals
