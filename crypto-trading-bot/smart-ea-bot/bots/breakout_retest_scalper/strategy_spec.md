# Strategy Spec — Breakout Retest Scalper (BRS)
**Bot:** breakout_retest_scalper  
**Status:** SPEC  
**Version:** v0.1

---

## Purpose
Capture momentum after range breakout with retest confirmation and volume spike.

## Assets
BTC/USD, ETH/USD

## Timeframe
5-minute candles

## Indicators
- ATR(14) for volatility and stop sizing
- Volume (relative to 20-bar average)
- Support/resistance levels (20-bar high/low)

## Long Entry Rules
1. Price breaks above 20-bar high (breakout)
2. Retests breakout level within 3 bars (retest confirmation)
3. Volume > 1.5× 20-bar average (volume confirmation)
4. ATR(14) > 0.3% of price (sufficient volatility)
5. Spread < 0.1%

## Short Entry Rules
1. Price breaks below 20-bar low (breakout)
2. Retests breakout level within 3 bars
3. Volume > 1.5× 20-bar average
4. ATR(14) > 0.3% of price
5. Spread < 0.1%

## Exit Rules (Long)
- Price ≥ entry × 1.012 (+1.2% profit)
- OR price ≤ entry × 0.994 (-0.6% stop)
- OR hold time ≥ 25 minutes
- OR price breaks back below retest level (failed breakout)

## Exit Rules (Short)
- Price ≤ entry × 0.988 (+1.2% profit)
- OR price ≥ entry × 1.006 (-0.6% stop)
- OR hold time ≥ 25 minutes
- OR price breaks back above retest level

## Stop-Loss
-0.6% from entry (hard stop)

## Take-Profit
+1.2% from entry (hard TP)

## Risk Rules
- 0.25% equity per trade
- Max 1 position per asset
- Max 2 total positions across all bots

## When NOT to Trade
- Outside US hours (09:30-16:00 ET)
- Volume < 1.5× average (no confirmation)
- ATR(14) < 0.3% of price
- Spread > 0.1%
- Within 15 minutes of last trade
- Daily loss ≥ 1% of equity
- Weekly loss ≥ 3% of equity
- Already in position for this asset

## Expected Weakness
False breakouts with no follow-through — price breaks out but immediately reverses.

## Validation Requirements
- Profit factor > 1.2
- Max drawdown < 10%
- 100+ trades in backtest
- Win rate > 45%
