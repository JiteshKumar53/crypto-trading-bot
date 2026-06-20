# Deep Analysis — Why This Project Was Unprofitable, and How to Fix It

**Date:** 2026-06-20
**Scope:** Full codebase review (188 Python files, ~29k LOC, 162 markdown docs)
**Verdict:** The bot was never *measured* correctly, so it was never *known* to be profitable in the first place. The "profitability" that justified going live was an artifact of broken metrics. Everything else (strategy, agents, watchdogs) is secondary to that.

---

## TL;DR

1. **The backtest scorecard is broken.** `src/backtest/metrics.py` does not compute profit factor, win rate, or per-trade PnL at all. The numbers that "passed" Trend Rider v5.6 (BTC PF=1.58, ETH PF=4.89) are arithmetic on raw buy/sell notional — they mostly reflect that crypto prices rose during the test window, not that the strategy has edge. **Fix this before anything else; you cannot improve what you measure wrong.**
2. **Backtests assume zero trading cost.** `BacktestEngine(commission=0.0)`. Real Alpaca crypto fees are ~0.15–0.25% per side. A 15m strategy turning over hundreds of times pays its entire thin edge to fees — exactly what the SimpleSMA15m result (-0.59%, 24.6% win) shows.
3. **The live engine doesn't actually trade on signals.** `ea_core_engine.py` Stage 7 (signal generation) is a no-op placeholder, Stage 10 risk-checks a hardcoded order (`qty=0.0026, price=77000`), strategy name is hardcoded `'grid_trading_v1'`, and Stage 12 never submits. The "live" path and the "backtest" path are disconnected.
4. **The edge doesn't exist.** Stripped of broken metrics, the actual strategy is an EMA/SMA crossover. On honest 15m data it loses (24.6% win rate, -8.78 Sharpe). On daily it only "wins" because it's long during a bull market — that's beta, not alpha.
5. **Massive process theater.** 22 strategy variants, 3 pipeline controllers, multiple "CEO reporting watchdogs," 162 markdown reports, "capsules," "self-evolution" docs. Enormous effort went into orchestration and reporting *around* a core that was never validated.

The best way to improve this project is to **invert the effort**: delete ~80% of the scaffolding, build one correct measurement harness, and only then ask whether any strategy survives honest, cost-aware testing. Most likely none of the current ones do — and that's the most valuable thing to learn.

---

## Evidence

### 1. `metrics.py` does not measure trading performance (root cause)

`src/backtest/metrics.py`, `_trade_metrics()`:

```python
wins = sum(1 for t in trades if t.side.value == "sell")
win_rate = wins / num_trades            # = fraction of trades that are sells, NOT winners

gross_profit = sum(t.qty * t.price for t in trades if t.side.value == "sell")
gross_loss   = sum(t.qty * t.price for t in trades if t.side.value == "buy")
profit_factor = gross_profit / gross_loss   # = sell_notional / buy_notional
```

- **Win rate** is just "how many of my fills were sells." For any strategy that fully exits what it enters, this is ~50% by construction — independent of whether trades made money.
- **Profit factor** is total sell value ÷ total buy value. In a rising market you sell at higher prices than you bought, so PF > 1 *automatically* — even for a coin-flip strategy. ETH "PF=4.89" is ETH's price appreciation, not strategy skill.
- The actual buy/sell matching loop is never implemented — it literally contains `pass`:

```python
for t in trades:
    if t.side.value == "sell":
        # Find corresponding buy
        # Simplified: just use price difference
        pass
```

- `worst_trade` is a hardcoded placeholder: `min(-abs(t.qty * t.price * 0.01) ...)` — a fake 1% of notional, not a real loss.

**Consequence:** Every gate decision in `MEMORY.md` ("v5.6 passes all gates," "walk-forward 3/3 positive folds") was made on numbers that don't mean what the labels say. The 18 "rejected" strategies and the 1 "accepted" one were sorted by noise.

### 2. Sharpe is inflated ~5x for daily strategies

`metrics.py` hardcodes `periods_per_year = 8760` (hourly) for annualization *and* Sharpe, regardless of timeframe. Trend Rider v5.6 trades on **daily** bars (365/yr). Annualizing daily returns with √8760 instead of √365 inflates Sharpe by √(8760/365) ≈ **4.9x**. Any Sharpe-based gate was meaningless for the daily strategy.

### 3. Zero-cost backtests

`src/backtest/backtest_engine.py`:

```python
def __init__(self, ..., commission: float = 0.0,  # "Alpaca is commission-free"
             slippage: float = 0.001):
```

Alpaca crypto is **not** commission-free (~0.15–0.25%/side depending on tier/volume). The `MEMORY.md` claim "Fee sensitivity committed (BTC PF=1.50 at 2x fees)" is doubly void: (a) 2× of 0 is still 0, and (b) the PF being stress-tested is the broken one. The only realistic transaction cost in the whole engine is 0.1% slippage — and even that runs through broken PnL accounting.

### 4. Live engine is disconnected from strategy

`src/core/ea_core_engine.py`:

- Stage 7 — *"Generate strategy signals"* → `result['stages']['signal_generation'] = {'status': 'success'}` (does nothing).
- Stage 8 — `strategy_name = 'grid_trading_v1'` hardcoded (unrelated to Trend Rider, the only "validated" strategy).
- Stage 10 — Risk Governor validates a **fabricated** order: `qty=0.0026, price=77000`, not a signal-derived one.
- Stage 12 — *"actual submission happens in PipelineController"* — placeholder, no order placed here.
- Line 141-142: duplicated `return result` (dead code) — a small tell of how rushed this path is.

So the engine that was reported as "🟢 ACTIVE — Approved BTC" in `TEAM_ACTIVITY_REPORT.md` is running a validation theater on a hardcoded order, not executing the validated strategy.

### 5. The strategy has no demonstrated edge

- **15m EMA/SMA crossover** (`bots/ea_system/strategy_ema_rsi.py`, `freqtrade-config/SimpleSMA15m.py`): honest freqtrade backtest = **199 trades, 24.6% win, -0.59%, Sharpe -8.78, 18 consecutive losses.** This is the *one* result measured by an external, correct engine (freqtrade) — and it's clearly negative.
- **Daily SMA crossover (Trend Rider v5.6)**: only "passes" via the broken in-house metrics. Long-only trend-following in 2021–2026 crypto captures the bull market (beta). That's not a tradeable edge — it underperforms buy-and-hold after costs and whipsaws.
- 2%/3% fixed SL/TP with a 50–70 RSI gate is a textbook setup with negative expectancy after fees on liquid majors.

### 6. Effort went almost entirely into scaffolding, not edge

- **22** strategy variants (`trend_rider_v5` → `v5_6`, `mean_reversion_scalper` v1→v3, etc.) — iterating shapes, not validating expectancy.
- **3** pipeline controllers (`pipeline_controller.py`, `_v2.py`, `_old.py` — 36KB of dead `_old`).
- **3+** reporting/watchdog services (`ceo_reporting_watchdog`, `ceo_reporting_reliability_watchdog`, `reporting_watchdog_service`).
- **162** markdown docs: CEO reports, "capsules," "self-evolution," team activity reports. By the project's own `TEAM_ACTIVITY_REPORT.md`, the "team" is mostly disabled modules and documents, not running agents.
- Backtest engine "BROKEN — signature mismatch" and 5-agent pipeline "DISABLED" per the team report — i.e., the validation and decision layers weren't even running while orders were being placed.

This is the signature failure mode of an autonomous agent optimizing for *visible activity* (reports, commits, variants) instead of the one hard, unglamorous thing: a correct, cost-aware measurement of edge.

---

## The Best Way to Improve This Project

Ordered by leverage. Do them in order; do not skip to strategy work.

### Phase 0 — Stop trusting the current numbers (now)
- Treat **every** historical "PASS/FAIL/PF/Sharpe/win-rate" in the repo as invalid. Archive `MEMORY.md`'s validation claims as "measured with broken metrics — void."
- Keep paper-only. There is no validated reason to risk real money.

### Phase 1 — Build one correct measurement harness (highest leverage)
This is the actual product. Until it exists, nothing else matters.
1. **Replace `metrics.py` with real round-trip accounting:** match buys→sells (FIFO), compute per-trade PnL net of fees, then derive win rate (winners/total), profit factor (Σ wins / Σ |losses|), expectancy, avg win/loss, max consecutive losses, true max drawdown on the equity curve.
2. **Timeframe-aware annualization:** pass `periods_per_year` from the data's frequency (365 daily, 35040 for 15m, 8760 hourly). Fix Sharpe/Sortino/Calmar accordingly.
3. **Realistic costs:** model Alpaca crypto fees (start 0.20%/side) + slippage as parameters, not zero. Make "survives 2× fees" a real test.
4. **Honestly, just use freqtrade.** It already gave you the one trustworthy result in this whole repo. Standardize on it for backtesting and stop maintaining a bespoke, buggy engine. The in-house engine's reason to exist (Alpaca-native daily data) doesn't justify re-implementing PnL accounting wrong.
5. **Add a no-lookahead + cost regression test** so a strategy can't "pass" without paying realistic costs.

### Phase 2 — Re-validate honestly, expect to fail
- Re-run Trend Rider v5.6 and the top 2–3 variants through the corrected harness with fees.
- Benchmark **against buy-and-hold BTC/ETH**, not against zero. A trend strategy that doesn't beat HODL after costs has no reason to exist.
- Most likely outcome: nothing survives. Document that clearly — a true negative is a real result and saves you from losing money.

### Phase 3 — If (and only if) you continue, change the research approach
Simple TA crossovers on liquid majors are efficiently arbitraged; that well is dry. If you keep going, pick *one* thesis with a plausible structural edge and test it rigorously:
- **Cross-sectional momentum / relative strength** across a basket (rank many coins, long top), not single-asset crossovers.
- **Volatility-regime filters** (trade trend only when realized vol/ADX regime supports it; sit out chop) — directly addresses the 18-consecutive-loss whipsaw.
- **Carry/funding-rate** strategies (perp funding) — a genuine structural edge, though it needs a different venue than Alpaca spot.
- Whatever you pick: out-of-sample + walk-forward + cost-aware, measured by the Phase 1 harness, beating HODL net of fees. One strategy, validated deeply > 22 variants validated never.

### Phase 4 — Delete the theater
- Remove `pipeline_controller_old.py` (36KB dead), collapse `pipeline_controller` + `_v2` into one.
- Collapse the three watchdog/reporting services into one optional health check.
- Archive the 150+ status/CEO/capsule markdown files; keep one `README` + one `DECISIONS.md`.
- Either wire the 5-agent LLM pipeline to actually influence orders **or delete it** — a disabled `use_agents=False` path that's still described as a "team member" is pure overhead.
- Fix or delete `ea_core_engine.py`'s fake-order stages. A live engine that risk-checks a hardcoded order is worse than no engine.

### Phase 5 — Re-define "done"
Replace the elaborate gate ceremony with three honest bars, all measured by the Phase 1 harness, all **net of realistic fees**:
1. Beats buy-and-hold of the same assets out-of-sample.
2. Positive expectancy with profit factor > 1.3 on **correctly matched** round trips.
3. Survives walk-forward and 2× fees.

If a strategy can't clear those, it doesn't go to paper, let alone live.

---

## The One-Sentence Takeaway

This project failed not because the strategy was bad (though it was) but because **the scoreboard was broken and everyone trusted it** — so all the energy poured into agents, watchdogs, and 22 strategy variants was optimizing against noise. Fix the scoreboard first; almost everything else here can be deleted.
