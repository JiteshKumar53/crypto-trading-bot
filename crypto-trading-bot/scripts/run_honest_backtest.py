"""
Honest, cost-aware backtest of the project's documented strategies.

Created 2026-06-20 (see DEEP_ANALYSIS_2026-06-20.md).

Purpose
-------
Re-validate the strategies the project actually shipped, using:
  * the CORRECTED metrics layer (real FIFO round-trip PnL),
  * REALISTIC trading costs (commission + slippage per side),
  * a buy-and-hold benchmark on the same data and same costs.

It uses the real Binance 15m OHLCV the project already had on disk
(BTC/USDT, ETH/USDT, Jan 2024 -> May 2026, ~82k bars each).

Strategies tested
-----------------
  1. EMA8/EMA21 + RSI(50-70) with 2% stop / 3% take-profit
     (the strategy the project marked "LIVE" in bots/ea_system).
  2. SMA50 crossover on 15m (the "SimpleSMA15m" control).
  3. SMA50 crossover resampled to DAILY (the only strategy the old,
     broken metrics ever "passed": Trend Rider v5.x).
  4. Buy & Hold (benchmark).

Indicators are precomputed vectorially so the run is O(n), and orders are
executed through the real BacktestEngine fill/accounting primitives so the
numbers reflect the production code paths.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from backtest.backtest_engine import BacktestEngine, Order, OrderSide  # noqa: E402
from backtest.metrics import MetricsCalculator  # noqa: E402

DATA_DIR = ROOT.parent / "freqtrade_data" / "data" / "binance"
INITIAL_CAPITAL = 10_000.0
COMMISSION = 0.001    # 0.10% per side (Binance spot taker floor)
SLIPPAGE = 0.0005     # 0.05% per side
CASH_USE = 0.98       # fraction of cash deployed per entry (leave headroom for slippage)


def load(symbol: str, daily: bool = False) -> pd.DataFrame:
    df = pd.read_feather(DATA_DIR / f"{symbol}_USDT-15m.feather")
    df = df.rename(columns={"date": "timestamp"}).set_index("timestamp").sort_index()
    if daily:
        df = df.resample("1D").agg(
            {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
        ).dropna()
    return df


def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(100.0)


def signals_ema_rsi(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Return (long_entry, long_exit) boolean arrays for the EMA/RSI strategy.

    Entry: EMA8 crosses above EMA21 AND 50 < RSI(14) < 70.
    Exit (cross side only; SL/TP handled in the runner): EMA8 crosses below EMA21.
    """
    close = df["close"]
    ema_f = _ema(close, 8)
    ema_s = _ema(close, 21)
    rsi = _rsi(close, 14)
    cross_up = (ema_f.shift(1) <= ema_s.shift(1)) & (ema_f > ema_s)
    cross_dn = (ema_f.shift(1) >= ema_s.shift(1)) & (ema_f < ema_s)
    entry = (cross_up & (rsi > 50) & (rsi < 70)).to_numpy()
    exit_ = cross_dn.to_numpy()
    return entry, exit_


def signals_sma_cross(df: pd.DataFrame, fast: int = 1, slow: int = 50) -> tuple[np.ndarray, np.ndarray]:
    """Price/SMA50 crossover (fast=1 means raw close vs SMA50)."""
    close = df["close"]
    sma_f = close.rolling(fast).mean() if fast > 1 else close
    sma_s = close.rolling(slow).mean()
    cross_up = (sma_f.shift(1) <= sma_s.shift(1)) & (sma_f > sma_s)
    cross_dn = (sma_f.shift(1) >= sma_s.shift(1)) & (sma_f < sma_s)
    return cross_up.fillna(False).to_numpy(), cross_dn.fillna(False).to_numpy()


def run_strategy(name, symbol, df, entry, exit_, stop_pct=None, take_pct=None):
    """Execute long-only signals through the real engine, return BacktestResult."""
    engine = BacktestEngine(
        initial_capital=INITIAL_CAPITAL, commission=COMMISSION, slippage=SLIPPAGE
    )
    engine.reset()

    closes = df["close"].to_numpy()
    timestamps = df.index
    entry_price = None

    for i in range(len(df)):
        price = float(closes[i])
        ts = timestamps[i]
        in_pos = symbol in engine.positions

        if in_pos:
            do_exit = bool(exit_[i])
            if stop_pct is not None and entry_price is not None:
                if (price - entry_price) / entry_price <= -stop_pct:
                    do_exit = True
            if take_pct is not None and entry_price is not None:
                if (price - entry_price) / entry_price >= take_pct:
                    do_exit = True
            if do_exit:
                qty = engine.positions[symbol].qty
                engine.place_order(Order(symbol, OrderSide.SELL, qty, timestamp=ts), price)
                entry_price = None
        else:
            if bool(entry[i]):
                qty = (engine.cash * CASH_USE) / price
                trade = engine.place_order(Order(symbol, OrderSide.BUY, qty, timestamp=ts), price)
                if trade:
                    entry_price = trade.price

        engine.update_equity(ts, {symbol: price})

    equity_df = pd.DataFrame(engine.equity_history).set_index("timestamp")
    equity_df["returns"] = equity_df["equity"].pct_change().fillna(0)
    metrics = MetricsCalculator.calculate(equity_df, engine.trades, INITIAL_CAPITAL)
    metrics["strategy"] = name
    metrics["symbol"] = symbol
    metrics["final_equity"] = float(equity_df["equity"].iloc[-1])
    return metrics


def run_buy_hold(symbol, df):
    engine = BacktestEngine(
        initial_capital=INITIAL_CAPITAL, commission=COMMISSION, slippage=SLIPPAGE
    )
    engine.reset()
    closes = df["close"].to_numpy()
    ts0 = df.index[0]
    price0 = float(closes[0])
    qty = (engine.cash * CASH_USE) / price0
    engine.place_order(Order(symbol, OrderSide.BUY, qty, timestamp=ts0), price0)
    for i in range(len(df)):
        engine.update_equity(df.index[i], {symbol: float(closes[i])})
    equity_df = pd.DataFrame(engine.equity_history).set_index("timestamp")
    equity_df["returns"] = equity_df["equity"].pct_change().fillna(0)
    metrics = MetricsCalculator.calculate(equity_df, engine.trades, INITIAL_CAPITAL)
    metrics["strategy"] = "BuyAndHold"
    metrics["symbol"] = symbol
    metrics["final_equity"] = float(equity_df["equity"].iloc[-1])
    return metrics


def fmt(m: dict) -> str:
    pf = m["profit_factor"]
    pf_s = "inf" if pf == float("inf") else f"{pf:.2f}"
    return (
        f"  {m['strategy']:<16} {m['symbol']:<8} "
        f"ret={m['total_return']*100:7.2f}%  "
        f"CAGR={m['annualized_return']*100:7.2f}%  "
        f"Sharpe={m['sharpe_ratio']:6.2f}  "
        f"MaxDD={m['max_drawdown']*100:6.2f}%  "
        f"trades={m['closed_trades']:>4}  "
        f"win={m['win_rate']*100:5.1f}%  "
        f"PF={pf_s:>5}  "
        f"fees=${m['total_commission']:.0f}"
    )


def main():
    results = []
    print("=" * 110)
    print("HONEST COST-AWARE BACKTEST  (commission=%.2f%%/side, slippage=%.2f%%/side)"
          % (COMMISSION * 100, SLIPPAGE * 100))
    print("Data: Binance 15m, Jan 2024 -> May 2026")
    print("=" * 110)

    for symbol in ["BTC", "ETH"]:
        df15 = load(symbol, daily=False)
        df1d = load(symbol, daily=True)

        e, x = signals_ema_rsi(df15)
        results.append(run_strategy("EMA_RSI_15m", symbol, df15, e, x,
                                    stop_pct=0.02, take_pct=0.03))

        e, x = signals_sma_cross(df15, fast=1, slow=50)
        results.append(run_strategy("SMA50_15m", symbol, df15, e, x))

        e, x = signals_sma_cross(df1d, fast=1, slow=50)
        results.append(run_strategy("SMA50_daily", symbol, df1d, e, x))

        results.append(run_buy_hold(symbol, df15))

    print("\nResults:\n")
    for symbol in ["BTC", "ETH"]:
        for m in results:
            if m["symbol"] == symbol:
                print(fmt(m))
        print()

    out = ROOT.parent / "freqtrade_data" / "honest_backtest_results.json"
    serializable = []
    for m in results:
        mm = {k: (None if v == float("inf") else v) for k, v in m.items()}
        serializable.append(mm)
    out.write_text(json.dumps(
        {"generated": datetime.now(timezone.utc).isoformat(),
         "commission_per_side": COMMISSION,
         "slippage_per_side": SLIPPAGE,
         "results": serializable}, indent=2))
    print(f"Saved JSON -> {out}")
    return results


if __name__ == "__main__":
    main()
