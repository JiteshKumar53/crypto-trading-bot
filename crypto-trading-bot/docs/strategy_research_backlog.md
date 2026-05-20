---
summary: "Strategy Research Backlog"
read_when:
  - New strategies to implement, backtest, or review
---

# Strategy Research Backlog

## Strategy Research Cards

### STRATEGY CARD #001: RSI Range Trading
- **Strategy name:** RSI Range Trading
- **Source:** Kraken Learn / Experienced Crypto Traders
- **Market type:** Crypto (BTC, ETH, SOL)
- **Timeframe:** 1-hour
- **Entry rules:**
  - Price approaches support (bottom of established range)
  - RSI falls below 30 (oversold)
  - Enter long position near support
- **Exit rules:**
  - Price approaches resistance (top of range)
  - RSI rises above 70 (overbought)
  - Exit position near resistance
- **Stop-loss:** Place below support -1% (e.g., if support $3,400, SL at $3,390)
- **Take-profit:** Near resistance -0.5% (e.g., if resistance $3,500, TP at $3,495)
- **Indicators required:** RSI(14), support/resistance levels
- **Best regime:** Ranging/sideways markets with clear S/R boundaries
- **Worst regime:** Strong trending markets (breakouts cause losses)
- **Why it may work:** Crypto often ranges 60-70% of time. Mean reversion profits from oversold bounces within established boundaries.
- **Known weakness:** False breakouts. If support breaks, losses accelerate quickly.
- **Implementation complexity:** Low — pure indicator math, no LLM needed
- **Backtest priority:** HIGH — matches current ranging-market problem
- **Recommended action:** Implement, backtest on BTC/ETH/SOL 1h, paper test

---

### STRATEGY CARD #002: Momentum Breakout + Volume Confirmation
- **Strategy name:** Momentum Breakout + Volume Confirmation
- **Source:** Kraken Learn / Crypto Day Trading Best Practices
- **Market type:** Crypto (BTC, ETH, SOL)
- **Timeframe:** 15-minute to 1-hour
- **Entry rules:**
  - Price consolidates in tight range for 3+ hours
  - Volume declining during consolidation (coiling)
  - Price breaks above resistance with 3x average volume spike
  - Momentum indicators (RSI, MACD) crossing into bullish territory
  - Enter long at breakout level +0.1%
- **Exit rules:**
  - Exit when volume tapers off and momentum indicators flatten
  - Trail stop at breakeven once +1% profit reached
  - Move trailing stop up as price extends
- **Stop-loss:** Below former resistance (now support) -0.5%
- **Take-profit:** Open — trail stop captures extended moves
- **Indicators required:** Volume, RSI, MACD, support/resistance
- **Best regime:** Consolidation → breakout transitions
- **Worst regime:** Choppy markets with frequent false breakouts
- **Why it may work:** Volume-confirmed breakouts filter fakeouts. Crypto has explosive moves after consolidation.
- **Known weakness:** False breakouts in low-liquidity periods. Stop-losses can be triggered before move extends.
- **Implementation complexity:** Medium — requires volume anomaly detection
- **Backtest priority:** HIGH — current market showing consolidation patterns
- **Recommended action:** Implement, backtest, add volume anomaly to existing chart monitor

---

### STRATEGY CARD #003: Trend Following with Pullback Entry
- **Strategy name:** Trend Following with Pullback Entry
- **Source:** Kraken Learn / Trend Following Discipline
- **Market type:** Crypto (BTC, ETH, SOL)
- **Timeframe:** 1-hour to 4-hour
- **Entry rules:**
  - Higher highs + higher lows on 1h/4h chart (established uptrend)
  - Price pulls back 1-3% from recent high (healthy correction)
  - RSI pulls back from overbought to 40-60 range
  - Enter long on pullback completion (first green candle after pullback)
- **Exit rules:**
  - Trail stop below most recent swing low
  - Move stop to breakeven once +2% profit
  - Exit if price breaks below recent swing low (trend reversal)
- **Stop-loss:** Below most recent swing low -0.5%
- **Take-profit:** Open — trailing stop captures extended trends
- **Indicators required:** Swing high/low detection, RSI, trend strength
- **Best regime:** Strong trending markets
- **Worst regime:** Ranging/sideways markets (whipsaws)
- **Why it may work:** Crypto trends are persistent but volatile. Pullback entries reduce risk vs chasing tops.
- **Known weakness:** Can miss the strongest moves if pullback never comes.
- **Implementation complexity:** Medium — requires swing detection
- **Backtest priority:** MEDIUM — good for trending phases
- **Recommended action:** Implement, backtest, compare to breakout strategy

---

### STRATEGY CARD #004: Partial Profit + Runner (Already Implemented)
- **Strategy name:** Partial Profit + Runner Exit
- **Source:** Internal / CEO Requirements
- **Market type:** Crypto (BTC, ETH, SOL)
- **Timeframe:** Hourly monitoring, 5-min execution
- **Entry rules:** Standard pipeline entry signals
- **Exit rules:**
  - At +0.5% profit: sell 50% of position
  - Remaining 50% becomes "runner" with trailing stop -2%
  - If momentum reverses: sell remaining
  - If trend continues: allow runner to extend
- **Stop-loss:** Initial -3%, then trailing at -2% from high
- **Take-profit:** No fixed TP — runner captures extended moves
- **Indicators required:** Position monitor, momentum detection
- **Best regime:** Volatile markets with follow-through
- **Worst regime:** Choppy markets with quick reversals
- **Why it may work:** Locks in profits early while keeping upside exposure. Reduces risk of giving back gains.
- **Known weakness:** Gives up half position on small moves. Runner may hit trailing stop quickly.
- **Implementation complexity:** Already implemented — monitor and improve
- **Backtest priority:** LOW — already live, track performance
- **Recommended action:** Monitor runner hit rate. Optimize trail tightness.

---

## Backlog

### To Research Next
1. [ ] Mean reversion with Bollinger Bands (BTC/ETH/SOL hourly)
2. [ ] Volume-weighted average price (VWAP) mean reversion
3. [ ] Multi-timeframe confluence strategy (1h + 4h alignment)
4. [ ] Failed breakout / fakeout fade strategy
5. [ ] Momentum divergence reversal (RSI/MACD divergence)
6. [ ] Low-latency pure-indicator strategy (no LLM dependency)
7. [ ] TradingView MCP integration feasibility

### Backlog Status
| # | Strategy | Status | Priority |
|---|----------|--------|----------|
| 001 | RSI Range Trading | Ready to implement | HIGH |
| 002 | Momentum Breakout | Ready to implement | HIGH |
| 003 | Trend Pullback | Ready to implement | MEDIUM |
| 004 | Partial Profit + Runner | Already live | MONITOR |
| 005 | Mean Reversion BB | Pending research | MEDIUM |
| 006 | VWAP Mean Reversion | Pending research | MEDIUM |
| 007 | Multi-timeframe | Pending research | MEDIUM |
| 008 | Failed Breakout Fade | Pending research | HIGH |
| 009 | Momentum Divergence | Pending research | MEDIUM |
| 010 | Pure Indicator (no LLM) | Pending research | HIGH |

---

## Next Steps

1. Implement RSI Range Trading strategy (card #001)
2. Backtest on BTC/ETH/SOL hourly data
3. Add to strategy engine if backtest passes
4. Continue researching from public sources

---

## TradingView MCP Status

- **Available:** No
- **Investigation:** Not installed. Can be configured via pip install or OpenClaw plugin if CEO approves external API.
- **Alternative:** Using public sources (Kraken, TrendRider, etc.) + LLM extraction
- **Decision:** Continue with public sources. Revisit MCP if research volume exceeds LLM capacity.

---

*Research active. No idle teams. — Jarvis*
