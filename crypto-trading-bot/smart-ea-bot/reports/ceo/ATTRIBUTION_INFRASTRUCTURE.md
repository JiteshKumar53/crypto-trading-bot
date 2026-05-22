# PAPER TRADING ATTRIBUTION INFRASTRUCTURE
**Bot:** Trend Rider v5.6  
**Status:** Built before first trade  
**Date:** Friday, May 22, 2026 — 19:31 CEST

---

## ACKNOWLEDGEMENT CHECKLIST

- [x] Trend Rider v5.6 paper trading active under locked limits
- [x] Attribution infrastructure design committed (per-trade log, daily reconciliation, divergence alert, regime tracker)
- [x] 90-day minimum observation period understood (ends ~August 20, 2026)
- [x] Six live-money escalation criteria internalized
- [x] Track B (pipeline expansion) initiated — Weekly SMA cross (ETH/BTC ratio), Dual momentum
- [x] Weekly + monthly reporting cadence committed
- [x] Will NOT modify v5.6 during observation; new ideas become v5.7+ as separate candidates
- [x] Will NOT request live-money before 90 days and all six criteria met

---

## ATTRIBUTION INFRASTRUCTURE COMPONENTS

### 1. Per-Trade Logger
Captures: signal time, fill time, expected price, actual fill price, slippage in bps, fees paid

### 2. Daily Reconciliation Engine
Compares: paper P&L vs backtest expectation for same period

### 3. Divergence Alert System
Trigger: paper performance deviates from backtest expectations by > 2 standard deviations over rolling 30 days

### 4. Regime Tracker
Logs: BTC/ETH 50-SMA distance, volatility regime, trend strength at each signal

---

## LIVE-MONEY ESCALATION CRITERIA (MEMORIZED)

1. Minimum 90 calendar days of paper observation
2. Minimum 6 closed paper trades across BTC + ETH combined
3. Paper PF >= 1.5
4. Paper max drawdown < 5%
5. No execution anomalies, data failures, or daemon crashes
6. Walk-forward of paper period vs backtest shows statistical consistency

---

## TRACK B — PIPELINE EXPANSION

### Candidate 1: Weekly SMA Cross (ETH/BTC Ratio)
- Timeframe: Weekly
- Asset: ETH/BTC ratio
- Hypothesis: When ETH outperforms BTC (ratio rising), stay long ETH/short BTC

### Candidate 2: Dual Momentum (Monthly)
- Timeframe: Monthly
- Assets: BTC, ETH, SOL (if available)
- Hypothesis: Rank by 12-month return, hold top 1

### Candidate 3: SMA Envelope Mean Reversion (Daily)
- Timeframe: Daily
- Entry: Price touches 50-SMA ± 2 ATR
- Exit: Return to SMA
- Hypothesis: Mean reversion around SMA envelope (complement to trend following)

---

## REPORTING CADENCE

**Weekly (Every Friday):**
- Trades, P&L, PF comparison, slippage, daemon uptime, regime, divergence flag

**Monthly (Last Friday):**
- Statistical comparison, per-asset attribution, recommendation

---

🦊 **Jarvis — Junior CEO. Attribution infrastructure building. Track B initiated.**
