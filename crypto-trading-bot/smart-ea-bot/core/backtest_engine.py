"""
Smart EA Bot Company — Backtest Engine
Vectorized backtesting for strategy validation.
No lookahead bias. Fees and slippage included.
"""

import logging
from typing import List, Dict, Callable, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Result of a backtest run."""
    strategy: str
    asset: str
    total_return_pct: float
    win_rate: float
    profit_factor: float
    max_drawdown_pct: float
    sharpe_ratio: float
    total_trades: int
    avg_win_pct: float
    avg_loss_pct: float
    worst_streak: int
    fees_pct: float
    net_profit_pct: float
    passes_thresholds: bool
    trades: List[Dict]  # Full trade list for analysis


class BacktestEngine:
    """
    Simple vectorized backtest engine.
    
    Usage:
        engine = BacktestEngine()
        result = engine.run(strategy_func, bars, "BTCUSD")
    """

    def __init__(self, initial_equity: float = 10000.0):
        self.initial_equity = initial_equity
        self.equity = initial_equity
        self.trades = []
        self.equity_curve = []

    def run(
        self,
        strategy: Callable,
        bars: List[Dict],
        asset: str,
        fee_pct: float = 0.10,
        slippage_pct: float = 0.05,
    ) -> BacktestResult:
        """
        Run backtest for a strategy on historical bars.
        
        Args:
            strategy: Pure function that takes bars and returns signals
            bars: List of OHLCV dicts
            asset: Symbol string
            fee_pct: Fee per trade side (0.1% = 0.10)
            slippage_pct: Slippage per trade (0.05% = 0.05)
        
        Returns:
            BacktestResult with full metrics
        """
        self.equity = self.initial_equity
        self.trades = []
        self.equity_curve = []

        # Generate signals (no lookahead — signal at bar t, execute at bar t+1)
        signals = strategy(bars)  # Returns list of signals aligned with bars

        position = None  # None or dict with entry info

        for i in range(len(bars) - 1):  # Last bar has no next bar to execute
            bar = bars[i]
            next_bar = bars[i + 1]
            signal = signals[i] if i < len(signals) else None

            # Check exit for existing position
            if position:
                exit_signal = self._check_exit(position, bar, next_bar)
                if exit_signal:
                    pnl = self._calculate_pnl(position, exit_signal, fee_pct, slippage_pct)
                    self.equity += pnl
                    self.trades.append({
                        "entry_time": position["entry_time"],
                        "exit_time": exit_signal["time"],
                        "side": position["side"],
                        "entry_price": position["entry_price"],
                        "exit_price": exit_signal["price"],
                        "pnl": pnl,
                        "pnl_pct": pnl / self.initial_equity * 100,
                        "reason": exit_signal["reason"],
                    })
                    position = None

            # Check entry (only if no position and signal)
            if not position and signal and signal.get("action") in ("buy", "sell"):
                position = {
                    "side": signal["action"],
                    "entry_price": next_bar["open"],  # Execute at next bar open
                    "entry_time": next_bar["timestamp"],
                    "stop_loss": signal.get("stop_loss"),
                    "take_profit": signal.get("take_profit"),
                    "max_hold_bars": signal.get("max_hold_bars", 6),  # 6 bars = 30 min
                    "bars_held": 0,
                }

            self.equity_curve.append({
                "timestamp": bar["timestamp"],
                "equity": self.equity,
            })

        # Close any open position at end
        if position and bars:
            last_bar = bars[-1]
            exit_signal = {
                "time": last_bar["timestamp"],
                "price": last_bar["close"],
                "reason": "end_of_data",
            }
            pnl = self._calculate_pnl(position, exit_signal, fee_pct, slippage_pct)
            self.equity += pnl
            self.trades.append({
                "entry_time": position["entry_time"],
                "exit_time": exit_signal["time"],
                "side": position["side"],
                "entry_price": position["entry_price"],
                "exit_price": exit_signal["price"],
                "pnl": pnl,
                "pnl_pct": pnl / self.initial_equity * 100,
                "reason": "end_of_data",
            })

        return self._build_result(asset, fee_pct)

    def _check_exit(self, position: Dict, bar: Dict, next_bar: Dict) -> Optional[Dict]:
        """Check if position should be closed."""
        position["bars_held"] += 1

        # Stop loss
        if position["side"] == "buy":
            if next_bar["low"] <= position["stop_loss"]:
                return {"time": next_bar["timestamp"], "price": position["stop_loss"], "reason": "stop_loss"}
        else:  # sell
            if next_bar["high"] >= position["stop_loss"]:
                return {"time": next_bar["timestamp"], "price": position["stop_loss"], "reason": "stop_loss"}

        # Take profit
        if position["take_profit"] is not None:
            if position["side"] == "buy":
                if next_bar["high"] >= position["take_profit"]:
                    return {"time": next_bar["timestamp"], "price": position["take_profit"], "reason": "take_profit"}
            else:  # sell
                if next_bar["low"] <= position["take_profit"]:
                    return {"time": next_bar["timestamp"], "price": position["take_profit"], "reason": "take_profit"}

        # Trailing stop (if enabled)
        if position.get("trailing_stop"):
            if position["side"] == "buy":
                # Update highest price seen
                highest_since_entry = max(position.get("highest_price", position["entry_price"]), next_bar["high"])
                position["highest_price"] = highest_since_entry
                trailing_level = highest_since_entry - position["trailing_distance"]
                if next_bar["low"] <= trailing_level:
                    return {"time": next_bar["timestamp"], "price": trailing_level, "reason": "trailing_stop"}
            else:  # sell
                # Update lowest price seen
                lowest_since_entry = min(position.get("lowest_price", position["entry_price"]), next_bar["low"])
                position["lowest_price"] = lowest_since_entry
                trailing_level = lowest_since_entry + position["trailing_distance"]
                if next_bar["high"] >= trailing_level:
                    return {"time": next_bar["timestamp"], "price": trailing_level, "reason": "trailing_stop"}

        # Time stop
        if position["bars_held"] >= position["max_hold_bars"]:
            return {"time": next_bar["timestamp"], "price": next_bar["close"], "reason": "time_stop"}

        return None

    def _calculate_pnl(self, position: Dict, exit: Dict, fee_pct: float, slippage_pct: float) -> float:
        """Calculate PnL for a trade including fees and slippage.
        
        Position sizing: 0.25% risk per trade.
        Position size = risk_amount / stop_loss_distance
        """
        risk_amount = self.initial_equity * 0.0025  # 0.25% of equity
        entry_price = position["entry_price"]
        stop_loss = position["stop_loss"]
        exit_price = exit["price"]
        
        # Calculate stop loss distance
        if position["side"] == "buy":
            sl_distance = abs(entry_price - stop_loss) / entry_price
            gross_return_pct = (exit_price - entry_price) / entry_price
        else:  # sell
            sl_distance = abs(stop_loss - entry_price) / entry_price
            gross_return_pct = (entry_price - exit_price) / entry_price
        
        # Avoid division by zero
        if sl_distance < 0.0001:
            sl_distance = 0.005  # Default to 0.5%
        
        # Position size based on risk
        position_size = risk_amount / sl_distance
        
        # Gross PnL
        gross_pnl = position_size * gross_return_pct
        
        # Fees and slippage on notional
        total_cost_pct = (fee_pct + slippage_pct) * 2 / 100
        fees = position_size * total_cost_pct
        
        net_pnl = gross_pnl - fees
        
        return net_pnl

    def _build_result(self, asset: str, fee_pct: float) -> BacktestResult:
        """Build BacktestResult from trades."""
        if not self.trades:
            return BacktestResult(
                strategy="unknown",
                asset=asset,
                total_return_pct=0.0,
                win_rate=0.0,
                profit_factor=0.0,
                max_drawdown_pct=0.0,
                sharpe_ratio=0.0,
                total_trades=0,
                avg_win_pct=0.0,
                avg_loss_pct=0.0,
                worst_streak=0,
                fees_pct=0.0,
                net_profit_pct=0.0,
                passes_thresholds=False,
                trades=[],
            )

        wins = [t for t in self.trades if t["pnl"] > 0]
        losses = [t for t in self.trades if t["pnl"] <= 0]

        total_pnl = sum(t["pnl"] for t in self.trades)
        total_return_pct = (self.equity - self.initial_equity) / self.initial_equity * 100

        win_rate = len(wins) / len(self.trades) if self.trades else 0
        gross_wins = sum(t["pnl"] for t in wins) if wins else 0
        gross_losses = abs(sum(t["pnl"] for t in losses)) if losses else 0
        profit_factor = gross_wins / gross_losses if gross_losses > 0 else float("inf")

        # Calculate max drawdown
        peak = self.initial_equity
        max_dd = 0
        for point in self.equity_curve:
            if point["equity"] > peak:
                peak = point["equity"]
            dd = (peak - point["equity"]) / peak * 100
            if dd > max_dd:
                max_dd = dd

        # Sharpe (simplified: assume daily returns, 252 days)
        returns = [t["pnl"] for t in self.trades]
        if len(returns) > 1:
            avg_return = sum(returns) / len(returns)
            variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
            std_dev = variance ** 0.5
            sharpe = (avg_return / std_dev) * (252 ** 0.5) if std_dev > 0 else 0
        else:
            sharpe = 0

        # Worst losing streak
        streak = 0
        worst = 0
        for t in self.trades:
            if t["pnl"] <= 0:
                streak += 1
                worst = max(worst, streak)
            else:
                streak = 0

        fees_total = len(self.trades) * fee_pct / 100 * self.initial_equity * 0.0025 * 4

        return BacktestResult(
            strategy="placeholder",
            asset=asset,
            total_return_pct=total_return_pct,
            win_rate=win_rate,
            profit_factor=profit_factor,
            max_drawdown_pct=max_dd,
            sharpe_ratio=sharpe,
            total_trades=len(self.trades),
            avg_win_pct=sum(t["pnl_pct"] for t in wins) / len(wins) if wins else 0,
            avg_loss_pct=sum(t["pnl_pct"] for t in losses) / len(losses) if losses else 0,
            worst_streak=worst,
            fees_pct=fees_total / self.initial_equity * 100,
            net_profit_pct=total_return_pct,
            passes_thresholds=(profit_factor > 1.2 and max_dd < 10 and len(self.trades) >= 100),
            trades=self.trades,
        )
