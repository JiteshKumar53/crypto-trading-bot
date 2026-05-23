# Freqtrade Repo Study

## What freqtrade does
Freqtrade is a Python-based crypto trading bot supporting multiple exchanges via CCXT, with backtesting, machine learning optimization (FreqAI), and both dry-run and live trading modes. It uses a persistent worker process with state-machine-driven execution.

## How they run their daemon

### Process management approach
- **Single persistent process**: `Worker` class runs `while True` loop
- **Throttling**: `_throttle()` ensures each iteration takes at least `PROCESS_THROTTLE_SECS` (5s default)
- **Candle-boundary sync**: Uses `timeframe_to_next_date()` to wake at new candle start, not fixed intervals
- **systemd integration**: `sdnotify` for `READY=1`, `WATCHDOG=1`, `RELOADING=1`, `STOPPING=1`

### Crash recovery
- **TemporaryError**: Retries after `RETRY_TIMEOUT` (30s), logs warning, continues loop
- **OperationalException**: Stops trader (`State.STOPPED`), sends RPC notification, requires manual `/start`
- **Unhandled exceptions**: Caught at `_process_running()` level, bot stays alive

### Missed signal handling
- Wakes at candle boundaries (`timeframe_to_next_date(timeframe) + 1s offset`)
- Ensures new candle is available before processing
- State machine: `RUNNING`/`PAUSED`/`STOPPED` — can pause without losing state

## How they handle paper trading (dry-run)

### Architecture difference from live
- `dry_run: true` in config — uses simulated wallet (`DRY_RUN_WALLET = 1000` default)
- **Separate database**: `tradesv3.dryrun.sqlite` vs `tradesv3.sqlite`
- Exchange wrapper simulates fills instead of real API calls
- No real orders placed; balance tracked in memory + DB

### Fill simulation
- Orders "filled" immediately at market price (no slippage simulation by default)
- Wallet balance updated in simulated `Wallets` class
- Trade record persisted to dry-run SQLite DB

## What I will adopt for our project

### 1. Retry decorator with exponential backoff
**File**: `smart-ea-bot/core/data_fetcher.py`  
**Change**: Add `@retrier` decorator with exponential backoff for API calls  
**Priority**: NOW  
**Reason**: Freqtrade's `calculate_backoff(retrycount, max_retries) = (max_retries - retrycount) ** 2 + 1` is cleaner than our fixed 60s. Prevents hammering Alpaca on 429 errors.

### 2. Separate state tracking for paper vs live
**File**: `smart-ea-bot/core/paper_daemon.py`  
**Change**: Add `trading_mode` field to heartbeat (`PAPER`/`LIVE`)  
**Priority**: NOW  
**Reason**: Freqtrade's explicit `dry_run` flag prevents confusion. Our heartbeat should clearly state mode.

### 3. Candle-boundary scheduling improvement
**File**: `smart-ea-bot/core/paper_daemon.py`  
**Change**: Currently sleeps until 00:05 UTC. Add check: if already past 00:05 but before 00:10, run immediately (catch missed window).  
**Priority**: LATER  
**Reason**: Freqtrade's `timeframe_to_next_date()` ensures no missed candles. Our cron handles this, but adding a grace window is safer.

### 4. systemd watchdog notifications (future)
**File**: `smart-ea-bot/scripts/systemd/` (new directory)  
**Change**: When we switch to systemd service, add `sdnotify` integration  
**Priority**: LATER (when systemd migration happens)  
**Reason**: Freqtrade's systemd integration prevents service manager from killing "hung" processes during long backtests. Not needed with current cron approach.

## What I will NOT adopt and why

### 1. Full `while True` persistent process
**Why not**: Our strategy checks once per day. A 24/7 process is overkill, wastes memory, and adds complexity. Cron + run-once is correct for daily SMA crossover.

### 2. Complex state machine (STOPPED/RUNNING/PAUSED)
**Why not**: We have one strategy, two assets. No need for multi-state orchestration. Our `SKIPPED`/`OK`/`ERROR`/`SIGNAL_FIRED` heartbeat states are sufficient.

### 3. SQLite trade database
**Why not**: Freqtrade needs SQL for multi-pair, multi-strategy, multi-exchange tracking. We track one trade at a time via heartbeat JSON + attribution log. Adding SQLite adds dependency and complexity without value.

### 4. CCXT abstraction layer
**Why not**: We use Alpaca directly. CCXT adds ~50MB dependency and abstraction overhead for a single broker. Our `data_fetcher.py` is 150 lines vs CCXT's 5000+.

### 5. Machine learning optimization (FreqAI/Hyperopt)
**Why not**: Overfitting risk. Our 17 rejected bots already explored complex optimization. v5.6 won with simplicity.

## Action items

| # | Action | File | Priority |
|---|--------|------|----------|
| 1 | Add retry decorator with exponential backoff | `core/data_fetcher.py` | NOW |
| 2 | Add `trading_mode` to heartbeat (PAPER/LIVE) | `core/paper_daemon.py` | NOW |
| 3 | Add grace window (00:05-00:10 UTC run-if-missed) | `core/paper_daemon.py` | LATER |
| 4 | systemd watchdog integration | `scripts/systemd/` | LATER |
| 5 | Document state machine rationale | `core/paper_daemon_audit.md` | NOW |
