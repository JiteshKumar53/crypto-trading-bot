# CEO Decisions Log

| Date | Decision | Authority | Notes |
|------|----------|-----------|-------|
| 2026-05-22 | Jarvis promoted to Junior CEO with full autonomy inside safety boundaries | CEO | Operational decisions autonomous; CEO approval for live money, risk increases, secrets |
| 2026-05-23 | Alpaca selected as single data source for both backtesting and live execution | Jarvis (recommended), CEO (approved) | Eliminates Yahoo-Alpaca reconciliation mismatch (0.03-0.54% variance) |
| 2026-05-23 | GitHub connected as permanent memory system | CEO | All commits pushed immediately; session protocol established |
| 2026-05-23 | Daemon scheduled via OpenClaw cron at 00:05 UTC daily | Jarvis (recommended), CEO (approved) | Survives container restarts; health check every 6 hours |
| 2026-05-23 | Trend Rider v5.6 enters paper observation | Jarvis | ENTRY_LOCK releases on first SMA crossover autonomously |
| 2026-05-23 | Fetch retry error handling fixed — re-raise after exhaustion | Jarvis | Swallowed errors wrote OK heartbeat instead of ERROR. Caught via testing.
| 2026-05-23 | Daemon integration tests use subprocess isolation | Jarvis | `alpaca_trade_api` import hangs in test environment. Subprocess + pre-import mock solves it.
| 2026-05-23 | No live trading without explicit CEO written approval | CEO | Absolute boundary; paper-only until Q1 2027 criteria met |
