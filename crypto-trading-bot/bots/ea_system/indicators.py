"""
EA System — Technical Indicators
Minimal, fast, no dependencies beyond stdlib.
"""

from typing import List, Optional


def ema(prices: List[float], period: int) -> List[float]:
    """Calculate Exponential Moving Average."""
    if len(prices) < period:
        return []
    
    multiplier = 2.0 / (period + 1)
    ema_values = [sum(prices[:period]) / period]  # SMA seed
    
    for price in prices[period:]:
        ema_values.append((price - ema_values[-1]) * multiplier + ema_values[-1])
    
    return ema_values


def rsi(prices: List[float], period: int = 14) -> List[float]:
    """Calculate Relative Strength Index."""
    if len(prices) < period + 1:
        return []
    
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        gains.append(max(change, 0))
        losses.append(abs(min(change, 0)))
    
    rsi_values = []
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        if avg_loss == 0:
            rsi_values.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(100.0 - (100.0 / (1 + rs)))
    
    return rsi_values


def get_last_crossover(ema_fast: List[float], ema_slow: List[float]) -> Optional[str]:
    """Check for EMA crossover on latest bar."""
    if len(ema_fast) < 2 or len(ema_slow) < 2:
        return None
    
    prev_fast = ema_fast[-2]
    prev_slow = ema_slow[-2]
    curr_fast = ema_fast[-1]
    curr_slow = ema_slow[-1]
    
    if prev_fast <= prev_slow and curr_fast > curr_slow:
        return "CROSS_UP"
    elif prev_fast >= prev_slow and curr_fast < curr_slow:
        return "CROSS_DOWN"
    
    return None
