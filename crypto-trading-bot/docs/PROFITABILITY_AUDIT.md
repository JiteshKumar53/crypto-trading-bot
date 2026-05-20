# CEO PROFITABILITY AUDIT

**Date:** 2026-05-20 14:30 CEST
**Auditor:** Jarvis (Junior CEO)
**Priority:** HIGHEST — All non-critical work paused

---

## EXECUTIVE SUMMARY

**The current system cannot reliably support the $30–$50/day target yet.**

The system is structurally broken in its exit logic. It is caught in an infinite partial-sell loop, repeatedly attempting to sell dust quantities that generate no meaningful profit while consuming API calls and creating log noise. The only meaningful realized profit in 24+ hours of trading is **$0.84** from a single BTC partial sell. All other "exits" are dust transactions of negligible value.

---

## 1. DIAGNOSIS: WHY WE ARE NOT PROFITABLE

### 1.1 The Partial-Sell Death Spiral (CRITICAL BUG)

The Position Monitor V2 partial profit logic has a fatal flaw:

1. Position enters at $X
2. Price rises +0.5% → triggers partial_profit_1 → sells 50% of position → SUCCESS
3. Remaining position still has same entry price
4. Price rises another +0.5% → triggers partial_profit_1 AGAIN → sells 50% of remaining → SUCCESS
5. This repeats, halving the quantity each time
6. Eventually reaches 0.00000001 qty → still "succeeds" but worth ~$0
7. Then tries 0.00000000 qty → FAILS with "order qty must be >= minimal qty"
8. **Keeps trying every 5 minutes forever**

**Evidence from daemon.log:**
- ETH partial sell chain: 0.235 → 0.117 → 0.058 → 0.029 → 0.014 → 0.007 → 0.003 → 0.001 → 0.0007 → 0.0003 → 0.0001 → 0.00005 → 0.00002 → 0.00001 → 0.000007 → 0.000003 → 0.000001 → 0.0000009 → 0.0000004 → 0.0000002 → 0.0000001 → 0.00000006 → 0.00000003 → 0.00000001 → 0 → FAILS
- 118 partial triggers logged in ~24 hours
- Only 2 meaningful partial sells actually executed (BTC at +0.53%, ETH initial at +0.65% before the spiral)

### 1.2 No Meaningful Round-Trip Trades

**Realized PnL breakdown:**
| Trade | Symbol | Realized PnL |
|-------|--------|---------------|
| Partial sell | BTCUSD | ~+$0.84 |
| Dust sell | ETHUSD | ~$0.00 |
| **TOTAL REALIZED** | | **~+$0.84** |

**All other "exits" are dust from the death spiral, not actual profit-taking.**

### 1.3 Positions Held Too Long Without Exits

Current open positions (as of 14:30 CEST):
| Asset | Entry | Current | Hours Held | Unrealized | Status |
|-------|-------|---------|------------|------------|--------|
| BTC | $77,293.58 | $77,409.60 | ~23h | +$1.87 (+0.15%) | Runner (50% sold) |
| ETH | $2,130.11 | $2,127.46 | ~19h | -$1.24 (-0.12%) | Holding (partial spiral) |
| SOL | $84.84 | $84.84 | ~5h | ~$0.00 (0.00%) | Holding |

**Analysis:**
- BTC: +0.15% after 23 hours = negligible. Partial taken at +0.53% was good, but runner not managed well.
- ETH: -0.12% after 19 hours. Should have been stopped or exited. The partial spiral consumed all potential profit.
- SOL: Flat after 5 hours. No exit strategy triggered yet.

### 1.4 Backtest Results Show Strategies Are NOT Profitable

From cycle logs (last 24h):

| Strategy | Asset | Backtest Return | Sharpe | Status |
|----------|-------|----------------|--------|--------|
| ma_crossover_20 | BTC | -3.53% | -9.44 | REJECTED |
| ma_crossover_20 | ETH | -6.61% | -17.55 | REJECTED |
| bb_20_2.0 | BTC | -1.02% | -2.73 | REJECTED (position limit) |
| rsi_14_30_70 | ETH | -2.85% | -3.76 | REJECTED (strategy fail) |
| bb_20_2.0_optimized | ETH | +0.75% | +10.44 | **EXECUTED** |
| macd_12_26_9_optimized | SOL | +3.72% | +10.57 | **EXECUTED** |

**Key finding:** Most strategies show **NEGATIVE** backtest returns. Only optimized variants pass, and even those have tiny edges (+0.75% to +3.72% over historical data).

### 1.5 Strategy Backtests Are Being Overridden

The cycle logs show a pattern:
1. Strategy backtest returns NEGATIVE → Risk Governor or Orchestrator **should block**
2. But for some cycles, the Orchestrator still approves
3. This suggests the backtest threshold or strategy validation is too permissive

### 1.6 Risk Governor Blocking BTC Due to Position Size Bug

BTC was consistently blocked with "Position pct 14.9x% exceeds max 10%" — but the position limit was supposed to be raised to 20% AND the max_open_positions increased to 5. This suggests the Risk Governor was running with **stale config** or the position size calculation is incorrect.

**Actually, looking more carefully:** The cycles showing "exceeds max 10%" were from BEFORE the config was updated. After the update, BTC was allowed (see cycle_20260520_121044 where BTC was approved).

### 1.7 Chart Monitor Format Bug

The chart monitor had an f-string format error: `"Invalid format specifier '.1f if chart_obs.rsi_value...'` — this means chart observations were NOT being included in decisions during several cycles, degrading decision quality.

### 1.8 Capital Underutilization

- Account equity: ~$10,000
- Invested: ~$2,240 (22.4%)
- Reserve: ~$7,760 (77.6%)
- **The 50% reserve rule is being massively underutilized**

We could deploy 2.5x more capital and still be within the 50% rule. Currently using only 22% of available trading capital.

### 1.9 Trade Frequency Too Low

- Day 1 (May 19): ~3-4 buy attempts, mostly blocked
- Day 2 (May 20): ~3 buy executions in morning cycle
- Total meaningful round-trip trades completed: **1** (BTC partial)
- To make $30/day with $0.84 average profit per trade: **Need 36 trades/day**
- Current rate: **~0.5 trades/day**

---

## 2. METRICS

### 2.1 Current Performance Metrics

| Metric | Value |
|--------|-------|
| **Account equity** | $9,987.82 |
| **Starting equity** | $10,000.00 |
| **Distance from breakeven** | -$12.18 (-0.12%) |
| **Total realized PnL** | ~+$0.84 |
| **Total unrealized PnL** | +$0.63 (open positions) |
| **Net PnL** | ~-$11.00 |
| **Total completed round-trip trades** | ~1 (BTC partial) |
| **Winning trades** | 1 |
| **Losing trades** | 0 (but holding unrealized losses) |
| **Win rate** | 100% (but meaningless with n=1) |
| **Average win** | $0.84 |
| **Average loss** | N/A (no completed losses) |
| **Profit factor** | N/A (insufficient data) |
| **Expected value per trade** | ~$0.84 (but not repeatable) |
| **Daily PnL** | ~-$12/day current trend |
| **Trades per day** | ~0.5 |
| **Average holding time** | ~16 hours |
| **Current exposure** | 22.4% of equity |
| **Max allowed exposure** | 50% of equity |

### 2.2 Required Math for $30–$50/day Target

| Target | Required Daily Return | Required per Trade (at 3 trades/day) | Required per Trade (at 5 trades/day) | Required per Trade (at 7 trades/day) | Required per Trade (at 10 trades/day) |
|--------|----------------------|--------------------------------------|--------------------------------------|--------------------------------------|---------------------------------------|
| $30 | 0.30% | $10.00 | $6.00 | $4.29 | $3.00 |
| $50 | 0.50% | $16.67 | $10.00 | $7.14 | $5.00 |

**Current actual:** $0.84 per completed trade → Need 36–60 trades/day
**Gap:** 72x–120x more trades OR 12x–20x larger profits per trade

### 2.3 Required Position Sizing

To make $10/trade at 3 trades/day:
- Need ~1.0% profit per trade
- With current 5% ($500) position size: need 1.0% move = achievable
- With larger 10% ($1,000) position size: need 0.5% move = easier
- With 15% ($1,500) position size: need 0.33% move = very achievable

**Conclusion:** Position size is NOT the main blocker. Exit logic and strategy quality are.

---

## 3. TOP 3 BLOCKERS

### Blocker #1: Partial-Sell Death Spiral (CRITICAL)
- **Impact:** Prevents meaningful profit-taking, wastes API calls, creates dust positions
- **Evidence:** 118 partial triggers in 24h, quantities halving to zero
- **Fix:** Implement "already_partially_sold" flag; only allow ONE partial per position

### Blocker #2: Strategy Backtests Show Negative Edge
- **Impact:** System is trading strategies that lose money historically
- **Evidence:** ma_crossover_20 at -3.53% Sharpe, bb_20_2.0 at -1.02%
- **Fix:** Only execute strategies with >+5% backtest return AND Sharpe > 2.0

### Blocker #3: No Complete Round-Trip Trades
- **Impact:** Capital is tied up in stale positions, no profit realization
- **Evidence:** Only 1 partial exit in 24+ hours; positions held 16-23 hours
- **Fix:** Implement time-based exits (max 8h hold), better stop-loss, take-profit levels

---

## 4. BIGGEST LOSING FACTOR

**The partial-sell death spiral is the #1 profit killer.** Here's why:

1. **It prevents proper exit management** — Instead of having a clean position with a runner, the system fragments the position into dust
2. **It consumes API rate limits** — 118 triggers = 118 API calls for zero profit
3. **It hides the real problem** — The logs look "active" but no actual profit is being generated
4. **It prevents new entries** — Dust positions still count as "open positions" blocking new trades
5. **The dust position bug was "fixed" but the root cause (repeated partial selling) was NOT**

---

## 5. STRATEGY PERFORMANCE ANALYSIS

### 5.1 Backtest Results by Strategy

| Strategy | Trades | Total Return | Sharpe | Verdict |
|----------|--------|-------------|--------|---------|
| ma_crossover_20 | 18-22 | -3.53% to -6.61% | -9.44 to -17.55 | ❌ REJECT |
| bb_20_2.0 | 4-5 | -1.02% | -2.73 | ❌ REJECT |
| rsi_14_30_70 | 4-7 | -2.85% to -3.40% | -3.76 to -4.83 | ❌ REJECT |
| bb_20_2.0_optimized | 2-4 | +0.75% to +3.72% | +4.17 to +10.57 | ⚠️ MARGINAL |
| rsi_14_30_70_optimized | 2-3 | +0.75% | +10.44 | ⚠️ MARGINAL |
| macd_12_26_9_optimized | 4 | +3.72% | +10.57 | ⚠️ MARGINAL |

**Conclusion:** The "optimized" strategies are barely profitable in backtests. The base strategies are clearly losing money. **No strategy has shown consistent >5% returns with >20 trades.**

### 5.2 Strategy Selection is Not Working

The system randomly picks from a strategy pool, but:
- Most strategies lose money
- The "optimized" versions have tiny edges that don't scale
- There's no strategy leaderboard or performance tracking
- Strategies are not regime-specific

---

## 6. EXIT LOGIC ANALYSIS

### 6.1 Current Exit Rules

| Rule | Trigger | Performance |
|------|---------|-------------|
| partial_profit_1 | +0.5% | **BUG: Repeats indefinitely** |
| partial_profit_2 | +1.0% | Never reached (death spiral kills position first) |
| take_profit | +2.0% | Never reached in current data |
| trailing_stop | -0.5% from peak | Rarely triggered, only on strong moves |
| stop_loss | -2.0% | NOT triggered despite ETH being -0.12% for 19h |
| time_exit | 24h | Reached but may be too long |
| breakeven | Price = entry + fees | Rarely used |

### 6.2 Problems

1. **partial_profit_1 repeats** — Should fire ONCE per position
2. **stop_loss at -2% is too wide** — For crypto, -1% or even -0.5% would be better
3. **time_exit at 24h is too long** — Should be 4-8 hours max
4. **No breakeven stop** — Should move stop to breakeven after +0.5%
5. **trailing_stop at 0.5% from peak is too tight** — Should be 1.0% for runners
6. **Fee breakeven at 0.5% is too conservative** — Alpaca crypto fees are 0% for makers, small for takers

---

## 7. POSITION SIZING ANALYSIS

### 7.1 Current Sizing

- Fixed ~$500 per trade (5% of $10,000)
- Max 5 open positions
- Total max exposure: 25% of equity
- **Actual exposure: 22.4%**

### 7.2 Problems

1. **Too conservative** — Using only 22% when 50% is allowed
2. **No dynamic sizing** — Same $500 whether signal is weak or strong
3. **No correlation adjustment** — All 3 assets are crypto, highly correlated
4. **No volatility adjustment** — BTC ($77k) and SOL ($85) have very different volatilities

### 7.3 Opportunity

If we increased position size to $1,000 (10%) per trade:
- Same $10 profit target requires only 1.0% move (vs 2.0% now)
- With 3 trades/day at 1.0% profit = $30/day target ACHIEVABLE
- Still within 50% reserve rule (3 positions × 10% = 30%)

---

## 8. TEAM PERFORMANCE AUDIT

| Team | Status | Problem |
|------|--------|---------|
| **Strategy Research** | ❌ UNDERUSED | Only 3 strategies researched, 10 in backlog. No new strategies implemented since RSI Range. |
| **Backtesting** | ❌ UNDERUSED | Backtests run but results are negative. No validation that strategies actually work. |
| **Technical Analysis** | ⚠️ PARTIAL | Agents run but timeout. Chart monitor has bugs. Signals are not regime-specific. |
| **Risk** | ⚠️ PARTIAL | Risk Governor works but position sizing is static. Death spiral is NOT caught. |
| **Execution** | ❌ BROKEN | Position monitor has fatal partial-sell bug. Exits are not tracked properly. |
| **Self-Evolution** | ❌ IDLE | No learning from losing trades. No strategy leaderboard. No performance tracking. |
| **Market Intelligence** | ⚠️ PARTIAL | Chart monitor added but buggy. No missed opportunity tracking. |

**Fix required:** Execution team must fix partial-sell bug immediately. Strategy Research must implement backtested profitable strategies. Self-Evolution must start tracking every trade's performance.

---

## 9. MARKET REGIME

Current regime (from chart monitor logs):
- BTC: uptrend, low volatility, RSI ~73 (overbought)
- ETH: ranging, low volatility, RSI ~71 (overbought)
- SOL: ranging, normal volatility, RSI ~63 (neutral)

**Problem:** RSI-based entries in overbought conditions (RSI > 70) are likely to reverse. The system is buying at local tops.

---

## 10. PROFITABILITY MATH: CAN WE REACH $30–$50/DAY?

### Current System Capability

| Scenario | Trades/Day | Avg Profit/Trade | Daily Profit | Verdict |
|----------|-----------|-----------------|--------------|---------|
| Current actual | 0.5 | $0.84 | $0.42 | ❌ FAIL |
| Optimistic (fix bugs) | 3 | $3.00 | $9.00 | ❌ FAIL |
| Aggressive (bigger size) | 3 | $10.00 | $30.00 | ⚠️ POSSIBLE |
| High frequency | 7 | $5.00 | $35.00 | ⚠️ POSSIBLE |

**Realistic assessment:** With current strategy quality and exit logic, even fixing all bugs would yield ~$5–$10/day. To reach $30–$50/day, we need:
1. ✅ Fix exit logic (prevents profit destruction)
2. ✅ Increase position size to 10% ($1,000/trade)
3. ✅ Improve strategy edge from ~0.5% to ~1.0% per trade
4. ✅ Increase trade frequency to 3–5/day with quality signals
5. ✅ Add regime-aware strategy selection

**Verdict: The current system cannot reliably support $30–$50/day. After bug fixes and strategy improvements, $15–$25/day is realistic. $30–$50/day requires better strategies AND higher frequency.**

---

## 11. JARVIS DECISION: IMMEDIATE ACTIONS

### Action 1: FIX THE PARTIAL-SELL DEATH SPIRAL (NOW)
- Add `partial_sold` flag to position state
- Only allow ONE partial_profit_1 trigger per position
- Fix dust quantity bug properly (not just minimum check)
- Test with existing positions

### Action 2: IMPROVE EXIT LOGIC (TODAY)
- Tighten stop_loss from -2% to -1%
- Add breakeven stop after +0.5%
- Reduce time_exit from 24h to 8h
- Improve trailing_stop to 1% from peak
- Lower fee breakeven to 0.2% (Alpaca crypto fees are low)

### Action 3: INCREASE POSITION SIZE (TODAY)
- Change from fixed $500 to 10% of equity ($1,000)
- Add confidence-adjusted sizing (strong signal = 15%, weak = 5%)
- Track per-asset allocation

### Action 4: IMPLEMENT STRATEGY LEADERBOARD (TODAY)
- Track every strategy's real performance
- Only execute top 3 strategies
- Auto-demote strategies with 3 consecutive losses

### Action 5: RESEARCH BETTER STRATEGIES (THIS WEEK)
- Backtest RSI Range Trading on BTC/ETH/SOL hourly
- Implement Momentum Breakout strategy
- Implement Trend Pullback strategy
- Add short-side logic for ranging markets

### Action 6: ADD DAILY PROFIT TARGET TRACKER (TODAY)
- Track daily PnL vs $30–$50 target
- Enter "improvement mode" if daily target missed by >50%
- Reduce trade size if 2 consecutive losing days

### Action 7: IMPLEMENT "DO NOT TRADE" MODE (TODAY)
- If all assets RSI > 70 or < 30 → no new entries
- If VIX equivalent > threshold → no new entries
- If consecutive losses > 2 → 4h cooldown

---

## 12. SUCCESS CRITERIA

Before declaring the system "progressing toward $30–$50/day":

1. **Partial-sell bug fixed** — Zero dust trades in 24h
2. **Complete round-trip trades** — At least 3 completed trades/day
3. **Positive realized PnL** — Daily realized PnL > $0 for 3 consecutive days
4. **Win rate > 50%** — More wins than losses
5. **Average win > average loss** — Win/loss ratio > 1.0
6. **Strategy edge confirmed** — At least 1 strategy with >+5% backtest return
7. **No stale positions** — Max hold time < 8 hours
8. **Capital utilization** — Exposure between 30–50% during active periods

---

## 13. NEXT MEASUREMENT CHECKPOINT

**Tomorrow, May 21, 14:00 CEST:**
- Verify partial-sell bug is fixed
- Count completed round-trip trades
- Calculate realized PnL
- Measure win rate and average win/loss
- Report on capital utilization

---

## 14. CEO REPORTING

| Field | Value |
|-------|-------|
| CEO approval required | **NO** |
| CEO informed | **YES** |
| Actions in progress | 7 immediate fixes |
| Expected improvement | $5–$15/day after bug fixes; $15–$25/day after strategy improvements |
| Realistic $30–$50/day timeline | 7–14 days if all fixes work |

---

*— Jarvis, Junior CEO*
*14:30 CEST, May 20, 2026*
