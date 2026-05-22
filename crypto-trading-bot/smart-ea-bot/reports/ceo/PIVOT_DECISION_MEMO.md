# PIVOT DECISION MEMO — Smart EA Bot Company
**From:** Jarvis, Junior CEO  
**To:** Jitesh Kumar, CEO  
**Date:** Friday, May 22, 2026 — 19:08 CEST  
**Subject:** Strategic Pivot to Higher-Timeframe Trend Following
**Reference:** round-4-complete-no-edge (tag `88f12ab`)

---

## 1. ACKNOWLEDGEMENT CHECKLIST

- [x] Round 4 committed, repo tagged `round-4-complete-no-edge`
- [x] Only escalation triggers are the 7 listed
- [x] Will NOT ask CEO approval for strategy class, timeframe, bot design, gate redesign, or paper-trade start
- [x] Pivot decision memo published NOW (not "within 5 days")
- [x] First new bot reaches gate report within 10 days (by June 1, 2026)
- [x] Exercising full Junior CEO authority

---

## 2. WHAT WE LEARNED FROM ROUNDS 1-4 (HONEST, NO HEDGING)

Eleven bots across seven strategy classes failed. The pattern is clear: **crypto 5m scalping has no edge with conventional technical indicators on the available data.** Mean reversion loses because crypto 5m noise overwhelms signal. Trend pullback either fires constantly (catastrophic overtrading) or never fires (EMA alignment too strict). Breakout retests never confirm on 5m. Volatility squeezes detect events but direction is coin-flip. VWAP reversion overtrades 2000+ times in 35 days. Multi-timeframe momentum produces zero signals because EMA alignment at 5m doesn't capture hourly trends.

The deeper truth: **we were trying to extract alpha from noise.** Crypto 5m bars are dominated by microstructure noise, arbitrage flows, and random walk behavior. Technical indicators — RSI, EMA crossovers, Bollinger Bands — were designed for slower markets. They lag on crypto. They generate false signals faster than true ones. The 0.10% fee + 0.05% slippage model is not the problem; the problem is that no signal survives the noise.

We also learned that **Alpaca crypto data is insufficient** (~35 days maximum, regardless of requested range). This means walk-forward validation is impossible at 5m granularity. Any "profitable" result on 35 days is almost certainly curve-fitted or lucky.

**Bottom line:** The scalping hypothesis is disproven. Not with "more tuning." Disproven with evidence from 11 independent bot attempts.

---

## 3. NEW STRATEGY CLASS CHOSEN: HIGHER-TIMEFRAME TREND FOLLOWING

**Thesis:** Crypto has genuine trend persistence at 4h and daily timeframes. This is well-documented in academic literature (e.g., Liu & Tsyvinski 2018, "Risks and Returns of Cryptocurrency"). At longer timeframes, the signal-to-noise ratio improves. Trends last days to weeks. Momentum persists because of retail herding behavior, institutional rebalancing, and macro narratives. A simple trend-following system — enter on pullback in established trend, exit on trend break — may have positive expectancy where scalping failed.

**Why this may have edge where scalping failed:**
- 4h/daily trends are driven by macro factors, not microstructure noise
- Fewer trades = lower fee drag (critical for PF > 1.2)
- Momentum strategies have demonstrated positive alpha in crypto academic literature
- Technical indicators work better when the signal isn't drowned by tick-level noise
- Can use Yahoo Finance data (1+ years) for validation

---

## 4. ALTERNATIVES CONSIDERED AND REJECTED

| Alternative | Rejection Reason |
|-------------|------------------|
| **Equities (SPY/QQQ) on Alpaca** | CEO scope is crypto-only. Good for proof-of-concept but doesn't advance the crypto trading mission. Deferred as Option B if crypto fails. |
| **Machine Learning (LSTM/XGBoost)** | Insufficient data for training (35 days). Would require Yahoo Finance first anyway. Risk of overfitting is high. Defer until basic trend following is proven/disproven. |
| **Market Making / Grid** | CEO explicitly excluded. High capital requirement, inventory risk, and "no martingale" policy makes this class unsuitable. |
| **Sentiment / News-driven** | Requires external data feeds (Twitter, news APIs). Adds complexity before proving basic price-based edge. Defer to Phase 2 if price-based strategies work. |
| **Arbitrage (cross-exchange)** | Requires multiple exchange APIs and latency optimization. Beyond current scope. |
| **Options strategies** | Alpaca doesn't support crypto options. Not viable. |
| **Portfolio / ensemble approach** | Ensembling losing strategies produces a losing portfolio. Need at least one profitable component first. |

**Decision:** Trend following on 4h/daily crypto is the highest-probability path with available tools and data.

---

## 5. VALIDATION GATE SET (REDESIGNED FOR HIGHER TIMEFRAME)

**Rationale for redesign:** 4h/daily timeframe naturally produces fewer trades. Requiring 100 trades at daily granularity would need 100+ days minimum, and 4h would need ~25 days. The spirit of the gate (statistical significance) is preserved while adapting to the new timeframe.

| Gate | Old (5m scalping) | New (4h/daily trend) | Justification |
|------|-------------------|----------------------|---------------|
| Profit factor | > 1.2 | > 1.3 | Fewer trades = need higher edge per trade |
| Minimum trades | ≥ 100 | ≥ 30 (daily) / ≥ 100 (4h) | Statistically significant for slower strategies |
| Max drawdown | < 10% | < 15% | Trend following naturally has deeper drawdowns; 15% is acceptable for PF > 1.3 |
| Fee survival | Survives 2x fees | Survives 1.5x fees | Fewer trades = lower fee drag; 1.5x is still conservative |
| Walk-forward | 70% positive windows | 2 of 3 OOS windows | Longer timeframe = fewer windows possible |
| Monthly stability | No 40% month | No single 30-day period > 50% profit | Adapted to crypto's higher volatility |
| Look-ahead | Strict | Strict | Non-negotiable |
| QA tests | Required | Required | Non-negotiable |

**Lock:** These gates are locked NOW. No bot will be evaluated against different gates.

---

## 6. FIRST TESTABLE BOT SPECIFICATION: "TREND RIDER v5"

**Hypothesis:** Crypto trends persist at 4h timeframe. Enter on EMA pullback in established trend. Exit on trend break or trailing stop.

**Timeframe:** 4h primary, 1d confirmation

**Assets:** BTC/USD, ETH/USD

**Entry Logic (LONG):**
1. 4h EMA 12 > EMA 26 > EMA 50 (strong uptrend)
2. Price pulls back to EMA 12 (deviation > 1 ATR from EMA 12)
3. RSI(14) between 40-55 (not overbought, showing momentum)
4. Volume > 1.2x 20-bar average
5. 1d EMA alignment confirms same direction (daily EMA 12 > EMA 26)

**Entry Logic (SHORT):**
1. 4h EMA 12 < EMA 26 < EMA 50 (strong downtrend)
2. Price rallies to EMA 12 (deviation > 1 ATR)
3. RSI(14) between 45-60
4. Volume > 1.2x average
5. 1d EMA alignment confirms same direction

**Exit Logic:**
- Stop loss: 2.5 ATR from entry
- Take profit: Trailing stop at 3 ATR from highest/lowest price since entry
- Time stop: Exit after 10 bars (40 hours) if neither SL nor TP hit
- Trend break exit: If EMA alignment reverses, exit immediately

**Risk Parameters:**
- Risk per trade: 0.5% equity (higher than scalping's 0.25% because fewer trades = need larger position)
- Max position size: $200 (up from $100 because 4h signals are higher quality)
- Max concurrent positions: 2
- No pyramiding

**Kill Conditions (when bot must stop):**
- 3 consecutive losing trades
- Drawdown > 10% from peak equity
- No signal for 30 days (strategy may be out of sync with market)

---

## 7. TIMELINE

| Milestone | Date | Deliverable |
|-----------|------|-------------|
| Today | May 22 | Pivot memo published, gates locked |
| Day 1-2 | May 23-24 | Yahoo Finance data fetcher, fetch 1 year 4h BTC/ETH |
| Day 3-4 | May 25-26 | Implement Trend Rider v5, backtest on design period |
| Day 5-6 | May 27-28 | Walk-forward validation on 3 OOS windows |
| Day 7-8 | May 29-30 | Fee sensitivity, QA tests, risk review |
| Day 9-10 | May 31-Jun 1 | Gate report published, PASS/FAIL decision |

**If PASS by June 1:** Start Alpaca paper trading autonomously per approved limits.

**If FAIL by June 1:** Analyze why, decide next pivot (equities on Alpaca or ML approach).

---

## 8. AGENT ASSIGNMENTS

| Agent | Task | Due |
|-------|------|-----|
| Strategy Research | Design Trend Rider v5, validate hypothesis against literature | May 23 |
| Architect | Build Yahoo Finance adapter, 4h data pipeline | May 24 |
| Backtest | Run backtest on design period, produce metrics | May 26 |
| QA | Verify no look-ahead, deterministic replay | May 28 |
| Risk Manager | Review risk parameters, approve gates | May 28 |
| GitHub Manager | Create issue for Trend Rider v5, branch `feature/trend-rider-v5` | May 22 |

---

## 9. SAFETY CONFIRMATIONS

| Control | Status |
|---------|--------|
| **Trading** | 🔴 OFF |
| **Daemon** | 🔴 STOPPED |
| **ENTRY_LOCK** | 🟢 ACTIVE |
| **Paper trading** | 🔴 BLOCKED until Trend Rider passes gates |
| **Live money** | 🔴 BLOCKED (CEO approval required) |
| **Risk Governor** | 🟢 ACTIVE, hard-coded limits |
| **Broker Reconciliation** | 🟢 ACTIVE |
| **Duplicate Prevention** | 🟢 ACTIVE |
| **Round 1-4 code** | 🟢 Preserved in Git (`round-4-complete-no-edge`) |

---

## 10. CEO ESCALATION TRIGGERS

**None triggered.** This pivot is fully within Junior CEO authority.

**Next expected escalation:** Only if Trend Rider passes gates AND I want to increase order size above $200 or add assets beyond BTC/ETH.

---

## CONCLUSION

Rounds 1-4 proved that crypto 5m scalping has no edge. The scalping hypothesis is dead. 

Trend following on 4h/daily is the next most promising hypothesis based on academic evidence and the signal-to-noise dynamics of crypto. If this fails after rigorous testing, I will escalate to the CEO with evidence that no conventional technical strategy works on available crypto data, and recommend either equities pivot or advanced ML approaches.

**I am exercising my authority as Junior CEO. No permission requested. Results will be reported.**

🦊 **Jarvis — Junior CEO, Smart EA Bot Company**
