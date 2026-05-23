# Paper Readiness Pack — Trend Rider v5.6 (Alpaca-Validated)
**Date:** Saturday, May 23, 2026 — 10:15 CEST  
**Bot:** Trend Rider v5.6  
**Strategy:** 50-day SMA trend following (daily timeframe)  
**Data Source:** Alpaca (single authoritative source)  
**Status:** ✅ **ALL GATES PASSED — PAPER TRADING AUTHORIZED**

---

## ⚠️ VERSION HISTORY

| Version | Date | Data Source | BTC PF | ETH PF | Status |
|---------|------|-------------|--------|--------|--------|
| v1.0 | 2026-05-22 | Yahoo Finance | 2.14 | 4.85 | Superseded |
| **v2.0** | **2026-05-23** | **Alpaca** | **1.58** | **4.89** | **Active** |

**Superseded:** v1.0 used Yahoo Finance data. A data source mismatch investigation (2026-05-23) revealed that Alpaca — the execution venue — should be the single authoritative source to eliminate reconciliation risk. v5.6 was revalidated on Alpaca 5-year data and passes all gates.

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

## 3. BACKTEST RESULTS (Alpaca 5-Year Data)

### Full Period (2021-05-23 to 2026-05-23)

| Metric | BTC/USD | ETH/USD |
|--------|---------|---------|
| **Trades** | 28 | 23 |
| **Total Return** | +3.04% | +13.14% |
| **Profit Factor** | **1.58** | **4.89** |
| **Max Drawdown** | 2.26% | 1.44% |
| **Win Rate** | ~54% | ~61% |
| **Fee Drag** | 0.04% | 0.04% |

### Walk-Forward (3-fold, Alpaca Data)

| Asset | Fold 1 | Fold 2 | Fold 3 | Positive |
|-------|--------|--------|--------|----------|
| BTC | ✅ PF 1.11 | ✅ PF 1.91 | ✅ PF 1.37 | 3/3 |
| ETH | ✅ PF 9.35 | ✅ PF 3.81 | ✅ PF 4.05 | 3/3 |

### Fee Sensitivity (Alpaca Data)

| Asset | 0.5x | 1x | 2x | 3x |
|-------|------|----|----|----|
| BTC | PF 1.63 | PF 1.58 | PF 1.50 | PF 1.43 |
| ETH | PF 5.00 | PF 4.89 | PF 4.68 | PF 4.48 |

**Survives 3x fees on both assets.** BTC PF drops to 1.43 at 3x but remains above 1.0.

---

## 4. DATA SOURCE RESOLUTION

### Root Cause (Fixed 2026-05-23)

Two independent bugs were found during data source reconciliation:

1. **data_fetcher.py hardcoded timeframe**: The `timeframe` parameter was ignored. All calls returned 5-minute bars regardless of requested timeframe.
2. **Reconciliation timezone offset**: Alpaca crypto daily bars use UTC timestamps starting at 20:00 UTC. The reconciliation script extracted dates in local timezone (-04:00), creating a 1-day offset.

Both bugs are fixed and regression tests are committed (see `core/tests/`).

### Decision

**Alpaca selected as single authoritative source.**
- Alpaca is the execution venue — same source for backtest + live eliminates mismatch risk
- v5.6 passes all gates on Alpaca data
- Alpaca provides 5+ years of daily crypto data
- No need for Yahoo Finance fallback

---

## 5. RISK REVIEW

| Risk Parameter | Value | Status |
|----------------|-------|--------|
| Risk per trade | 0.25% equity | ✅ Within limit |
| Max order size | $100 | ✅ Within limit |
| Max positions | 2 | ✅ Within limit |
| Max daily loss | 1% | ✅ Strategy max DD 2.26% |
| Max weekly loss | 3% | ✅ Well within limit |
| Leverage | 0x | ✅ No leverage |
| Martingale | No | ✅ No averaging down |

**Risk Manager Approval:** ✅ **APPROVED**

---

## 6. QA RESULTS

| Test | Result |
|------|--------|
| Deterministic replay | ✅ PASS |
| No lookahead bias | ✅ PASS |
| Fee impact realism | ✅ PASS (0.04% drag) |
| Risk Governor blocks | ✅ PASS (blocked $35,000 order) |
| Regression: data_fetcher timeframe | ✅ PASS |
| Regression: reconciliation timezone | ✅ PASS |

**QA Approval:** ✅ **APPROVED**

---

## 7. EXPECTED TRADE FREQUENCY

| Asset | Expected Trades/Year | Expected Hold Time |
|-------|---------------------|-------------------|
| BTC/USD | ~5-6 | 1-3 months |
| ETH/USD | ~4-5 | 1-3 months |

**Low frequency, high conviction.**

---

## 8. FAILURE CONDITIONS

Bot must STOP paper trading if:
- 3 consecutive losing trades
- Drawdown > 10% from peak
- No signal for 90 days (strategy out of sync)
- Any safety system triggers (Risk Governor, Broker Reconciliation)

---

## 9. STOP/RE-LOCK CONDITIONS

Paper trading will be halted and ENTRY_LOCK re-activated if:
- Live drawdown exceeds 5% (half of max allowed)
- Paper results diverge > 20% from backtest expectations
- Any safety system is triggered
- CEO issues HALT command
- Market regime fundamentally changes (e.g., crypto crash with no recovery)

---

## 10. DAEMON STARTUP PLAN (v2.0)

1. **Pre-flight checks:**
   - Verify ENTRY_LOCK is released
   - Verify Alpaca paper credentials
   - Verify Risk Governor active
   - Verify no existing positions

2. **Startup sequence:**
   - Fetch daily bars from Alpaca (single authoritative source)
   - Compute 50-day SMA
   - Check current price vs SMA
   - If signal present, place paper order (max $100)
   - Log all decisions

3. **Daily cycle:**
   - Fetch yesterday's close from Alpaca
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

## 11. ROLLBACK PLAN

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
- 5 years of Alpaca data showing PF 1.58 (BTC), PF 4.89 (ETH)
- Walk-forward validation (3/3 positive for both assets)
- Fee survival up to 3x normal fees
- QA tests all passing
- Risk review approving parameters
- Data source resolved (Alpaca single source)

**Date:** Saturday, May 23, 2026 — 10:15 CEST  
**Commit:** `e521999` — data_crisis_resolved: Alpaca single source, daemon v2.0  
**Tag:** (pending merge) `v5.6-alpaca-validated`

🦊 **Jarvis — Junior CEO. Data crisis resolved. Paper trading ready on signal.**
