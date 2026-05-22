"""
Smart EA Bot Company — Mean Reversion Scalper v3
RSI Divergence + VWAP distance strategy.
Pure function: bars in → signals out.
"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


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


def calculate_vwap(bars: List[Dict]) -> List[float]:
    """Calculate VWAP."""
    vwaps = []
    cumulative_tp_vol = 0
    cumulative_vol = 0
    
    for bar in bars:
        tp = (bar["high"] + bar["low"] + bar["close"]) / 3
        vol = bar.get("volume", 1)
        cumulative_tp_vol += tp * vol
        cumulative_vol += vol
        vwaps.append(cumulative_tp_vol / cumulative_vol if cumulative_vol > 0 else bar["close"])
    
    return vwaps


def mean_reversion_v3_strategy(bars: List[Dict]) -> List[Dict]:
    """
    Mean Reversion v3 — RSI Divergence + VWAP Distance.
    
    Logic:
    1. Find RSI bullish divergence (price lower, RSI higher)
    2. Find RSI bearish divergence (price higher, RSI lower)
    3. Only trade when price is far from VWAP
    4. Only trade in ranging regime (price between EMAs)
    5. ATR-based SL/TP
    """
    if len(bars) < 50:
        return [{"action": "hold"} for _ in bars]
    
    closes = [bar["close"] for bar in bars]
    lows = [bar["low"] for bar in bars]
    highs = [bar["high"] for bar in bars]
    
    rsi = calculate_rsi(closes, period=14)
    ema20 = calculate_ema(closes, period=20)
    ema50 = calculate_ema(closes, period=50)
    vwap = calculate_vwap(bars)
    
    signals = []
    
    for i in range(len(bars)):
        signal = {"action": "hold"}
        
        if i < 30 or i >= len(bars) - 1:
            signals.append(signal)
            continue
        
        current_price = closes[i]
        current_rsi = rsi[i]
        current_ema20 = ema20[i]
        current_ema50 = ema50[i]
        current_vwap = vwap[i]
        
        # Regime: ranging = price between EMAs
        ranging = (current_ema20 > current_ema50 and current_price < current_ema20 and current_price > current_ema50) or \
                  (current_ema20 < current_ema50 and current_price > current_ema20 and current_price < current_ema50)
        
        if not ranging:
            signals.append(signal)
            continue
        
        # VWAP distance
        vwap_distance = abs(current_price - current_vwap) / current_vwap if current_vwap > 0 else 0
        far_from_vwap = vwap_distance > 0.005  # More than 0.5% from VWAP
        
        if not far_from_vwap:
            signals.append(signal)
            continue
        
        # Bullish divergence: price makes lower low, RSI makes higher low
        if i >= 10:
            recent_lows = lows[i-10:i+1]
            recent_rsi = rsi[i-10:i+1]
            
            # Find local lows
            price_low_idx = recent_lows.index(min(recent_lows))
            rsi_low_idx = recent_rsi.index(min(recent_rsi))
            
            # Divergence: price lower but RSI higher
            if price_low_idx > rsi_low_idx and current_price < current_vwap:
                signal = {
                    "action": "buy",
                    "stop_loss": current_price * 0.994,
                    "take_profit": current_vwap * 1.002,
                    "max_hold_bars": 8,
                    "reason": "rsi_divergence_long",
                }
            
            # Bearish divergence: price higher but RSI lower
            price_high_idx = recent_lows.index(max(recent_lows))
            rsi_high_idx = recent_rsi.index(max(recent_rsi))
            
            if price_high_idx > rsi_high_idx and current_price > current_vwap:
                signal = {
                    "action": "sell",
                    "stop_loss": current_price * 1.006,
                    "take_profit": current_vwap * 0.998,
                    "max_hold_bars": 8,
                    "reason": "rsi_divergence_short",
                }
        
        signals.append(signal)
    
    return signals
