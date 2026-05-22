"""
Smart EA Bot Company — Trend Pullback Scalper Strategy
Pure function: bars in → signals out.
"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def calculate_ema(prices: List[float], period: int = 20) -> List[float]:
    """Calculate EMA for a list of prices."""
    if len(prices) < period:
        return prices[:]
    
    emas = [sum(prices[:period]) / period]
    multiplier = 2 / (period + 1)
    
    for i in range(period, len(prices)):
        ema = (prices[i] * multiplier) + (emas[-1] * (1 - multiplier))
        emas.append(ema)
    
    # Pad beginning
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


def calculate_vwap(bars: List[Dict]) -> List[float]:
    """Calculate VWAP (Volume Weighted Average Price)."""
    vwaps = []
    cumulative_tp_vol = 0
    cumulative_vol = 0
    
    for bar in bars:
        tp = (bar["high"] + bar["low"] + bar["close"]) / 3
        vol = bar.get("volume", 1)
        cumulative_tp_vol += tp * vol
        cumulative_vol += vol
        
        if cumulative_vol > 0:
            vwaps.append(cumulative_tp_vol / cumulative_vol)
        else:
            vwaps.append(bar["close"])
    
    return vwaps


def trend_pullback_strategy(bars: List[Dict]) -> List[Dict]:
    """
    EMA Trend Pullback Strategy.
    Buy pullbacks to EMA in uptrend.
    """
    if len(bars) < 50:
        return [{"action": "hold"} for _ in bars]
    
    closes = [bar["close"] for bar in bars]
    
    ema20 = calculate_ema(closes, period=20)
    ema50 = calculate_ema(closes, period=50)
    rsi = calculate_rsi(closes, period=14)
    vwap = calculate_vwap(bars)
    
    signals = []
    
    for i in range(len(bars)):
        signal = {"action": "hold"}
        
        if i < 50 or i >= len(bars) - 1:
            signals.append(signal)
            continue
        
        current_price = closes[i]
        current_ema20 = ema20[i]
        current_ema50 = ema50[i]
        current_rsi = rsi[i]
        current_vwap = vwap[i]
        
        # Trend filter
        uptrend = current_ema20 > current_ema50 and current_price > current_ema20
        downtrend = current_ema20 < current_ema50 and current_price < current_ema20
        
        # Pullback to EMA
        pullback_buy = current_price <= current_ema20 * 1.002 and current_price >= current_ema20 * 0.998
        pullback_sell = current_price >= current_ema20 * 0.998 and current_price <= current_ema20 * 1.002
        
        # Long entry
        if uptrend and pullback_buy and current_rsi > 40 and current_rsi < 60:
            signal = {
                "action": "buy",
                "stop_loss": current_ema50 * 0.99,
                "take_profit": current_price * 1.015,
                "max_hold_bars": 12,
                "reason": "ema_pullback",
            }
        
        # Short entry
        elif downtrend and pullback_sell and current_rsi < 60 and current_rsi > 40:
            signal = {
                "action": "sell",
                "stop_loss": current_ema50 * 1.01,
                "take_profit": current_price * 0.985,
                "max_hold_bars": 12,
                "reason": "ema_pullback_short",
            }
        
        signals.append(signal)
    
    return signals
