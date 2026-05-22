"""
Smart EA Bot Company — v4-B: VWAP Reversion Bot (Longer TF)
Hypothesis: Price reverts to VWAP on 15m timeframe after deviation.
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


def vwap_reversion_strategy(bars: List[Dict]) -> List[Dict]:
    """
    VWAP Reversion Strategy (v4-B).
    
    Hypothesis: Price reverts to VWAP on 15m timeframe after deviation.
    
    Logic:
    1. Calculate VWAP
    2. Measure price deviation from VWAP in ATR units
    3. Only trade when deviation > 1.5 ATR
    4. Filter: ADX proxy < 25 (no strong trend)
    5. Entry: Return toward VWAP
    6. Exit: VWAP touch or ATR stop
    """
    if len(bars) < 50:
        return [{"action": "hold"} for _ in bars]
    
    closes = [bar["close"] for bar in bars]
    
    vwap = calculate_vwap(bars)
    ema20 = calculate_ema(closes, period=20)
    ema50 = calculate_ema(closes, period=50)
    atr = calculate_atr(bars, period=14)
    
    signals = []
    
    for i in range(len(bars)):
        signal = {"action": "hold"}
        
        if i < 30 or i >= len(bars) - 1:
            signals.append(signal)
            continue
        
        current_price = closes[i]
        current_vwap = vwap[i]
        current_atr = atr[i] if i < len(atr) else atr[-1]
        
        # Trend filter: no strong trend
        ema_spread = abs(ema20[i] - ema50[i]) / ema50[i] if ema50[i] > 0 else 0
        ranging = ema_spread < 0.02  # Less than 2% spread
        
        if not ranging:
            signals.append(signal)
            continue
        
        # Deviation from VWAP in ATR units
        deviation = abs(current_price - current_vwap) / current_atr if current_atr > 0 else 0
        
        if deviation < 1.5:
            signals.append(signal)
            continue
        
        # Long: price below VWAP, deviation large, reverting up
        if current_price < current_vwap and deviation >= 1.5:
            # Check if price is starting to revert (current close > previous close)
            if i > 0 and closes[i] > closes[i-1]:
                signal = {
                    "action": "buy",
                    "stop_loss": current_price - current_atr * 1.5,
                    "take_profit": current_vwap,
                    "max_hold_bars": 10,
                    "reason": "vwap_reversion_long",
                }
        
        # Short: price above VWAP, deviation large, reverting down
        elif current_price > current_vwap and deviation >= 1.5:
            if i > 0 and closes[i] < closes[i-1]:
                signal = {
                    "action": "sell",
                    "stop_loss": current_price + current_atr * 1.5,
                    "take_profit": current_vwap,
                    "max_hold_bars": 10,
                    "reason": "vwap_reversion_short",
                }
        
        signals.append(signal)
    
    return signals
