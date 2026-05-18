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


class RSIStrategy(Strategy):
    """
    Relative Strength Index (RSI) strategy.
    Buy when RSI crosses below oversold (30) from above.
    Sell when RSI crosses above overbought (70) from below.
    """

    def __init__(self, symbol: str, period: int = 14, oversold: int = 30, overbought: int = 70, allocation_pct: float = 0.95):
        super().__init__(f"rsi_{period}_{oversold}_{overbought}", symbol)
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.allocation_pct = allocation_pct
        self.in_position = False
        self.prev_rsi = None

    def _calculate_rsi(self, closes):
        if len(closes) < self.period + 1:
            return float('nan')
        delta = closes.diff()
        gain = delta.where(delta > 0, 0).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]

    def on_bar(self, engine, timestamp, prices, data):
        if len(data) < self.period + 1:
            return None
        price = prices.get(self.symbol)
        if not price or price <= 0:
            return None
        closes = data["close"]
        rsi = self._calculate_rsi(closes)
        if pd.isna(rsi):
            return None
        orders = []
        prev = self.prev_rsi if self.prev_rsi is not None else rsi
        if prev > self.oversold and rsi <= self.oversold and not self.in_position:
            cash_to_use = engine.cash * self.allocation_pct
            qty = cash_to_use / price
            if qty > 0:
                self.in_position = True
                orders.append(Order(symbol=self.symbol, side=OrderSide.BUY, qty=qty, order_type=OrderType.MARKET, timestamp=timestamp))
                logger.info(f"[{self.name}] BUY {qty:.6f} {self.symbol} at ${price:.2f} (RSI: {rsi:.1f})")
        elif prev < self.overbought and rsi >= self.overbought and self.in_position:
            pos = engine.positions.get(self.symbol)
            if pos and pos.qty > 0:
                self.in_position = False
                orders.append(Order(symbol=self.symbol, side=OrderSide.SELL, qty=pos.qty, order_type=OrderType.MARKET, timestamp=timestamp))
                logger.info(f"[{self.name}] SELL {pos.qty:.6f} {self.symbol} at ${price:.2f} (RSI: {rsi:.1f})")
        self.prev_rsi = rsi
        return orders if orders else None

    def reset(self):
        super().reset()
        self.in_position = False
        self.prev_rsi = None


class MACDStrategy(Strategy):
    """
    MACD strategy with signal line crossover.
    Buy when MACD crosses above signal line.
    Sell when MACD crosses below signal line.
    """

    def __init__(self, symbol: str, fast: int = 12, slow: int = 26, signal: int = 9, allocation_pct: float = 0.95):
        super().__init__(f"macd_{fast}_{slow}_{signal}", symbol)
        self.fast = fast
        self.slow = slow
        self.signal = signal
        self.allocation_pct = allocation_pct
        self.in_position = False
        self.prev_macd = None
        self.prev_signal = None

    def _calculate_macd(self, closes):
        if len(closes) < self.slow + self.signal:
            return float('nan'), float('nan')
        ema_fast = closes.ewm(span=self.fast, adjust=False).mean()
        ema_slow = closes.ewm(span=self.slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal, adjust=False).mean()
        return macd_line.iloc[-1], signal_line.iloc[-1]

    def on_bar(self, engine, timestamp, prices, data):
        if len(data) < self.slow + self.signal:
            return None
        price = prices.get(self.symbol)
        if not price or price <= 0:
            return None
        closes = data["close"]
        macd, signal = self._calculate_macd(closes)
        if pd.isna(macd) or pd.isna(signal):
            return None
        orders = []
        prev_macd = self.prev_macd if self.prev_macd is not None else macd
        prev_signal = self.prev_signal if self.prev_signal is not None else signal
        if prev_macd <= prev_signal and macd > signal and not self.in_position:
            cash_to_use = engine.cash * self.allocation_pct
            qty = cash_to_use / price
            if qty > 0:
                self.in_position = True
                orders.append(Order(symbol=self.symbol, side=OrderSide.BUY, qty=qty, order_type=OrderType.MARKET, timestamp=timestamp))
                logger.info(f"[{self.name}] BUY {qty:.6f} {self.symbol} at ${price:.2f} (MACD: {macd:.4f}, Signal: {signal:.4f})")
        elif prev_macd >= prev_signal and macd < signal and self.in_position:
            pos = engine.positions.get(self.symbol)
            if pos and pos.qty > 0:
                self.in_position = False
                orders.append(Order(symbol=self.symbol, side=OrderSide.SELL, qty=pos.qty, order_type=OrderType.MARKET, timestamp=timestamp))
                logger.info(f"[{self.name}] SELL {pos.qty:.6f} {self.symbol} at ${price:.2f} (MACD: {macd:.4f}, Signal: {signal:.4f})")
        self.prev_macd = macd
        self.prev_signal = signal
        return orders if orders else None

    def reset(self):
        super().reset()
        self.in_position = False
        self.prev_macd = None
        self.prev_signal = None


class BollingerBandsStrategy(Strategy):
    """
    Bollinger Bands mean-reversion strategy.
    Buy when price touches or crosses below lower band.
    Sell when price touches or crosses above upper band.
    """

    def __init__(self, symbol: str, period: int = 20, std_dev: float = 2.0, allocation_pct: float = 0.95):
        super().__init__(f"bb_{period}_{std_dev}", symbol)
        self.period = period
        self.std_dev = std_dev
        self.allocation_pct = allocation_pct
        self.in_position = False

    def _calculate_bands(self, closes):
        if len(closes) < self.period:
            return float('nan'), float('nan'), float('nan')
        ma = closes.rolling(window=self.period).mean()
        std = closes.rolling(window=self.period).std()
        middle = ma.iloc[-1]
        upper = middle + self.std_dev * std.iloc[-1]
        lower = middle - self.std_dev * std.iloc[-1]
        return middle, upper, lower

    def on_bar(self, engine, timestamp, prices, data):
        if len(data) < self.period:
            return None
        price = prices.get(self.symbol)
        if not price or price <= 0:
            return None
        closes = data["close"]
        middle, upper, lower = self._calculate_bands(closes)
        if pd.isna(middle):
            return None
        orders = []
        if price <= lower and not self.in_position:
            cash_to_use = engine.cash * self.allocation_pct
            qty = cash_to_use / price
            if qty > 0:
                self.in_position = True
                orders.append(Order(symbol=self.symbol, side=OrderSide.BUY, qty=qty, order_type=OrderType.MARKET, timestamp=timestamp))
                logger.info(f"[{self.name}] BUY {qty:.6f} {self.symbol} at ${price:.2f} (BB lower: ${lower:.2f})")
        elif price >= upper and self.in_position:
            pos = engine.positions.get(self.symbol)
            if pos and pos.qty > 0:
                self.in_position = False
                orders.append(Order(symbol=self.symbol, side=OrderSide.SELL, qty=pos.qty, order_type=OrderType.MARKET, timestamp=timestamp))
                logger.info(f"[{self.name}] SELL {pos.qty:.6f} {self.symbol} at ${price:.2f} (BB upper: ${upper:.2f})")
        return orders if orders else None

    def reset(self):
        super().reset()
        self.in_position = False
