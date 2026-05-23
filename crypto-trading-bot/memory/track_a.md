# Track A — Paper Trading Observation

## Bot: Trend Rider v5.6
- **Type:** 50-day SMA crossover, daily timeframe
- **Assets:** BTC/USD, ETH/USD
- **Data source:** Alpaca (single authoritative)
- **Backtest PF:** BTC 1.58, ETH 4.89 (Alpaca 5-year)
- **Walk-forward:** 3/3 positive folds on both assets
- **Fee sensitivity:** BTC survives 2x fees (PF=1.50), ETH survives 3x

## Infrastructure
- **Daemon:** cron 00:05 UTC daily
- **Health check:** every 6 hours
- **Heartbeat:** `smart-ea-bot/core/logs/daemon_heartbeat.json`
- **Max order:** $100 per trade
- **Risk per trade:** 0.25%

## ENTRY_LOCK Status
- **Current:** ACTIVE
- **Release trigger:** First SMA50 crossover (autonomous, no CEO approval needed)
- **Observation period:** 90 days from first trade
- **Live criteria:** 90 days + 6 trades + PF>=1.5 + DD<5%

## Current Market Levels (2026-05-23 13:00 UTC)
- BTC: $74,646 vs SMA50 $76,542 (-2.5%)
- ETH: $2,027 vs SMA50 $2,262 (-10.4%)

## Status: WAITING FOR SIGNAL
