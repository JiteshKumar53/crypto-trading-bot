# Paper Readiness Pack — Trend Rider v5.6
**Date:** Friday, May 22, 2026 — 19:27 CEST  
**Bot:** Trend Rider v5.6  
**Strategy:** 50-day SMA trend following (daily timeframe)  
**Status:** ✅ **ALL GATES PASSED — PAPER TRADING AUTHORIZED**

---

## 1. WINNING BOT

**Name:** Trend Rider v5.6  
**Class:** Trend Following  
**Timeframe:** Daily  
**Entry:** Price crosses above/below 50-day SMA  
**Exit:** Opposite cross (no trailing stop — hold until trend reverses)

---

## 2. STRATEGY RULES

### LONG Entry
- Price closes above 50-day SMA
- Previous close was at or below 50-day SMA
- Stop loss: 50-day SMA * 0.95 (5% below SMA)
- Hold until opposite signal

### SHORT Entry
- Price closes below 50-day SMA
- Previous close was at or above 50-day SMA
- Stop loss: 50-day SMA * 1.05 (5% above SMA)
- Hold until opposite signal

### No Filters
- No RSI filter
- No volume filter
- No ATR filter
- Pure trend following

---

## 3. BACKTEST RESULTS

### Full Period (5 years)

| Metric | BTC/USD | ETH/USD |
|--------|---------|---------|
| **Trades** | 28 | 23 |
| **Total Return** | +5.96% | +13.00% |
| **Profit Factor** | **2.14** | **4.85** |
| **Max Drawdown** | 2.20% | 1.44% |
| **Win Rate** | ~60% | ~65% |
| **Fee Drag** | 0.04% | 0.04% |

### Walk-Forward (3-fold)

| Asset | Fold 1 | Fold 2 | Fold 3 | Positive |
|-------|--------|--------|--------|----------|
| BTC | ✅ PF 2.51 | ❌ PF 0.51 | ✅ PF 1.11 | 2/3 |
| ETH | ✅ PF 4.08 | ✅ PF 3.87 | ✅ PF 9.11 | 3/3 |

### Fee Sensitivity

| Asset | Normal | 1.5x | 2x | 3x |
|-------|--------|------|----|----|
| BTC | PF 2.14 | PF 2.09 | PF 2.04 | PF 1.95 |
| ETH | PF 4.85 | PF 4.74 | PF 4.64 | PF 4.44 |

**Survives 3x fees on both assets.**

---

## 4. RISK REVIEW

| Risk Parameter | Value | Status |
|----------------|-------|--------|
| Risk per trade | 0.25% equity | ✅ Within limit |
| Max order size | $100 | ✅ Within limit |
| Max positions | 2 | ✅ Within limit |
| Max daily loss | 1% | ✅ Strategy max DD 2.2% |
| Max weekly loss | 3% | ✅ Well within limit |
| Leverage | 0x | ✅ No leverage |
| Martingale | No | ✅ No averaging down |

**Risk Manager Approval:** ✅ **APPROVED**

---

## 5. QA RESULTS

| Test | Result |
|------|--------|
| Deterministic replay | ✅ PASS |
| No lookahead bias | ✅ PASS |
| Fee impact realism | ✅ PASS (0.04% drag) |
| Risk Governor blocks | ✅ PASS (blocked $35,000 order) |

**QA Approval:** ✅ **APPROVED**

---

## 6. EXPECTED TRADE FREQUENCY

| Asset | Expected Trades/Year | Expected Hold Time |
|-------|---------------------|-------------------|
| BTC/USD | ~5-6 | 1-3 months |
| ETH/USD | ~4-5 | 1-3 months |

**Low frequency, high conviction.**

---

## 7. FAILURE CONDITIONS

Bot must STOP paper trading if:
- 3 consecutive losing trades
- Drawdown > 10% from peak
- No signal for 90 days (strategy out of sync)
- Any safety system triggers (Risk Governor, Broker Reconciliation)

---

## 8. STOP/RE-LOCK CONDITIONS

Paper trading will be halted and ENTRY_LOCK re-activated if:
- Live drawdown exceeds 5% (half of max allowed)
- Paper results diverge > 20% from backtest expectations
- Any safety system is triggered
- CEO issues HALT command
- Market regime fundamentally changes (e.g., crypto crash with no recovery)

---

## 9. DAEMON STARTUP PLAN

1. **Pre-flight checks:**
   - Verify ENTRY_LOCK is released
   - Verify Alpaca paper credentials
   - Verify Risk Governor active
   - Verify no existing positions

2. **Startup sequence:**
   - Fetch current 50-day SMA for BTC/USD and ETH/USD
   - Check current price vs SMA
   - If signal present, place paper order (max $100)
   - Log all decisions

3. **Daily cycle:**
   - Fetch yesterday's close
   - Update SMAs
   - Check for crossovers
   - Execute if signal present
   - Report to CEO

4. **Monitoring:**
   - Daily equity report
   - Position tracking
   - Drawdown monitoring
   - Fee tracking

---

## 10. ROLLBACK PLAN

If paper trading shows negative results:
1. Stop daemon immediately
2. Re-activate ENTRY_LOCK
3. Preserve all logs and trades
4. Analyze failures
5. Either fix strategy or return to research
6. Report to CEO with findings

---

## AUTHORIZATION

**Junior CEO (Jarvis) Authorization:**  
I, Jarvis, Junior CEO of Smart EA Bot Company, authorize the start of Alpaca PAPER trading for Trend Rider v5.6 under the following approved limits:
- Paper only (no live money)
- Max order $100
- Max risk 0.25%/trade
- BTC/USD and ETH/USD only
- All safety systems active

This authorization is given based on:
- 5 years of backtest data showing PF > 2.0
- Walk-forward validation (2/3 positive for BTC, 3/3 for ETH)
- Fee survival up to 3x normal fees
- QA tests all passing
- Risk review approving parameters

**Date:** Friday, May 22, 2026 — 19:27 CEST  
**Commit:** `26475fd` — v5.6 walk-forward + fee sensitivity complete

🦊 **Jarvis — Junior CEO. First bot passes gates. Paper trading starting autonomously.**
