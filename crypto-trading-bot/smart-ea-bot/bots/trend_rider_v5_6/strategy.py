"""
Smart EA Bot Company — Trend Rider v5.6
50-day SMA trend following (faster than 200 SMA).
"""

from typing import List, Dict


def calculate_sma(prices: List[float], period: int) -> List[float]:
    smas = []
    for i in range(len(prices)):
        window = prices[max(0, i - period + 1):i + 1]
        smas.append(sum(window) / len(window))
    return smas


def trend_rider_v5_6_strategy(bars: List[Dict]) -> List[Dict]:
    """50-day SMA trend following."""
    if len(bars) < 100:
        return [{"action": "hold"} for _ in bars]
    
    closes = [bar["close"] for bar in bars]
    sma50 = calculate_sma(closes, period=50)
    
    signals = []
    
    for i in range(len(bars)):
        signal = {"action": "hold"}
        
        if i < 50 or i >= len(bars) - 1:
            signals.append(signal)
            continue
        
        current_price = closes[i]
        current_sma50 = sma50[i]
        prev_sma50 = sma50[i-1]
        
        if current_price > current_sma50 and closes[i-1] <= prev_sma50:
            signal = {
                "action": "buy",
                "stop_loss": current_sma50 * 0.95,
                "take_profit": None,
                "trailing_stop": False,
                "max_hold_bars": 100,
                "reason": "sma50_cross_long",
            }
        elif current_price < current_sma50 and closes[i-1] >= prev_sma50:
            signal = {
                "action": "sell",
                "stop_loss": current_sma50 * 1.05,
                "take_profit": None,
                "trailing_stop": False,
                "max_hold_bars": 100,
                "reason": "sma50_cross_short",
            }
        
        signals.append(signal)
    
    return signals
