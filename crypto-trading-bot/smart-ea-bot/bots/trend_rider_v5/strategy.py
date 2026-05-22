"""
Smart EA Bot Company — Trend Rider v5
Higher-timeframe trend following (4h primary, 1d confirmation).
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


def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
    """Calculate RSI."""
    if len(prices) < period + 1:
        return [50.0] * len(prices)
    
    rsis = [50.0] * period
    for i in range(period, len(prices)):
        gains = []
        losses = []
        for j in range(i - period + 1, i + 1):
            change = prices[j] - prices[j - 1]
            if change > 0:
                gains.append(change)
            else:
                losses.append(abs(change))
        
        avg_gain = sum(gains) / period if gains else 0
        avg_loss = sum(losses) / period if losses else 0
        
        if avg_loss == 0:
            rsis.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsis.append(100 - (100 / (1 + rs)))
    
    return rsis


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


def trend_rider_v5_strategy(bars: List[Dict]) -> List[Dict]:
    """
    Trend Rider v5 — 4h Trend Following Strategy.
    
    Hypothesis: Crypto trends persist at 4h timeframe. 
    Enter on EMA pullback in established trend. Exit on trend break or trailing stop.
    
    Timeframe: 4h primary, 1d confirmation
    """
    if len(bars) < 100:
        return [{"action": "hold"} for _ in bars]
    
    closes = [bar["close"] for bar in bars]
    highs = [bar["high"] for bar in bars]
    lows = [bar["low"] for bar in bars]
    volumes = [bar.get("volume", 0) for bar in bars]
    
    ema12 = calculate_ema(closes, period=12)    # 48h EMA
    ema26 = calculate_ema(closes, period=26)    # 104h EMA
    ema50 = calculate_ema(closes, period=50)    # 200h EMA
    rsi = calculate_rsi(closes, period=14)
    atr = calculate_atr(bars, period=14)
    
    # Volume average
    vol_avg_window = 20
    vol_avgs = []
    for i in range(len(bars)):
        window = volumes[max(0, i - vol_avg_window + 1):i + 1]
        vol_avgs.append(sum(window) / len(window))
    
    signals = []
    
    for i in range(len(bars)):
        signal = {"action": "hold"}
        
        if i < 50 or i >= len(bars) - 1:
            signals.append(signal)
            continue
        
        current_price = closes[i]
        current_ema12 = ema12[i]
        current_ema26 = ema26[i]
        current_ema50 = ema50[i]
        current_rsi = rsi[i]
        current_atr = atr[i] if i < len(atr) else atr[-1]
        current_volume = volumes[i]
        current_vol_avg = vol_avgs[i]
        
        # Trend alignment (4h)
        strong_uptrend = current_ema12 > current_ema26 > current_ema50
        strong_downtrend = current_ema12 < current_ema26 < current_ema50
        
        # Trend strength (EMA spread)
        trend_strength = abs(current_ema12 - current_ema50) / current_ema50 if current_ema50 > 0 else 0
        valid_trend = trend_strength > 0.02  # At least 2% spread
        
        if not valid_trend:
            signals.append(signal)
            continue
        
        # Volume confirmation
        volume_ok = current_volume > current_vol_avg * 1.2
        
        if not volume_ok:
            signals.append(signal)
            continue
        
        # Price deviation from EMA12 in ATR units
        deviation = abs(current_price - current_ema12) / current_atr if current_atr > 0 else 0
        
        # LONG: Uptrend + pullback to EMA12 + RSI not overbought
        if strong_uptrend and current_price < current_ema12 and deviation >= 1.0:
            if 40 <= current_rsi <= 55:
                signal = {
                    "action": "buy",
                    "stop_loss": current_price - current_atr * 2.5,
                    "take_profit": None,  # Trailing stop
                    "trailing_stop": True,
                    "trailing_distance": current_atr * 3.0,
                    "max_hold_bars": 20,  # 80 hours = ~3.3 days
                    "reason": "trend_pullback_long",
                }
        
        # SHORT: Downtrend + pullback to EMA12 + RSI not oversold
        elif strong_downtrend and current_price > current_ema12 and deviation >= 1.0:
            if 45 <= current_rsi <= 60:
                signal = {
                    "action": "sell",
                    "stop_loss": current_price + current_atr * 2.5,
                    "take_profit": None,
                    "trailing_stop": True,
                    "trailing_distance": current_atr * 3.0,
                    "max_hold_bars": 20,
                    "reason": "trend_pullback_short",
                }
        
        signals.append(signal)
    
    return signals
