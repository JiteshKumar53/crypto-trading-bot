# Strategy Spec — Mean Reversion Scalper (MRS)
**Bot:** mean_reversion_scalper  
**Status:** SPEC  
**Version:** v0.1

---

## Purpose
Capture small profits from RSI mean reversion in range-bound crypto markets.

## Assets
BTC/USD, ETH/USD

## Timeframe
5-minute candles

## Indicators
- RSI(14) on close price
- SMA(20) trend filter
- ATR(14) volatility filter

## Long Entry Rules
1. RSI(14) < 30 (oversold)
2. Close price > SMA(20) (not in strong downtrend)
3. Previous bar RSI was < 35 (confirming oversold, not flash)
4. ATR(14) > 0.3% of price (not flat market)

## Short Entry Rules
1. RSI(14) > 70 (overbought)
2. Close price < SMA(20) (not in strong uptrend)
3. Previous bar RSI was > 65 (confirming overbought)
4. ATR(14) > 0.3% of price

## Exit Rules (Long)
- RSI(14) > 50 (mean reversion complete)
- OR profit ≥ +1.0%
- OR loss ≥ -0.5% (stop-loss)
- OR hold time ≥ 30 minutes (time stop)

## Exit Rules (Short)
- RSI(14) < 50
- OR profit ≥ +1.0%
- OR loss ≥ -0.5%
- OR hold time ≥ 30 minutes

## Stop-Loss
-0.5% from entry (hard stop)

## Take-Profit
+1.0% from entry (hard TP)

## Risk Rules
- 0.25% equity per trade
- Max 1 position per asset
- Max 2 total positions across all bots

## When NOT to Trade
- Outside US hours (09:30-16:00 ET)
- ATR(14) < 0.3% of price
- Within 15 minutes of last trade (cooldown)
- Daily loss ≥ 1% of equity
- Weekly loss ≥ 3% of equity
- Already in position for this asset

## Expected Weakness
Fails in strong trends where RSI stays oversold/overbought for extended periods.

## Validation Requirements
- Profit factor > 1.2
- Max drawdown < 10%
- 100+ trades in backtest
- Win rate > 45%
