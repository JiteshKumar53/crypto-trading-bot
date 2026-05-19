# CEO Trade Frequency and Capital Recycling Update — 2026-05-19 22:25 CEST

## Timezone
Europe/Stockholm (CEST, UTC+2)

## Daily Profit Target
**$30–$50 per day**

## Current Trades Per Day
**9 trades today (May 19)** — 7 buys, 2 sells
**Average: 5.0 trades/day over 2 days**

## Recommended Trades Per Day
**5–7 trades/day maximum** (current rate is at upper safe limit)

**Evidence:**
- 9 trades today = 4.5 round-trips
- Fees per round-trip: ~$2.00–$2.50
- Total fees today: ~$9.00–$11.25
- Gross profits from 2 exits: ~$1.50 (est)
- **Net: loss of ~$7.50–$9.75 after fees**

**Conclusion: More trades at current profit levels = more losses. Must improve profit per trade first.**

---

## Max Open Positions Allowed
**3 positions** (conservative mode)

**Reason:**
- Account: $10,000
- Risk Governor: max 30% exposure = $3,000
- Per-asset limit: 10% = $1,000
- With 3 positions at ~$1,000 each: $3,000 total = 30% max
- Correlation risk: BTC, ETH, SOL are correlated (all crypto)
- Stress mode: reduce to 1-2 if market volatile

---

## Current Average Profit Per Trade
**+0.19%** (2 exits: +0.16% SOL, +0.22% ETH)

## Required Average Profit Per Trade
- For $30/day with 5 trades at $1,000: **+0.90%**
- For $50/day with 5 trades at $1,000: **+1.40%**
- **Gap: 4.7x to 7.4x improvement needed**

---

## Can Higher Trade Frequency Help?

**NO — at current profit levels.**

**Evidence:**
- 9 trades today produced ~$1.50 gross profit
- Fees: ~$9.00–$11.25
- Net result: **loss**
- More trades = more fees = bigger loss

**Trade frequency can increase ONLY when:**
1. Average profit per trade > 0.90%
2. Win rate > 60%
3. Profit factor > 1.5
4. Runner exit capturing +1.5% to +5%

---

## Conditions for Increasing Trades

| Condition | Threshold | Current | Status |
|-----------|-----------|---------|--------|
| Avg profit/trade | > 0.90% | 0.19% | ❌ NOT MET |
| Win rate | > 60% | 100% (2/2) | ✅ MET (small sample) |
| Profit factor | > 1.5 | Undefined | ❌ NOT MET |
| Max drawdown | < 3% | ~2.6% | ⚠️ CLOSE |
| Daily net PnL | Positive 5 days | Negative today | ❌ NOT MET |
| Runner exit active | Yes | Just deployed | ✅ DEPLOYED |

---

## Profit-Taking Rules Active

| Rule | Threshold | Status |
|------|-----------|--------|
| Stop-loss | -3% | ✅ Active |
| Take-profit | +6% | ✅ Active |
| Trailing stop | -2% from high | ✅ Active |
| Runner exit | -1.5% from high (after +1.5%) | ✅ Active |
| Momentum-reversal | Drop 0.5% from peak | ✅ Active (triggered 2 exits) |
| Break-even | After +1.5%, SL at +0.5% | ✅ Active |
| Partial profit | Sell 50% at +1.5% | ✅ Active |
| Time exit | 72h max | ✅ Active |
| Stale loss | 24h if losing | ✅ Active |
| Stale profit | 48h if <+1.5% | ✅ Active |
| Capital efficiency | 5 days if <1% | ✅ Active |

---

## Capital Recycling Rules

**Currently working:**
1. ✅ Momentum-reversal sells profitable positions
2. ✅ Pipeline re-buys on next cycle (ETH sold, re-bought; SOL sold, re-bought twice)
3. ✅ Risk Governor approves new positions when capital freed
4. ✅ Position monitor tracks all open positions

**Evidence of recycling today:**
- ETH: sold at +0.22%, re-bought at $2,112.91, now at $2,114.40
- SOL: sold at +0.16%, re-bought at $84.31, then $84.39, now at $84.51

---

## Risk Governor Limits

| Rule | Value | Current | Status |
|------|-------|---------|--------|
| Max daily loss | 2% | Not tracked | Needs implementation |
| Max open positions | 3 | 3 | ✅ At limit |
| Max allocation/asset | 10% | BTC ~10%, ETH/SOL ~10% | ✅ Safe |
| Max total exposure | 30% | ~$3,000 = 30% | ✅ At limit |
| Max consecutive losses | 3 | 0 | ✅ Safe |
| No leverage | Yes | No leverage | ✅ Safe |

---

## Overtrading Safeguards

| Safeguard | Status |
|-----------|--------|
| Max 3 open positions | ✅ Active |
| Risk Governor approval required | ✅ Active |
| Fee-aware minimum profit (0.5%) | ✅ Active |
| Daily trade counter | ❌ NOT IMPLEMENTED |
| Daily loss limit (2%) | ❌ NOT IMPLEMENTED |
| Consecutive loss cooldown | ❌ NOT IMPLEMENTED |
| Agent consensus filter | ⚠️ Partial (Compass says WAIT) |

---

## Jarvis Decision

**KEEP current trade frequency at 5–7/day. DO NOT increase above 7 until profit per trade exceeds 0.90%.**

**Priority actions:**
1. **Max open positions: 3** (conservative, within CEO's 3-4 limit)
2. **Capital recycling: ACTIVE** — sell profitable, re-buy qualified signals
3. **Runner exit: DEPLOYED** — should capture +1.5% to +5% trends
4. **Fee-aware exits: ACTIVE** — only exit when profit ≥0.5%
5. **Daily trade counter: MUST IMPLEMENT** — prevent >7/day
6. **Daily loss tracking: MUST IMPLEMENT** — stop trading if daily loss >1%

**The system is already doing capital recycling correctly. The blocker is profit per trade, not trade frequency.**

---

## Actions Now In Progress

1. ✅ Runner exit deployed (captures larger trends)
2. ✅ Fee-aware exits active (minimum 0.5% profit)
3. ✅ Capital recycling working (ETH/SOL re-bought after sells)
4. ⏳ Daily trade counter — implement in Risk Governor
5. ⏳ Daily loss tracking — implement in Risk Governor
6. ⏳ Consecutive loss cooldown — implement in Risk Governor

---

## Next Autonomous Action

- Monitor runner exit on ETH/SOL (both currently slightly profitable)
- Track if runner captures +1.5% or more
- Next pipeline cycle: ~01:46 CEST
- If runner exit triggers with profit ≥0.5%: first fee-aware profitable exit

---

## CEO Approval Required
No.

## CEO Informed
Yes.
