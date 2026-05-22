"""
Smart EA Bot Company — Dual Momentum Bot v1
Monthly momentum: hold the best-performing asset.
Low correlation to Trend Rider v5.6.
"""

from typing import List, Dict


def dual_momentum_strategy(bars_dict: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
    """
    Dual Momentum Strategy v1.
    
    Hypothesis: Assets with strongest 12-month momentum continue outperforming.
    Rank BTC/ETH by 12-month return, hold top 1.
    
    Args:
        bars_dict: {"BTCUSD": [bars], "ETHUSD": [bars]}
    
    Returns:
        Dict of signals per asset
    """
    # Calculate 12-month (252 trading days) returns
    returns = {}
    
    for asset, bars in bars_dict.items():
        if len(bars) < 252:
            returns[asset] = 0
            continue
        
        current_price = bars[-1]["close"]
        price_252_days_ago = bars[-252]["close"] if len(bars) >= 252 else bars[0]["close"]
        ret = (current_price - price_252_days_ago) / price_252_days_ago
        returns[asset] = ret
    
    # Rank and select top
    ranked = sorted(returns.items(), key=lambda x: x[1], reverse=True)
    top_asset = ranked[0][0] if ranked else None
    
    signals = {}
    
    for asset, bars in bars_dict.items():
        signals[asset] = []
        
        for i in range(len(bars)):
            signal = {"action": "hold"}
            
            if i < 252 or i >= len(bars) - 1:
                signals[asset].append(signal)
                continue
            
            # Rebalance signal (once per month approx)
            # For simplicity, signal every 21 bars (approx 1 month)
            if i % 21 == 0:
                if asset == top_asset and returns[asset] > 0:
                    signal = {
                        "action": "buy",
                        "stop_loss": bars[i]["close"] * 0.90,
                        "take_profit": None,
                        "trailing_stop": False,
                        "max_hold_bars": 21,
                        "reason": "dual_momentum_top",
                    }
                elif asset != top_asset:
                    signal = {
                        "action": "sell",
                        "stop_loss": None,
                        "take_profit": None,
                        "max_hold_bars": 0,
                        "reason": "dual_momentum_exit",
                    }
            
            signals[asset].append(signal)
    
    return signals
