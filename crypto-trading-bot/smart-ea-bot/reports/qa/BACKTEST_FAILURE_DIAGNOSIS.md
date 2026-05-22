# Backtest Failure Diagnosis — Smart EA Bot Company
**Date:** Friday, May 22, 2026 — 18:29 CEST  
**Diagnosed By:** Backtest Agent + Strategy Research Agent (operated by Jarvis)
**Status:** CRITICAL — All strategies failed. Paper trading BLOCKED.

---

## 1. BACKTEST SUMMARY

| Bot | Asset | Trades | Return | Win Rate | PF | Max DD | Pass |
|-----|-------|--------|--------|----------|-----|--------|------|
| **Mean Reversion Scalper (MRS)** | BTC/USD | **0** | 0% | 0% | 0 | 0% | ❌ |
| **Mean Reversion Scalper (MRS)** | ETH/USD | **0** | 0% | 0% | 0 | 0% | ❌ |
| **Trend Pullback Scalper (TPS)** | BTC/USD | **523** | -42.35% | **0.21%** | 0.22 | 42.5% | ❌ |
| **Trend Pullback Scalper (TPS)** | ETH/USD | **493** | -29.38% | **0.27%** | 0.30 | 29.45% | ❌ |

**Data Range:** 2026-02-21 to 2026-03-28 (~5 weeks)  
**Candles:** 10,000 per asset (5m bars)  
**Fees:** 0.10% per side + 0.05% slippage  
**Bars with issues:** 1 gap (100 min, within tolerance)

---

## 2. ROOT CAUSE ANALYSIS

### Bot 1 — Mean Reversion Scalper (MRS)

**Failure Type:** **B + C + D** (Bad Parameters + Bad Market Regime + Overstrict Filters)

**Diagnosis:**
| Issue | Evidence | Classification |
|-------|----------|----------------|
| **0 trades** | No entries triggered across 10,000 bars | B (parameters) |
| RSI < 30 too rare | Crypto RSI rarely reaches 30 in 5m | C (market regime) |
| ATR filter >= 0.3% | May reject bars unnecessarily | B (parameters) |
| Previous RSI constraint | "prev RSI < 35" adds unnecessary filter | B (parameters) |

**Conclusion:** MRS never fired because entry conditions are **far too strict** for crypto. In a 5m timeframe on crypto, RSI rarely hits < 30 or > 70. The strategy is designed for slower markets.

**Fix Required:**
- Widen RSI thresholds to < 40 / > 60
- Add RSI divergence (price lower, RSI higher)
- Remove previous-bar RSI constraint
- Add Bollinger Band %B instead of raw RSI

---

### Bot 2 — Trend Pullback Scalper (TPS)

**Failure Type:** **A + E + F + G + I** (Bad Strategy Logic + False Signals + Too Tight SL + Too Small TP + Overtrading)

**Diagnosis:**
| Issue | Evidence | Classification |
|-------|----------|----------------|
| **523 trades in 5 weeks** | ~105 trades/week = overtrading | I (overtrading) |
| **0.21% win rate** | ~1 win per 500 trades | A (bad logic) |
| **avg win 0.11%, avg loss -0.13%** | Losses bigger than wins | G (TP too small) |
| **fees = 0.52% of equity** | 500 trades × fees = death by a thousand cuts | D (fee impact) |
| **SL = EMA distance** | When price far from EMA50, SL is massive | F (SL too loose) |
| **TP = 1.5%** | Price rarely reaches 1.5% in 20 minutes | G (TP too optimistic) |

**Conclusion:** TPS fires on **almost every bar** because entry criteria are too loose (just "near EMA20"). It enters at every minor fluctuation. Most trades hit stop-loss or time-stop. The 0.21% win rate means **99.79% of trades lose**.

**Fix Required:**
- Require price to **cross** EMA, not just be near it
- Use ATR-based SL/TP (not fixed percentages)
- Add ADX > 25 trend filter (reject chop)
- Add minimum pullback distance (e.g., price must move X% from EMA)
- Reduce trade frequency with cooldown

---

## 3. CLASSIFICATION SUMMARY

| Failure | MRS | TPS | Explanation |
|---------|-----|-----|-------------|
| A. Bad strategy logic | — | ✅ | TPS fires on every bar |
| B. Bad parameters | ✅ | — | MRS thresholds too strict |
| C. Bad market regime | ✅ | — | Crypto rarely oversold on 5m |
| D. Fee impact | — | ✅ | 0.52% fees ate equity |
| E. False signals | — | ✅ | TPS 99.79% false rate |
| F. SL too tight/loose | — | ✅ | TPS SL too loose |
| G. TP too small | — | ✅ | 1.5% TP rarely reached |
| H. Trend filter missing | — | ✅ | No ADX, no chop filter |
| I. Overtrading | — | ✅ | 523 trades in 5 weeks |

---

## 4. KEY LESSON

**The first two strategies were not designed for crypto 5m behavior.**

- MRS was too conservative — never fired.
- TPS was too aggressive — fired constantly and lost.
- Neither had a **regime filter** to avoid bad conditions.
- Neither had **proper risk/reward ratios**.

**Before creating more scalping bots, we must build a regime filter.**

---

## 5. RECOMMENDATION

**DO NOT PAPER TRADE MRS or TPS v1.**

**DO build:**
1. Regime filter (before any new bot)
2. MRS v2 (wider thresholds, divergence-based)
3. TPS v2 (ADX trend filter, ATR SL/TP)
4. Breakout bot (range-based, retest confirmation)
5. Volatility squeeze bot
6. Ensemble selector (regime + strategy agreement)

---

🦊 **Backtest Agent + Strategy Research Agent (operated by Jarvis)**
