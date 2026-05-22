# Strategy Spec — Mean Reversion Scalper v2 (MRSv2)
**Bot:** mean_reversion_scalper_v2  
**Status:** SPEC → BACKTEST QUEUE  
**Version:** v0.2

---

## Purpose
Capture small profits from RSI mean reversion in **range-bound markets only**.  
**Never trade in trends.** Never trade in chop. Wait for the right regime.

## Assets
BTC/USD, ETH/USD

## Timeframe
5-minute candles

## Regime Requirement
- **Only trades when regime = `ranging`**
- ADX < 20 (weak trend)
- Price within ±1.5% of VWAP (balanced, not trending)
- BB width < 2% (not expanding)

## Indicators
- RSI(14) on close price
- SMA(20) as reference centerline
- Bollinger Bands(20, 2.0) for overbought/oversold bands
- VWAP for intraday mean
- ATR(14) for volatility floor

## Long Entry Rules
1. **Regime = `ranging`** (mandatory)
2. RSI(14) < 25 (deeply oversold — stricter than v1's 30)
3. Close price < Lower BB(20, 2.0) (price below lower band)
4. Price > VWAP × 0.985 (not in a free-fall — within 1.5% below VWAP)
5. Previous bar RSI was < 30 (confirming oversold, not flash spike)
6. ATR(14) > 0.2% of price (not dead market)
7. Volume > 50th percentile of last 20 bars (some participation)

## Short Entry Rules
1. **Regime = `ranging`** (mandatory)
2. RSI(14) > 75 (deeply overbought)
3. Close price > Upper BB(20, 2.0) (price above upper band)
4. Price < VWAP × 1.015 (within 1.5% above VWAP)
5. Previous bar RSI was > 70 (confirming overbought)
6. ATR(14) > 0.2% of price
7. Volume > 50th percentile of last 20 bars

## Exit Rules (Long)
- RSI(14) > 55 (mean reversion complete — not 50, gives room)
- OR price crosses back above VWAP (mean reverted)
- OR profit ≥ +0.6% (smaller TP — scalp, don't hold)
- OR loss ≥ -0.3% (tight SL — fail fast)
- OR hold time ≥ 20 minutes (time stop)

## Exit Rules (Short)
- RSI(14) < 45
- OR price crosses back below VWAP
- OR profit ≥ +0.6%
- OR loss ≥ -0.3%
- OR hold time ≥ 20 minutes

## Stop-Loss
-0.3% from entry (tight — range trades need tight risk)

## Take-Profit
+0.6% from entry (1:2 risk/reward)

## Risk Rules
- 0.25% equity per trade
- Max 1 position per asset
- Max 2 total positions
- Cooldown: 10 minutes between trades

## What Changed from v1
| Aspect | v1 | v2 |
|--------|-----|-----|
| Regime filter | None | `ranging` only |
| RSI threshold | <30/>70 | <25/>75 (stricter) |
| SMA filter | Contradictory | Removed (replaced by BB + VWAP) |
| SL | -0.5% | -0.3% (tighter) |
| TP | +1.0% | +0.6% (realistic scalp) |
| Volume filter | None | Added |
| BB confirmation | None | Mandatory |

## Expected Weakness
- May miss some reversions that don't hit extreme RSI
- Requires patience — only trades in ranging regimes (~30% of time)
- VWAP can shift during the day

## Validation Requirements
- Profit factor > 1.2
- Max drawdown < 10%
- 100+ trades in backtest
- Win rate > 45%
