# Architecture Review — Live vs Research Separation
**Role:** Agent Blueprint (Chief Architect)
**Updated:** Friday, May 22, 2026 — 07:54 CEST
**CEO:** Jitesh Kumar
**Junior CEO:** Jarvis (Second Brain)

---

## 1. ARCHITECTURE PRINCIPLES

| Principle | Status | Evidence |
|-----------|--------|----------|
| Safety-first design | ✅ | Risk Governor runs before every order |
| Deterministic execution | ✅ | No LLM in live path |
| Broker-first truth | ✅ | Reconciliation before trading |
| Fail-safe defaults | ✅ | EA Core blocks if any stage fails |
| Observability | ✅ | Watchdog v3 reports all fields |
| Separation of concerns | ✅ | Live path ≠ Research path |

---

## 2. LIVE EXECUTION PATH

```
Market Data
  ↓
DataFetcher.fetch_hourly_bars()
  ↓
EA Core Engine (deterministic)
  ├── broker_fetch (Alpaca API)
  ├── reconciliation (BrokerFirstReconciliation)
  ├── halt_check
  ├── strategy_validation (grid_trading_v1 TESTING)
  ├── position_check
  ├── risk_governor (deterministic checks)
  ├── duplicate_check
  └── execution_ready
  ↓
PipelineController v2
  ├── sizing cap ($100 force_testing_mode)
  ├── orchestrator (ea_core_mode=True)
  └── AlpacaPaperClient.submit_order()
  ↓
PositionTracker (SL/TP recording)
  ↓
Watchdog v3 (CEO reporting)
```

**Components:**
| Module | Type | Risk Level | Status |
|--------|------|-----------|--------|
| PipelineController v2 | Python class | HIGH | ✅ Active |
| EA Core Engine | Python class | HIGH | ✅ Active |
| BrokerFirstReconciliation | Python class | HIGH | ✅ Fixed |
| Risk Governor | Python class | HIGH | ✅ Active |
| AlpacaPaperClient | Python class | HIGH | ✅ Active |
| PositionTracker | Python class | MEDIUM | ✅ Active |
| Watchdog v3 | Python script | LOW | ✅ Active |

---

## 3. RESEARCH PATH (Offline Only)

```
Market Data
  ↓
AgentRunner (5-agent pipeline)
  ├── Candles: Technical Analysis
  ├── Ledger: Fundamental Analysis
  ├── Pulse: Sentiment Analysis
  ├── Shield: Risk Assessment
  └── Compass: Thesis Synthesis
  ↓
Output: logs/agent_research/latest_recommendations.json
  ↓
Strategy Researcher reviews
  ↓
May suggest: parameter changes, new indicators, timeframe adjustments
  ↓
NO ORDER EXECUTION
```

**Components:**
| Module | Type | Risk Level | Status |
|--------|------|-----------|--------|
| AgentRunner | Python class | LOW | 🔴 DISABLED for execution |
| Candles agent | LLM (kimi-k2.6) | LOW | 🔴 Offline only |
| Ledger agent | LLM (deepseek) | LOW | 🔴 Offline only |
| Pulse agent | LLM (qwen3.5) | LOW | 🔴 Offline only |
| Shield agent | LLM (deepseek) | LOW | 🔴 Offline only |
| Compass agent | LLM (kimi-k2.6) | LOW | 🔴 Offline only |

---

## 4. RISK CONTROL VERIFICATION

| Control | Type | Where Enforced | Status |
|---------|------|---------------|--------|
| Paper mode | Hard-coded | AlpacaPaperClient | ✅ Cannot switch to live without code change |
| $100 sizing cap | Config | PipelineController | ✅ force_testing_mode=True |
| ENTRY_LOCK | File-based | autonomous_pipeline.py | ✅ Blocks if file exists |
| Risk Governor | Deterministic code | EA Core → Orchestrator | ✅ Runs every order |
| Broker reconciliation | Deterministic code | EA Core Stage 3 | ✅ Runs every cycle |
| Duplicate prevention | Deterministic code | EA Core Stage 11 | ✅ Checks local+broker state |
| SL/TP tracking | File-based | PositionTracker | ✅ Records per position |
| Watchdog reporting | File-based | CEOReportingWatchdog | ✅ Every 30 minutes |

---

## 5. COUPLING ANALYSIS

| Module | Coupled To | Risk | Action |
|--------|-----------|------|--------|
| PipelineController | EA Core, Alpaca, Risk Governor | MEDIUM | Acceptable — all are live path |
| EA Core | PositionManager, BrokerRecon, RiskGov | LOW | Acceptable — all deterministic |
| AgentRunner | Ollama API, 5 LLM agents | HIGH | 🔴 **DISABLED from execution** |
| Watchdog | None (independent) | LOW | ✅ Correctly decoupled |
| Opportunity Scanner | DataFetcher only | LOW | ✅ Correctly decoupled |

---

## 6. FAILURE ISOLATION

| Failure Scenario | Impact | Isolated? | Fallback |
|-----------------|--------|-----------|----------|
| Ollama timeout | None (execution path doesn't use Ollama) | ✅ Yes | N/A |
| EA Core crash | All trading blocked | ✅ Yes | ENTRY_LOCK auto-enables |
| Alpaca API down | Orders fail | ✅ Yes | Watchdog reports error |
| Risk Governor fails | Trading blocked | ✅ Yes | EA Core returns BLOCKED |
| Reconciliation mismatch | Trading blocked | ✅ Yes | EA Core returns BLOCKED |
| Duplicate detected | Single order blocked | ✅ Yes | Other assets unaffected |
| Watchdog fails | No CEO report | ⚠️ Partial | Fallback report generated |

---

## 7. LOGS SUFFICIENCY

| Log Type | File | Content | Sufficient? |
|----------|------|---------|-------------|
| Cycle logs | `logs/cycle_*.json` | Full EA Core stages per asset | ✅ Yes |
| Daemon log | `logs/daemon.log` | Position monitor, cycle timing | ✅ Yes |
| Pipeline log | `logs/autonomous_pipeline.log` | Pipeline execution details | ✅ Yes |
| Watchdog history | `logs/ceo_report_history.jsonl` | All CEO reports | ✅ Yes |
| Position tracker | `logs/position_tracker.json` | SL/TP per position | ✅ Yes |
| QA tests | `qa_test_suite.py` | Safety test results | ✅ Yes |
| COO status | `memory/coo_status.md` | Validation checklist | ✅ Yes |

---

## 8. ARCHITECTURE RECOMMENDATIONS

### Immediate (This Week)
1. **Keep AgentRunner DISABLED in execution path** — No LLM in live trading
2. **Maintain force_testing_mode=True** — Until CEO approves promotion
3. **Add circuit breaker** — Auto-halt after 3 consecutive failures
4. **Add position size audit log** — Every order must log "sizing_cap_enforced: true"

### Medium Term (This Month)
5. **Refactor AgentRunner** — Add explicit `execution_mode=False` flag
6. **Add chaos tests** — Simulate broker failures, timeouts, API errors
7. **Add performance benchmarks** — Track cycle time, API latency
8. **Separate config from code** — Move sizing caps, SL/TP % to config file

### Long Term (This Quarter)
9. **Add distributed tracing** — Each order gets trace ID across all modules
10. **Add rollback capability** — Revert strategy params without code deploy
11. **Add A/B testing framework** — Compare strategy variants in paper mode

---

## 9. CURRENT ARCHITECTURE GRADE

| Dimension | Score | Notes |
|-----------|-------|-------|
| Safety | A- | Deterministic controls, but no circuit breaker yet |
| Separation | A | Live and research paths properly separated |
| Observability | A | Watchdog v3, position tracker, cycle logs all active |
| Testability | B+ | 29 QA tests, but no chaos tests |
| Modularity | B+ | Some coupling between PipelineController and EA Core |
| Documentation | B | COO status and architecture review created today |

**Overall: B+ → A- with circuit breaker and chaos tests**

---

## 10. SIGN-OFF

**Chief Architect:** Agent Blueprint (operated by Jarvis)
**Date:** 2026-05-22
**Status:** Architecture is sound for VALIDATION MODE. Live path is deterministic and safe. Research path is properly isolated.

**Required before strategy promotion:**
- Circuit breaker implemented
- Chaos tests passing
- 3 clean cycles completed
- Strategy quality report produced

🦊 Chief Architect Blueprint (operated by Jarvis)
