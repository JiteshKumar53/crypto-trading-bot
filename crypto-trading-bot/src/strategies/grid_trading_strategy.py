"""
Grid Trading Strategy
Agent: Strategy Research Team
Source: External Research (beincrypto.com, gate.com, xcryptobot.com)

Designed for sideways/ranging crypto markets.
Places buy orders below price and sell orders above within a defined grid.
Profits from price oscillation without requiring trend direction.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class Signal:
    action: str
    confidence: float
    reason: str
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class GridTradingStrategy:
    """
    Grid Trading Strategy for sideways/ranging crypto markets.
    
    Creates a grid of buy orders below current price and sell orders above.
    Each grid level is a fixed percentage apart.
    
    When price drops to a buy level: enter long position
    When price rises to a sell level: exit long position (take profit)
    
    This is NOT a breakout strategy - it profits from range-bound oscillation.
    
    Grid parameters:
    - grid_levels: Number of grid lines above and below center
    - grid_spacing_pct: Distance between grid lines (e.g., 0.01 = 1%)
    - position_size_per_grid: Fraction of equity per grid level
    """

    def __init__(
        self,
        grid_levels: int = 5,
        grid_spacing_pct: float = 0.015,  # 1.5% between grid lines
        position_size_per_grid: float = 0.05,  # 5% equity per level
        lookback_period: int = 48,  # 2 days of hourly data for range detection
    ):
        self.grid_levels = grid_levels
        self.grid_spacing_pct = grid_spacing_pct
        self.position_size_per_grid = position_size_per_grid
        self.lookback_period = lookback_period
        self.name = "Grid_Trading"
        
        # Track which grid levels have active positions
        self.active_grids: Dict[int, bool] = {}  # grid_index -> has_position

    def calculate_grid_levels(self, center_price: float) -> List[float]:
        """Calculate grid price levels around center price."""
        levels = []
        for i in range(-self.grid_levels, self.grid_levels + 1):
            level = center_price * (1 + i * self.grid_spacing_pct)
            levels.append(level)
        return levels

    def detect_range(self, df: pd.DataFrame) -> Tuple[float, float, float]:
        """
        Detect the trading range from recent data.
        Returns: (support, resistance, center_price)
        """
        if len(df) < self.lookback_period:
            return df['low'].min(), df['high'].max(), df['close'].iloc[-1]
        
        recent = df.tail(self.lookback_period)
        support = recent['low'].min()
        resistance = recent['high'].max()
        center = (support + resistance) / 2
        return support, resistance, center

    def get_nearest_grid_level(self, price: float, grid_levels: List[float]) -> int:
        """Find the nearest grid level index."""
        distances = [abs(price - level) for level in grid_levels]
        return distances.index(min(distances))

    def generate_signal(
        self, 
        df: pd.DataFrame, 
        current_position: Optional[str] = None,
        equity: float = 10000.0
    ) -> Signal:
        """
        Generate trading signal based on grid levels.
        
        Strategy:
        - When price drops near a grid buy level (below center): BUY
        - When price rises near a grid sell level (above center): SELL (take profit)
        - No stop loss - grid trading assumes range-bound behavior
        """
        if len(df) < self.lookback_period:
            return Signal("HOLD", 0.0, "Insufficient data for range detection")
        
        current_price = df['close'].iloc[-1]
        prev_price = df['close'].iloc[-2]
        
        # Detect range and calculate grid
        support, resistance, center = self.detect_range(df)
        grid_levels = self.calculate_grid_levels(center)
        
        # Find which grid level we're near
        current_level_idx = self.get_nearest_grid_level(current_price, grid_levels)
        current_level_price = grid_levels[current_level_idx]
        
        # Calculate distance to nearest grid level as percentage
        distance_to_grid = abs(current_price - current_level_price) / current_level_price
        
        # Grid trading logic:
        # If we're near a grid level below center -> BUY (price dipped)
        # If we're near a grid level above center -> SELL (price peaked)
        
        # SAFETY FIX: If already holding a position, don't buy again at same level
        # Grid trading should buy once per level, then sell at next level up
        if current_position == "long":
            # Only look for exits when long
            if current_level_idx > len(grid_levels) // 2 and distance_to_grid < 0.005:
                confidence = 1.0 - distance_to_grid * 100
                return Signal(
                    action="SELL",
                    confidence=min(1.0, confidence),
                    reason=f"Grid sell: Price near level {current_level_idx} ({current_level_price:.2f}), taking profit from dip.",
                    entry_price=current_price,
                )
            
            if current_price < support * 0.99:
                return Signal(
                    action="SELL",
                    confidence=0.9,
                    reason=f"Stop loss: Price {current_price:.2f} below support {support:.2f}. Range breakout detected.",
                    entry_price=current_price,
                )
            
            # Already long, no sell signal - HOLD
            return Signal("HOLD", 0.0, f"Holding position. Price {current_price:.2f}. Waiting for next grid level.")
        
        if current_position is None or current_position == "":
            # Looking for entry - price near a grid level below center
            if current_level_idx < len(grid_levels) // 2 and distance_to_grid < 0.005:
                confidence = 1.0 - distance_to_grid * 100
                return Signal(
                    action="BUY",
                    confidence=min(1.0, confidence),
                    reason=f"Grid buy: Price near level {current_level_idx} ({current_level_price:.2f}), {distance_to_grid:.2%} from grid. Center: {center:.2f}",
                    entry_price=current_price,
                    stop_loss=support * 0.98,
                    take_profit=center,
                )
        
        return Signal("HOLD", 0.0, f"Price {current_price:.2f} not near any grid level. Center: {center:.2f}")

    def get_parameters(self) -> Dict:
        return {
            "grid_levels": self.grid_levels,
            "grid_spacing_pct": self.grid_spacing_pct,
            "position_size_per_grid": self.position_size_per_grid,
            "lookback_period": self.lookback_period,
        }

    def get_name(self) -> str:
        return f"{self.name}::{self.grid_levels}x{self.grid_spacing_pct}"
