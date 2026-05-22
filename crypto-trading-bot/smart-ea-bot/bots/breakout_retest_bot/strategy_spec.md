# Strategy Spec — Breakout Retest Bot
**Bot:** breakout_retest_bot  
**Status:** SPEC → BACKTEST QUEUE  
**Version:** v0.1

---

## Purpose
Trade range breakouts that successfully retest the broken level.  
Only enter after price confirms the breakout by returning to test it and bouncing.

## Assets
BTC/USD, ETH/USD

## Timeframe
5-minute candles

## Regime Requirement
- **Only trades when regime = `ranging` or `high_volatility`**
- ADX < 25 (not trending strongly)
- Price has been in a defined range for 30+ bars

## Indicators
- Donchian Channel(20) for range detection
- ATR(14) for stop sizing
- Volume for breakout confirmation
- ADX(14) for regime confirmation

## Range Detection
1. Identify 20-bar high and low (Donchian Channel)
2. Range width must be > 1.5% and < 5% of price (not too tight, not too wide)
3. Price must have touched both upper and lower bounds at least twice each in last 30 bars

## Long Entry Rules (Breakout + Retest)
1. **Regime = `ranging` or `high_volatility`**
2. Price breaks above 20-bar high by > 0.2% (confirmed breakout)
3. Volume on breakout bar > 80th percentile of last 20 bars
4. Price retraces to within 0.3% of the broken high (retest)
5. Close of retest bar > open (bullish candle on retest)
6. ADX < 25 (not already trending)

## Short Entry Rules (Breakout + Retest)
1. **Regime = `ranging` or `high_volatility`**
2. Price breaks below 20-bar low by > 0.2%
3. Volume on breakout bar > 80th percentile
4. Price retraces to within 0.3% of the broken low
5. Close of retest bar < open (bearish candle on retest)
6. ADX < 25

## Exit Rules (Long)
- Price reaches breakout level + (2.0 × ATR)
- OR price closes below retest low (false breakout)
- OR hold time ≥ 40 minutes

## Exit Rules (Short)
- Price reaches breakout level - (2.0 × ATR)
- OR price closes above retest high (false breakout)
- OR hold time ≥ 40 minutes

## Stop-Loss
Retest low - (0.5 × ATR) for longs  
Retest high + (0.5 × ATR) for shorts

## Take-Profit
Range width projected from breakout point

## Risk Rules
- 0.25% equity per trade
- Max 1 position per asset
- Cooldown: 30 minutes after any breakout trade

## Expected Weakness
- Requires clean ranges — crypto often gaps
- Retest may not happen immediately
- False breakouts common in low liquidity

## Validation Requirements
- Profit factor > 1.2
- Max drawdown < 10%
- 100+ trades in backtest
