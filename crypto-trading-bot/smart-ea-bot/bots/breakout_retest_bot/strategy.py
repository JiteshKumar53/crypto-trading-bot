"""
Smart EA Bot Company — Breakout Retest Bot
Trades range breakouts with retest confirmation.
Pure function: bars in → signals out.
"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


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


def breakout_retest_strategy(bars: List[Dict]) -> List[Dict]:
    """
    Breakout Retest Strategy.
    
    Logic:
    1. Detect consolidation range (20-bar high/low)
    2. Wait for breakout above range high
    3. Wait for retest of breakout level
    4. Enter on confirmation
    5. ATR-based SL/TP
    """
    if len(bars) < 50:
        return [{"action": "hold"} for _ in bars]
    
    closes = [bar["close"] for bar in bars]
    highs = [bar["high"] for bar in bars]
    lows = [bar["low"] for bar in bars]
    volumes = [bar.get("volume", 1) for bar in bars]
    
    ema20 = calculate_ema(closes, period=20)
    ema50 = calculate_ema(closes, period=50)
    atr = calculate_atr(bars, period=14)
    
    signals = []
    breakout_high = None
    breakout_low = None
    breakout_bar = None
    
    for i in range(len(bars)):
        signal = {"action": "hold"}
        
        if i < 30:
            signals.append(signal)
            continue
        
        current_price = closes[i]
        current_high = highs[i]
        current_low = lows[i]
        current_atr = atr[i] if i < len(atr) else atr[-1]
        current_volume = volumes[i]
        avg_volume = sum(volumes[max(0, i-20):i+1]) / min(20, i+1) if i > 0 else current_volume
        
        # Calculate range
        range_high = max(highs[max(0, i-20):i+1])
        range_low = min(lows[max(0, i-20):i+1])
        range_size = range_high - range_low
        range_pct = range_size / range_high if range_high > 0 else 0
        
        # Trend filter
        uptrend = ema20[i] > ema50[i] if i < len(ema20) and i < len(ema50) else False
        downtrend = ema20[i] < ema50[i] if i < len(ema20) and i < len(ema50) else False
        
        # Detect breakout
        if breakout_high is None:
            if current_high > range_high * 1.005 and current_volume > avg_volume * 1.3:
                breakout_high = range_high
                breakout_bar = i
        
        # Detect breakdown
        if breakout_low is None:
            if current_low < range_low * 0.995 and current_volume > avg_volume * 1.3:
                breakout_low = range_low
                breakout_bar = i
        
        # Long entry on retest of breakout high
        if breakout_high and i > breakout_bar + 2:
            # Price pulled back to breakout level
            if current_low <= breakout_high * 1.002 and current_low >= breakout_high * 0.998:
                if uptrend and current_volume > avg_volume * 0.8:
                    signal = {
                        "action": "buy",
                        "stop_loss": current_price - current_atr * 2,
                        "take_profit": current_price + current_atr * 3,
                        "max_hold_bars": 12,
                        "reason": "breakout_retest_long",
                    }
                    breakout_high = None  # Reset
        
        # Short entry on retest of breakdown low
        if breakout_low and i > breakout_bar + 2:
            if current_high >= breakout_low * 0.998 and current_high <= breakout_low * 1.002:
                if downtrend and current_volume > avg_volume * 0.8:
                    signal = {
                        "action": "sell",
                        "stop_loss": current_price + current_atr * 2,
                        "take_profit": current_price - current_atr * 3,
                        "max_hold_bars": 12,
                        "reason": "breakdown_retest_short",
                    }
                    breakout_low = None  # Reset
        
        # Reset breakouts if too much time passed
        if breakout_high and i > breakout_bar + 10:
            breakout_high = None
        if breakout_low and i > breakout_bar + 10:
            breakout_low = None
        
        signals.append(signal)
    
    return signals
