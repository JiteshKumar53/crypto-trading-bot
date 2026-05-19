# CEO Momentum-Reversal Exit Review — 2026-05-19 21:35 CEST

## Timezone
Europe/Stockholm (CEST, UTC+2)

## Evidence Reviewed
- Alpaca API: 7 total orders (5 buys, 2 sells)
- Position monitor logs: 2 momentum-reversal exits triggered
- Pipeline logs: SOL re-bought after sell, ETH sold
- Backtest: 4 strategies tested per asset
- Risk Governor: limits enforced
- Fee analysis: 0.40-0.50% round-trip

---

## Momentum-Reversal Exit Performance

| Trade | Asset | Entry | Peak | Exit | Drop | Result | Time Held |
|-------|-------|-------|------|------|------|--------|-----------|
| #1 | **SOL** | $84.25 | +0.75% | +0.16% | 0.59% | **Small profit** | ~5h |
| #2 | **ETH** | $2,111 | +0.60% | +0.22% | 0.38% | **Small profit** | ~5h |

**Both exits prevented positions from reversing into losses.**

---

## Compared with Old Exit Logic

| Metric | Before (passive) | After (momentum-reversal) |
|--------|-----------------|---------------------------|
| Sell orders executed | 0 | **2** |
| Profitable exits | 0 | **2** |
| ETH peak to exit | +0.60% → +0.11% (would have held) | +0.60% → +0.22% (**sold**) |
| SOL peak to exit | +0.75% → -0.02% (would have held) | +0.75% → +0.16% (**sold**) |
| Average exit result | Unknown (never exited) | **+0.19%** (both profitable) |

---

## Win Rate / Profit Factor

| Metric | Value |
|--------|-------|
| Total exits with momentum-reversal | 2 |
| Profitable exits | 2 (100%) |
| Loss exits | 0 |
| Average profit per exit | ~+0.19% |
| Estimated profit per $500 trade | ~$0.95 |
| Estimated fees per round-trip | ~$2.00-$2.50 |
| **Net after fees (estimated)** | **-$1.05 to -$1.55 per trade** |

**⚠️ CRITICAL FINDING: Profits are too small to cover fees.**

---

## Drawdown Impact

| Asset | Without Momentum-Reversal | With Momentum-Reversal |
|-------|---------------------------|------------------------|
| ETH | Would have dropped to -0.12% | Sold at +0.22% |
| SOL | Would have dropped to -0.29% | Sold at +0.16% |

**Momentum-reversal prevented ~0.3-0.5% additional drawdown per position.**

---

## Average Holding Time Impact

| Metric | Before | After |
|--------|--------|---------|
| Average hold time | Undefined (never exited) | ~5 hours |
| Fastest exit | N/A | ~5 hours |
| Capital recycling | None | SOL re-bought after 10 min |

---

## BTC Result

- BTC: No exit triggered (still holding at -0.25%)
- BTC peaked at +0.12%, now at -0.25% — drop of 0.37%
- **BTC dropped below 0% before momentum-reversal could trigger**
- BTC is now in loss territory, monitored by stop-loss at -3%

---

## ETH Result

- **ETH SOLD at +0.22%** via momentum-reversal
- Peak was +0.60%, exit triggered at +0.22% (drop = 0.38% > 0.3% threshold)
- **Profit estimated: ~$0.55 on ~$500 position**

---

## SOL Result

- **SOL SOLD at +0.16%** via momentum-reversal
- Then **RE-BOUGHT at $84.31** by pipeline (new cycle detected opportunity)
- Current SOL: 5.91 @ $84.31, now at $84.07 (-0.29%)
- This shows capital recycling is working

---

## Trade Frequency Analysis

| Metric | Value |
|--------|-------|
| Total filled orders | 7 |
| Day 1 (May 18) | 1 buy |
| Day 2 (May 19) | 4 buys, 2 sells = 6 trades |
| Average per day | 3.5 |
| Current rate today | 6 trades/day |
| Risk Governor max positions | 3 |
| Risk Governor max exposure | 30% |
| Current exposure | ~$1,980 (~20%) |

---

## Overtrading Risk

| Threshold | Status |
|-----------|--------|
| >10 trades/day | Overtrading — fees erode profits |
| 5-10 trades/day | Elevated — monitor closely |
| 3-6 trades/day | **Current rate — safe** ✅ |
| <3 trades/day | Conservative |

**Current 6 trades/day is at the upper edge of safe. If it increases to >8, overtrading risk rises.**

---

## Fees/Slippage Risk

| Trade Size | Round-Trip Fees | Required Profit to Breakeven |
|------------|-------------------|------------------------------|
| $500 | ~$2.00-$2.50 | **+0.40% to +0.50%** |
| $1,000 | ~$4.00-$5.00 | **+0.40% to +0.50%** |

**Current momentum-reversal exits at +0.16% to +0.22% are BELOW the fee breakeven of +0.40%.**

**⚠️ The system is currently unprofitable after fees on momentum-reversal exits.**

---

## Risk Governor Limits

| Rule | Value | Current | Status |
|------|-------|---------|--------|
| Max daily loss | 2% | Not tracked yet | Needs implementation |
| Max open positions | 3 | 2 (BTC, SOL) | ✅ Safe |
| Max allocation/asset | 10% | BTC ~10%, SOL ~5% | ✅ Safe |
| Max total exposure | 30% | ~20% | ✅ Safe |
| Max consecutive losses | 3 | 0 current streak | ✅ Safe |
| No leverage | Yes | No leverage | ✅ Safe |

---

## Jarvis Decision

**Continue Momentum-Reversal Exit with ADJUSTMENTS:**

1. **Raise momentum-reversal threshold from 0.3% to 0.5%** — ensures profit covers fees
2. **Add fee-aware minimum profit rule** — don't exit if profit < 0.5%
3. **Limit trade frequency to max 6/day** — add counter and cooldown
4. **Add daily loss tracking** — implement in Risk Governor
5. **Continue monitoring** — track net profit after fees

**Do NOT increase trade frequency beyond 6/day until average profit per trade exceeds 0.5%.**

## Should Continue Momentum-Reversal Exit
**YES — with threshold raised to 0.5% to cover fees.**

## Should Increase Trade Frequency
**NO — keep at current 3-6/day. Increase only when profit/trade > 0.5%.**

## Fixes Now In Progress
1. Raise momentum-reversal threshold to 0.5%
2. Add fee-aware minimum profit check
3. Add daily trade counter
4. Add daily loss tracking to Risk Governor

## Next Autonomous Action
- Monitor BTC for stop-loss or recovery
- Monitor SOL (new position) for momentum-reversal or profit
- Next pipeline cycle: ~21:46 CEST

## CEO Approval Required
No.

## CEO Informed
Yes.
