# Strategy Spec — Volatility Breakout Bot
**Bot:** volatility_breakout_bot  
**Status:** SPEC → BACKTEST QUEUE  
**Version:** v0.1

---

## Purpose
Trade explosive moves AFTER volatility compression.  
Only enters when Bollinger Bands squeeze or ATR compresses, then price breaks out with volume.

## Assets
BTC/USD, ETH/USD

## Timeframe
5-minute candles

## Regime Requirement
- **Only trades when regime = `high_volatility`**
- Must have been in compression (low vol) for 10+ bars before breakout

## Indicators
- Bollinger Band Width (20, 2.0) for compression detection
- ATR(14) for compression confirmation
- Volume spike for breakout confirmation
- ADX(14) for trend strength after breakout

## Compression Detection
1. BB width < 10th percentile of last 50 bars → compression
2. OR ATR < 20th percentile of last 50 bars → compression
3. Must persist for 10+ consecutive bars

## Long Entry Rules
1. **Regime = `high_volatility`**
2. Compression detected for 10+ bars
3. Price closes above upper BB by > 0.3% (breakout)
4. Volume on breakout bar > 90th percentile of last 50 bars
5. ADX on breakout bar > 20 (trend starting)
6. Body of breakout candle > 60% of range (strong candle)

## Short Entry Rules
1. **Regime = `high_volatility`**
2. Compression detected for 10+ bars
3. Price closes below lower BB by > 0.3%
4. Volume on breakout bar > 90th percentile of last 50 bars
5. ADX > 20
6. Body of breakout candle > 60% of range

## Exit Rules (Long)
- Price reaches entry + (3.0 × ATR)
- OR price closes below middle BB (momentum lost)
- OR ADX drops below 15 (trend weakening)
- OR hold time ≥ 60 minutes

## Exit Rules (Short)
- Price reaches entry - (3.0 × ATR)
- OR price closes above middle BB
- OR ADX drops below 15
- OR hold time ≥ 60 minutes

## Stop-Loss
Entry - (1.5 × ATR) for longs  
Entry + (1.5 × ATR) for shorts

## Take-Profit
Entry ± (3.0 × ATR) (wider TP — volatility breakouts can run)

## Risk Rules
- 0.25% equity per trade
- Max 1 position per asset
- Cooldown: 60 minutes after any breakout trade
- Max 1 trade per compression cycle

## Expected Weakness
- Many breakouts fail immediately — requires strong confirmation
- Compression periods can be long (low frequency)
- Wide stops mean larger losses when wrong

## Validation Requirements
- Profit factor > 1.2
- Max drawdown < 10%
- 50+ trades in backtest (lower bar due to low frequency)
