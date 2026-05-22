"""
Smart EA Bot Company — v4-A: Multi-Timeframe Momentum Bot
Hypothesis: Crypto trends on 1h timeframe; enter on 15m pullback.
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


def multi_timeframe_momentum(bars: List[Dict]) -> List[Dict]:
    """
    Multi-Timeframe Momentum Strategy (v4-A).
    
    Hypothesis: Crypto trends on 1h timeframe; enter on 15m pullback.
    
    Logic:
    1. 1h trend filter: EMA 12 > EMA 26 (uptrend) or < (downtrend)
    2. 15m entry: RSI pullback to 40-50 in uptrend, 50-60 in downtrend
    3. Volume confirmation: current > 1.2x average
    4. ATR-based trailing stop
    5. No trade if ADX proxy (EMA spread) < 1%
    """
    if len(bars) < 60:  # Need at least 60 bars for 1h alignment
        return [{"action": "hold"} for _ in bars]
    
    closes = [bar["close"] for bar in bars]
    volumes = [bar.get("volume", 1) for bar in bars]
    
    # 15m EMAs
    ema12 = calculate_ema(closes, period=12)
    ema26 = calculate_ema(closes, period=26)
    ema50 = calculate_ema(closes, period=50)
    rsi = calculate_rsi(closes, period=14)
    atr = calculate_atr(bars, period=14)
    
    # Volume average
    vol_avg = sum(volumes[:20]) / 20 if len(volumes) >= 20 else sum(volumes) / len(volumes)
    
    signals = []
    
    for i in range(len(bars)):
        signal = {"action": "hold"}
        
        if i < 50 or i >= len(bars) - 1:
            signals.append(signal)
            continue
        
        current_price = closes[i]
        current_rsi = rsi[i]
        current_atr = atr[i] if i < len(atr) else atr[-1]
        current_volume = volumes[i]
        
        # Trend filter (15m proxy for 1h)
        ema_spread = abs(ema12[i] - ema26[i]) / ema26[i] if ema26[i] > 0 else 0
        strong_trend = ema_spread > 0.01  # 1% spread
        
        if not strong_trend:
            signals.append(signal)
            continue
        
        uptrend = ema12[i] > ema26[i] and ema12[i] > ema50[i]
        downtrend = ema12[i] < ema26[i] and ema12[i] < ema50[i]
        
        # Volume filter
        volume_ok = current_volume > vol_avg * 1.2
        
        if not volume_ok:
            signals.append(signal)
            continue
        
        # Long entry: uptrend + RSI pullback
        if uptrend and 40 <= current_rsi <= 50:
            # Check previous RSI was higher (pullback)
            if i > 0 and rsi[i-1] > current_rsi:
                signal = {
                    "action": "buy",
                    "stop_loss": current_price - current_atr * 2.5,
                    "take_profit": current_price + current_atr * 4,
                    "trailing_stop": True,
                    "trailing_distance": current_atr * 2,
                    "max_hold_bars": 20,
                    "reason": "momentum_pullback_long",
                }
        
        # Short entry: downtrend + RSI pullback
        elif downtrend and 50 <= current_rsi <= 60:
            # Check previous RSI was lower (pullback in downtrend)
            if i > 0 and rsi[i-1] < current_rsi:
                signal = {
                    "action": "sell",
                    "stop_loss": current_price + current_atr * 2.5,
                    "take_profit": current_price - current_atr * 4,
                    "trailing_stop": True,
                    "trailing_distance": current_atr * 2,
                    "max_hold_bars": 20,
                    "reason": "momentum_pullback_short",
                }
        
        signals.append(signal)
    
    return signals
