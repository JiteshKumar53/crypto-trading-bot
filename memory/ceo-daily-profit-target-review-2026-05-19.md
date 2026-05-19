# CEO Daily Profit Target Review — 2026-05-19 22:15 CEST

## Timezone
Europe/Stockholm (CEST, UTC+2)

## Account Equity Assumed
**$10,000** (Alpaca paper trading)

## Current Daily Trade Limit
**6 trades/day maximum** (3-6 recommended)

## Target Profit Per Day
**$30–$50 per day**

---

## Trades/Day Scenario Analysis

### Position Size
- Risk Governor allows: **5%–10% of portfolio per trade** ($500–$1,000)
- Conservative sizing: **$500 per trade** (5%)
- Aggressive sizing: **$1,000 per trade** (10%)

### Fee Structure (Alpaca Crypto)
- Round-trip (buy + sell): **~0.40%–0.50%**
- Per $500 trade: **~$2.00–$2.50 in fees**
- Per $1,000 trade: **~$4.00–$5.00 in fees**

---

## Required Average Profit Per Trade

### Scenario: 3 trades/day, $500 position
| Target | Gross Needed | Fees (3 trades) | Net Required | Per Trade |
|--------|--------------|-----------------|--------------|-----------|
| $30/day | $36.75 | $6.75 | $30 | **2.45%** |
| $50/day | $56.75 | $6.75 | $50 | **3.78%** |

### Scenario: 6 trades/day, $500 position
| Target | Gross Needed | Fees (6 trades) | Net Required | Per Trade |
|--------|--------------|-----------------|--------------|-----------|
| $30/day | $43.50 | $13.50 | $30 | **1.45%** |
| $50/day | $63.50 | $13.50 | $50 | **2.12%** |

### Scenario: 3 trades/day, $1,000 position
| Target | Gross Needed | Fees (3 trades) | Net Required | Per Trade |
|--------|--------------|-----------------|--------------|-----------|
| $30/day | $42.00 | $12.00 | $30 | **1.40%** |
| $50/day | $62.00 | $12.00 | $50 | **2.07%** |

### Scenario: 6 trades/day, $1,000 position
| Target | Gross Needed | Fees (6 trades) | Net Required | Per Trade |
|--------|--------------|-----------------|--------------|-----------|
| $30/day | $54.00 | $24.00 | $30 | **0.90%** |
| $50/day | $84.00 | $24.00 | $50 | **1.40%** |

---

## Current Performance Reality

| Metric | Value |
|--------|-------|
| **Current average profit per trade** | **+0.19%** (2 exits: +0.16%, +0.22%) |
| **Current average loss per trade** | **Unknown** (no loss exits yet) |
| **Current win rate** | **100%** (2/2 exits profitable, but below fee breakeven) |
| **Current profit factor** | **Undefined** (only 2 exits, not enough data) |
| **Current max drawdown** | **-0.56%** (BTC unrealized) |
| **Current average holding time** | **~5 hours** |
| **Total trades today** | **6** (4 buys, 2 sells) |
| **Performance by asset (BTC)** | Entry $77,088, current $76,893, **-0.25%** |
| **Performance by asset (ETH)** | **Sold at +0.22%** |
| **Performance by asset (SOL)** | **Sold at +0.16%, re-bought at $84.31, now -0.10%** |
| **Performance by strategy** | BollingerBands optimized: +0.74% (peak), momentum-reversal captured +0.16% |
| **Performance by regime** | Ranging regime — all strategies struggling |

---

## Is 3–6 Trades/Day Sufficient?

**NO — at current performance levels.**

**Math:**
- Current average profit per trade: **+0.19%**
- Required for $30/day with 6 trades at $500: **+1.45%**
- Required for $50/day with 6 trades at $500: **+2.12%**
- **Gap: 0.19% vs 1.45–2.12% = 7.6x to 11x improvement needed**

**Even with 6 trades at $1,000 position size:**
- Required for $30/day: +0.90%
- Current: +0.19%
- **Gap: 4.7x improvement needed**

---

## Main Blocker

**Average profit per trade is too small.**

Current exits capture ~0.2% moves. The system needs to capture **1.5%–3.8% moves** to hit the profit target.

The reasons:
1. Crypto ranging regime prevents large directional moves
2. Momentum-reversal exits are too tight (prevent larger profits)
3. No "runner" strategy to capture trends
4. Position sizing is conservative ($500 vs $1,000 potential)
5. Strategies are basic (MA, RSI, MACD, Bollinger)

---

## Can Profit Improve Without Overtrading?

**YES — through these improvements:**

| Improvement | Impact | Status |
|-------------|--------|--------|
| **Increase position size to $1,000** | Doubles profit per trade | Risk Governor allows (10% max) |
| **Add "runner" exit (trailing stop at 3%)** | Captures larger trends | **NOT IMPLEMENTED** |
| **Only trade trending regimes** | Avoids ranging chop | **NOT IMPLEMENTED** |
| **Improve entries with better strategies** | Higher win rate | **IN PROGRESS** |
| **Partial profit + let remainder run** | Lock in profit, capture upside | **Partially implemented** |
| **Skip trades in weak regimes** | Avoid losing trades | **NOT IMPLEMENTED** |
| **Add mean-reversion strategies** | Profit from ranging markets | **NOT IMPLEMENTED** |

---

## Recommended Trade-Frequency Policy

**Dynamic Limits Based on Performance:**

| Condition | Max Trades/Day | Position Size | Rationale |
|-----------|----------------|---------------|-----------|
| Win rate < 50% | 3 max | $500 | Reduce risk |
| Win rate 50–60% | 4–5 max | $500–$750 | Moderate |
| Win rate > 60% | 6 max | $750–$1,000 | Increase edge |
| Daily loss > 1% | STOP (cooldown 24h) | $0 | Protect capital |
| Consecutive losses = 2 | 3 max | $500 | Reduce size |
| Consecutive losses = 3 | STOP (cooldown) | $0 | Risk Governor rule |
| Trending regime | 6 max | $1,000 | Larger moves expected |
| Ranging regime | 3 max | $500 | Chop risk |

---

## Conditions to Increase Trade Frequency Above 6/Day

**NEVER increase above 6/day unless ALL conditions met:**
1. Win rate > 65% over last 20 trades
2. Average profit per trade > 1.5%
3. Profit factor > 1.5
4. Max drawdown < 3%
5. Daily net PnL positive for 5 consecutive days
6. Agent recommendations show >70% agreement

---

## Team Actions Now

| Team | Action | Priority |
|------|--------|----------|
| **Jarvis (Junior CEO)** | Deploy runner exit strategy, dynamic sizing | **CRITICAL** |
| **Strategy Research** | Find mean-reversion strategies for ranging regime | **HIGH** |
| **Backtesting** | Validate runner exit on 168h data | **HIGH** |
| **Risk Team** | Implement daily PnL tracking, loss limits | **HIGH** |
| **Technical Analysis** | Improve entry timing (better MA windows) | **MEDIUM** |
| **Position Monitor** | Add runner trailing stop (3% from entry, not peak) | **CRITICAL** |

---

## Jarvis Decision

**I am implementing a "runner" exit strategy that allows profitable trades to capture larger moves:**

1. **Deploy "runner" trailing stop:** Once profit hits +1.5%, move trailing stop to +0.5% (lock in profit). Continue trailing at -1.5% from highest price. This lets winners run to +3%, +4%, +5% while protecting downside.
2. **Increase position size for high-confidence trades:** When backtest Sharpe > 2.0 and win rate > 60%, size up to $1,000 (10%).
3. **Add regime filter:** In ranging regime, max 3 trades/day, $500 size. In trending regime, max 6 trades/day, $1,000 size.
4. **Skip trades when agents disagree:** If Compass says WAIT and Shield says Reduce, skip the trade entirely.

**Expected improvement:**
- Current: +0.19% average profit
- Target with runner: +1.5%–3.0% on winning trades
- With $1,000 size and 3 trades/day at +2%: $60 gross - $6.75 fees = **$53.25 net/day**

---

## Next Autonomous Action

1. Implement runner exit in PositionMonitorV2
2. Add dynamic position sizing to PipelineController
3. Add regime-based trade limits
4. Backtest runner strategy on all 3 assets
5. Commit and restart daemon

## CEO Approval Required
No.

## CEO Informed
Yes.
