"""
Smart EA Bot Company — Volatility Squeeze Bot
Trades Bollinger Band squeezes + ATR compression breakout.
Pure function: bars in → signals out.
"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def calculate_bollinger(prices: List[float], period: int = 20, std_dev: float = 2.0) -> tuple:
    """Calculate Bollinger Bands. Returns (upper, middle, lower, bandwidth)."""
    upper = []
    middle = []
    lower = []
    bandwidth = []
    
    for i in range(len(prices)):
        if i < period - 1:
            window = prices[:i+1]
        else:
            window = prices[i-period+1:i+1]
        
        mean = sum(window) / len(window)
        variance = sum((p - mean) ** 2 for p in window) / len(window)
        std = variance ** 0.5
        
        middle.append(mean)
        upper.append(mean + std_dev * std)
        lower.append(mean - std_dev * std)
        bandwidth.append((std_dev * std * 2) / mean if mean > 0 else 0)
    
    return upper, middle, lower, bandwidth


def calculate_ema(prices: List[float], period: int = 20) -> List[float]:
    """Calculate EMA."""
    if len(prices) < period:
        return prices[:]
    emas = [sum(prices[:period]) / period]
    multiplier = 2 / (period + 1)
    for i in range(period, len(prices)):
        ema = (prices[i] * multiplier) + (emas[-1] * (1 - multiplier))
        emas.append(ema)
    return [emas[0]] * (period - 1) + emas


def calculate_atr(bars: List[Dict], period: int = 14) -> List[float]:
    """Calculate ATR."""
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


def volatility_squeeze_strategy(bars: List[Dict]) -> List[Dict]:
    """
    Volatility Squeeze Strategy.
    
    Logic:
    1. Detect Bollinger Band squeeze (narrow bands)
    2. Wait for ATR compression
    3. Trade breakout from squeeze
    4. Volume confirmation required
    5. ATR-based SL/TP
    """
    if len(bars) < 50:
        return [{"action": "hold"} for _ in bars]
    
    closes = [bar["close"] for bar in bars]
    volumes = [bar.get("volume", 1) for bar in bars]
    
    bb_upper, bb_middle, bb_lower, bb_bandwidth = calculate_bollinger(closes, period=20)
    ema20 = calculate_ema(closes, period=20)
    ema50 = calculate_ema(closes, period=50)
    atr = calculate_atr(bars, period=14)
    
    signals = []
    squeeze_active = False
    squeeze_bar = None
    squeeze_direction = None
    
    for i in range(len(bars)):
        signal = {"action": "hold"}
        
        if i < 30:
            signals.append(signal)
            continue
        
        current_price = closes[i]
        current_atr = atr[i] if i < len(atr) else atr[-1]
        current_volume = volumes[i]
        avg_volume = sum(volumes[max(0, i-20):i+1]) / min(20, i+1) if i > 0 else current_volume
        
        bb_width = bb_bandwidth[i] if i < len(bb_bandwidth) else 0.02
        avg_bb_width = sum(bb_bandwidth[max(0, i-20):i+1]) / min(20, i+1)
        
        # Trend filter
        uptrend = ema20[i] > ema50[i] if i < len(ema20) and i < len(ema50) else False
        downtrend = ema20[i] < ema50[i] if i < len(ema20) and i < len(ema50) else False
        
        # Detect squeeze
        if bb_width < avg_bb_width * 0.6 and not squeeze_active:
            squeeze_active = True
            squeeze_bar = i
            squeeze_direction = None
        
        # Detect breakout from squeeze
        if squeeze_active and i > squeeze_bar + 3:
            # Long breakout
            if current_price > bb_upper[i] and current_volume > avg_volume * 1.5 and uptrend:
                if squeeze_direction is None or squeeze_direction == "long":
                    signal = {
                        "action": "buy",
                        "stop_loss": current_price - current_atr * 1.5,
                        "take_profit": current_price + current_atr * 4,
                        "max_hold_bars": 16,
                        "reason": "squeeze_breakout_long",
                    }
                    squeeze_active = False
                    squeeze_direction = "long"
            
            # Short breakout
            elif current_price < bb_lower[i] and current_volume > avg_volume * 1.5 and downtrend:
                if squeeze_direction is None or squeeze_direction == "short":
                    signal = {
                        "action": "sell",
                        "stop_loss": current_price + current_atr * 1.5,
                        "take_profit": current_price - current_atr * 4,
                        "max_hold_bars": 16,
                        "reason": "squeeze_breakout_short",
                    }
                    squeeze_active = False
                    squeeze_direction = "short"
            
            # Reset squeeze if no breakout after 15 bars
            if i > squeeze_bar + 15:
                squeeze_active = False
                squeeze_direction = None
        
        signals.append(signal)
    
    return signals
