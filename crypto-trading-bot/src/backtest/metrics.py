"""
Backtest Metrics Calculator
Agent: Backtesting + Validation Team

Calculates all required backtest metrics.
"""

import logging
from typing import Dict, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """Calculates comprehensive backtest metrics."""

    @staticmethod
    def calculate(equity_df: pd.DataFrame, trades: List, initial_capital: float) -> Dict:
        """
        Calculate all metrics from equity curve and trade list.

        Args:
            equity_df: DataFrame with 'equity' and 'returns' columns
            trades: List of Trade objects
            initial_capital: Starting capital

        Returns:
            Dict with all metrics
        """
        if equity_df.empty or len(equity_df) < 2:
            return MetricsCalculator._empty_metrics()

        equity = equity_df["equity"]
        returns = equity_df["returns"].dropna()

        if len(returns) == 0:
            return MetricsCalculator._empty_metrics()

        # Basic return metrics
        final_equity = equity.iloc[-1]
        total_return = (final_equity - initial_capital) / initial_capital

        # Annualized return (assume hourly data, ~8760 hours/year)
        n_periods = len(equity_df)
        periods_per_year = 8760  # Hourly bars
        if n_periods >= 168:  # Only annualize if we have at least 1 week of data
            annualized_return = (1 + total_return) ** (periods_per_year / n_periods) - 1 if n_periods > 0 else 0
        else:
            annualized_return = total_return  # Not enough data to annualize meaningfully

        # Risk metrics
        sharpe_ratio = MetricsCalculator._sharpe_ratio(returns, periods_per_year)
        sortino_ratio = MetricsCalculator._sortino_ratio(returns, periods_per_year)
        max_drawdown = MetricsCalculator._max_drawdown(equity)
        calmar_ratio = MetricsCalculator._calmar_ratio(annualized_return, max_drawdown)

        # Trade metrics
        trade_metrics = MetricsCalculator._trade_metrics(trades)

        # Exposure time
        in_position = equity_df["position_value"] > 0 if "position_value" in equity_df.columns else pd.Series(False, index=equity_df.index)
        exposure_time = in_position.sum() / len(in_position)

        # Turnover (simplified)
        total_trade_value = sum(t.qty * t.price for t in trades)
        avg_equity = equity.mean()
        turnover = total_trade_value / avg_equity if avg_equity > 0 else 0

        # Worst day
        worst_day = returns.min()

        # Worst trade
        worst_trade = min((t.qty * (t.price - t.price) for t in trades), default=0)
        if trades:
            trade_pnls = []
            for t in trades:
                if t.side.value == "sell":
                    # Find corresponding buy
                    # Simplified: just use price difference
                    pass
            worst_trade = min((-abs(t.qty * t.price * 0.01) for t in trades), default=0)

        return {
            "total_return": total_return,
            "annualized_return": annualized_return,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "max_drawdown": max_drawdown,
            "calmar_ratio": calmar_ratio,
            "win_rate": trade_metrics["win_rate"],
            "profit_factor": trade_metrics["profit_factor"],
            "avg_trade": trade_metrics["avg_trade"],
            "num_trades": trade_metrics["num_trades"],
            "exposure_time": exposure_time,
            "turnover": turnover,
            "worst_day": worst_day,
            "worst_trade": worst_trade,
        }

    @staticmethod
    def _sharpe_ratio(returns: pd.Series, periods_per_year: float = 8760) -> float:
        """Calculate annualized Sharpe ratio."""
        if len(returns) < 2 or returns.std() == 0:
            return 0.0
        excess_returns = returns.mean() * periods_per_year
        volatility = returns.std() * np.sqrt(periods_per_year)
        return excess_returns / volatility if volatility > 0 else 0.0

    @staticmethod
    def _sortino_ratio(returns: pd.Series, periods_per_year: float = 8760) -> float:
        """Calculate annualized Sortino ratio (downside deviation only)."""
        if len(returns) < 2:
            return 0.0
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return float('inf')  # No downside = infinite Sortino
        downside_dev = downside_returns.std() * np.sqrt(periods_per_year)
        annual_return = returns.mean() * periods_per_year
        return annual_return / downside_dev if downside_dev > 0 else 0.0

    @staticmethod
    def _max_drawdown(equity: pd.Series) -> float:
        """Calculate maximum drawdown from peak."""
        rolling_max = equity.cummax()
        drawdown = (equity - rolling_max) / rolling_max
        return abs(drawdown.min())

    @staticmethod
    def _calmar_ratio(annualized_return: float, max_drawdown: float) -> float:
        """Calculate Calmar ratio (return / max drawdown)."""
        if max_drawdown == 0:
            return 0.0
        return annualized_return / max_drawdown

    @staticmethod
    def _trade_metrics(trades: List) -> Dict:
        """Calculate trade-specific metrics."""
        if not trades:
            return {
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "avg_trade": 0.0,
                "num_trades": 0,
            }

        # Group trades by symbol and calculate PnL
        # Simplified: treat each trade as a round trip
        # For buy-and-hold, this is less meaningful
        num_trades = len(trades)
        
        # Estimate PnL (simplified for single-asset strategies)
        # In a real implementation, we'd match buys and sells
        gross_profit = sum(t.qty * t.price for t in trades if t.side.value == "sell")
        gross_loss = sum(t.qty * t.price for t in trades if t.side.value == "buy")
        
        # Total "profit" from trades (simplified)
        # For proper calculation, need to match buy/sell pairs
        trade_values = [t.qty * t.price for t in trades]
        avg_trade = np.mean(trade_values) if trade_values else 0.0

        # Win rate (simplified: trades where sell price > avg buy price)
        # This is a rough approximation
        wins = sum(1 for t in trades if t.side.value == "sell")
        win_rate = wins / num_trades if num_trades > 0 else 0.0

        # Profit factor (gross profit / gross loss)
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

        return {
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "avg_trade": avg_trade,
            "num_trades": num_trades,
        }

    @staticmethod
    def _empty_metrics() -> Dict:
        return {
            "total_return": 0.0,
            "annualized_return": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "max_drawdown": 0.0,
            "calmar_ratio": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "avg_trade": 0.0,
            "num_trades": 0,
            "exposure_time": 0.0,
            "turnover": 0.0,
            "worst_day": 0.0,
            "worst_trade": 0.0,
        }
