"""
Smart EA Bot Company — v4-C: Overnight Momentum Bot
Hypothesis: Crypto has overnight momentum (24h market).
Pure function: bars_in → signals_out.
"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def calculate_ema(prices: List[float], period: int) -> List[float]:
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


def overnight_momentum_strategy(bars: List[Dict]) -> List[Dict]:
    """
    Overnight Momentum Strategy (v4-C).
    
    Hypothesis: Crypto has overnight momentum (24h market).
    
    Logic:
    1. Calculate previous day's high/low (288 5m bars)
    2. Entry: Breakout above previous day's high with volume
    3. Filter: EMA alignment confirms trend
    4. Exit: Next day's close or trailing stop
    
    Note: On 5m bars, "previous day" = 288 bars ago.
    """
    if len(bars) < 600:  # Need at least 2 days + EMA warmup
        return [{"action": "hold"} for _ in bars]
    
    closes = [bar["close"] for bar in bars]
    highs = [bar["high"] for bar in bars]
    lows = [bar["low"] for bar in bars]
    volumes = [bar.get("volume", 1) for bar in bars]
    
    ema20 = calculate_ema(closes, period=20)
    ema50 = calculate_ema(closes, period=50)
    atr = calculate_atr(bars, period=14)
    
    # Daily bars per day (5m bars)
    BARS_PER_DAY = 288
    
    signals = []
    
    for i in range(len(bars)):
        signal = {"action": "hold"}
        
        if i < BARS_PER_DAY * 2 or i >= len(bars) - 1:
            signals.append(signal)
            continue
        
        current_price = closes[i]
        current_high = highs[i]
        current_low = lows[i]
        current_atr = atr[i] if i < len(atr) else atr[-1]
        current_volume = volumes[i]
        
        # Previous day's range
        prev_day_start = i - BARS_PER_DAY
        prev_day_high = max(highs[prev_day_start:i])
        prev_day_low = min(lows[prev_day_start:i])
        
        # Volume average
        vol_avg = sum(volumes[max(0, i-20):i+1]) / min(20, i+1)
        
        # Trend filter
        uptrend = ema20[i] > ema50[i] if i < len(ema20) and i < len(ema50) else False
        downtrend = ema20[i] < ema50[i] if i < len(ema20) and i < len(ema50) else False
        
        # Long: Breakout above previous day's high
        if current_high > prev_day_high * 1.005 and current_volume > vol_avg * 1.5 and uptrend:
            signal = {
                "action": "buy",
                "stop_loss": current_price - current_atr * 2,
                "take_profit": current_price + (prev_day_high - prev_day_low) * 1.5,
                "trailing_stop": True,
                "trailing_distance": current_atr * 2,
                "max_hold_bars": BARS_PER_DAY,  # Hold up to 1 day
                "reason": "overnight_momentum_long",
            }
        
        # Short: Breakdown below previous day's low
        elif current_low < prev_day_low * 0.995 and current_volume > vol_avg * 1.5 and downtrend:
            signal = {
                "action": "sell",
                "stop_loss": current_price + current_atr * 2,
                "take_profit": current_price - (prev_day_high - prev_day_low) * 1.5,
                "trailing_stop": True,
                "trailing_distance": current_atr * 2,
                "max_hold_bars": BARS_PER_DAY,
                "reason": "overnight_momentum_short",
            }
        
        signals.append(signal)
    
    return signals
