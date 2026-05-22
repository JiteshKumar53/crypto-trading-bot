"""
Smart EA Bot Company — Trend Rider v5.4
Daily timeframe with faster EMAs for more signals.
Based on v5.3 which showed PF 1.54 on ETHUSD but only 11 trades.
"""

from typing import List, Dict


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


def trend_rider_v5_4_strategy(bars: List[Dict]) -> List[Dict]:
    """
    Trend Rider v5.4 — Daily EMA Cross (Faster).
    
    Changes from v5.3:
    - EMA 5/13 cross (was 9/21) — faster signals
    - EMA 30 trend filter (was 50) — more lenient
    - ATR multiplier reduced to 2.0 (was 2.5) — closer stops
    
    Goal: More trades while maintaining PF > 1.3.
    """
    if len(bars) < 50:
        return [{"action": "hold"} for _ in bars]
    
    closes = [bar["close"] for bar in bars]
    
    ema5 = calculate_ema(closes, period=5)
    ema13 = calculate_ema(closes, period=13)
    ema30 = calculate_ema(closes, period=30)
    atr = calculate_atr(bars, period=14)
    
    signals = []
    
    for i in range(len(bars)):
        signal = {"action": "hold"}
        
        if i < 30 or i >= len(bars) - 1:
            signals.append(signal)
            continue
        
        current_price = closes[i]
        current_atr = atr[i] if i < len(atr) else atr[-1]
        
        prev_ema5 = ema5[i-1]
        prev_ema13 = ema13[i-1]
        curr_ema5 = ema5[i]
        curr_ema13 = ema13[i]
        curr_ema30 = ema30[i]
        
        cross_up = prev_ema5 <= prev_ema13 and curr_ema5 > curr_ema13
        cross_down = prev_ema5 >= prev_ema13 and curr_ema5 < curr_ema13
        
        if cross_up and curr_ema13 > curr_ema30:
            signal = {
                "action": "buy",
                "stop_loss": current_price - current_atr * 2.0,
                "take_profit": None,
                "trailing_stop": True,
                "trailing_distance": current_atr * 2.0,
                "max_hold_bars": 15,
                "reason": "daily_fast_cross_long",
            }
        elif cross_down and curr_ema13 < curr_ema30:
            signal = {
                "action": "sell",
                "stop_loss": current_price + current_atr * 2.0,
                "take_profit": None,
                "trailing_stop": True,
                "trailing_distance": current_atr * 2.0,
                "max_hold_bars": 15,
                "reason": "daily_fast_cross_short",
            }
        
        signals.append(signal)
    
    return signals
