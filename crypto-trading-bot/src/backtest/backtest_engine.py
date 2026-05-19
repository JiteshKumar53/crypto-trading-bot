"""
Backtest Engine
Agent: Backtesting + Validation Team

Event-driven backtest engine for crypto strategies.
Simulates order execution with fees and slippage.
"""

import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"


@dataclass
class Order:
    symbol: str
    side: OrderSide
    qty: float
    order_type: OrderType = OrderType.MARKET
    price: Optional[float] = None  # For limit orders
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Trade:
    symbol: str
    side: OrderSide
    qty: float
    price: float
    timestamp: datetime
    commission: float = 0.0
    slippage: float = 0.0


@dataclass
class Position:
    symbol: str
    qty: float
    avg_entry_price: float
    market_value: float = 0.0
    unrealized_pnl: float = 0.0


@dataclass
class BacktestResult:
    """Container for backtest results and metrics."""
    strategy_name: str
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_equity: float
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    calmar_ratio: float
    win_rate: float
    profit_factor: float
    avg_trade: float
    num_trades: int
    exposure_time: float
    turnover: float
    worst_day: float
    worst_trade: float
    trades: List[Trade] = field(default_factory=list)
    equity_curve: pd.DataFrame = field(default_factory=pd.DataFrame)

    def summary(self) -> str:
        return f"""
Backtest Summary: {self.strategy_name} on {self.symbol}
Period: {self.start_date.date()} to {self.end_date.date()}
Initial Capital: ${self.initial_capital:,.2f}
Final Equity: ${self.final_equity:,.2f}
Total Return: {self.total_return:.2%}
Annualized Return: {self.annualized_return:.2%}
Sharpe Ratio: {self.sharpe_ratio:.2f}
Sortino Ratio: {self.sortino_ratio:.2f}
Max Drawdown: {self.max_drawdown:.2%}
Calmar Ratio: {self.calmar_ratio:.2f}
Win Rate: {self.win_rate:.1%}
Profit Factor: {self.profit_factor:.2f}
Number of Trades: {self.num_trades}
Exposure Time: {self.exposure_time:.1%}
Worst Day: {self.worst_day:.2%}
Worst Trade: {self.worst_trade:.2%}
"""


class BacktestEngine:
    """
    Event-driven backtest engine.
    Simulates trading with configurable fees and slippage.
    """

    def __init__(
        self,
        initial_capital: float = 10000.0,
        commission: float = 0.0,  # Alpaca is commission-free
        slippage: float = 0.001,  # 0.1% slippage per trade
    ):
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.cash = initial_capital
        self.equity = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.equity_history: List[Dict] = []

    def reset(self):
        """Reset engine state for a new backtest."""
        self.cash = self.initial_capital
        self.equity = self.initial_capital
        self.positions = {}
        self.trades = []
        self.equity_history = []

    def place_order(self, order: Order, current_price: float) -> Optional[Trade]:
        """
        Execute an order at current market price with slippage.
        Returns the executed Trade or None if rejected.
        """
        # Apply slippage
        if order.side == OrderSide.BUY:
            fill_price = current_price * (1 + self.slippage)
        else:
            fill_price = current_price * (1 - self.slippage)

        order_value = order.qty * fill_price
        commission = order_value * self.commission

        # Check if we have enough cash for buys
        if order.side == OrderSide.BUY:
            if order_value + commission > self.cash:
                logger.warning(
                    f"Insufficient cash for {order.side.value} {order.qty} {order.symbol}: "
                    f"need ${order_value + commission:.2f}, have ${self.cash:.2f}"
                )
                return None
            self.cash -= (order_value + commission)
        else:  # SELL
            pos = self.positions.get(order.symbol)
            if not pos or pos.qty < order.qty:
                logger.warning(
                    f"Insufficient position for {order.side.value} {order.qty} {order.symbol}: "
                    f"have {pos.qty if pos else 0}"
                )
                return None
            self.cash += (order_value - commission)

        # Update position
        pos = self.positions.get(order.symbol)
        if order.side == OrderSide.BUY:
            if pos:
                # Update average entry price
                total_cost = pos.qty * pos.avg_entry_price + order.qty * fill_price
                pos.qty += order.qty
                pos.avg_entry_price = total_cost / pos.qty
            else:
                self.positions[order.symbol] = Position(
                    symbol=order.symbol,
                    qty=order.qty,
                    avg_entry_price=fill_price,
                )
        else:  # SELL
            if pos:
                realized_pnl = (fill_price - pos.avg_entry_price) * order.qty
                pos.qty -= order.qty
                if pos.qty <= 0:
                    del self.positions[order.symbol]

        trade = Trade(
            symbol=order.symbol,
            side=order.side,
            qty=order.qty,
            price=fill_price,
            timestamp=order.timestamp,
            commission=commission,
            slippage=self.slippage,
        )
        self.trades.append(trade)
        return trade

    def update_equity(self, timestamp: datetime, prices: Dict[str, float]):
        """Update portfolio equity based on current prices."""
        position_value = 0.0
        for symbol, pos in self.positions.items():
            if symbol in prices:
                pos.market_value = pos.qty * prices[symbol]
                pos.unrealized_pnl = pos.market_value - (pos.qty * pos.avg_entry_price)
                position_value += pos.market_value

        self.equity = self.cash + position_value
        self.equity_history.append({
            "timestamp": timestamp,
            "cash": self.cash,
            "equity": self.equity,
            "position_value": position_value,
        })

    def run(
        self,
        strategy: Callable,
        data: pd.DataFrame,
        symbol: str,
    ) -> BacktestResult:
        """
        Run a backtest with the given strategy and data.

        Args:
            strategy: A callable that takes (engine, timestamp, prices, data_slice) and returns orders
            data: DataFrame with OHLCV data
            symbol: Trading symbol

        Returns:
            BacktestResult with metrics
        """
        self.reset()

        # Ensure data is sorted by time
        data = data.sort_index()

        # Detect if multi-index (Alpaca format: symbol, timestamp)
        if isinstance(data.index, pd.MultiIndex):
            # Use level 1 (timestamp) as primary
            timestamps = data.index.get_level_values(1)
        else:
            timestamps = data.index

        for i in range(len(data)):
            row = data.iloc[i]
            timestamp = timestamps[i] if hasattr(timestamps, '__getitem__') else timestamps[i]

            # Current price for this bar
            if "close" in row:
                current_price = float(row["close"])
            else:
                continue

            # Slice data up to this point (no lookahead)
            data_slice = data.iloc[:i+1]

            # Get orders from strategy
            try:
                orders = strategy(self, timestamp, {symbol: current_price}, data_slice)
                if orders:
                    for order in orders:
                        self.place_order(order, current_price)
            except Exception as e:
                logger.error(f"Strategy error at {timestamp}: {e}")

            # Update equity
            self.update_equity(timestamp, {symbol: current_price})

        # Calculate metrics
        return self._calculate_metrics(symbol, data)

    def _calculate_metrics(self, symbol: str, data: pd.DataFrame) -> BacktestResult:
        """Calculate all backtest metrics."""
        from .metrics import MetricsCalculator

        if not self.equity_history:
            # Empty backtest
            return BacktestResult(
                strategy_name="unknown",
                symbol=symbol,
                start_date=datetime.now(timezone.utc),
                end_date=datetime.now(timezone.utc),
                initial_capital=self.initial_capital,
                final_equity=self.initial_capital,
                total_return=0.0,
                annualized_return=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                max_drawdown=0.0,
                calmar_ratio=0.0,
                win_rate=0.0,
                profit_factor=0.0,
                avg_trade=0.0,
                num_trades=0,
                exposure_time=0.0,
                turnover=0.0,
                worst_day=0.0,
                worst_trade=0.0,
            )

        equity_df = pd.DataFrame(self.equity_history)
        equity_df.set_index("timestamp", inplace=True)

        # Calculate returns
        equity_df["returns"] = equity_df["equity"].pct_change().fillna(0)

        # Calculate metrics
        metrics = MetricsCalculator.calculate(equity_df, self.trades, self.initial_capital)

        # Determine strategy name from caller
        import inspect
        strategy_name = "unknown"
        # This will be set by the strategy wrapper

        if isinstance(data.index, pd.MultiIndex):
            start_date = data.index.get_level_values(1)[0]
            end_date = data.index.get_level_values(1)[-1]
        else:
            start_date = data.index[0]
            end_date = data.index[-1]

        return BacktestResult(
            strategy_name=strategy_name,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_equity=self.equity,
            **metrics,
            trades=self.trades,
            equity_curve=equity_df,
        )
