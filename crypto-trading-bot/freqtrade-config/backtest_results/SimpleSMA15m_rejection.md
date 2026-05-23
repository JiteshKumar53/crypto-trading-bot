# Freqtrade Day Trading — Initial Backtest Results

## Strategy: SimpleSMA15m (SMA50 crossover on 15m)

### Result: REJECTED

| Metric | Value |
|--------|-------|
| Total Trades | 199 |
| Win Rate | 24.6% (49 wins / 150 losses) |
| Avg Profit | -0.15% per trade |
| Total Profit | -29.75 USDT (-0.59%) |
| Sharpe Ratio | -8.78 |
| Sortino | -10.91 |
| Max Drawdown | 31.86 USDT (0.64%) |
| Avg Duration | 1h 22m |
| Consecutive Losses (max) | 18 |

### Analysis
- Same SMA50 logic that passes on daily timeframe **fails on 15m**
- Win rate 24.6% — worse than coin flip
- Consecutive losses: 18 in a row
- Lesson confirmed: SMA is a trend-following tool, not a day-trading tool

### Conclusion
SMA crossover strategies are **not viable for 15m day trading**. Need different approach:
- Mean reversion (RSI oversold bounces)
- Volatility breakout (ATR expansion)
- Order flow patterns
- Momentum divergence

Next: Study freqtrade community strategies for proven 15m approaches.
