"""
Smart EA Bot Company — Mock Data Generator
Generate synthetic OHLCV bars for testing strategies and backtest engine.
"""

import random
import math
from typing import List, Dict
from datetime import datetime, timezone, timedelta


def generate_mock_bars(
    symbol: str = "BTCUSD",
    num_bars: int = 500,
    start_price: float = 75000.0,
    volatility: float = 0.002,
    trend: float = 0.0,
    seed: int = 42,
) -> List[Dict]:
    """
    Generate synthetic 5m OHLCV bars.
    
    Args:
        symbol: Asset symbol
        num_bars: Number of bars to generate
        start_price: Starting price
        volatility: Price volatility per bar (0.002 = 0.2%)
        trend: Price trend per bar (0.0001 = slight uptrend)
        seed: Random seed for reproducibility
    
    Returns:
        List of OHLCV dicts
    """
    random.seed(seed)
    bars = []
    price = start_price
    timestamp = datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc)

    for i in range(num_bars):
        # Generate bar with trend and volatility
        change = random.gauss(trend, volatility)
        
        # Add some mean reversion opportunities
        if i > 20 and i % 30 < 5:  # Every ~30 bars, create oversold condition
            change = -abs(random.gauss(0.003, volatility))
        elif i > 20 and i % 30 > 10 and i % 30 < 15:  # Overbought condition
            change = abs(random.gauss(0.003, volatility))
        
        open_price = price
        close_price = price * (1 + change)
        
        # Generate high/low from open/close
        high_price = max(open_price, close_price) * (1 + abs(random.gauss(0, volatility * 0.5)))
        low_price = min(open_price, close_price) * (1 - abs(random.gauss(0, volatility * 0.5)))
        
        volume = random.uniform(100, 1000)
        
        bars.append({
            "timestamp": timestamp.isoformat(),
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": round(volume, 2),
            "symbol": symbol,
        })
        
        price = close_price
        timestamp += timedelta(minutes=5)
    
    return bars


def generate_trending_bars(
    symbol: str = "BTCUSD",
    num_bars: int = 500,
    start_price: float = 75000.0,
    trend: float = 0.0003,  # Uptrend
    volatility: float = 0.0015,
    seed: int = 43,
) -> List[Dict]:
    """Generate bars in a clear trend for pullback strategy testing."""
    random.seed(seed)
    bars = []
    price = start_price
    timestamp = datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc)
    
    for i in range(num_bars):
        change = random.gauss(trend, volatility)
        
        open_price = price
        close_price = price * (1 + change)
        
        high_price = max(open_price, close_price) * (1 + abs(random.gauss(0, volatility * 0.3)))
        low_price = min(open_price, close_price) * (1 - abs(random.gauss(0, volatility * 0.3)))
        
        # Create pullbacks to EMA periodically
        if i > 20 and i % 25 == 0:
            # Force a pullback bar
            close_price = price * 0.998
            low_price = close_price * 0.997
            high_price = open_price * 1.001
        
        volume = random.uniform(100, 1000)
        
        bars.append({
            "timestamp": timestamp.isoformat(),
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": round(volume, 2),
            "symbol": symbol,
        })
        
        price = close_price
        timestamp += timedelta(minutes=5)
    
    return bars
