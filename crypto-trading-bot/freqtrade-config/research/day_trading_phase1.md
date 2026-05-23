# Day Trading EA System — Phase 1 Report

## Installation
- **Freqtrade Version:** 2026.4
- **Python:** 3.13.5
- **Exchange:** Binance (dry-run mode)
- **Virtual Environment:** `/data/.openclaw/venvs/freqtrade`
- **Data Directory:** `/data/.openclaw/workspace/freqtrade_data`

## Configuration
- **Timeframe:** 15m (primary)
- **Pairs:** BTC/USDT, ETH/USDT
- **Stake:** $100 per trade
- **Dry-run wallet:** $5,000
- **Fee:** 0.1% (Binance taker)

## First Backtest — SimpleSMA15m (Control Test)

### Result: REJECTED

| Metric | Value |
|--------|-------|
| Total Trades | 199 |
| Win Rate | 24.6% (49W / 150L) |
| Avg Profit | -0.15% per trade |
| Total Return | -29.75 USDT (-0.59%) |
| Sharpe | -8.78 |
| Sortino | -10.91 |
| Max Consecutive Losses | 18 |
| Avg Duration | 1h 22m |

### Lesson
Same SMA50 logic that passes on daily (PF 1.58) **completely fails on 15m**. Confirms:
- SMA is a trend-following tool, not a day-trading tool
- 15m timeframe requires different edge (momentum, mean reversion, breakout)

## Community Strategy Research (In Progress)

### Strategy001 — EMA + Heikin-Ashi Cross
- **Logic:** EMA20/50 cross + Heikin-Ashi confirmation
- **Timeframe:** 5m (original), need to test on 15m
- **Indicators:** EMA, Heikin-Ashi
- **Potential:** Mean reversion + momentum hybrid
- **Status:** Need to adapt to 15m and backtest

### Strategy005 — Volume + RSI + Fisher Transform
- **Logic:** Volume spike + RSI threshold + Fisher transform
- **Timeframe:** 5m (original)
- **Indicators:** Volume, RSI, Fisher RSI, MACD, SAR, Stochastic
- **Potential:** Multi-factor confirmation, noise filtering
- **Status:** Need to adapt to 15m and backtest

## Next Steps
1. Download Strategy001 and Strategy005 from freqtrade-strategies repo
2. Adapt to 15m timeframe
3. Backtest both on BTC/USDT + ETH/USDT (2 years)
4. Apply day-trading gates (PF>1.3, win rate>50%, 500+ trades, DD<15%)
5. Select candidates for walk-forward validation

## Key Insight
Day trading requires:
- **Frequent signals** (5-15/day = 1000-3000/year)
- **Multiple confirmation factors** (not single indicator)
- **Volume confirmation** (institutional participation)
- **Mean reversion awareness** (crypto mean-reverts intraday)
- **Quick exits** (1-4 hour hold times, not days)
