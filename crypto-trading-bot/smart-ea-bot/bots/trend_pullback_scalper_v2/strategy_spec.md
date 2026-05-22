# Strategy Spec — Trend Pullback Scalper v2 (TPSv2)
**Bot:** trend_pullback_scalper_v2  
**Status:** SPEC → BACKTEST QUEUE  
**Version:** v0.2

---

## Purpose
Capture pullbacks to EMA20 in **established trends only**.  
**Never trade in ranging or choppy markets.** Wait for trend + momentum confirmation.

## Assets
BTC/USD, ETH/USD

## Timeframe
5-minute candles (primary), 15-minute trend confirmation

## Regime Requirement
- **Only trades when regime = `trending_up` (long) or `trending_down` (short)**
- ADX > 30 (strong trend)
- EMA20 slope consistent for 10+ bars

## Indicators
- EMA 20/50/200 for trend hierarchy
- RSI(14) for pullback depth
- ATR(14) for stop-loss sizing
- ADX(14) for trend strength
- Volume for confirmation

## Long Entry Rules
1. **Regime = `trending_up`** (mandatory)
2. Price > EMA20 > EMA50 > EMA200 (strong uptrend hierarchy)
3. EMA20 slope > 0 for last 10 bars (confirmed uptrend)
4. Price touches or dips below EMA20 (pullback to fast EMA)
5. RSI(14) between 45 and 55 (not oversold, confirming healthy pullback)
6. ADX(14) > 30 (strong trend)
7. Volume on pullback bar > 70th percentile of last 20 bars (institutional participation)
8. Price > EMA50 × 1.01 (not too deep — pullback, not reversal)

## Short Entry Rules
1. **Regime = `trending_down`** (mandatory)
2. Price < EMA20 < EMA50 < EMA200
3. EMA20 slope < 0 for last 10 bars
4. Price touches or rises above EMA20
5. RSI(14) between 45 and 55
6. ADX(14) > 30
7. Volume on pullback bar > 70th percentile
8. Price < EMA50 × 0.99

## Exit Rules (Long)
- Price reaches EMA20 + (1.5 × ATR) (momentum continuation target)
- OR RSI(14) > 70 (overbought — exit on exhaustion)
- OR price breaks below EMA50 (trend broken)
- OR ATR-based stop: entry - (1.5 × ATR) (wider than v1, based on actual volatility)
- OR hold time ≥ 30 minutes

## Exit Rules (Short)
- Price reaches EMA20 - (1.5 × ATR)
- OR RSI(14) < 30
- OR price breaks above EMA50
- OR ATR-based stop: entry + (1.5 × ATR)
- OR hold time ≥ 30 minutes

## Stop-Loss
1.5 × ATR from entry (dynamic — adapts to market volatility)

## Take-Profit
2.0 × ATR from entry (1:1.3 risk/reward — modest but achievable in trends)

## Risk Rules
- 0.25% equity per trade
- Max 1 position per asset
- Max 2 total positions
- Cooldown: 15 minutes between trades
- Max 1 trade per trend direction per day per asset

## What Changed from v1
| Aspect | v1 | v2 |
|--------|-----|-----|
| Regime filter | None | `trending_up`/`trending_down` only |
| EMA hierarchy | 20/50 only | 20/50/200 (stronger trend) |
| Pullback definition | ±0.2% of EMA20 | Touch/dip below EMA20 |
| RSI filter | 40-60 (too wide) | 45-55 (strict) |
| ADX filter | None | >30 (strong trend only) |
| SL | -0.4% fixed | 1.5 × ATR (dynamic) |
| TP | +0.8% fixed | 2.0 × ATR (dynamic) |
| Volume filter | None | >70th percentile |
| Trend confirmation | 5 bars | 10 bars |

## Expected Weakness
- Requires strong trends (ADX > 30) — only ~20% of market time
- May miss early trend entries
- Deep pullbacks can hit ATR stop before continuation

## Validation Requirements
- Profit factor > 1.2
- Max drawdown < 10%
- 100+ trades in backtest
- Win rate > 40%
