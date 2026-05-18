"""
Strategy Engine
Agent: Strategy Engineering Team

Converts agent recommendations into testable strategy logic.
Provides base strategy class and buy-and-hold baseline.
"""

import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime
import pandas as pd

from backtest.backtest_engine import BacktestEngine, Order, OrderSide, OrderType

logger = logging.getLogger(__name__)


class Strategy:
    """
    Base strategy class.
    Strategies override the `on_bar` method to generate orders.
    """

    def __init__(self, name: str, symbol: str):
        self.name = name
        self.symbol = symbol
        self.orders: List[Order] = []
        self.position_size = 0.0  # Current position

    def on_bar(
        self,
        engine: BacktestEngine,
        timestamp: datetime,
        prices: Dict[str, float],
        data: pd.DataFrame,
    ) -> Optional[List[Order]]:
        """
        Called on each bar. Returns list of orders or None.

        Args:
            engine: BacktestEngine instance (for accessing cash, positions, etc.)
            timestamp: Current bar timestamp
            prices: Dict of symbol -> current price
            data: DataFrame with all data up to current bar (no lookahead)
        """
        return None

    def reset(self):
        """Reset strategy state."""
        self.orders = []
        self.position_size = 0.0


class BuyAndHoldStrategy(Strategy):
    """
    Baseline strategy: Buy on first bar, hold until end.
    No selling.
    """

    def __init__(self, symbol: str, allocation_pct: float = 0.95):
        super().__init__("buy_and_hold", symbol)
        self.allocation_pct = allocation_pct  # Use 95% of capital (keep some cash)
        self.has_entered = False

    def on_bar(
        self,
        engine: BacktestEngine,
        timestamp: datetime,
        prices: Dict[str, float],
        data: pd.DataFrame,
    ) -> Optional[List[Order]]:
        if self.has_entered:
            return None

        price = prices.get(self.symbol)
        if not price or price <= 0:
            return None

        # Calculate position size: use allocation_pct of cash
        cash_to_use = engine.cash * self.allocation_pct
        qty = cash_to_use / price

        if qty <= 0:
            return None

        self.has_entered = True
        self.position_size = qty

        logger.info(f"[{self.name}] BUY {qty:.6f} {self.symbol} at ${price:.2f}")

        return [Order(
            symbol=self.symbol,
            side=OrderSide.BUY,
            qty=qty,
            order_type=OrderType.MARKET,
            timestamp=timestamp,
        )]

    def reset(self):
        super().reset()
        self.has_entered = False
        self.position_size = 0.0


class SimpleMAStrategy(Strategy):
    """
    Simple Moving Average crossover strategy.
    Buy when price > MA, sell when price < MA.
    """

    def __init__(self, symbol: str, ma_window: int = 20, allocation_pct: float = 0.95):
        super().__init__(f"ma_crossover_{ma_window}", symbol)
        self.ma_window = ma_window
        self.allocation_pct = allocation_pct
        self.in_position = False

    def on_bar(
        self,
        engine: BacktestEngine,
        timestamp: datetime,
        prices: Dict[str, float],
        data: pd.DataFrame,
    ) -> Optional[List[Order]]:
        if len(data) < self.ma_window:
            return None  # Not enough data

        price = prices.get(self.symbol)
        if not price:
            return None

        # Calculate MA using only past data (no lookahead)
        closes = data["close"].values
        ma = pd.Series(closes).rolling(window=self.ma_window).mean().iloc[-1]

        if pd.isna(ma):
            return None

        orders = []

        if price > ma and not self.in_position:
            # Buy signal
            cash_to_use = engine.cash * self.allocation_pct
            qty = cash_to_use / price
            if qty > 0:
                self.in_position = True
                orders.append(Order(
                    symbol=self.symbol,
                    side=OrderSide.BUY,
                    qty=qty,
                    order_type=OrderType.MARKET,
                    timestamp=timestamp,
                ))
                logger.info(f"[{self.name}] BUY {qty:.6f} {self.symbol} at ${price:.2f} (MA: {ma:.2f})")

        elif price < ma and self.in_position:
            # Sell signal
            pos = engine.positions.get(self.symbol)
            if pos and pos.qty > 0:
                self.in_position = False
                orders.append(Order(
                    symbol=self.symbol,
                    side=OrderSide.SELL,
                    qty=pos.qty,
                    order_type=OrderType.MARKET,
                    timestamp=timestamp,
                ))
                logger.info(f"[{self.name}] SELL {pos.qty:.6f} {self.symbol} at ${price:.2f} (MA: {ma:.2f})")

        return orders if orders else None

    def reset(self):
        super().reset()
        self.in_position = False
