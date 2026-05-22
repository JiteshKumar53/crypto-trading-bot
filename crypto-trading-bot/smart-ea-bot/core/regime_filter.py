"""
Smart EA Bot Company — Market Regime Filter
Determines if market is suitable for trading.
No agent execution. Pure function. Deterministic.
"""

from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


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


def calculate_adx(bars: List[Dict], period: int = 14) -> List[float]:
    """Calculate ADX (Average Directional Index)."""
    if len(bars) < period * 2:
        return [25.0] * len(bars)  # Neutral
    
    # Calculate +DM and -DM
    plus_dm = [0.0]
    minus_dm = [0.0]
    
    for i in range(1, len(bars)):
        up_move = bars[i]["high"] - bars[i-1]["high"]
        down_move = bars[i-1]["low"] - bars[i]["low"]
        
        if up_move > down_move and up_move > 0:
            plus_dm.append(up_move)
        else:
            plus_dm.append(0.0)
        
        if down_move > up_move and down_move > 0:
            minus_dm.append(down_move)
        else:
            minus_dm.append(0.0)
    
    # Calculate ATR first
    atr = calculate_atr(bars, period)
    
    # Calculate +DI and -DI
    plus_di = []
    minus_di = []
    
    for i in range(period, len(bars)):
        atr_val = atr[i] if i < len(atr) else atr[-1]
        if atr_val > 0:
            plus_di_val = 100 * (sum(plus_dm[max(0, i-period+1):i+1]) / period) / atr_val
            minus_di_val = 100 * (sum(minus_dm[max(0, i-period+1):i+1]) / period) / atr_val
        else:
            plus_di_val = 0
            minus_di_val = 0
        
        plus_di.append(plus_di_val)
        minus_di.append(minus_di_val)
    
    # Calculate DX and ADX
    dx_values = []
    for i in range(len(plus_di)):
        di_sum = plus_di[i] + minus_di[i]
        di_diff = abs(plus_di[i] - minus_di[i])
        if di_sum > 0:
            dx_values.append(100 * di_diff / di_sum)
        else:
            dx_values.append(0.0)
    
    # Smooth DX with SMA for ADX
    adx = []
    for i in range(len(dx_values)):
        window = dx_values[max(0, i - period + 1):i + 1]
        adx.append(sum(window) / len(window))
    
    # Pad beginning
    return [25.0] * (period * 2) + adx


def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> tuple:
    """Calculate Bollinger Bands. Returns (upper, middle, lower, bandwidth)."""
    sma = []
    upper = []
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
        
        sma.append(mean)
        upper.append(mean + std_dev * std)
        lower.append(mean - std_dev * std)
        bandwidth.append((std_dev * std * 2) / mean if mean > 0 else 0)
    
    return upper, sma, lower, bandwidth


def regime_filter(bars: List[Dict]) -> List[Dict]:
    """
    Market Regime Filter.
    Returns list of regime states aligned with bars.
    
    Regimes:
    - trending_up: Clear uptrend, TPS suitable
    - trending_down: Clear downtrend, TPS short suitable
    - ranging: Sideways, MRS suitable
    - choppy: No direction, AVOID ALL BOTS
    - high_volatility: High ATR, use wider SL/TP
    - no_trade: Low volume/liquidity, AVOID
    """
    if len(bars) < 50:
        return [{"regime": "no_trade", "reason": "insufficient_data"} for _ in bars]
    
    closes = [bar["close"] for bar in bars]
    
    ema20 = calculate_ema(closes, period=20)
    ema50 = calculate_ema(closes, period=50)
    atr = calculate_atr(bars, period=14)
    adx = calculate_adx(bars, period=14)
    bb_upper, bb_middle, bb_lower, bb_bandwidth = calculate_bollinger_bands(closes, period=20)
    
    regimes = []
    
    for i in range(len(bars)):
        if i < 50:
            regimes.append({"regime": "no_trade", "reason": "warming_up"})
            continue
        
        regime = "no_trade"
        reasons = []
        
        # Trend detection
        uptrend = ema20[i] > ema50[i] and ema20[i] > ema20[i-5] if i >= 5 else False
        downtrend = ema20[i] < ema50[i] and ema20[i] < ema20[i-5] if i >= 5 else False
        
        # ADX strength
        adx_val = adx[i] if i < len(adx) else 25
        strong_trend = adx_val > 25
        weak_trend = adx_val < 20
        
        # Volatility
        atr_pct = (atr[i] / closes[i] * 100) if i < len(atr) and closes[i] > 0 else 0
        high_vol = atr_pct > 0.8
        low_vol = atr_pct < 0.2
        
        # Bollinger Band width
        bb_width = bb_bandwidth[i] if i < len(bb_bandwidth) else 0.02
        squeeze = bb_width < 0.015  # Tight bands = potential breakout
        expansion = bb_width > 0.04  # Wide bands = high volatility
        
        # Classification
        if low_vol:
            regime = "no_trade"
            reasons.append("low_volatility")
        elif squeeze and strong_trend:
            regime = "trending_up" if uptrend else "trending_down"
            reasons.append("breakout_squeeze")
        elif strong_trend and uptrend:
            regime = "trending_up"
            reasons.append("strong_uptrend")
        elif strong_trend and downtrend:
            regime = "trending_down"
            reasons.append("strong_downtrend")
        elif weak_trend and bb_width < 0.03:
            regime = "ranging"
            reasons.append("sideways_low_vol")
        elif high_vol and not strong_trend:
            regime = "choppy"
            reasons.append("high_vol_no_trend")
        elif expansion:
            regime = "high_volatility"
            reasons.append("bb_expansion")
        else:
            regime = "ranging"
            reasons.append("default_range")
        
        regimes.append({
            "regime": regime,
            "reasons": reasons,
            "adx": round(adx_val, 2),
            "atr_pct": round(atr_pct, 4),
            "bb_width": round(bb_width, 4),
            "uptrend": uptrend,
            "downtrend": downtrend,
        })
    
    return regimes


def is_tradeable(regime_state: Dict) -> bool:
    """Check if current regime allows trading."""
    return regime_state["regime"] in [
        "trending_up",
        "trending_down",
        "ranging",
        "high_volatility",
    ]


def get_recommended_bots(regime_state: Dict) -> List[str]:
    """Get list of bots suitable for current regime."""
    regime = regime_state["regime"]
    
    bot_map = {
        "trending_up": ["trend_pullback_scalper"],
        "trending_down": ["trend_pullback_scalper"],
        "ranging": ["mean_reversion_scalper"],
        "high_volatility": ["breakout_retest_scalper", "volatility_breakout"],
        "choppy": [],
        "no_trade": [],
    }
    
    return bot_map.get(regime, [])
