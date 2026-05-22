# CRITICAL DATA MISMATCH REPORT — Smart EA Bot Company
**Date:** Friday, May 22, 2026 — 19:47 CEST  
**Severity:** 🔴 **CRITICAL — Paper Trading BLOCKED until resolved**  
**Reporter:** Jarvis, Junior CEO

---

## FINDING

Alpaca paper trading API returns **completely different prices** than Yahoo Finance for the same crypto symbols:

| Asset | Yahoo Finance | Alpaca | Difference |
|-------|-------------|--------|------------|
| BTC/USD | ~$78,000 | ~$61,000 | **25-30%** |
| ETH/USD | ~$2,100 | ~$3,380 | **35-46%** |

This is not a small discrepancy. These are fundamentally different prices.

---

## IMPACT

1. **Backtest Invalidity:** All v5.6 backtest results (PF 2.14 BTC, PF 4.85 ETH) were computed on Yahoo Finance data. Alpaca paper trades will execute at 25-46% different prices.

2. **SMA Cross Invalidity:** The 50-day SMA calculated from Yahoo data will produce DIFFERENT signals than an SMA calculated from Alpaca data.

3. **Paper Trading Cannot Proceed:** The daemon will place orders at Alpaca prices, but the backtest was validated at Yahoo prices. The strategy logic may not hold.

4. **90-Day Observation Worthless:** If prices don't match, the observation period compares apples to oranges.

---

## HYPOTHESIS: WHY THE MISMATCH

**Most Likely:** Alpaca crypto paper trading data is from a different venue or is simulated/stale data. Yahoo Finance aggregates from major exchanges. Alpaca may be using a specific exchange or internal pricing.

**Alternative:** The Alpaca API might be returning data for different symbols (BTCUSD vs BTC/USD vs BTC-USD may map to different instruments).

**Alternative:** Alpaca's paper crypto data may be intentionally different from live to prevent arbitrage abuse.

---

## REQUIRED ACTIONS

### Option A: Use Yahoo Finance for BOTH backtest AND live pricing
- **Problem:** Yahoo Finance does not support trading. We can only observe prices, not execute trades.
- **Feasibility:** Low

### Option B: Re-validate ALL bots using Alpaca data only
- **Problem:** Alpaca crypto data is only ~35 days. SMA strategies need 200+ days minimum.
- **Feasibility:** Low (insufficient data for SMA strategies)

### Option C: Switch to Alpaca EQUITIES
- **Problem:** CEO wants crypto.
- **Feasibility:** Requires CEO approval to change scope

### Option D: Find a broker with Yahoo-matching crypto data
- **Options:** Binance, Coinbase Pro, Kraken
- **Problem:** Requires new API integration
- **Feasibility:** Medium but time-consuming

### Option E: Accept Alpaca data as ground truth and re-design for Alpaca's price history
- **Problem:** Need 200+ days of Alpaca data for SMA. Currently have 35.
- **Feasibility:** Wait for data to accumulate (6+ months)

---

## RECOMMENDATION

**STOP paper trading immediately.** Do not place any orders until data source mismatch is resolved.

**Next Steps:**
1. Investigate Alpaca's crypto data source and pricing methodology
2. Compare Alpaca prices to other exchanges (Coinbase, Binance) to understand discrepancy
3. If Alpaca data is fundamentally different, either:
   a) Find a broker with matching data, OR
   b) Switch to equities (SPY/QQQ) where Alpaca has reliable data, OR
   c) Build a data bridge that normalizes prices between sources

---

## DECISION REQUIRED

This is a **structural project compromise** (Escalation Trigger #7). The entire validation framework is built on data that doesn't match the execution venue.

I need CEO guidance on:
1. Whether to investigate further (hours of work)
2. Whether to pivot to equities immediately
3. Whether to seek alternative broker integration

**Current Status:**
- Paper Daemon: 🟡 Built but NOT RUNNING (ENTRY_LOCK active)
- Trend Rider v5.6: 🟡 Validated on Yahoo, UNVALIDATED on Alpaca
- Track B: 🟡 On hold pending data resolution

---

🦊 **Jarvis — Junior CEO. Paper trading BLOCKED pending data source resolution. Requesting CEO guidance on path forward.**
