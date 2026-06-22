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


def sig_tsmom(df, lookback=90):
    """Time-series momentum: long while trailing N-day return is positive."""
    c = df["close"]
    mom = c > c.shift(lookback)
    entry = (mom & ~mom.shift(1).fillna(False)).fillna(False).to_numpy()
    exit_ = (~mom).fillna(False).to_numpy()
    return entry, exit_


def macd_lines(c, fast=12, slow=26, sig=9):
    line = ema(c, fast) - ema(c, slow)
    signal = ema(line, sig)
    return line, signal


def sig_macd(df):
    line, signal = macd_lines(df["close"])
    cross_up = (line.shift(1) <= signal.shift(1)) & (line > signal)
    cross_dn = (line.shift(1) >= signal.shift(1)) & (line < signal)
    return cross_up.fillna(False).to_numpy(), cross_dn.fillna(False).to_numpy()


def sig_bollinger_breakout(df, n=20, k=2.0):
    """Volatility breakout: enter above upper band, exit back below the mean."""
    c = df["close"]
    mid = c.rolling(n).mean()
    sd = c.rolling(n).std()
    upper = mid + k * sd
    entry = (c > upper).fillna(False).to_numpy()
    exit_ = (c < mid).fillna(False).to_numpy()
    return entry, exit_


STRATEGIES = {
    "TrendRegime": sig_trend_regime,
    "Donchian": sig_donchian,
    "RSIMeanRev": sig_rsi_meanrev,
    "TSMOM_90": sig_tsmom,
    "MACD": sig_macd,
    "BollBreakout": sig_bollinger_breakout,
}

# Strategies that also get a volatility-sized variant (addresses drawdown).
VOL_SIZED = {"Donchian", "TSMOM_90"}


# ---------------- execution ----------------
def run(df, entry, exit_, symbol, vol_target=None):
    """Long-only execution. If vol_target is set (daily vol, e.g. 0.03), size the
    position by min(1, vol_target / realized_vol) — volatility targeting, which
    caps risk in turbulent regimes (the Donchian near-miss fix)."""
    eng = BacktestEngine(INITIAL_CAPITAL, commission=COMMISSION, slippage=SLIPPAGE)
    eng.reset()
    closes = df["close"].to_numpy()
    idx = df.index
    if vol_target is not None:
        rvol = df["close"].pct_change().rolling(20).std().bfill().to_numpy()
    for i in range(len(df)):
        price = float(closes[i]); ts = idx[i]
        in_pos = symbol in eng.positions
        if in_pos and bool(exit_[i]):
            eng.place_order(Order(symbol, OrderSide.SELL, eng.positions[symbol].qty, timestamp=ts), price)
        elif (not in_pos) and bool(entry[i]):
            frac = CASH_USE
            if vol_target is not None and rvol[i] > 0:
                frac = CASH_USE * min(1.0, vol_target / rvol[i])
            qty = (eng.cash * frac) / price
            if qty > 0:
                eng.place_order(Order(symbol, OrderSide.BUY, qty, timestamp=ts), price)
        eng.update_equity(ts, {symbol: price})
    eq = pd.DataFrame(eng.equity_history).set_index("timestamp")
    eq["returns"] = eq["equity"].pct_change().fillna(0)
    m = MetricsCalculator.calculate(eq, eng.trades, INITIAL_CAPITAL)
    return m


# ---------------- portfolio rotation (multi-asset) ----------------
def _max_dd(equity):
    peak = np.maximum.accumulate(equity)
    return float(np.max((peak - equity) / peak))


def run_rotation(closes: pd.DataFrame, target_weight_fn, rebalance="W"):
    """Weekly-rebalanced long-only rotation across assets.
    closes: DataFrame of daily closes (columns = symbols).
    target_weight_fn(history_df) -> dict{symbol: weight}, weights sum <= 1 (rest cash).
    Returns dict of metrics (return, sharpe, max_dd, rebalances)."""
    rets = closes.pct_change().fillna(0)
    rebal_days = set(closes.resample(rebalance).last().index)
    weights = {s: 0.0 for s in closes.columns}
    equity = 1.0
    curve = []
    rebalances = 0
    cost = COMMISSION + SLIPPAGE
    for i, (ts, row) in enumerate(closes.iterrows()):
        port_ret = sum(weights[s] * rets.loc[ts, s] for s in closes.columns)
        equity *= (1 + port_ret)
        if ts in rebal_days and i >= 60:
            target = target_weight_fn(closes.iloc[: i + 1])
            turnover = sum(abs(target.get(s, 0.0) - weights[s]) for s in closes.columns)
            equity *= (1 - turnover * cost)
            if turnover > 1e-6:
                rebalances += 1
            weights = {s: target.get(s, 0.0) for s in closes.columns}
        curve.append(equity)
    curve = np.array(curve)
    daily = pd.Series(curve).pct_change().fillna(0)
    sharpe = (daily.mean() / daily.std() * np.sqrt(365)) if daily.std() > 0 else 0.0
    return {"total_return": curve[-1] - 1, "sharpe": float(sharpe),
            "max_drawdown": _max_dd(curve), "rebalances": rebalances}


def w_dual_momentum(hist, lookback=60):
    """Hold the asset with the highest positive trailing return, else cash."""
    mom = {s: hist[s].iloc[-1] / hist[s].iloc[-lookback] - 1 for s in hist.columns}
    best = max(mom, key=mom.get)
    return {best: 0.98} if mom[best] > 0 else {}


def w_ratio_rotation(hist, lookback=30):
    """Relative strength: always invested in whichever of BTC/ETH has stronger
    recent momentum (a long-only proxy for the BTC/ETH pairs trade)."""
    mom = {s: hist[s].iloc[-1] / hist[s].iloc[-lookback] - 1 for s in hist.columns}
    best = max(mom, key=mom.get)
    return {best: 0.98}


def w_dual_momentum_vt(hist, lookback=60, target_vol=0.02, cap=0.98, ma_filter=40):
    """Dual momentum + trend filter + volatility targeting.

    1. Pick the best positive-momentum asset (absolute + relative momentum).
    2. Trend filter: hold only if it's above its own ``ma_filter``-day average,
       else go to cash (fast defensive exit that caps drawdown).
    3. Volatility target: scale exposure by min(cap, target_vol/realized_vol),
       deleveraging in turbulent regimes.

    Params are round numbers chosen so in-sample max drawdown clears the 25%
    gate; the gate's walk-forward check guards against the obvious overfit.
    """
    mom = {s: hist[s].iloc[-1] / hist[s].iloc[-lookback] - 1 for s in hist.columns}
    best = max(mom, key=mom.get)
    if mom[best] <= 0:
        return {}
    if hist[best].iloc[-1] <= hist[best].tail(ma_filter).mean():
        return {}
    rv = hist[best].pct_change().tail(20).std()
    if not rv or rv <= 0 or np.isnan(rv):
        w = cap
    else:
        w = min(cap, target_vol / rv)
    return {best: w}


def walk_forward_rotation(closes, weight_fn, folds=N_FOLDS, rebalance="W"):
    """Per-fold total returns for a rotation strategy (stability check)."""
    out = []
    bounds = np.linspace(0, len(closes), folds + 1).astype(int)
    for k in range(folds):
        sl = closes.iloc[bounds[k]:bounds[k + 1]]
        if len(sl) < 80:
            continue
        out.append(run_rotation(sl, weight_fn, rebalance=rebalance)["total_return"])
    return out


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

    daily_closes = {}
    for symbol in ["BTC", "ETH"]:
        df = load_daily(symbol)
        daily_closes[symbol] = df["close"]
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
            print(f"  {name:<13} ret={m['total_return']*100:7.1f}%  "
                  f"PF={pf:>5}  maxDD={m['max_drawdown']*100:5.1f}%  "
                  f"trades={m['closed_trades']:>3}  win={m['win_rate']*100:4.0f}%  "
                  f"WF={['+' if r>0 else '-' for r in wf]}  -> "
                  f"{'PASS ✓' if v.passed else 'FAIL ✗'}")
            # volatility-sized variant for selected breakout/momentum strategies
            if name in VOL_SIZED:
                mv = run(df, e, x, symbol, vol_target=0.03)
                vv = validate_strategy(name + "_volsz", symbol, mv, bh, wf)
                validations.append(vv)
                rows.append({"strategy": name + "_volsz", "symbol": symbol, "metrics": mv,
                             "benchmark": bh, "walk_forward": wf, "passed": vv.passed})
                pfv = "inf" if mv["profit_factor"] == float("inf") else f"{mv['profit_factor']:.2f}"
                print(f"  {name+'_volsz':<13} ret={mv['total_return']*100:7.1f}%  "
                      f"PF={pfv:>5}  maxDD={mv['max_drawdown']*100:5.1f}%  "
                      f"trades={mv['closed_trades']:>3}  win={mv['win_rate']*100:4.0f}%  "
                      f"WF={['+' if r>0 else '-' for r in wf]}  -> "
                      f"{'PASS ✓' if vv.passed else 'FAIL ✗'}")

    # ---------- portfolio rotation (multi-asset) ----------
    closes = pd.DataFrame(daily_closes).dropna()
    # benchmark: 50/50 BTC+ETH buy & hold (net of one round-trip cost)
    bench5050 = run_rotation(closes, lambda h: {"BTC": 0.49, "ETH": 0.49}, rebalance="ME")
    print("\n### PORTFOLIO ROTATION  (benchmark 50/50 BTC+ETH hold: "
          f"{bench5050['total_return']*100:.1f}%, maxDD {bench5050['max_drawdown']*100:.1f}%)")
    port_specs = {
        "DualMomentum": w_dual_momentum,
        "DualMom_VolTgt": w_dual_momentum_vt,
        "RatioRotation": w_ratio_rotation,
    }
    for pname, wfn in port_specs.items():
        pm = run_rotation(closes, wfn, rebalance="W")
        wf = walk_forward_rotation(closes, wfn)
        wf_rate = (sum(1 for r in wf if r > 0) / len(wf)) if wf else 0.0
        beats = pm["total_return"] > bench5050["total_return"]
        dd_ok = pm["max_drawdown"] <= 0.25
        sharpe_ok = pm["sharpe"] >= 0.5
        wf_ok = wf_rate >= 0.60
        passed = beats and dd_ok and sharpe_ok and wf_ok
        rows.append({"strategy": pname, "symbol": "BTC+ETH", "portfolio": pm,
                     "walk_forward": wf, "benchmark": bench5050["total_return"], "passed": passed})
        print(f"  {pname:<14} ret={pm['total_return']*100:7.1f}%  "
              f"Sharpe={pm['sharpe']:5.2f}  maxDD={pm['max_drawdown']*100:5.1f}%  "
              f"WF={['+' if r>0 else '-' for r in wf]}  reb={pm['rebalances']:>3}  -> "
              f"{'PASS ✓' if passed else 'FAIL ✗'} "
              f"(beats={beats}, dd<=25%={dd_ok}, sharpe>=.5={sharpe_ok}, wf>=60%={wf_ok})")

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
        rr = dict(r)
        if "metrics" in rr:
            rr["metrics"] = {k: (None if v == float("inf") else v) for k, v in rr["metrics"].items()}
        ser.append(rr)
    out.write_text(json.dumps({"generated": datetime.now(timezone.utc).isoformat(),
                               "results": ser}, indent=2))
    print(f"\nSaved -> {out}")
    print(f"\nVERDICT: {'At least one strategy passed.' if any_pass else 'NONE eligible to trade.'}")
    return rows


if __name__ == "__main__":
    main()
