"""
Smart EA Bot Company — Weekly Ratio Bot v1
ETH/BTC ratio trend following on weekly timeframe.
Low correlation to Trend Rider v5.6.
"""

from typing import List, Dict


def calculate_sma(prices: List[float], period: int) -> List[float]:
    smas = []
    for i in range(len(prices)):
        window = prices[max(0, i - period + 1):i + 1]
        smas.append(sum(window) / len(window))
    return smas


def weekly_ratio_strategy(bars: List[Dict]) -> List[Dict]:
    """
    Weekly Ratio Strategy v1.
    
    Hypothesis: When ETH outperforms BTC (ratio rising), stay long ETH/short BTC.
    When ETH underperforms (ratio falling), reverse.
    
    Entry: Weekly close above/below 20-week SMA of ETH/BTC ratio.
    """
    if len(bars) < 25:
        return [{"action": "hold"} for _ in bars]
    
    ratios = [bar["close"] for bar in bars]
    sma20 = calculate_sma(ratios, 20)
    
    signals = []
    
    for i in range(len(bars)):
        signal = {"action": "hold"}
        
        if i < 20 or i >= len(bars) - 1:
            signals.append(signal)
            continue
        
        current_ratio = ratios[i]
        prev_ratio = ratios[i-1]
        current_sma = sma20[i]
        prev_sma = sma20[i-1]
        
        # Ratio cross above 20-week SMA
        if current_ratio > current_sma and prev_ratio <= prev_sma:
            signal = {
                "action": "buy",  # Long ETH/BTC ratio
                "stop_loss": current_sma * 0.95,
                "take_profit": None,
                "trailing_stop": False,
                "max_hold_bars": 52,  # Hold for up to 1 year
                "reason": "ratio_cross_long",
            }
        
        # Ratio cross below 20-week SMA
        elif current_ratio < current_sma and prev_ratio >= prev_sma:
            signal = {
                "action": "sell",  # Short ETH/BTC ratio (equivalent to long BTC/short ETH)
                "stop_loss": current_sma * 1.05,
                "take_profit": None,
                "trailing_stop": False,
                "max_hold_bars": 52,
                "reason": "ratio_cross_short",
            }
        
        signals.append(signal)
    
    return signals
