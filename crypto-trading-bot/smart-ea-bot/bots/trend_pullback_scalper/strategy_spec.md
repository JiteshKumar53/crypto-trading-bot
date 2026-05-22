# Strategy Spec — Trend Pullback Scalper (TPS)
**Bot:** trend_pullback_scalper  
**Status:** SPEC  
**Version:** v0.1

---

## Purpose
Capture pullbacks to VWAP in established intraday trends.

## Assets
BTC/USD, ETH/USD

## Timeframe
5-minute candles (primary), 15-minute (confirmation)

## Indicators
- VWAP (session-based)
- SMA(20) slope
- RSI(14)

## Long Entry Rules
1. Price > VWAP (uptrend context)
2. SMA(20) slope > 0 (rising over last 5 bars)
3. Price touches or crosses below VWAP (pullback to VWAP)
4. RSI(14) > 40 (not oversold, confirms trend strength)
5. Spread < 0.1% (liquid enough)

## Short Entry Rules
1. Price < VWAP (downtrend context)
2. SMA(20) slope < 0 (falling over last 5 bars)
3. Price touches or crosses above VWAP (pullback to VWAP)
4. RSI(14) < 60 (not overbought)
5. Spread < 0.1%

## Exit Rules (Long)
- Price ≥ entry × 1.008 (+0.8% profit)
- OR price ≤ entry × 0.996 (-0.4% stop)
- OR hold time ≥ 20 minutes
- OR price crosses back below VWAP (trend broken)

## Exit Rules (Short)
- Price ≤ entry × 0.992 (+0.8% profit)
- OR price ≥ entry × 1.004 (-0.4% stop)
- OR hold time ≥ 20 minutes
- OR price crosses back above VWAP

## Stop-Loss
-0.4% from entry (hard stop)

## Take-Profit
+0.8% from entry (hard TP)

## Risk Rules
- 0.25% equity per trade
- Max 1 position per asset
- Max 2 total positions across all bots

## When NOT to Trade
- Outside US hours (09:30-16:00 ET)
- Spread > 0.1% (illiquid)
- Within 10 minutes of last trade
- Daily loss ≥ 1% of equity
- Weekly loss ≥ 3% of equity
- Already in position for this asset

## Expected Weakness
Fails in choppy markets with no clear trend or when VWAP is not respected.

## Validation Requirements
- Profit factor > 1.2
- Max drawdown < 10%
- 100+ trades in backtest
- Win rate > 45%
