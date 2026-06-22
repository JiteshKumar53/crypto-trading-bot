# Strategy Tournament + Validation Gate — Results (broadened)

**Date:** 2026-06-20
**Companion to:** `DEEP_ANALYSIS_2026-06-20.md`, `BACKTEST_RESULTS_2026-06-20.md`
**Run with:** `python3 crypto-trading-bot/scripts/strategy_tournament.py`
**Data:** Binance daily (resampled from 15m), BTC/USDT + ETH/USDT, 2024→2026
**Costs:** 0.10%/side commission + 0.05%/side slippage
**Method:** corrected metrics + buy-and-hold benchmark + 3-fold walk-forward, every result through `src/strategy_gate.py`.

## The upgrade

- **`src/strategy_gate.py`** — reusable validation gate. Eligible to trade only if it passes **all** gates: beats buy-and-hold net of fees, ≥10 closed trades, profit factor ≥1.30, positive expectancy, max drawdown ≤25%, ≥60% walk-forward folds positive.
- **`scripts/strategy_tournament.py`** — now tests a **broad** set of structurally different approaches, not just the repo's three:
  - **Single-asset:** trend+regime, Donchian breakout, RSI mean-reversion, **time-series momentum (TSMOM)**, **MACD**, **Bollinger breakout**, plus **volatility-sized** variants of the breakout/momentum strategies.
  - **Portfolio / multi-asset (genuinely different):** **dual-momentum rotation** (BTC/ETH/cash) and **BTC↔ETH relative-strength rotation**, benchmarked against a **50/50 BTC+ETH hold**.

## Single-asset results

| Strategy | Asset | Return | PF | Max DD | Trades | Walk-fwd | Verdict |
|----------|-------|-------:|---:|-------:|-------:|:--------:|:-------:|
| **Donchian (vol-sized)** | **BTC** | **+100.3%** | **2.22** | **24.5%** | 15 | + + − | **✓ PASS** |
| Donchian | BTC | +94.2% | 2.08 | 27.3% | 15 | + + − | ✗ (DD) |
| TSMOM-90 (vol-sized) | BTC | +34.7% | 2.68 | 16.6% | 13 | − + − | ✗ (< HODL, WF) |
| TSMOM-90 | BTC | +32.4% | 2.47 | 18.2% | 13 | − + − | ✗ (< HODL, WF) |
| MACD | BTC | +36.0% | 1.29 | 35.3% | 34 | + + − | ✗ |
| RSI mean-rev | BTC | +12.0% | 1.86 | 27.1% | 5 | + + − | ✗ |
| Bollinger breakout | BTC | +4.0% | 1.04 | 35.0% | 18 | + + − | ✗ |
| Trend+Regime | BTC | −35.6% | 0.22 | 35.6% | 7 | − + − | ✗ |
| Bollinger breakout | ETH | +43.0% | 1.43 | 36.3% | 16 | + + − | ✗ (DD, WF) |
| TSMOM-90 | ETH | +27.2% | 1.96 | 42.2% | 11 | − + − | ✗ |
| *(all other ETH)* | ETH | negative | <1 | high | — | — | ✗ |

Buy & hold (net): **BTC +80.5%, ETH +0.8%.**

## Portfolio rotation results

| Strategy | Return | Sharpe | Max DD | vs 50/50 hold | Verdict |
|----------|-------:|-------:|-------:|:--:|:-------:|
| **Dual-Momentum (BTC/ETH/cash)** | **+69.8%** | 0.74 | 40.9% | beats (hold = −9.8%) | ✗ (DD only) |
| Ratio Rotation (BTC↔ETH) | +1.2% | 0.27 | 54.9% | beats | ✗ |

50/50 BTC+ETH hold (net): **−9.8%, maxDD 54.6%.**

## Verdict: the door was worth opening

1. **First strategy to ever pass the gate: volatility-sized Donchian on BTC.** +100.3% (vs HODL +80.5%), PF 2.22, and the vol-targeting pulled max drawdown to 24.5% — under the cap — *while improving* return and profit factor versus plain Donchian. This is now the project's first strategy **eligible to paper-trade**.
2. **Dual-momentum rotation is the most exciting lead.** It returned **+69.8% while a 50/50 hold lost −9.8%** — an ~80-point spread — by rotating into the stronger asset and to cash in downturns. It fails the gate *only* on drawdown (40.9%). Apply the same volatility-targeting that fixed Donchian and it is a strong candidate. This is exactly the kind of structural (cross-sectional/relative-strength) edge that single-asset TA lacks.
3. **The dry well is confirmed for the rest.** Trend/MACD/RSI/Bollinger on single majors still don't clear the bar after costs — but breadth surfaced the two ideas that do carry real signal.

## Next experiments (now there are several doors open)

1. **Promote vol-sized BTC Donchian** to the paper pipeline behind the gate (once Alpaca egress is opened).
2. **Vol-target the dual-momentum rotation** (add a cash/defensive sleeve when realized vol is high) to bring drawdown under 25% — likely the strongest overall strategy.
3. **Add more assets** (SOL, and a wider basket) — cross-sectional momentum strengthens with more candidates; 2 assets is the minimum case and it already beat holding.

## Reproduce

```bash
cd crypto-trading-bot
python3 scripts/strategy_tournament.py
```
Machine-readable output: `freqtrade_data/tournament_results.json`.
