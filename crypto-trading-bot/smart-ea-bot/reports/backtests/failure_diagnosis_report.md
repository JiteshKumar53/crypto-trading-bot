# Backtest Failure Diagnosis Report

**Date:** 2026-05-22
**Prepared By:** Jarvis (Junior CEO) — Autonomous Decision
**Status:** TRADING OFF, DAEMON STOPPED, ENTRY_LOCK ACTIVE

---

## A. MRS (Mean Reversion Scalper) — Catastrophic Failure

| Metric | BTC/USD | ETH/USD |
|--------|---------|---------|
| **Data Range** | 2026-02-21 to 2026-03-28 (35 days) | Same |
| **Candles** | 10,000 (5-min) | 10,000 (5-min) |
| **Total Trades** | **0** | **0** |
| **Total Return** | 0.00% | 0.00% |
| **Win Rate** | N/A | N/A |
| **Profit Factor** | N/A | N/A |
| **Max Drawdown** | 0.00% | 0.00% |
| **Fees/Slippage** | N/A | N/A |

### Why MRS Generated ZERO Trades

The MRS entry rules are mutually contradictory:

**Long entry requires:**
1. RSI(14) < 30 (oversold)
2. Close price > SMA(20) (not in strong downtrend)

**Short entry requires:**
1. RSI(14) > 70 (overbought)
2. Close price < SMA(20) (not in strong uptrend)

**The Problem:** These conditions are almost **mutually exclusive** in trending crypto markets.

- If RSI < 30, price is typically FALLING → price is usually BELOW SMA(20), not above.
- If RSI > 70, price is typically RISING → price is usually ABOVE SMA(20), not below.

**Data Proof:**
- BTC/USD: 1,242 RSI < 30 bars, 1,117 RSI > 70 bars — but ZERO satisfied both conditions.
- ETH/USD: 1,180 RSI < 30 bars, 1,178 RSI > 70 bars — same result.

**Classification:** A + J (Bad strategy logic + engine did its job correctly)

The backtest engine ran correctly. The strategy was logically broken from the start.

---

## B. TPS (Trend Pullback Scalper) — Catastrophic Failure

| Metric | BTC/USD | ETH/USD |
|--------|---------|---------|
| **Data Range** | 2026-02-21 to 2026-03-28 (35 days) | Same |
| **Candles** | 10,000 (5-min) | 10,000 (5-min) |
| **Total Trades** | 522 | 494 |
| **Total Return** | **-42.35%** | **-29.38%** |
| **Win Rate** | **20.5%** | **26.9%** |
| **Profit Factor** | **0.22** | **0.30** |
| **Max Drawdown** | **42.5%** | **29.45%** |
| **Avg Win** | +0.11% | +0.09% |
| **Avg Loss** | -0.13% | -0.12% |
| **Worst Losing Streak** | 17 | 22 |
| **Fees/Slippage** | 0.52% | 0.49% |

### Exit Breakdown (BTC/USD TPS)

| Exit Reason | Count | % of Trades |
|-------------|-------|-------------|
| Time Stop | 418 | 80.1% |
| Stop Loss | 77 | 14.8% |
| Take Profit | 27 | 5.2% |

### Root Cause Analysis

**1. The Pullback Definition Is Broken**

```python
pullback_buy = current_price <= ema20 * 1.002 and current_price >= ema20 * 0.998
pullback_sell = current_price >= ema20 * 0.998 and current_price <= ema20 * 1.002
```

This defines "pullback" as price being within ±0.2% of EMA20. But in a strong uptrend, price is *already* near EMA20 much of the time. The signal triggers almost every time price touches EMA20, even when the trend has just started and there's no real "pullback" to capture.

**2. Stop-Loss Is Arbitrary and Too Wide**

SL is set to `ema50 * 0.99` (1% below EMA50). But:
- EMA50 can be far from entry price in strong trends
- In volatile crypto, price can easily wick 1% against you
- SL distance varies wildly based on EMA spacing, not actual market structure

**3. Take-Profit Is Too Far vs Stop-Loss Too Wide**

Risk/reward is inverted. TP = +0.8% from entry, but the actual win rate is 20%. Expected value per trade is deeply negative:

```
EV = (0.205 * +0.11%) + (0.795 * -0.13%) = +0.0225% - 0.103% = -0.08% per trade
With 522 trades: -0.08% * 522 = -41.76% (matches actual -42.35%)
```

**4. Overtrading — No Real Regime Filter**

The strategy fires constantly in any market. During the 35-day period, it averaged 15 trades/day. Most of these are false signals because:
- No ADX or trend strength filter
- No volume confirmation
- "Pullback" zone is too wide
- RSI filter (40-60) is too permissive — it lets in almost everything

**5. Time Stop Dominates (80% of exits)**

Price doesn't reach TP or SL within 20 minutes, so the time stop kicks in. This means:
- The entry signal had no edge
- Trades were random entries that drifted
- Time stop = random close at an arbitrary time

**Classification:** A + C + E + I (Bad strategy logic + Bad market regime handling + Too many false signals + Overtrading)

The engine ran correctly. The strategy logic is fundamentally flawed.

---

## C. Engine Verification

| Check | Result |
|-------|--------|
| No look-ahead bias | ✅ Signal at bar t, execution at bar t+1 |
| Fees included | ✅ 0.10% per side |
| Slippage included | ✅ 0.05% |
| Position sizing | ✅ 0.25% risk model |
| OHLC consistency | ✅ Verified on data |
| Duplicate timestamps | ✅ None found |

**Verdict:** The backtest engine is **functionally correct**. The failures are **strategy failures**, not engine bugs.

---

## D. Summary Classification Table

| Bot | Classification | Primary Cause | Secondary Cause |
|-----|----------------|---------------|-----------------|
| MRS | **A** (Bad logic) | Entry rules are mutually contradictory | No regime filter |
| TPS | **A + E + I** (Bad logic + False signals + Overtrading) | Pullback definition too loose | No trend strength filter |

**No engine bug.** No data corruption. Strategies were bad ideas from spec to code.

---

## E. Lessons

1. **Never trust a strategy without signal analysis.** Before backtesting, count how many signals the rules would generate on real data.
2. **Mutually contradictory conditions kill strategies silently.** Zero trades looks like no data — it's actually a logic bug.
3. **"Pullback" needs precise definition.** ±0.2% of EMA is not a pullback — it's just noise.
4. **Win rate < 30% with small wins means the signal has zero edge.** Expected value math doesn't lie.
5. **80% time-stop exits = strategy has no actual entry edge.** You're just entering random positions and closing them later.

---

**Next Action:** Design 6+ new bot candidates with regime-aware, evidence-based rules. No paper trading until profit factor > 1.2.

**Trading Status:** OFF. Confirmed. No exceptions.
