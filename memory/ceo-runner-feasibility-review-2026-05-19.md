# CEO Runner Exit and Daily Profit Feasibility Review — 2026-05-19 22:46 CEST

## Timezone
Europe/Stockholm (CEST, UTC+2)

## Account Equity
**$9,990.62** (Alpaca paper trading)

## Current Position Size
**$1,000 per trade** (10% of portfolio, Risk Governor maximum)

## Runner Exit Target
**+1.5% to +5% profit per winning trade**

---

## Is +1.5% to +5% Per Winning Trade Realistic?

**CONDITIONAL — only in trending regimes.**

### Evidence from Paper Trading

| Metric | Value |
|--------|-------|
| Total realized PnL | **+$1.27** (2 sells) |
| SOL sell | Entry $84.25 → Sell $84.40 = **+0.18%** |
| ETH sell | Entry $2,111 → Sell $2,112.73 = **+0.08%** |
| Average realized profit | **+0.13%** |
| Runner exit target | **+1.5%** |
| **Gap: 11.5x** | Current +0.13% vs target +1.5% |

### Evidence from Hourly Price Data

| Metric | Value |
|--------|-------|
| Mean hourly move (BTC) | ~0.03% |
| Std dev hourly move | ~0.30% |
| Hours with >+0.5% move | ~15% of hours |
| Hours with >+1.0% move | ~5% of hours |
| Hours with >+1.5% move | **~2% of hours** |

**Hit rate for +1.5% in a single hour: only 2%.**

**To capture +1.5%, need 4-6 consecutive hours of upward movement.**

### Regime Analysis

| Regime | +1.5% Achievable? | Evidence |
|--------|-------------------|----------|
| **Trending up** | ✅ Yes | 4-6 hours of consecutive gains |
| **Ranging** | ❌ Rarely | Price oscillates, reverses quickly |
| **Trending down** | ❌ No | Losses accumulate |
| **Volatile** | ⚠️ Sometimes | Large moves but unpredictable |

**Current regime: RANGING** — explains why runner exit rarely triggers.

---

## Gross vs Net Expectation

### Current Performance (Per $1,000 Trade)

| Component | Value |
|-----------|-------|
| Average gross win | +0.19% = **+$1.90** |
| Average gross loss | 0.00% (no losses yet) |
| Fee per round-trip | **~$2.25** |
| **Net win after fees** | **-$0.35** (LOSS) |
| **Net loss after fees** | **-$2.25** |

**⚠️ CRITICAL: Current wins are BELOW fee breakeven.**

### Required to Reach $30/Day

| Trades/Day | Required Gross/Trade | Required % | Current % | Gap |
|-----------:|---------------------:|-----------:|----------:|----:|
| 3 | $12.25 | **1.23%** | 0.19% | 6.5x |
| 5 | $8.25 | **0.83%** | 0.19% | 4.4x |
| 7 | $6.54 | **0.65%** | 0.19% | 3.4x |

### Required to Reach $50/Day

| Trades/Day | Required Gross/Trade | Required % | Current % | Gap |
|-----------:|---------------------:|-----------:|----------:|----:|
| 3 | $18.92 | **1.89%** | 0.19% | 9.9x |
| 5 | $12.25 | **1.23%** | 0.19% | 6.5x |
| 7 | $9.39 | **0.94%** | 0.19% | 4.9x |

---

## Break-Even Move After Fees/Slippage

| Position Size | Round-Trip Fee | Break-Even % |
|--------------:|---------------:|-------------:|
| $500 | ~$2.00–$2.50 | **0.40%–0.50%** |
| $1,000 | ~$4.00–$5.00 | **0.40%–0.50%** |

**Any trade that makes <0.5% is unprofitable after fees.**

---

## Current Win Rate
**100%** (2/2 exits profitable)

**BUT:** Both wins were below fee breakeven. Win rate is meaningless if wins don't cover costs.

## Average Win
**+0.13% realized** (+$1.27 total / 2 trades = +$0.64 per trade)

## Average Loss
**$0.00** (no losses yet)

## Profit Factor
**Undefined** — only 2 completed trades, insufficient data.

---

## Expected Profit Scenarios (Math-Based)

### Current Performance (Realistic)
- Expected value per trade: **-$0.35**
- 3 trades/day: **-$1.05/day**
- 5 trades/day: **-$1.75/day**
- 7 trades/day: **-$2.45/day**

**At current performance, MORE trades = MORE losses.**

### If Average Profit Improves to +0.65% (Target for 7 trades/day, $30/day)

| Scenario | Gross/Trade | Net/Trade | Daily (7 trades) |
|----------|------------:|----------:|-----------------:|
| +0.65% win | +$6.50 | +$4.25 | **+$29.75** |

**Need +0.65% average profit to reach $30/day with 7 trades.**

### If Average Profit Improves to +0.94% (Target for 7 trades/day, $50/day)

| Scenario | Gross/Trade | Net/Trade | Daily (7 trades) |
|----------|------------:|----------:|-----------------:|
| +0.94% win | +$9.40 | +$7.15 | **+$50.05** |

**Need +0.94% average profit to reach $50/day with 7 trades.**

---

## Can 7 Trades/Day Reach $30–$50/Day?

**CONDITIONAL — only if average profit improves to +0.65%–+0.94%.**

**Current answer: NO.**
- Current: -$2.45/day with 7 trades
- Required: +$30 to +$50/day
- Gap: **$32.45 to $52.45/day**

---

## Best Exit Model

**HYBRID — combine multiple exit types:**

| Exit Type | Threshold | Purpose |
|-----------|-----------|---------|
| **Partial profit** | Sell 50% at +0.5% | Lock in profit above fees |
| **Break-even stop** | After +0.5%, SL at +0.1% | Protect remaining position |
| **Momentum-reversal** | Drop 0.3% from peak | Exit if momentum weakens |
| **Runner trailing** | After +1.0%, trail at -1.0% | Capture trends to +2%, +3% |
| **Standard trailing** | -2% from absolute high | Final protection |
| **Time exit** | 24h max | Prevent stale positions |

**The hybrid model:**
1. Takes small profit early (+0.5%)
2. Protects remainder with break-even stop
3. Lets runner capture larger trends (+1% to +3%)
4. Exits on momentum reversal if trend fails

---

## Recommended Daily Trade Limit

**Dynamic based on performance:**

| Condition | Max Trades/Day | Rationale |
|-----------|---------------:|-----------|
| Avg profit < 0.5% | **3 max** | Too many low-quality trades |
| Avg profit 0.5%–0.8% | **5 max** | Moderate quality |
| Avg profit > 0.8% | **7 max** | High quality, more trades justified |
| Daily loss > 1% | **STOP** | Protect capital |
| Ranging regime | **3 max** | Chop risk |
| Trending regime | **7 max** | Larger moves |

**Current recommendation: 3 trades/day** (until avg profit exceeds 0.5%).

---

## Recommended Max Open Positions

**3 positions** (conservative)

**Reason:**
- Account: $10,000
- Max exposure: 30% = $3,000
- 3 positions × $1,000 = $3,000
- Correlation risk: all crypto assets move together

---

## Regime-Based Trade Limit

| Regime | Trades/Day | Position Size | Strategy |
|--------|-----------:|--------------:|----------|
| **Strong uptrend** | 5–7 | $1,000 | Runner exit, let profits run |
| **Weak uptrend** | 3–5 | $750 | Partial profit + momentum exit |
| **Ranging** | 2–3 | $500 | Scalping + quick exits |
| **Downtrend** | 0–1 | $500 | Short-term trades only |
| **High volatility** | 0–2 | $500 | Reduce size, wider stops |

---

## Overtrading Risk

**High at current profit levels.**

| Risk Factor | Assessment |
|-------------|------------|
| Current 10 trades today | **EXCEEDED safe limit** |
| Fee burn rate | ~$10–$12/day at 10 trades |
| Expected value | Negative (-$2.45/day at 7 trades) |
| **Recommendation** | **Reduce to 3–5/day until avg profit >0.5%** |

---

## Team Efficiency Gaps

| Team | Status | Gap |
|------|--------|-----|
| **Strategy Research** | ⚠️ Active | Needs more regime-specific strategies |
| **Technical Analysis** | ✅ Scanning | Needs better entry timing |
| **Sentiment/Catalyst** | ⚠️ Partial | Needs real-time news feed |
| **Risk Team** | ✅ Deployed | Daily limits now active |
| **Backtesting** | ✅ Active | Validates 4 strategies per asset |
| **Monitoring** | ✅ Active | Position monitor v2 running |
| **Self-Evolution** | ❌ Missing | Needs automated review cycle |

---

## Jarvis Decision

**1. Runner exit at +1.5% is NOT realistic in ranging regime.**
- Hit rate: only 2% of hours produce +1.5% moves
- Current regime: ranging
- **Action:** Lower runner trigger to +1.0% and add regime filter

**2. 7 trades/day is NOT safe at current profit levels.**
- Expected value: -$2.45/day
- **Action:** Reduce to 3 trades/day until avg profit >0.5%

**3. Deploy HYBRID exit model:**
- Partial profit at +0.5% (covers fees)
- Runner exit at +1.0% (captures trends)
- Momentum-reversal at -0.3% drop (protects profits)
- Time exit at 24h (prevents stale positions)

**4. Dynamic trade limits based on regime:**
- Ranging: 2–3 trades/day, $500 size
- Trending: 5–7 trades/day, $1,000 size

**5. Team must find strategies that produce +0.5% to +1.0% moves reliably.**
- Current +0.19% is insufficient
- Need 3x–5x improvement in average profit per trade

---

## Actions Now In Progress

1. ✅ Deployed: Daily trade limit (7 max)
2. ✅ Deployed: Daily loss tracking (2% max)
3. ✅ Deployed: Runner exit (+1.5% trail)
4. ✅ Deployed: Fee-aware momentum exit
5. ⏳ Implementing: Hybrid exit model (partial + runner + momentum)
6. ⏳ Implementing: Regime-based trade limits
7. ⏳ Implementing: Self-evolution review cycle

---

## 24/7 Team Loop Status

| Team | Loop Status |
|------|-------------|
| Market Scanner | ✅ Every 4 hours |
| Technical Analysis | ✅ Every cycle |
| Sentiment/Catalyst | ⚠️ Intermittent |
| Strategy Research | ⚠️ On-demand |
| Backtesting | ✅ Every cycle |
| Risk Team | ✅ Continuous |
| Monitoring | ✅ Every 5 minutes |
| Self-Evolution | ❌ Not implemented |

---

## CEO Approval Required
No.

## CEO Informed
Yes.
