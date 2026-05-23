# Day Trading EA System — Phase 1 Complete Report

## Infrastructure
- **Freqtrade:** 2026.4 installed in virtual environment
- **Exchange:** Binance (dry-run mode)
- **Data:** 81,999 bars per pair (Jan 2024 - May 2026, 15m)
- **Pairs:** BTC/USDT, ETH/USDT
- **Config:** `/data/.openclaw/workspace/freqtrade_data/config.json`

## Backtest Results

### 1. SimpleSMA15m (Control)
| Metric | Value |
|--------|-------|
| Trades | 199 |
| Win Rate | 24.6% |
| Total Return | -0.59% |
| Status | **REJECTED** |

### 2. Strategy003_15m (Mean Reversion)
| Metric | Value |
|--------|-------|
| Trades | 5 (too few!) |
| Win Rate | 80% |
| Total Return | -0.06% |
| Status | **REJECTED** — insufficient frequency |

## Key Findings

1. **SMA strategies fail on 15m** — confirmed. Same logic passes on daily, fails on 15m.
2. **Mean reversion needs tuning** — Strategy003 parameters (RSI<28, MFI<16) too strict for crypto 15m. Crypto RSI rarely drops below 30 on 15m.
3. **Trade frequency is the challenge** — Need 5-15 trades/day, but current strategies produce 1-2 trades/week.

## What Works in Day Trading (Research So Far)
- **Volume confirmation** — Strategy005's volume spike filter
- **Multi-factor entry** — RSI + MFI + Fisher + EMA cross (Strategy003 logic is sound, just parameters too strict)
- **Quick exits** — 1-4 hour hold times, not days
- **Trend context** — EMA50 > EMA100 filter prevents counter-trend trades

## What Doesn't Work
- **Single indicator** — SMA, RSI alone = noise
- **Too strict parameters** — Crypto volatility means thresholds must adapt
- **5m timeframe** — Too noisy, fees eat profits
- **15m without volume filter** — False signals galore

## Next Steps (Phase 2 — Strategy Research)

### Candidate Strategies to Adapt
1. **Strategy005 (Volume + RSI + Fisher)** — Most promising. Volume spike + RSI threshold + Fisher transform. Need to adapt to 15m.
2. **Strategy001 (EMA + Heikin-Ashi)** — EMA cross with candle confirmation. May work on 15m with relaxed thresholds.
3. **Custom Mean Reversion** — RSI(14) < 35 + Bollinger Band touch + volume > 2x average.
4. **Custom Momentum Breakout** — Price > upper Bollinger + volume spike + MACD histogram rising.

### Parameter Tuning Needed
- RSI threshold: 28 → 35 (crypto adapts)
- MFI threshold: 16 → 25
- Fisher RSI: -0.94 → -0.75
- Volume multiplier: 4x → 2x

### Day Trading Gates (Revised)
| Gate | Threshold | Why |
|------|-----------|-----|
| G1 | PF > 1.3 | Profit factor |
| G2 | Trades >= 500/2yr | Frequency |
| G3 | Max DD < 15% | Risk |
| G4 | Win rate > 45% | Edge |
| G5 | Survives 2x fees | Robustness |
| G6 | Walk-forward 70%+ | Stability |
| G7 | No month > 30% profit | Diversification |
| G8 | Profitable BTC+ETH | Breadth |
| G9 | Duration 1-8 hours | Day trading |
| G10 | Sharpe > 0.5 | Risk-adjusted |

## Status
- **Phase 1 (Setup):** ✅ Complete
- **Phase 2 (Research):** 🔄 In Progress — need to adapt and backtest 3-5 candidates
- **Phase 3 (Tournament):** ⏳ Next week
- **Phase 4 (Paper):** ⏳ Week 3-4

## Recommendation
Proceed with Strategy005 adaptation first (volume + RSI + Fisher + MACD). It has the most confirmation factors and best backtest results in community repo. Then test custom mean reversion and momentum breakout strategies.

**Timeline to first viable candidate: 3-5 days of parameter tuning and backtesting.**
