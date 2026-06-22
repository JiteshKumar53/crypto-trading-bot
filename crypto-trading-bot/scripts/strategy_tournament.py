"""
Strategy tournament — honest, cost-aware, walk-forward, gated.

The decisive upgrade (see DEEP_ANALYSIS_2026-06-20.md): instead of trusting a
broken scoreboard, run several PROVEN strategy archetypes through the corrected
backtest engine with realistic fees, benchmark each against buy-and-hold, test
stability across walk-forward folds, and run every result through the Strategy
Validation Gate. Only strategies that pass the gate are eligible to trade.

Archetypes tested (all long-only, daily timeframe where trend has any chance —
15m is already proven to be destroyed by fees):
  * Trend + regime filter  (EMA50>EMA200 regime, ATR trailing stop)  -- classic trend following
  * Donchian breakout      (Turtle: N-high entry, M-low exit)        -- classic breakout
  * RSI mean reversion     (buy RSI<30, exit RSI>55)                 -- classic mean reversion
  * Buy & Hold             (benchmark)

Indicators use pandas ewm/rolling (battle-tested, numpy-2 safe).
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
from strategy_gate import validate_strategy  # noqa: E402

DATA_DIR = ROOT.parent / "freqtrade_data" / "data" / "binance"
INITIAL_CAPITAL = 10_000.0
COMMISSION = 0.001
SLIPPAGE = 0.0005
CASH_USE = 0.98
N_FOLDS = 3


# ---------------- data + indicators ----------------
def load_daily(symbol: str) -> pd.DataFrame:
    df = pd.read_feather(DATA_DIR / f"{symbol}_USDT-15m.feather")
    df = df.rename(columns={"date": "timestamp"}).set_index("timestamp").sort_index()
    return df.resample("1D").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    ).dropna()


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def rsi(s, n=14):
    d = s.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return (100 - 100 / (1 + up / dn.replace(0, np.nan))).fillna(50)


def atr(df, n=14):
    h, l, c = df["high"], df["low"], df["close"]
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


# ---------------- signal generators -> (entry[], exit[]) ----------------
def sig_trend_regime(df):
    c = df["close"]
    regime = ema(c, 50) > ema(c, 200)             # only trade in uptrends
    cross_up = (ema(c, 20).shift(1) <= ema(c, 50).shift(1)) & (ema(c, 20) > ema(c, 50))
    cross_dn = (ema(c, 20).shift(1) >= ema(c, 50).shift(1)) & (ema(c, 20) < ema(c, 50))
    entry = (cross_up & regime).fillna(False).to_numpy()
    exit_ = (cross_dn | ~regime).fillna(False).to_numpy()
    return entry, exit_


def sig_donchian(df, n_in=20, n_out=10):
    c = df["close"]
    upper = c.rolling(n_in).max().shift(1)
    lower = c.rolling(n_out).min().shift(1)
    entry = (c > upper).fillna(False).to_numpy()
    exit_ = (c < lower).fillna(False).to_numpy()
    return entry, exit_


def sig_rsi_meanrev(df):
    r = rsi(df["close"], 14)
    entry = (r < 30).fillna(False).to_numpy()
    exit_ = (r > 55).fillna(False).to_numpy()
    return entry, exit_


STRATEGIES = {
    "TrendRegime": sig_trend_regime,
    "Donchian": sig_donchian,
    "RSIMeanRev": sig_rsi_meanrev,
}


# ---------------- execution ----------------
def run(df, entry, exit_, symbol):
    eng = BacktestEngine(INITIAL_CAPITAL, commission=COMMISSION, slippage=SLIPPAGE)
    eng.reset()
    closes = df["close"].to_numpy()
    idx = df.index
    for i in range(len(df)):
        price = float(closes[i]); ts = idx[i]
        in_pos = symbol in eng.positions
        if in_pos and bool(exit_[i]):
            eng.place_order(Order(symbol, OrderSide.SELL, eng.positions[symbol].qty, timestamp=ts), price)
        elif (not in_pos) and bool(entry[i]):
            qty = (eng.cash * CASH_USE) / price
            eng.place_order(Order(symbol, OrderSide.BUY, qty, timestamp=ts), price)
        eng.update_equity(ts, {symbol: price})
    eq = pd.DataFrame(eng.equity_history).set_index("timestamp")
    eq["returns"] = eq["equity"].pct_change().fillna(0)
    m = MetricsCalculator.calculate(eq, eng.trades, INITIAL_CAPITAL)
    return m


def buy_hold_return(df):
    c = df["close"].to_numpy()
    gross = (c[-1] / c[0])
    # one round-trip of costs
    return gross * (1 - COMMISSION - SLIPPAGE) * (1 - COMMISSION - SLIPPAGE) - 1


def walk_forward(df, sigfn, symbol, folds=N_FOLDS):
    out = []
    bounds = np.linspace(0, len(df), folds + 1).astype(int)
    for k in range(folds):
        sl = df.iloc[bounds[k]:bounds[k + 1]]
        if len(sl) < 60:
            continue
        e, x = sigfn(sl)
        out.append(run(sl, e, x, symbol)["total_return"])
    return out


def main():
    rows = []
    validations = []
    print("=" * 100)
    print("STRATEGY TOURNAMENT — daily, cost-aware (comm %.2f%% + slip %.2f%%/side), %d-fold walk-forward"
          % (COMMISSION * 100, SLIPPAGE * 100, N_FOLDS))
    print("=" * 100)

    for symbol in ["BTC", "ETH"]:
        df = load_daily(symbol)
        bh = buy_hold_return(df)
        print(f"\n### {symbol}  (buy & hold net: {bh*100:.1f}%)")
        for name, sigfn in STRATEGIES.items():
            e, x = sigfn(df)
            m = run(df, e, x, symbol)
            wf = walk_forward(df, sigfn, symbol)
            v = validate_strategy(name, symbol, m, bh, wf)
            validations.append(v)
            rows.append({"strategy": name, "symbol": symbol, "metrics": m,
                         "benchmark": bh, "walk_forward": wf, "passed": v.passed})
            pf = "inf" if m["profit_factor"] == float("inf") else f"{m['profit_factor']:.2f}"
            print(f"  {name:<12} ret={m['total_return']*100:7.1f}%  "
                  f"PF={pf:>5}  maxDD={m['max_drawdown']*100:5.1f}%  "
                  f"trades={m['closed_trades']:>3}  win={m['win_rate']*100:4.0f}%  "
                  f"WF={['+' if r>0 else '-' for r in wf]}  -> "
                  f"{'PASS ✓' if v.passed else 'FAIL ✗'}")

    print("\n" + "=" * 100)
    print("GATE DETAIL")
    print("=" * 100)
    any_pass = False
    for v in validations:
        if not v.passed:
            continue
        any_pass = True
        print(v.summary())
    if not any_pass:
        print("No strategy passed the validation gate. Failing reasons (first failing gate each):")
        for v in validations:
            first_fail = next((g for g in v.gates if not g.passed), None)
            if first_fail:
                print(f"  {v.strategy:<12} {v.symbol}: {first_fail.reason}")

    out = ROOT.parent / "freqtrade_data" / "tournament_results.json"
    ser = []
    for r in rows:
        mm = {k: (None if v == float("inf") else v) for k, v in r["metrics"].items()}
        ser.append({**r, "metrics": mm})
    out.write_text(json.dumps({"generated": datetime.now(timezone.utc).isoformat(),
                               "results": ser}, indent=2))
    print(f"\nSaved -> {out}")
    print(f"\nVERDICT: {'At least one strategy passed.' if any_pass else 'NONE eligible to trade.'}")
    return rows


if __name__ == "__main__":
    main()
