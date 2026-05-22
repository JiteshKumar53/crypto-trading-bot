"""
Smart EA Bot Company — Trend Rider v5.5
200-day SMA trend following (classic trend following).
Hypothesis: Crypto has long-term trend persistence. Stay long above 200 SMA, short below.
"""

from typing import List, Dict


def calculate_sma(prices: List[float], period: int) -> List[float]:
    smas = []
    for i in range(len(prices)):
        window = prices[max(0, i - period + 1):i + 1]
        smas.append(sum(window) / len(window))
    return smas


def trend_rider_v5_5_strategy(bars: List[Dict]) -> List[Dict]:
    """
    Trend Rider v5.5 — 200-day SMA trend following.
    Classic trend following: long when price > 200 SMA, short when <.
    """
    if len(bars) < 250:
        return [{"action": "hold"} for _ in bars]
    
    closes = [bar["close"] for bar in bars]
    sma200 = calculate_sma(closes, period=200)
    
    signals = []
    
    for i in range(len(bars)):
        signal = {"action": "hold"}
        
        if i < 200 or i >= len(bars) - 1:
            signals.append(signal)
            continue
        
        current_price = closes[i]
        current_sma200 = sma200[i]
        prev_sma200 = sma200[i-1]
        
        # Cross above 200 SMA
        if current_price > current_sma200 and closes[i-1] <= prev_sma200:
            signal = {
                "action": "buy",
                "stop_loss": current_sma200 * 0.95,
                "take_profit": None,
                "trailing_stop": False,
                "max_hold_bars": 1000,  # Hold for months
                "reason": "sma200_cross_long",
            }
        
        # Cross below 200 SMA
        elif current_price < current_sma200 and closes[i-1] >= prev_sma200:
            signal = {
                "action": "sell",
                "stop_loss": current_sma200 * 1.05,
                "take_profit": None,
                "trailing_stop": False,
                "max_hold_bars": 1000,
                "reason": "sma200_cross_short",
            }
        
        signals.append(signal)
    
    return signals
