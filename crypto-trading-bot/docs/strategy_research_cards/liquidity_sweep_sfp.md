# STRATEGY RESEARCH CARD

## Strategy Name

Liquidity Sweep / Swing Failure Pattern (SFP) Reversal

## Source

https://dypto-crypto.com/resources/swing-failure-pattern/

## Source Type

- [ ] GitHub open-source repo
- [ ] TradingView public strategy/indicator
- [x] Experienced trader / crypto education site
- [ ] Quant researcher
- [ ] YouTube strategy explanation
- [ ] Trading book / classic concept
- [ ] Other

## Market Type

- [ ] Trending markets
- [x] Ranging/sideways markets (best)
- [x] High volatility
- [ ] Low volatility
- [ ] Specific: crypto manipulation conditions

## Best Asset

Crypto (BTC, ETH, SOL) — works best where stop-hunts and liquidity grabs are common

## Best Timeframe

1h, 4h, daily (higher timeframes reduce noise)

## Entry Rules

### Bullish SFP (Long Entry)
1. **Liquidity sweep:** Price briefly breaks below a prior swing low
2. **Failure to hold:** Candle fails to close below that level (rejection)
3. **Sharp reversal:** Price reverses upward with momentum
4. **Confirmation:** Next candle closes above the prior swing low (structure restored)
5. **Entry:** On confirmation candle close

### Bearish SFP (Short Entry)
1. **Liquidity sweep:** Price briefly spikes above a prior swing high
2. **Failure to hold:** Candle fails to close above that level (rejection)
3. **Sharp reversal:** Price reverses downward with momentum
4. **Confirmation:** Next candle closes below the prior swing high
5. **Entry:** On confirmation candle close

## Exit Rules

1. **Target 1:** Prior swing high (for longs) / prior swing low (for shorts) — nearest liquidity
2. **Target 2:** Opposite side of range
3. **Trail stop:** Move to break-even after Target 1 hit

## Stop-Loss

Below the failed low (for longs) — the liquidity sweep low itself  
Above the failed high (for shorts) — the liquidity sweep high itself

## Take-Profit

- Level 1: Nearest prior swing point (1:1 risk-reward minimum)
- Level 2: Opposite side of range (higher reward)

## Partial-Profit Logic

- Sell 50% at Level 1 (nearest prior swing)
- Move stop to break-even
- Let runner to Level 2 (opposite range side)

## Trailing-Stop Logic

- After Level 1 hit: Move stop to entry price
- After Level 2 hit: Trailing stop at -0.5% from highest (for longs)

## Indicators Required

| Indicator | Parameters | Purpose |
|-----------|-----------|---------|
| Swing High/Low | Window = 10-20 bars | Identify liquidity levels |
| Volume | Current vs average | Confirm manipulation (spike on sweep) |
| Candlestick | Wick analysis | Identify rejection (long wick) |
| Structure | Prior swing levels | Targets and invalidation |

## Best Regime

- Ranging/sideways markets with clear swing levels
- Markets with visible support/resistance
- High volatility where stops cluster
- Post-trend exhaustion (end of trending move)

## Worst Regime

- Strong trending markets (SFPs fail, trend continues)
- Low volatility (no liquidity to sweep)
- News-driven momentum (manipulation overwhelmed)
- Choppy markets without clear levels

## Why It May Work

1. **Smart money leaves footprints** — Liquidity sweeps reveal institutional manipulation
2. **Risk is well-defined** — Invalidation level is clear (the failed breakout level)
3. **High R:R potential** — Small risk, large reward to opposite side of range
4. **Works in crypto specifically** — Crypto markets are manipulated with stop-hunts
5. **Contrarian edge** — Most traders get trapped in false breakouts; SFP traders profit from them

## Known Weaknesses

1. **Requires clear levels** — No levels = no setup
2. **Needs confirmation** — Entering before confirmation risks catching falling knife
3. **Trending markets destroy SFPs** — In strong trends, "failed" breakouts become real breakouts
4. **Whipsaw risk** — Price can sweep, reverse, then sweep again
5. **Crypto-specific** — May not work in regulated/liquid markets
6. **Requires patience** — Setups are relatively rare

## Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| False SFP (trend continuation) | HIGH | Require confirmation candle |
| Multiple sweeps | MEDIUM | Wait for structure restoration |
| Missed entry | LOW | Confirmation provides clear entry |
| Trend continuation | HIGH | Only trade in ranging regime |

## Implementation Complexity

- [x] Simple (2-3 indicators, basic rules)
- [ ] Medium
- [ ] Complex

## Backtest Priority

- [x] High — implement and backtest immediately
- [ ] Medium
- [ ] Low

## Jarvis Recommendation

**PROMISING for crypto — addresses our weakness in ranging markets.**

Our RSI Range strategy failed because it tried to mean-revert in a trending market. This SFP strategy is DIFFERENT:
- It waits for a sweep (extreme)
- Then enters on confirmation of reversal
- Risk is clearly defined
- Works specifically in crypto where manipulation is common

**Key advantage for our project:**
- SFPs happen in crypto hourly data — we saw BTC make false moves today
- Small risk, large reward
- Contrarian — most traders get trapped

**Critical requirement:**
- Must detect ranging regime first
- Must wait for confirmation (not enter on sweep)
- Must not trade in strong trends

**Recommendation:** Implement with regime filter:
1. Only trade when ADX < 25 (no strong trend)
2. Only trade when RSI is neutral (40-60)
3. Require confirmation candle close
4. Use partial-profit and runner logic

---

## VALIDATION PIPELINE STATUS

### Phase 1: Research
- [x] Source verified as public/recognized
- [x] Rules extracted clearly
- [x] Hypothesis documented
- [x] Weaknesses identified
- [x] Risk assessed

### Phase 2: Implementation
- [ ] Python implementation created
- [ ] Unit tests written
- [ ] No-lookahead check implemented
- [ ] Code reviewed

### Phase 3: Backtest
- [ ] 6+ months hourly data (BTC, ETH, SOL)
- [ ] Fees included
- [ ] Slippage included
- [ ] ≥10 trades per asset
- [ ] All metrics calculated

### Phase 4: Evaluation
- [ ] Passes minimum thresholds
- [ ] No-lookahead clean
- [ ] Regime fit confirmed

### Phase 5: Promotion
- [ ] Decision: PENDING

---

## DECISION LOG

| Date | Decision | By | Reason |
|------|----------|-----|--------|
| 2026-05-21 | Research complete | Jarvis | Strategy extracted from crypto education site |
| | | | |

---

## FILES

- Research notes: `docs/strategy_research_cards/liquidity_sweep_sfp.md`
- Implementation: PENDING
- Tests: PENDING
- Backtest results: PENDING
