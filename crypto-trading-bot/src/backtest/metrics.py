"""
Backtest Metrics Calculator
Agent: Backtesting + Validation Team

Computes performance metrics from an equity curve and a list of fills.

REWRITTEN 2026-06-20 (see DEEP_ANALYSIS_2026-06-20.md):
The previous version did NOT compute trading performance. It defined
win_rate as "fraction of fills that are sells" and profit_factor as
"sell_notional / buy_notional" — both meaningless and biased positive in
a rising market. This version matches buys to sells FIFO and computes real
round-trip PnL net of commission, then derives win rate, profit factor,
expectancy, and consecutive-loss stats from actual closed trades.

Annualization is now inferred from the equity curve's timestamp spacing
instead of being hardcoded to hourly (which inflated daily Sharpe ~5x).
"""

import logging
from collections import deque, defaultdict
from typing import Dict, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

SECONDS_PER_YEAR = 365.25 * 24 * 3600


class MetricsCalculator:
    """Calculates comprehensive backtest metrics from honest round-trip PnL."""

    @staticmethod
    def calculate(equity_df: pd.DataFrame, trades: List, initial_capital: float) -> Dict:
        """
        Calculate all metrics from equity curve and fill list.

        Args:
            equity_df: DataFrame indexed by timestamp with 'equity' and
                'returns' columns (and optionally 'position_value').
            trades: List of Trade objects (individual fills) with
                .side, .qty, .price, .commission.
            initial_capital: Starting capital.

        Returns:
            Dict with all metrics (keys match BacktestResult fields).
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

        # Timeframe-aware annualization factor inferred from the equity index
        periods_per_year = MetricsCalculator._infer_periods_per_year(equity_df)

        n_periods = len(equity_df)
        # Only annualize when the sample is a meaningful fraction of a year.
        # Extrapolating a few periods to a full year is both meaningless and
        # numerically explosive, so fall back to the raw return instead.
        years = n_periods / periods_per_year if periods_per_year > 0 else 0.0
        if total_return > -1.0 and years >= 0.05:
            annualized_return = (1 + total_return) ** (1.0 / years) - 1
        else:
            annualized_return = total_return

        # Risk metrics
        sharpe_ratio = MetricsCalculator._sharpe_ratio(returns, periods_per_year)
        sortino_ratio = MetricsCalculator._sortino_ratio(returns, periods_per_year)
        max_drawdown = MetricsCalculator._max_drawdown(equity)
        calmar_ratio = MetricsCalculator._calmar_ratio(annualized_return, max_drawdown)

        # Honest trade metrics from FIFO-matched round trips
        trade_metrics = MetricsCalculator._trade_metrics(trades)

        # Exposure time
        if "position_value" in equity_df.columns:
            in_position = equity_df["position_value"] > 0
        else:
            in_position = pd.Series(False, index=equity_df.index)
        exposure_time = in_position.sum() / len(in_position) if len(in_position) else 0.0

        # Turnover (total traded notional / average equity)
        total_trade_value = sum(t.qty * t.price for t in trades)
        avg_equity = equity.mean()
        turnover = total_trade_value / avg_equity if avg_equity > 0 else 0.0

        # Worst single-period return on the equity curve
        worst_day = float(returns.min())

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
            "worst_trade": trade_metrics["worst_trade"],
            # --- new honest fields ---
            "closed_trades": trade_metrics["closed_trades"],
            "gross_profit": trade_metrics["gross_profit"],
            "gross_loss": trade_metrics["gross_loss"],
            "expectancy": trade_metrics["expectancy"],
            "avg_win": trade_metrics["avg_win"],
            "avg_loss": trade_metrics["avg_loss"],
            "max_consecutive_losses": trade_metrics["max_consecutive_losses"],
            "total_commission": trade_metrics["total_commission"],
        }

    @staticmethod
    def _infer_periods_per_year(equity_df: pd.DataFrame) -> float:
        """Infer annualization factor from median timestamp spacing."""
        try:
            idx = equity_df.index
            if not isinstance(idx, pd.DatetimeIndex):
                idx = pd.to_datetime(idx)
            if len(idx) < 2:
                return 8760.0
            # Use timedelta arithmetic (resolution-agnostic) rather than a raw
            # int64 view: pandas datetime64 may be ns/us/ms depending on source.
            deltas = idx.to_series().diff().dropna()
            median_seconds = deltas.median().total_seconds()
            if median_seconds <= 0:
                return 8760.0
            return SECONDS_PER_YEAR / median_seconds
        except Exception:
            return 8760.0  # fallback: hourly

    @staticmethod
    def _sharpe_ratio(returns: pd.Series, periods_per_year: float) -> float:
        """Annualized Sharpe ratio (risk-free rate assumed 0)."""
        if len(returns) < 2 or returns.std() == 0:
            return 0.0
        mean = returns.mean() * periods_per_year
        vol = returns.std(ddof=1) * np.sqrt(periods_per_year)
        return float(mean / vol) if vol > 0 else 0.0

    @staticmethod
    def _sortino_ratio(returns: pd.Series, periods_per_year: float) -> float:
        """Annualized Sortino ratio (downside deviation only)."""
        if len(returns) < 2:
            return 0.0
        downside = returns[returns < 0]
        if len(downside) == 0:
            return 0.0  # no downside observed -> undefined; report 0 not inf
        downside_dev = downside.std(ddof=1) * np.sqrt(periods_per_year)
        annual_return = returns.mean() * periods_per_year
        return float(annual_return / downside_dev) if downside_dev > 0 else 0.0

    @staticmethod
    def _max_drawdown(equity: pd.Series) -> float:
        """Maximum drawdown from running peak (returned as a positive fraction)."""
        rolling_max = equity.cummax()
        drawdown = (equity - rolling_max) / rolling_max
        return float(abs(drawdown.min()))

    @staticmethod
    def _calmar_ratio(annualized_return: float, max_drawdown: float) -> float:
        if max_drawdown == 0:
            return 0.0
        return annualized_return / max_drawdown

    @staticmethod
    def _trade_metrics(trades: List) -> Dict:
        """
        Match fills into round trips (FIFO, per symbol) and compute real PnL.

        Each closed round trip's PnL is net of the buy-side and sell-side
        commission allocated to the matched quantity.
        """
        if not trades:
            return MetricsCalculator._empty_trade_metrics()

        # FIFO lots per symbol: each lot is [qty_remaining, price, commission_per_unit]
        lots: Dict[str, deque] = defaultdict(deque)
        closed_pnls: List[float] = []   # currency PnL per closed round trip
        closed_returns: List[float] = []  # PnL as fraction of cost basis
        total_commission = 0.0

        for t in trades:
            side = t.side.value if hasattr(t.side, "value") else str(t.side)
            qty = float(t.qty)
            price = float(t.price)
            commission = float(getattr(t, "commission", 0.0) or 0.0)
            total_commission += commission
            comm_per_unit = commission / qty if qty else 0.0

            if side == "buy":
                lots[t.symbol].append([qty, price, comm_per_unit])
            else:  # sell -> close existing long lots FIFO
                remaining = qty
                sell_cpu = comm_per_unit
                while remaining > 1e-12 and lots[t.symbol]:
                    lot = lots[t.symbol][0]
                    lot_qty, buy_price, buy_cpu = lot
                    matched = min(remaining, lot_qty)
                    cost_basis = matched * buy_price
                    pnl = (
                        matched * (price - buy_price)
                        - matched * buy_cpu
                        - matched * sell_cpu
                    )
                    closed_pnls.append(pnl)
                    closed_returns.append(pnl / cost_basis if cost_basis > 0 else 0.0)
                    lot[0] -= matched
                    remaining -= matched
                    if lot[0] <= 1e-12:
                        lots[t.symbol].popleft()
                # Sells with no matching long lot (e.g. shorts) are ignored here;
                # this engine is long-only.

        num_fills = len(trades)
        closed_trades = len(closed_pnls)

        if closed_trades == 0:
            m = MetricsCalculator._empty_trade_metrics()
            m["num_trades"] = num_fills  # preserve fill count for callers/tests
            m["total_commission"] = total_commission
            return m

        wins = [p for p in closed_pnls if p > 0]
        losses = [p for p in closed_pnls if p <= 0]
        gross_profit = float(sum(wins))
        gross_loss = float(abs(sum(losses)))

        win_rate = len(wins) / closed_trades
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (
            float("inf") if gross_profit > 0 else 0.0
        )
        expectancy = float(np.mean(closed_pnls))
        avg_win = float(np.mean(wins)) if wins else 0.0
        avg_loss = float(np.mean(losses)) if losses else 0.0
        worst_trade = float(min(closed_returns)) if closed_returns else 0.0

        # Max consecutive losing round trips
        max_consec = 0
        run = 0
        for p in closed_pnls:
            if p <= 0:
                run += 1
                max_consec = max(max_consec, run)
            else:
                run = 0

        return {
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "avg_trade": expectancy,
            "num_trades": num_fills,
            "closed_trades": closed_trades,
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "expectancy": expectancy,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "worst_trade": worst_trade,
            "max_consecutive_losses": max_consec,
            "total_commission": total_commission,
        }

    @staticmethod
    def _empty_trade_metrics() -> Dict:
        return {
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "avg_trade": 0.0,
            "num_trades": 0,
            "closed_trades": 0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "expectancy": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "worst_trade": 0.0,
            "max_consecutive_losses": 0,
            "total_commission": 0.0,
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
            "closed_trades": 0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "expectancy": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "max_consecutive_losses": 0,
            "total_commission": 0.0,
        }
