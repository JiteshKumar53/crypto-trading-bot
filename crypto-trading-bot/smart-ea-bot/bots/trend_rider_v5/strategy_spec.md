# Trend Rider v5 — Strategy Specification

## Hypothesis
Crypto trends persist at the 4h timeframe. Retail herding behavior, institutional rebalancing, and macro narratives create momentum that lasts days to weeks. A simple trend-following system — enter on pullback in established trend, exit on trend break or trailing stop — has positive expectancy where scalping failed.

## Timeframe
- **Primary:** 4h
- **Confirmation:** Daily EMA alignment (not yet implemented — future enhancement)

## Assets
- BTC/USD (primary)
- ETH/USD (secondary)

## Entry Rules (LONG)
1. 4h EMA 12 > EMA 26 > EMA 50 (strong uptrend)
2. Price below EMA 12 (pullback)
3. Deviation from EMA 12 >= 1 ATR
4. RSI(14) between 40-55 (momentum present, not overbought)
5. Volume > 1.2x 20-bar average

## Entry Rules (SHORT)
1. 4h EMA 12 < EMA 26 < EMA 50 (strong downtrend)
2. Price above EMA 12 (pullback/rally)
3. Deviation from EMA 12 >= 1 ATR
4. RSI(14) between 45-60
5. Volume > 1.2x average

## Exit Rules
- **Stop loss:** 2.5 ATR from entry
- **Take profit:** Trailing stop at 3 ATR from highest/lowest price since entry
- **Time stop:** Exit after 20 bars (80 hours / ~3.3 days)
- **Trend break:** If EMA alignment reverses, exit immediately

## Risk Parameters
- Risk per trade: 0.5% equity
- Max position size: $200
- Max concurrent positions: 2
- No pyramiding

## Kill Conditions
- 3 consecutive losing trades
- Drawdown > 10% from peak equity
- No signal for 30 days

## Why This May Work Where Scalping Failed
1. 4h trends are driven by macro factors, not microstructure noise
2. Fewer trades = lower fee drag
3. Momentum strategies have demonstrated positive alpha in crypto academic literature
4. Technical indicators work better when signal isn't drowned by tick-level noise
5. Yahoo Finance provides 1+ year of data for robust validation

## Validation Gates (Locked)
| Gate | Threshold |
|------|-----------|
| Profit factor | > 1.3 |
| Minimum trades | >= 30 (daily) / >= 100 (4h) |
| Max drawdown | < 15% |
| Fee survival | Survives 1.5x fees |
| Walk-forward | Positive in 2 of 3 OOS windows |
| Monthly stability | No 30-day period > 50% of profit |
| Look-ahead | Strict (verified by QA) |
| QA tests | Required |

## Fee Model
- 0.10% per side
- 0.05% slippage

## Data Source
Yahoo Finance (free, no API key required)
