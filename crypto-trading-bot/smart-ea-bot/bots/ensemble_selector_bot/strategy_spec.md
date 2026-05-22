# Strategy Spec — Ensemble Selector Bot
**Bot:** ensemble_selector_bot  
**Status:** SPEC → BACKTEST QUEUE  
**Version:** v0.1

---

## Purpose
Does NOT trade directly. Instead, it **orchestrates** other bots by:
1. Running regime filter
2. Collecting signals from all eligible bots
3. Only allowing a trade when regime + bot type + signal all agree
4. Passing final signal to Risk Governor for execution

## Assets
BTC/USD, ETH/USD

## Timeframe
5-minute candles

## Inputs
- Regime classification from `regime_filter.py`
- Signals from all subordinate bots

## Logic

### Step 1: Regime Classification
```python
regime = classify_regime(bars)[-1]["regime"]
```

### Step 2: Collect Eligible Signals
For each bot in `BOT_REGIME_COMPATIBILITY`:
- If `is_bot_allowed(regime, bot_type)` is True:
  - Run bot strategy on bars
  - Collect signal at current bar

### Step 3: Signal Agreement Rules

**Single Bot Mode:**
- If only 1 bot is eligible and generates a signal → pass through
- If multiple bots eligible but only 1 generates signal → pass through

**Multi-Bot Agreement Mode:**
- If 2+ bots generate the SAME direction signal (e.g., both say BUY):
  - Require ADX > 20 (some trend)
  - Require volume > 60th percentile
  - Then allow trade
- If bots disagree (one BUY, one SELL) → HOLD

### Step 4: Risk Governor Handoff
After agreement, signal goes to Risk Governor:
- Position sizing: 0.25% equity
- Max positions: 2 total
- Daily/weekly loss limits: 1% / 3%

## What This Prevents
- MRS trading in strong trends
- TPS trading in choppy markets
- Breakout bot trading when no range exists
- Any bot trading in low liquidity

## Expected Weakness
- More conservative — may miss some good trades
- Requires all subordinate bots to exist and function
- Adds latency (but minimal on 5-min candles)

## Validation Requirements
- Ensemble must produce profit factor > 1.2
- Max drawdown < 10%
- Must improve upon best single-bot performance
