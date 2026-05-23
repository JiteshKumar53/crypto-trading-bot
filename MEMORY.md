# Jarvis — Long-Term Memory

## Project
Crypto-only autonomous AI trading system using OpenClaw + Alpaca paper trading.
Phase: Pre-paper validation complete. Awaiting first signal.

## Decisions Made

### Data Source Authority (2026-05-23)
**DECISION:** Alpaca is the single authoritative data source for both backtesting and live execution.

**Reasoning:**
- Yahoo Finance and Alpaca differ by 0.03-0.04% mean, up to 0.54% max
- v5.6 passes all gates on Alpaca data (BTC PF=1.58, ETH PF=4.89)
- Same source eliminates reconciliation complexity and mismatch risk
- Alpaca provides 5+ years of daily crypto data

**What changed:**
- data_fetcher.py fixed to respect `timeframe` parameter (was hardcoded to 5m)
- paper_daemon.py v2.0 — uses Alpaca daily data, removed Yahoo dependency

### Trading Timeline (2026-05-23, from CEO directive)
**Paper trading:** 7-14 days from now (early June 2026) when:
- [x] Data source resolved
- [x] v5.6 revalidated on clean data
- [x] Daemon rebuilt on clean source
- [x] Unit tests for data_fetcher committed and passing (4 tests)
- [x] Unit tests for reconciliation committed and passing (4 tests)
- [x] Fee sensitivity on Alpaca data committed (BTC PF=1.50 at 2x fees)
- [x] PAPER_READINESS_PACK.md updated with Alpaca v2.0
- [x] Daemon failure mode audit complete (10 scenarios, all handled)
- [x] Daemon heartbeat mechanism working (logs/daemon_heartbeat.json)
- [x] Daemon integration tests verified (6 logic paths confirmed)
- [x] All tests pass in single run (8 tests, 0 failures)
- [x] Final reconciliation 0.0% (daemon vs backtest, same Alpaca source)
- [x] Daemon dry-run successful (~735ms, clean, heartbeat written)
- [x] Merged and tagged v5.6-production-ready
- [ ] SMA crossover signal fires → ENTRY_LOCK releases autonomously

**Live-money trading:** Q1 2027 earliest (90 days paper + 6 trades + PF≥1.5 + DD<5%)

## Daemon v3.0 (2026-05-23)
Hardened paper trading daemon with:
- Heartbeat mechanism: `logs/daemon_heartbeat.json` after every check
- Retry logic: 3 retries with 60s backoff for API failures
- Duplicate detection: Skips if ran <20h ago
- Missed check detection: Logs WARNING if last run >25h ago
- Error recovery: Catches exceptions, writes ERROR heartbeat, continues
- NaN detection: Validates closes before SMA computation
- Order size validation: Ensures qty * price ≤ $100 * 1.01
- No retry on orders: Prevents double-fill risk
- Audit document: `core/paper_daemon_audit.md`

## Daemon Hardening Tests (Verified)
1. ✅ Daily bars fetched (not 5m)
2. ✅ SMA matches backtest (within 0.01%)
3. ✅ No trade without signal
4. ✅ Signal detected on crossover
5. ✅ API failure recovery (no crash)
6. ✅ Duplicate run prevention

## Strategy Validation

### Trend Rider v5.6 — ONLY passing strategy (18 attempts)
- **Type:** 50-day SMA crossover, daily timeframe
- **Assets:** BTC/USD, ETH/USD
- **Backtest (Yahoo 5y):** BTC PF=2.14, ETH PF=4.85, DD 1.44-2.20%
- **Backtest (Alpaca 5y):** BTC PF=1.58, ETH PF=4.89, DD 2.26-1.44%
- **Walk-forward:** 3/3 positive folds on both assets (Alpaca data)
- **Status:** PASS all gates on both data sources

## Key Lessons
1. **Simplicity + longer timeframe** beat complexity (50 SMA on daily vs RSI+volume+ATR on 5m)
2. **Daily data has sufficient history** — don't need 5m granularity for trend following
3. **Same source for backtest + live** — eliminates reconciliation headaches
4. **Small OHLCV differences matter** — 0.5% variance at crossover points can shift trade timing

## Boundaries
- No real-money trading without explicit CEO approval
- No disabling risk controls without CEO approval
- ENTRY_LOCK releases autonomously on first valid signal
- Max order $100, 0.25% risk/trade

## Model Routing
- deepseek-v4-pro: Technical, fundamental, risk (reliable, 40-90s)
- qwen3.5: Sentiment, code generation (moderate, ~77s)
- kimi-k2.6: DEPRECATED — times out at 180s regardless of data size
