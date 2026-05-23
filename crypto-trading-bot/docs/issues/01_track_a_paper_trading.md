# Track A: Paper Trading — Trend Rider v5.6

**Label:** track-a
**Status:** Active observation
**Created:** 2026-05-23

## Overview
Trend Rider v5.6 is our first production strategy entering paper trading observation.

## Strategy Details
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

## ENTRY_LOCK
- **Current:** ACTIVE
- **Release trigger:** First SMA50 crossover (autonomous)
- **Observation period:** 90 days from first trade
- **Live criteria:** 90 days + 6 trades + PF>=1.5 + DD<5%

## Current Market Levels
- BTC: $74,646 vs SMA50 $76,542 (-2.5%)
- ETH: $2,027 vs SMA50 $2,262 (-10.4%)

## Checklist
- [x] Strategy validated (v5.6)
- [x] Data pipeline fixed (single source)
- [x] Unit tests passing (14/14)
- [x] Fee sensitivity confirmed
- [x] Daemon v3.0 with heartbeat
- [x] Scheduled via OpenClaw cron
- [x] Health check scheduled
- [ ] First SMA crossover signal
- [ ] 90-day observation complete
- [ ] Live-money approval (Q1 2027)
