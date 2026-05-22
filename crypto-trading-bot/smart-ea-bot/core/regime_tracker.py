"""
Smart EA Bot Company — Regime Tracker
Logs market regime at each signal for attribution analysis.
"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def calculate_sma(prices: List[float], period: int) -> List[float]:
    smas = []
    for i in range(len(prices)):
        window = prices[max(0, i - period + 1):i + 1]
        smas.append(sum(window) / len(window))
    return smas


def calculate_atr(bars: List[Dict], period: int = 14) -> List[float]:
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


def get_regime_state(bars: List[Dict]) -> Dict:
    """
    Analyze current market regime.
    Returns regime classification for attribution logging.
    """
    if len(bars) < 50:
        return {"error": "insufficient_data"}
    
    closes = [bar["close"] for bar in bars]
    current_price = closes[-1]
    
    sma50 = calculate_sma(closes, 50)[-1]
    sma_distance_pct = (current_price - sma50) / sma50 * 100 if sma50 > 0 else 0
    
    # Volatility (ATR as % of price)
    atr = calculate_atr(bars, 14)[-1]
    atr_pct = atr / current_price * 100 if current_price > 0 else 0
    
    # Trend strength (SMA slope)
    sma20 = calculate_sma(closes, 20)
    if len(sma20) >= 20:
        slope = (sma20[-1] - sma20[-10]) / sma20[-10] * 100 if sma20[-10] > 0 else 0
    else:
        slope = 0
    
    # Classify regime
    if slope > 2:
        trend = "strong_uptrend"
    elif slope > 0.5:
        trend = "uptrend"
    elif slope < -2:
        trend = "strong_downtrend"
    elif slope < -0.5:
        trend = "downtrend"
    else:
        trend = "ranging"
    
    if atr_pct > 5:
        volatility = "high"
    elif atr_pct > 2:
        volatility = "medium"
    else:
        volatility = "low"
    
    return {
        "sma50_distance_pct": round(sma_distance_pct, 4),
        "trend_strength": trend,
        "volatility_regime": volatility,
        "atr_pct": round(atr_pct, 4),
        "sma_slope_pct": round(slope, 4),
    }
