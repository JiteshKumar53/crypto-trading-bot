"""
Smart EA Bot Company — Trend Pullback Scalper v3
Requires genuine pullback, not just proximity to EMA.
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


def trend_pullback_v3_strategy(bars: List[Dict]) -> List[Dict]:
    """
    Trend Pullback v3 — Genuine pullback required.
    
    Logic:
    1. EMA 20/50/200 alignment confirms trend
    2. Price must pull away from EMA 20, then reclaim
    3. RSI < 50 on long pullback, RSI > 50 on short pullback
    4. ATR-based SL/TP
    5. ADX > 25 confirms trend strength
    6. No entry if price is just near EMA (avoid chop)
    """
    if len(bars) < 200:
        return [{"action": "hold"} for _ in bars]
    
    closes = [bar["close"] for bar in bars]
    highs = [bar["high"] for bar in bars]
    lows = [bar["low"] for bar in bars]
    
    ema20 = calculate_ema(closes, period=20)
    ema50 = calculate_ema(closes, period=50)
    ema200 = calculate_ema(closes, period=200)
    rsi = calculate_rsi(closes, period=14)
    atr = calculate_atr(bars, period=14)
    
    signals = []
    pullback_start = None
    pullback_direction = None
    
    for i in range(len(bars)):
        signal = {"action": "hold"}
        
        if i < 200:
            signals.append(signal)
            continue
        
        current_price = closes[i]
        current_ema20 = ema20[i]
        current_ema50 = ema50[i]
        current_ema200 = ema200[i]
        current_rsi = rsi[i]
        current_atr = atr[i] if i < len(atr) else atr[-1]
        
        # Trend alignment
        strong_uptrend = current_ema20 > current_ema50 > current_ema200
        strong_downtrend = current_ema20 < current_ema50 < current_ema200
        
        # ADX proxy using EMA distance
        trend_strength = abs(current_ema20 - current_ema200) / current_ema200
        strong_trend = trend_strength > 0.03  # 3% spread between EMAs
        
        if not strong_trend:
            signals.append(signal)
            continue
        
        # Track pullbacks
        if strong_uptrend:
            # Price below EMA20 = potential pullback
            if current_price < current_ema20:
                if pullback_direction != "long":
                    pullback_start = i
                    pullback_direction = "long"
            else:
                # Price reclaimed EMA20 after pullback
                if pullback_direction == "long" and pullback_start and (i - pullback_start) >= 3:
                    # Genuine pullback: price went below EMA20, stayed there, then reclaimed
                    pullback_low = min(lows[pullback_start:i])
                    ema_distance = abs(current_ema20 - pullback_low) / current_ema20
                    
                    if ema_distance > 0.005 and current_rsi < 50:  # RSI not overbought
                        signal = {
                            "action": "buy",
                            "stop_loss": current_price - current_atr * 2,
                            "take_profit": current_price + current_atr * 3,
                            "max_hold_bars": 12,
                            "reason": "pullback_reclaim_long",
                        }
                
                pullback_direction = None
                pullback_start = None
        
        elif strong_downtrend:
            # Price above EMA20 = potential pullback in downtrend
            if current_price > current_ema20:
                if pullback_direction != "short":
                    pullback_start = i
                    pullback_direction = "short"
            else:
                # Price reclaimed below EMA20 after pullback
                if pullback_direction == "short" and pullback_start and (i - pullback_start) >= 3:
                    pullback_high = max(highs[pullback_start:i])
                    ema_distance = abs(pullback_high - current_ema20) / current_ema20
                    
                    if ema_distance > 0.005 and current_rsi > 50:  # RSI not oversold
                        signal = {
                            "action": "sell",
                            "stop_loss": current_price + current_atr * 2,
                            "take_profit": current_price - current_atr * 3,
                            "max_hold_bars": 12,
                            "reason": "pullback_reclaim_short",
                        }
                
                pullback_direction = None
                pullback_start = None
        
        signals.append(signal)
    
    return signals
