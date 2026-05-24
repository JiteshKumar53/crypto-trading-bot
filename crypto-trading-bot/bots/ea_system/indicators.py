"""
EA System — Technical Indicators
Minimal, fast, no dependencies beyond stdlib.
"""

from typing import List, Optional, Tuple


def bollinger_bands(prices: List[float], period: int = 20, std: float = 2.0) -> Tuple[List[float], List[float], List[float]]:
    """Calculate Bollinger Bands (upper, middle, lower).
    Returns: (upper_band, sma, lower_band)
    """
    if len(prices) < period:
        return [], [], []

    sma_vals = sma(prices, period)
    if not sma_vals:
        return [], [], []

    upper = []
    lower = []
    for i in range(len(sma_vals)):
        window = prices[i:i + period]
        std_dev = (sum((x - sma_vals[i]) ** 2 for x in window) / period) ** 0.5
        upper.append(sma_vals[i] + std * std_dev)
        lower.append(sma_vals[i] - std * std_dev)

    return upper, sma_vals, lower


def vwap(highs: List[float], lows: List[float], closes: List[float], volumes: List[float], window: int = 24) -> List[float]:
    """Calculate Volume Weighted Average Price over a rolling window.
    Default window: 24 bars = 6 hours of 15m data.
    Returns rolling VWAP up to each bar.
    """
    if len(closes) == 0 or len(volumes) == 0:
        return []

    typical_prices = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]
    vwaps = []
    for i in range(len(typical_prices)):
        start = max(0, i - window + 1)
        tp_window = typical_prices[start:i+1]
        vol_window = volumes[start:i+1]
        cum_pv = sum(tp * vol for tp, vol in zip(tp_window, vol_window))
        cum_vol = sum(vol_window)
        if cum_vol == 0:
            vwaps.append(typical_prices[i])
        else:
            vwaps.append(cum_pv / cum_vol)
    return vwaps


def sma(prices: List[float], period: int) -> List[float]:
    """Calculate Simple Moving Average."""
    if len(prices) < period:
        return []
    return [sum(prices[i:i+period]) / period for i in range(len(prices) - period + 1)]


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
