# Strategy Tournament + Validation Gate — Results

**Date:** 2026-06-20
**Companion to:** `DEEP_ANALYSIS_2026-06-20.md`, `BACKTEST_RESULTS_2026-06-20.md`
**Run with:** `python3 crypto-trading-bot/scripts/strategy_tournament.py`
**Data:** Binance daily (resampled from 15m), BTC/USDT + ETH/USDT, 2024→2026
**Costs:** 0.10%/side commission + 0.05%/side slippage
**Method:** corrected metrics + buy-and-hold benchmark + 3-fold walk-forward, every result run through `src/strategy_gate.py`.

## The upgrade

This replaces the old "trust the (broken) scoreboard" workflow with an enforceable discipline:

- **`src/strategy_gate.py`** — a reusable, importable validation gate. A strategy is eligible to trade **only if it passes every gate**: beats buy-and-hold net of fees, ≥10 closed trades, profit factor ≥1.30, positive expectancy, max drawdown ≤25%, and ≥60% of walk-forward folds positive.
- **`scripts/strategy_tournament.py`** — runs three *proven* strategy archetypes (trend+regime filter, Donchian breakout, RSI mean-reversion) plus a buy-and-hold benchmark, on daily data (15m is already proven to be destroyed by fees), with walk-forward, and prints a PASS/FAIL with a reason for every gate.

The live pipeline should call `validate_strategy(...)` and **refuse to size any strategy that does not return `passed=True`.**

## Results

| Strategy | Asset | Return | PF | Max DD | Trades | Win% | Walk-fwd | Verdict |
|----------|-------|-------:|---:|-------:|-------:|-----:|:--------:|:-------:|
| Trend+Regime | BTC | −35.6% | 0.22 | 35.6% | 7 | 14% | − + − | ✗ FAIL |
| **Donchian breakout** | BTC | **+94.2%** | **2.08** | 27.3% | 15 | 33% | + + − | ✗ FAIL (DD 27.3% > 25%) |
| RSI mean-rev | BTC | +12.0% | 1.86 | 27.1% | 5 | 40% | + + − | ✗ FAIL (< HODL 80.5%) |
| Trend+Regime | ETH | −11.6% | 0.57 | 33.9% | 4 | 25% | − + − | ✗ FAIL |
| Donchian breakout | ETH | −3.2% | 0.98 | 52.1% | 18 | 39% | − + − | ✗ FAIL |
| RSI mean-rev | ETH | −18.8% | 0.51 | 46.0% | 6 | 50% | + − − | ✗ FAIL |

**Buy & hold (net):** BTC +80.5%, ETH +0.8%.

## Verdict: **NONE eligible to trade** — but one genuine near-miss

- **BTC Donchian breakout is the one promising candidate.** It is the *only* strategy that both **beat buy-and-hold** (+94.2% vs +80.5%) **and** cleared the edge bar (PF 2.08, 2/3 walk-forward folds positive). It failed on a single gate: max drawdown 27.3% vs the 25% cap. That is a tractable, honest near-miss — addressable with position sizing or a volatility-scaled stop, **not** with another rewrite.
- Everything else fails decisively: trend-following and mean-reversion on these assets/period do **not** beat holding after costs. This confirms the deep analysis: simple TA on liquid majors has little durable edge.
- ETH is brutal for all strategies — its choppy, net-flat period (HODL +0.8%) punishes every approach.

## What this changes for the project

1. **The gate is now the law.** No more strategies promoted on noise. The 18 historical "rejections" and 1 "acceptance" were sorted by broken metrics; this gate sorts by reality.
2. **A concrete next experiment exists** (and only one, deliberately): take BTC Donchian — the near-miss — and add volatility-scaled position sizing / ATR stop to pull max drawdown under 25% *without* curve-fitting, re-run the tournament, and see if it passes honestly. If it does, it becomes the first strategy ever eligible to paper-trade through the gate.
3. **Discipline over breadth.** One validated strategy beats twenty unvalidated variants. The tournament + gate is the machine that enforces that.

## Reproduce

```bash
cd crypto-trading-bot
python3 scripts/strategy_tournament.py   # prints the table + gate detail
```
Machine-readable output: `freqtrade_data/tournament_results.json`.
