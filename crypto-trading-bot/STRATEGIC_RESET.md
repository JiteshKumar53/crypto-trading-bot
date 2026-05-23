# SIMPLE EA BOT — Strategic Reset
**Branch:** `ea-simple-reset`  
**Status:** DESIGN PHASE — NO TRADING  
**Date:** Friday, May 22, 2026 — 12:29 CEST  
**CEO:** Jitesh Kumar  
**Developer/PM:** Jarvis (Second Brain)

---

## 1. WHY THE RESET

### Old Project Problems
| Problem | Evidence |
|---------|----------|
| Too many bugs | 6+ critical bugs in 48 hours (sizing, PositionRecord, backtest engine, reconciliation) |
| Weak agent reliability | Ollama timeouts, 5-agent pipeline never completed a full cycle |
| Poor continuity | System required constant hotfixes, no stable 24h run |
| No proven edge | Zero backtested strategies with positive Sharpe |
| No profit evidence | 1 BTC paper trade, -$2.19 unrealized |
| Overengineered | 60+ modules for a simple trading task |

### New Philosophy
**Build a working EA first. Scale later.**

---

## 2. NEW SIMPLIFIED EA ARCHITECTURE

### Core Principles
1. **Deterministic only** — No LLM agents in execution path
2. **Simple first** — One strategy, two assets, proven rules
3. **Backtest before trade** — No paper trading without backtest evidence
4. **Risk-first** — Hard limits in code, not configuration
5. **Jarvis = developer** — Not an autonomous CEO making trading decisions

### Architecture Diagram
```
[5m OHLCV Data] → [Strategy Engine] → [Signal]
                                       ↓
[Account State] ← [Risk Governor] ← [Position Sizing]
                                       ↓
                              [Alpaca Paper API]
                                       ↓
                              [Position Tracker]
                                       ↓
                              [Trade Logger]
```

### File Structure (Minimal)
```
simple_ea/
├── config.py              # All constants in one place
├── data_fetcher.py        # Fetch 5m bars from Alpaca
├── strategy_mean_reversion.py  # Strategy 1
├── strategy_trend_pullback.py  # Strategy 2 (backup)
├── backtest_engine.py     # Simple vectorized backtest
├── risk_governor.py       # Hard risk limits
├── execution.py           # Paper order submission
├── position_tracker.py    # Track entries/exits/SL/TP
├── trade_logger.py        # CSV/JSONL logging
├── main.py                # Entry point (daemon or CLI)
└── tests/
    ├── test_strategy.py
    ├── test_backtest.py
    ├── test_risk.py
    └── test_integration.py
```

### Old Code Status
| Component | Action | Reason |
|-----------|--------|--------|
| `src/core/ea_core_engine.py` | RETIRE | Overengineered, 12 stages, fragile |
| `src/pipeline_controller_v2.py` | RETIRE | Too complex, force_testing_mode hack |
| `src/orchestrator.py` | RETIRE | Agent recommendation requirement |
| `src/agents/` (5-agent pipeline) | RETIRE | LLM agents unreliable, slow |
| `src/broker/broker_first_reconciliation.py` | ADAPT | Keep broker fetch, simplify |
| `src/broker/alpaca_client.py` | KEEP | Works, paper API wrapper |
| `src/position_tracker.py` | ADAPT | Keep SL/TP tracking, simplify |
| `src/ceo_reporting_watchdog.py` | RETIRE | Overkill reporting, simple logging instead |
| `src/opportunity_scanner.py` | RETIRE | Not needed for deterministic EA |
| `qa_test_suite.py` (29 tests) | RETIRE | Tests for old architecture |
| `scripts/autonomous_daemon.py` | RETIRE | Daemon with 4h cycle too slow |
| `docs/` | ARCHIVE | Move to `old_project_docs/` |
| `dashboard/` | RETIRE | Web dashboard not needed |

---

## 3. TWO PROPOSED STRATEGIES

### Strategy A: RSI Mean Reversion Scalp
**Logic:** Buy when RSI is oversold, sell when RSI is overbought.

| Parameter | Value |
|-----------|-------|
| **Primary timeframe** | 5-minute |
| **Indicator** | RSI(14) |
| **Entry long** | RSI < 30 and price > SMA(20) |
| **Entry short** | RSI > 70 and price < SMA(20) |
| **Exit long** | RSI > 50 OR +1% profit OR -0.5% stop |
| **Exit short** | RSI < 50 OR +1% profit OR -0.5% stop |
| **Max hold time** | 30 minutes |
| **Cooldown** | 15 minutes between trades |
| **Session** | US market hours only (09:30-16:00 ET) |
| **Filter** | No trades if ATR(14) < 0.3% of price (too flat) |

**Risk per trade:** 0.25% of equity = ~$25 per trade at $10,000 equity

**Expected behavior:**
- High frequency (5-10 trades/day per asset)
- Small wins/losses
- Requires volatile but not trending market

---

### Strategy B: VWAP Trend Pullback Scalp
**Logic:** Buy pullbacks to VWAP in uptrend, sell rallies to VWAP in downtrend.

| Parameter | Value |
|-----------|-------|
| **Primary timeframe** | 5-minute |
| **Indicators** | VWAP(session), SMA(20), RSI(14) |
| **Trend up** | Price > VWAP and SMA(20) rising |
| **Trend down** | Price < VWAP and SMA(20) falling |
| **Entry long** | Price touches VWAP from above in uptrend + RSI(14) > 40 |
| **Entry short** | Price touches VWAP from below in downtrend + RSI(14) < 60 |
| **Exit long** | +0.8% profit OR -0.4% stop OR 20 min hold |
| **Exit short** | +0.8% profit OR -0.4% stop OR 20 min hold |
| **Max hold time** | 20 minutes |
| **Cooldown** | 10 minutes between trades |
| **Session** | US market hours only |
| **Filter** | No trades if spread > 0.1% (too illiquid) |

**Risk per trade:** 0.25% of equity = ~$25 per trade

**Expected behavior:**
- Lower frequency (3-6 trades/day per asset)
- Trades with trend, not against it
- Better in trending markets

---

## 4. BACKTEST PLAN

### Requirements Before Paper Trading
| Metric | Minimum Threshold | Target |
|--------|-------------------|--------|
| Total return (1 month) | > 0% | > 2% |
| Win rate | > 45% | > 50% |
| Profit factor | > 1.2 | > 1.5 |
| Max drawdown | < 3% | < 2% |
| Sharpe ratio | > 0.5 | > 1.0 |
| Number of trades | ≥ 100 | ≥ 200 |
| Average win | > average loss × 1.2 | > × 1.5 |
| Worst losing streak | < 8 trades | < 5 trades |

### Backtest Methodology
1. **Data:** 5-minute OHLCV bars, 3 months history (Alpaca crypto)
2. **Fees:** 0.1% per trade (Alpaca crypto commission)
3. **Slippage:** 0.05% per trade
4. **No look-ahead:** Only use past bars for signal
5. **Walk-forward:** Train on month 1-2, test on month 3
6. **Both assets:** BTC/USD and ETH/USD separately

### Backtest Output Format
```json
{
  "strategy": "rsi_mean_reversion",
  "asset": "BTCUSD",
  "period": "2026-02-01 to 2026-04-30",
  "total_return_pct": 3.2,
  "win_rate": 0.52,
  "profit_factor": 1.45,
  "max_drawdown_pct": 1.8,
  "sharpe_ratio": 1.1,
  "total_trades": 245,
  "avg_win_pct": 0.35,
  "avg_loss_pct": -0.22,
  "worst_streak": 6,
  "fees_pct": 0.49,
  "net_profit_pct": 2.71,
  "passes_thresholds": true
}
```

---

## 5. DEVELOPMENT CHECKLIST

### Phase 1 — Clean Reset (Today)
- [x] Create `ea-simple-reset` branch
- [x] Preserve old project in `recovery-validation-v3`
- [ ] Create `simple_ea/` directory
- [ ] Write `config.py` with all risk constants
- [ ] Write `data_fetcher.py` (5m bars)
- [ ] Write `trade_logger.py` (CSV + JSONL)

### Phase 2 — Strategy Development (This weekend)
- [ ] Implement Strategy A (RSI Mean Reversion)
- [ ] Implement Strategy B (VWAP Pullback)
- [ ] Write `backtest_engine.py` (vectorized)
- [ ] Run backtests for both strategies on BTC/USD
- [ ] Run backtests for both strategies on ETH/USD
- [ ] Document results in `validation/backtest_results.md`

### Phase 3 — Risk & Execution (Monday)
- [ ] Write `risk_governor.py` (hard limits)
- [ ] Write `execution.py` (paper orders)
- [ ] Write `position_tracker.py` (SL/TP monitoring)
- [ ] Write tests for all components
- [ ] Run integration tests

### Phase 4 — Paper Trading (If backtests pass)
- [ ] Wire components into `main.py`
- [ ] Run paper mode for 1-2 weeks
- [ ] Log every trade with reason
- [ ] Compare results to backtest expectations
- [ ] Daily CEO reports (simple text, not watchdog)

### Phase 5 — Review (After paper proof)
- [ ] Analyze paper results
- [ ] Compare to backtest
- [ ] Adjust parameters if drift > 20%
- [ ] Ask CEO about tiny live test

---

## 6. WHAT OLD CODE TO KEEP

| File | Location | Why |
|------|----------|-----|
| Alpaca client | `src/broker/alpaca_client.py` | API wrapper works, needs no changes |
| Position record | `src/core/position_manager.py` (dataclass only) | Track positions |
| `.env` | Root | API keys, already configured |

### What to Retire
Everything else from old architecture. The old system was built for an AI-agent trading company. We now need a simple EA bot. Start fresh with clean code.

---

## 7. RISK CONSTANTS (Hard-Coded in config.py)

```python
# Risk limits — cannot be changed without code commit
MAX_POSITIONS_TOTAL = 2
MAX_POSITIONS_PER_ASSET = 1
RISK_PER_TRADE_PCT = 0.25  # 0.25% of equity
DAILY_MAX_LOSS_PCT = 1.0    # Stop trading after 1% daily loss
WEEKLY_MAX_LOSS_PCT = 3.0   # Stop trading after 3% weekly loss
MAX_HOLD_TIME_MINUTES = 30  # Force exit after 30 min
COOLDOWN_MINUTES = 15       # Wait 15 min between trades
NO_MARTINGALE = True        # Never increase size after loss
NO_AVERAGING_DOWN = True    # Never add to losing position
NO_REVENGE_TRADING = True   # 30 min cooldown after stop-loss
SESSION_START = "09:30"     # ET
SESSION_END = "16:00"       # ET
```

---

## 8. REPORTING FORMAT (Simple)

No watchdog. No dashboard. No web UI.

**Daily report (CLI output + file):**
```
=== EA Report: 2026-05-22 ===
Strategy: RSI Mean Reversion
Mode: PAPER
Equity: $10,000.00
Day P/L: +$12.50 (+0.13%)
Open positions: 0
Trades today: 3 (2 wins, 1 loss)
Win rate: 66.7%
Max drawdown: -0.08%
Status: RUNNING
```

**Trade log (CSV):**
```
timestamp,symbol,side,entry_price,exit_price,qty,pnl,reason,sl,tp
2026-05-22T09:35:00,BTCUSD,buy,77450.00,77520.00,0.0032,+$22.40,rsi_exit_rsi>50,77200,77800
```

---

## 9. CEO APPROVAL REQUIRED FOR

| Action | Requires CEO? |
|--------|---------------|
| Phase 1-3 development | ❌ No — autonomous |
| Backtest parameter changes | ❌ No — autonomous |
| Phase 4 paper trading start | ❌ No — autonomous (paper only) |
| Live trading (Phase 6) | ✅ YES — explicit approval |
| Increase risk limits | ✅ YES — explicit approval |
| Add leverage | ✅ YES — explicit approval |
| Add new assets (SOL, etc.) | ✅ YES — explicit approval |
| Delete old code permanently | ✅ YES — explicit approval |
| Resume old agent system | ✅ YES — explicit approval |

---

## 10. NEXT ACTION

**Jarvis to begin Phase 1 immediately:**
1. Create `simple_ea/` directory
2. Write `config.py` with all hard-coded risk limits
3. Write `data_fetcher.py` (Alpaca 5m bars)
4. Report back when Phase 1 complete

**No trading. No daemon. No agents. Just clean code.**

🦊 **Jarvis — Developer/PM. Strategic reset acknowledged. Building simple EA from scratch.**
