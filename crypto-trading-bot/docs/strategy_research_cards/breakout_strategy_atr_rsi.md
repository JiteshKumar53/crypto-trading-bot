# STRATEGY RESEARCH CARD

## Strategy Name

ATR + RSI Breakout Strategy

## Source

https://github.com/Aksee123/Breakout_Strategy

## Source Type

- [x] GitHub open-source repo
- [ ] TradingView public strategy/indicator
- [ ] Experienced trader
- [ ] Quant researcher
- [ ] YouTube strategy explanation
- [ ] Trading book / classic concept
- [ ] Other

## Market Type

- [x] Trending markets (breakout continuation)
- [ ] Ranging/sideways markets
- [x] High volatility
- [ ] Low volatility

## Best Asset

Crypto (BTC, ETH, SOL) — works on trending crypto assets

## Best Timeframe

1h, 4h (recommended by author), daily for swing

## Entry Rules

1. **Bullish breakout:** Price breaks above recent swing high (lookback period configurable)
2. **Bearish breakout:** Price breaks below recent swing low (lookback period configurable)
3. **Trend filter:** Price above EMA 233 (for longs), below EMA 233 (for shorts)
4. **Volatility filter:** ATR confirms sufficient volatility (not in compressed range)
5. **Volume confirmation:** Volume spike on breakout candle
6. **RSI filter:** RSI confirms momentum direction (not overbought for longs)
7. **MACD filter (optional):** MACD confirms momentum direction
8. **Session filter (optional):** Only trade during specific hours

## Exit Rules

1. **Take profit:** Configurable percentage from entry (or disabled for swing-only)
2. **Stop loss:** Two options:
   - Swing-based: Stop below recent swing low (for longs)
   - Fixed percentage: Configurable fixed SL percentage
3. **Risk-reward:** Optional 1:1 mode where TP = SL distance

## Stop-Loss

- Swing-based: Below recent swing low (for longs)
- Fixed: Configurable percentage (suggest 1.5% for crypto hourly)

## Take-Profit

- Configurable percentage (suggest 3% for crypto hourly)
- Optional 1:1 risk-reward mode

## Partial-Profit Logic

Not included in original — would need to add:
- Sell 50% at 1× risk (1.5% profit)
- Move stop to break-even
- Let runner with trailing stop

## Trailing-Stop Logic

Not included in original — would need to add:
- Activate trailing stop after +0.8% profit
- Trail at -0.8% from highest

## Indicators Required

| Indicator | Parameters | Purpose |
|-----------|-----------|---------|
| Swing High/Low | Window = 20 bars | Breakout levels |
| EMA | Period = 233 | Trend direction filter |
| ATR | Period = 14 | Volatility filter |
| RSI | Period = 14 | Momentum confirmation |
| MACD | Fast=12, Slow=26, Signal=9 | Optional momentum filter |
| Volume | Current vs average | Breakout confirmation |

## Best Regime

- Strong trending markets (uptrend or downtrend)
- High volatility with clear swing levels
- Markets with sustained directional moves

## Worst Regime

- Choppy/ranging markets with false breakouts
- Low volatility (ATR compressed)
- Whipsaw conditions around EMA 233
- News-driven sudden reversals

## Why It May Work

1. **Breakouts have directional edge** — When price breaks a significant swing level, momentum often continues
2. **Multiple filters reduce false signals** — EMA, ATR, volume, RSI all must align
3. **Trend alignment** — Only trades in direction of EMA 233 trend
4. **Risk management built-in** — Clear SL and TP levels
5. **Configurable** — Can adapt parameters per asset/timeframe

## Known Weaknesses

1. **False breakouts** — Crypto is notorious for fake breakouts that reverse immediately
2. **Late entries** — Breakout confirmation often means missing the best price
3. **EMA 233 lag** — Slow EMA may miss early trend changes
4. **No partial profit** — All-or-nothing exits miss scaling opportunities
5. **No runner logic** — Winners cut short at fixed TP
6. **Session filter may miss moves** — Crypto trades 24/7, session filters reduce opportunities

## Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| False breakout | HIGH | Multiple filters (EMA, ATR, volume, RSI) |
| Late entry | MEDIUM | Use limit orders near breakout level |
| Trend reversal | MEDIUM | EMA 233 filter + SL |
| Whipsaw | HIGH | Wider SL or avoid choppy regimes |
| Gap risk | MEDIUM | Fixed SL limits max loss |

## Implementation Complexity

- [ ] Simple
- [x] Medium (4-5 indicators, conditional logic)
- [ ] Complex

## Backtest Priority

- [x] High — implement and backtest immediately
- [ ] Medium
- [ ] Low

## Jarvis Recommendation

**PROCEED WITH CAUTION — High potential but significant risks.**

This strategy addresses our key need: **trending market strategies**. Our RSI Range strategy failed because crypto hourly is trending, not ranging. Breakout strategies are designed for trending markets.

**Strengths for our project:**
- Multiple filters reduce false signals (unlike simple MA crossover)
- Built-in risk management
- Configurable per asset
- Publicly available with clear rules

**Concerns:**
- False breakouts are crypto's biggest enemy
- Needs partial-profit and runner logic (not in original)
- EMA 233 is very slow — may miss early moves

**Recommendation:** Implement with modifications:
1. Add partial-profit logic (sell 50% at 1× risk)
2. Add trailing-stop runner logic
3. Tighten filters for crypto hourly (reduce false signals)
4. Add regime detection — only trade in trending regimes

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
| 2026-05-21 | Research complete | Jarvis | Strategy extracted from GitHub repo |
| | | | |

---

## FILES

- Research notes: `docs/strategy_research_cards/breakout_strategy_atr_rsi.md`
- Implementation: PENDING
- Tests: PENDING
- Backtest results: PENDING
