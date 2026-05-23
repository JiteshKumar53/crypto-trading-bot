# Repo Training — Tier 1

**Label:** research
**Status:** In progress
**Created:** 2026-05-23

## Target Repositories

### 1. freqtrade/freqtrade
- **Status:** ✅ COMPLETED 2026-05-23
- **Focus:** Daemon architecture, crash recovery, dry-run patterns
- **Output:** `research/repo_studies/freqtrade.md`
- **Key takeaways:**
  - Adopt: exponential backoff retry, trading_mode in heartbeat
  - Do NOT adopt: while True persistent process (overkill for daily checks), SQLite DB

### 2. alpacahq/alpaca-py
- **Status:** ⏳ NOT STARTED
- **Focus:** Daily bar fetching, crypto-specific API quirks, error handling, rate limits
- **Output:** `research/repo_studies/alpaca_py.md`

### 3. polakowo/vectorbt
- **Status:** ⏳ NOT STARTED
- **Focus:** Replace backtest engine? Speed comparison. Walk-forward and fee sensitivity support
- **Output:** `research/repo_studies/vectorbt.md`
- **End with:** RECOMMENDATION — adopt / do not adopt / adopt partially

### 4. github/spec-kit
- **Status:** ⏳ NOT STARTED
- **Focus:** Spec-driven workflow for strategy templates and issue/PR discipline
- **Output:** `research/repo_studies/spec_kit.md`

## Schedule
- One repo study per day during dead time (while waiting for signal)
- Priority: alpaca-py → vectorbt → spec-kit
