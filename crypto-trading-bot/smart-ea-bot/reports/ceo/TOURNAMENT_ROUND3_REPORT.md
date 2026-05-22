# Strategy Tournament Report v3 — Smart EA Bot Company
**Date:** Friday, May 22, 2026 — 18:40 CEST  
**Branch:** `smart-ea-bot-foundation`  
**Commit:** `1c9aad9` — Tournament Round 3 complete
**Status:** 🔴 **NO BOT PASSED — PAPER TRADING BLOCKED**

---

## A. DATA RANGE USED

| Asset | Start | End | Duration | Bars |
|-------|-------|-----|----------|------|
| BTC/USD | 2026-02-21 | 2026-03-28 | ~5 weeks | 10,000 |
| ETH/USD | 2026-02-21 | 2026-03-28 | ~5 weeks | 10,000 |

**IMPORTANT LIMITATION:** Alpaca crypto paper data is limited to recent history. Despite requesting 365 days, the API returned only ~5 weeks. This is a significant constraint for proper strategy validation.

---

## B. NUMBER OF CANDLES PER ASSET

- **BTC/USD:** 10,000 five-minute candles
- **ETH/USD:** 10,000 five-minute candles
- **Total:** 20,000 candles

This represents approximately 35 trading days per asset — insufficient for robust statistical validation.

---

## C. BOTS IMPLEMENTED

| Bot | Status | Description |
|-----|--------|-------------|
| **MRS v3** | ✅ Implemented | RSI Divergence + VWAP Distance + Ranging Regime |
| **TPS v3** | ✅ Implemented | EMA 20/50/200 + Pullback Reclaim + Trend Strength |
| **Breakout Retest Bot** | ✅ Implemented | Range Detection + Breakout + Volume + Retest |
| **Volatility Squeeze Bot** | ✅ Implemented | Bollinger Squeeze + ATR Compression + Breakout |
| **Regime Filter** | ✅ Implemented | ADX + ATR + BB Width Classification |

---

## D. TOURNAMENT ROUND 3 TABLE

### ALL RESULTS (24 total)

| Rank | Bot | Asset | Fee | Trades | Return % | PF | Max DD | Status |
|------|-----|-------|-----|--------|----------|----|--------|--------|
| 1 | Volatility Bot | ETH | low_cost | 44 | -5.02% | 0.57 | 5.53% | ❌ |
| 2 | MRS v3 | ETH | low_cost | 249 | -12.20% | 0.55 | 12.77% | ❌ |
| 3 | Volatility Bot | BTC | low_cost | 40 | -10.13% | 0.32 | 10.59% | ❌ |
| 4 | Volatility Bot | ETH | normal | 44 | -11.22% | 0.32 | 11.22% | ❌ |
| 5 | MRS v3 | ETH | normal | 249 | -28.16% | 0.27 | 27.92% | ❌ |
| 6 | TPS v3 | ETH | low_cost | 3 | -0.41% | 0.26 | 0.55% | ❌ |
| 7 | MRS v3 | BTC | low_cost | 238 | -16.37% | 0.24 | 16.57% | ❌ |
| 8 | TPS v3 | ETH | normal | 3 | -0.57% | 0.16 | 0.68% | ❌ |
| 9 | Volatility Bot | BTC | normal | 40 | -20.41% | 0.12 | 20.41% | ❌ |
| 10 | Volatility Bot | ETH | high_cost | 44 | -23.64% | 0.10 | 23.64% | ❌ |
| 11 | MRS v3 | BTC | normal | 238 | -31.40% | 0.08 | 31.52% | ❌ |
| 12 | MRS v3 | ETH | high_cost | 249 | -60.07% | 0.08 | 59.72% | ❌ |
| 13 | TPS v3 | ETH | high_cost | 3 | -0.89% | 0.05 | 0.94% | ❌ |
| 14 | MRS v3 | BTC | high_cost | 238 | -61.47% | 0.02 | 61.48% | ❌ |
| 15 | Volatility Bot | BTC | high_cost | 40 | -40.98% | 0.01 | 40.98% | ❌ |
| 16-24 | TPS v3 / Breakout | All | All | 0 | 0.00% | 0.00 | 0.00% | ❌ |

**🥇 BEST PERFORMER:** Volatility Squeeze Bot on ETH/USD (low fees) — PF 0.57, still loses money.

**❌ PASSING:** 0 out of 24

---

## E. FEE SENSITIVITY RESULTS

| Bot | Asset | Normal PF | Low PF | High PF | Sensitivity |
|-----|-------|-----------|--------|---------|-------------|
| MRS v3 | BTC | 0.08 | 0.24 | 0.02 | HIGH — fails all scenarios |
| MRS v3 | ETH | 0.27 | 0.55 | 0.08 | HIGH — fails all scenarios |
| TPS v3 | ETH | 0.16 | 0.26 | 0.05 | HIGH — fails all scenarios |
| Volatility | BTC | 0.12 | 0.32 | 0.01 | HIGH — fails all scenarios |
| Volatility | ETH | 0.32 | 0.57 | 0.10 | HIGH — fails all scenarios |

**Finding:** No bot survives even 0.5x fees. Strategy logic lacks genuine edge.

---

## F. WALK-FORWARD RESULTS

**NOT PERFORMED** due to insufficient data range. Only ~5 weeks available.

**Recommendation:** Need longer data (1+ year) for proper walk-forward validation.

---

## G. PASS/FAIL PER BOT

| Bot | Pass/Fail | Trades (Best) | PF (Best) | Return (Best) | Reason |
|-----|-----------|---------------|-----------|---------------|--------|
| **MRS v3** | ❌ FAIL | 249 | 0.55 | -12.20% | RSI divergence doesn't capture edge in crypto 5m |
| **TPS v3** | ❌ FAIL | 3 | 0.26 | -0.41% | Too strict — almost no signals |
| **Breakout Bot** | ❌ FAIL | 0 | 0.00 | 0.00% | Retest conditions too strict for 5m timeframe |
| **Volatility Bot** | ❌ FAIL | 44 | 0.57 | -5.02% | Squeeze detected but direction random |

---

## H. PAPER-TRADING GATE

| Gate | Status |
|------|--------|
| Profit factor > 1.2 | ❌ FAILED (best: 0.57) |
| 100+ trades | ❌ FAILED (some pass but losing) |
| Max drawdown < 10% | ❌ FAILED (best PF is still losing) |
| Survives fees | ❌ FAILED |
| Walk-forward | ⚠️ INSUFFICIENT DATA |
| No lookahead bias | ✅ PASSED |
| QA tests | ✅ PASSED |
| Risk review | ⚠️ N/A (no winning bot) |
| Stable monthly | ⚠️ INSUFFICIENT DATA |
| Explainable logic | ✅ PASSED |

**PAPER TRADING GATE: ❌ BLOCKED**

---

## I. KEY FINDINGS

### What We've Learned

1. **Crypto 5m scalping is extremely difficult**
   - Mean reversion: Doesn't exist predictably at this granularity after fees
   - Trend pullback: Requires genuine momentum, not just proximity
   - Breakout/retest: Too slow to develop on 5m candles
   - Volatility squeeze: Can detect squeezes but direction is random

2. **Data limitation**
   - Alpaca crypto history is only ~5 weeks
   - Insufficient for robust statistical validation
   - Need alternative data source or longer timeframe

3. **Parameter tuning can't fix bad edge**
   - Even with 0.5x fees, best PF is 0.57 (still losing)
   - No amount of parameter tweaking will create edge where none exists

4. **Regime filter works but can't save bad strategies**
   - Correctly identifies trending vs ranging
   - But all tested strategies lose in all regimes

---

## J. NEXT AUTONOMOUS ACTION

### Option A: Longer Timeframe Approach
- **15m or 1h candles** instead of 5m
- Fewer trades, potentially better edge
- Test same strategies on 15m data

### Option B: Different Strategy Class
- **Momentum-based strategies** (not mean reversion)
- **Multi-timeframe strategies** (15m trend + 5m entry)
- **Order flow / volume profile** strategies
- **Machine learning models** (requires more data)

### Option C: Alternative Data Source
- **Binance data** (longer history available)
- **Coinbase data** (different exchange)
- **Synthetic data** for testing engine only (not strategy)

### Option D: Portfolio Approach
- **Multiple uncorrelated strategies**
- **Dynamic allocation** based on recent performance
- **Risk parity** rather than directional bets

**RECOMMENDATION:** Try 15m timeframe first. If still fails, explore momentum strategies or multi-timeframe approach.

---

## K. SAFETY CONFIRMATIONS

| Control | Status |
|---------|--------|
| **Trading** | 🔴 OFF |
| **Daemon** | 🔴 STOPPED |
| **ENTRY_LOCK** | 🟢 ACTIVE |
| **Paper trading** | 🔴 BLOCKED |
| **Live money** | 🔴 BLOCKED |
| **Code** | 🟢 Preserved in Git (`smart-ea-bot-foundation`) |
| **Data** | 🟢 Alpaca paper data used |
| **Risk limits** | 🟢 Hard-coded, never bypassed |

---

## L. EVIDENCE FILES

| File | Path |
|------|------|
| Tournament Report | `reports/backtests/tournament_v3_20260522_184008.md` |
| Raw Results JSON | `reports/backtests/tournament_v3_20260522_184008.json` |
| Failure Diagnosis | `reports/qa/BACKTEST_FAILURE_DIAGNOSIS.md` |
| Regime Filter | `core/regime_filter.py` |
| MRS v3 | `bots/mean_reversion_scalper_v3/strategy.py` |
| TPS v3 | `bots/trend_pullback_scalper_v3/strategy.py` |
| Breakout Bot | `bots/breakout_retest_bot/strategy.py` |
| Volatility Bot | `bots/volatility_breakout_bot/strategy.py` |

---

## M. CONCLUSION

**The Smart EA Bot Company has successfully identified that crypto 5m scalping does not have an edge with the tested approaches.**

This is not a failure — it is valuable information. We now know:
- Mean reversion scalping on 5m crypto doesn't work
- Trend pullback requires better momentum detection
- Breakout strategies need longer timeframes
- Volatility squeeze detects events but not direction

**The project continues. The search for edge continues.**

**Next autonomous action: Test 15m timeframe strategies and explore momentum-based approaches.**

---

🦊 **Jarvis — Junior CEO. Tournament Round 3 complete. 0 winners. Research continues autonomously.**
