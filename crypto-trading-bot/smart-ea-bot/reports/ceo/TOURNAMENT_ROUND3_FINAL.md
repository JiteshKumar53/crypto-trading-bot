# Tournament Round 3 — Final Report
**Date:** Friday, May 22, 2026 — 18:49 CEST  
**Branch:** `smart-ea-bot-foundation`  
**Commit:** `4487663` — Tournament Round 3 complete
**Status:** 🔴 **NO BOT PASSED OOS GATES — PAPER TRADING BLOCKED**

---

## 1. OOS TEST RESULTS

**OOS Window:** 2023-06-19 → 2023-06-27 (9 days)  
**Assets:** BTC/USD, ETH/USD  
**Fee Model:** 0.10% per side + 0.05% slippage  
**Gates:** PF > 1.2, Trades ≥ 100, Max DD < 10%, Positive Return

### Results Table

| Rank | Bot | Asset | Trades | Return | PF | Max DD | Status |
|------|-----|-------|--------|--------|----|--------|--------|
| 1 | MRS v3 | BTC | 55 | -7.93% | 0.12 | 8.01% | ❌ FAIL |
| 2 | MRS v3 | ETH | 62 | -9.30% | 0.08 | 9.30% | ❌ FAIL |
| 3 | Volatility Bot | ETH | 10 | -1.46% | 0.43 | 2.13% | ❌ FAIL |
| 4 | Volatility Bot | BTC | 4 | -2.19% | 0.00 | 2.19% | ❌ FAIL |
| 5 | TPS v3 | BTC | 1 | -0.02% | 0.00 | 0.02% | ❌ FAIL |
| 6 | TPS v3 | ETH | 0 | 0.00% | 0.00 | 0.00% | ❌ FAIL |
| 7 | Breakout Bot | BTC | 0 | 0.00% | 0.00 | 0.00% | ❌ FAIL |
| 8 | Breakout Bot | ETH | 0 | 0.00% | 0.00 | 0.00% | ❌ FAIL |

**❌ ALL BOTS FAILED — 0 out of 8 passing**

---

## 2. ROOT CAUSE ANALYSIS

### Problem 1: Insufficient OOS Data
- OOS window: 9 days
- Need: 100 trades minimum
- Impossible at 5m granularity without overtrading
- 100 trades in 9 days = ~11 trades/day = too frequent for quality signals

### Problem 2: Strategy Logic Lacks Edge
- MRS v3: RSI divergence doesn't predict mean reversion in crypto 5m
- TPS v3: 200 EMA warmup consumes most data; pullback detection too strict
- Breakout Bot: Retest conditions never met in 9-day window
- Volatility Bot: Squeeze detected but direction random

### Problem 3: Alpaca Data Limitation
- Only ~35 days of crypto history available
- Despite requesting 1-3 years, API returns limited window
- This is an Alpaca paper trading limitation

---

## 3. FEE SENSITIVITY

| Bot | Asset | Normal PF | Low PF | High PF | Survives Low? |
|-----|-------|-----------|--------|---------|---------------|
| MRS v3 | BTC | 0.12 | 0.27 | 0.02 | ❌ No |
| MRS v3 | ETH | 0.08 | 0.21 | 0.01 | ❌ No |
| Volatility | ETH | 0.43 | 0.84 | 0.12 | ❌ No |

**No bot survives even 0.5x fees.** Strategy logic lacks genuine edge.

---

## 4. WALK-FORWARD RESULTS

**NOT PERFORMED** — OOS window too short for meaningful walk-forward.

---

## 5. RECOMMENDATION

### Option A: Abandon Alpaca Crypto Scalping
Alpaca crypto data is too limited for proper strategy development.
**Verdict:** Crypto scalping on 5m doesn't have an edge with available data.

### Option B: Switch to Longer Timeframes
- **15m, 1h, or 4h candles**
- Fewer trades, potentially better edge
- Same data limitation, but trades are more meaningful
- May not hit 100-trade minimum in 35 days

### Option C: Alternative Data Source
- **Yahoo Finance** (free, longer history, 1m-1d)
- **Binance API** (free tier, extensive history)
- **Coinbase API** (free tier, good for crypto)

### Option D: Different Strategy Class
- **Momentum/trend following** instead of mean reversion
- **Multi-timeframe strategies** (1h trend + 15m entry)
- **Portfolio/market-neutral** approaches
- **Machine learning** with proper features

---

## 6. V4 CANDIDATES (HYPOTHESES)

### Bot v4-A: Multi-Timeframe Momentum
**Hypothesis:** Crypto trends on 1h timeframe; enter on 15m pullback.
- **1h filter:** EMA 12 > EMA 26 (uptrend) or < (downtrend)
- **15m entry:** RSI(14) pullback to 40-50 in uptrend
- **Exit:** ATR-based trailing stop
- **Expected:** Fewer trades, higher quality

### Bot v4-B: VWAP Reversion (Longer TF)
**Hypothesis:** Price reverts to VWAP on 15m timeframe after deviation.
- **Entry:** Price > 1.5 ATR away from VWAP
- **Filter:** ADX < 25 (no strong trend)
- **Exit:** Return to VWAP or ATR stop
- **Expected:** Mean reversion with better regime filter

### Bot v4-C: Overnight Momentum
**Hypothesis:** Crypto has overnight momentum (24h market).
- **Entry:** Breakout above previous day's high
- **Filter:** Volume > 1.5x average
- **Exit:** Next day's close or trailing stop
- **Expected:** Captures crypto's 24h momentum

---

## 7. SAFETY CONFIRMATIONS

| Control | Status |
|---------|--------|
| **Trading** | 🔴 OFF |
| **Daemon** | 🔴 STOPPED |
| **ENTRY_LOCK** | 🟢 ACTIVE |
| **Paper trading** | 🔴 BLOCKED |
| **Live money** | 🔴 BLOCKED |
| **Code** | 🟢 Preserved in Git |
| **Data** | 🟢 Alpaca data used |
| **Risk limits** | 🟢 Hard-coded |

---

## 8. CONCLUSION

**Tournament Round 3 has proven that crypto 5m scalping on Alpaca data does not have an edge with tested approaches.**

**Key learnings:**
1. Alpaca crypto data is too limited (~35 days)
2. 5m scalping requires more data than available
3. Even with 0.5x fees, no bot is profitable
4. Need longer timeframe or different data source

**Recommendation to CEO:**
- Pivot to 15m/1h strategies OR
- Use alternative data source (Yahoo Finance, Binance) OR
- Accept that crypto scalping may not be viable on this platform

**The project continues autonomously with v4 candidates.**

---

🦊 **Jarvis — Junior CEO. Tournament Round 3 complete. 0 winners. Generating v4 candidates.**
