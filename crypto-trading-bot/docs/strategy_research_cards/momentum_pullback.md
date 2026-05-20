# STRATEGY RESEARCH CARD

## Strategy Name

Momentum Pullback / Trend Continuation

## Source

https://thrive.fi/blog/trading/momentum-trading-crypto
https://www.altrady.com/blog/crypto-trading-strategies/pullback-trading-strategy

## Source Type

- [ ] GitHub open-source repo
- [ ] TradingView public strategy/indicator
- [x] Experienced trader / crypto education site
- [ ] Quant researcher
- [ ] YouTube strategy explanation
- [ ] Trading book / classic concept
- [ ] Other

## Market Type

- [x] Trending markets
- [ ] Ranging/sideways markets
- [x] High volatility
- [ ] Low volatility

## Best Asset

Crypto (BTC, ETH, SOL) — works best in trending crypto markets

## Best Timeframe

1h, 4h (for pullbacks within larger trends)

## Entry Rules

### Core Concept
"Don't chase extremes — enter on the first pullback after momentum ignites"

### Long Entry (Uptrend Pullback)
1. **Trend confirmed:** Price above EMA 20 and EMA 50, ADX > 25
2. **Momentum spike:** Strong bullish candle with volume spike (1.5x average)
3. **Pullback begins:** Price retraces to EMA 20 or 38.2% Fibonacci level
4. **Reversal confirmation:** Bullish candle at support with volume
5. **Entry:** On close of reversal candle

### Short Entry (Downtrend Pullback)
1. **Trend confirmed:** Price below EMA 20 and EMA 50, ADX > 25
2. **Momentum spike:** Strong bearish candle with volume spike
3. **Pullback begins:** Price retraces to EMA 20 or 38.2% Fibonacci
4. **Reversal confirmation:** Bearish candle at resistance with volume
5. **Entry:** On close of reversal candle

## Exit Rules

1. **Take profit 1:** Prior swing high (for longs)
2. **Take profit 2:** 1.618 Fibonacci extension from pullback
3. **Trail stop:** Move to break-even after TP1

## Stop-Loss

Below the pullback low (for longs)  
Above the pullback high (for shorts)

## Take-Profit

- Level 1: Prior swing high (1:1.5 risk-reward)
- Level 2: 1.618 Fibonacci extension (1:3 risk-reward)

## Partial-Profit Logic

- Sell 50% at Level 1 (prior swing high)
- Move stop to break-even
- Let runner to Level 2 (Fibonacci extension)

## Trailing-Stop Logic

- After Level 1: Stop at entry price
- After Level 2: Trail at -0.5% from highest

## Indicators Required

| Indicator | Parameters | Purpose |
|-----------|-----------|---------|
| EMA | 20, 50 | Trend direction |
| ADX | 14 | Trend strength (>25 = strong trend) |
| Volume | Current vs 20-bar average | Confirm momentum |
| Fibonacci | 38.2%, 50%, 61.8% | Pullback depth targets |
| RSI | 14 | Oversold/overbought on pullback |

## Best Regime

- Strong trending markets (ADX > 25)
- Momentum-driven moves (volume spikes)
- Crypto bull markets or bear markets (not chop)

## Worst Regime

- Ranging/sideways markets (no trend to continue)
- Low volatility (no momentum to pull back from)
- Choppy markets (false trend signals)
- Low volume (no momentum confirmation)

## Why It May Work

1. **Trends persist** — "The trend is your friend"
2. **Optimal entry timing** — Enter after pullback, not at peak
3. **Good risk-reward** — Stop below pullback low, target prior high
4. **High probability** — Pullbacks in strong trends usually continue
5. **Volume confirms** — Momentum spikes show institutional interest

## Known Weaknesses

1. **Requires clear trend** — No trend = false signals
2. **Needs volume confirmation** — Low volume pullbacks may keep falling
3. **Late entry possible** — Pullback may become reversal
4. **Multiple pullbacks** — Price can pull back multiple times before continuing
5. **Trend change risk** — What looks like pullback becomes reversal

## Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| Pullback becomes reversal | HIGH | ADX > 25 filter |
| False trend signal | MEDIUM | EMA alignment filter |
| Late entry | LOW | Enter on reversal candle |
| Multiple pullbacks | MEDIUM | Wait for volume confirmation |

## Implementation Complexity

- [ ] Simple
- [x] Medium (4-5 indicators, conditional logic)
- [ ] Complex

## Backtest Priority

- [x] High — implement and backtest immediately
- [ ] Medium
- [ ] Low

## Jarvis Recommendation

**PROMISING — Best for trending crypto markets.**

This strategy directly addresses our need for TREND strategies. Our previous strategies (RSI Range, MA Crossover) were mean-reversion or trend-agnostic. They failed because crypto hourly is trending.

**Key advantages:**
- Designed for trending markets — matches crypto hourly behavior
- Good risk-reward (1:1.5 to 1:3)
- Volume confirmation reduces false signals
- Multiple exit levels (partial profit + runner)

**Critical requirement:**
- Must confirm ADX > 25 (strong trend)
- Must wait for pullback, not chase momentum
- Must have volume spike on momentum candle

**Recommendation:** Implement with these modifications:
1. Add EMA alignment filter (price above both EMAs for longs)
2. Require ADX > 25
3. Require volume spike >1.5x average
4. Use partial-profit and runner logic
5. Only trade in trending regimes (not ranging)

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

- Research notes: `docs/strategy_research_cards/momentum_pullback.md`
- Implementation: PENDING
- Tests: PENDING
- Backtest results: PENDING
