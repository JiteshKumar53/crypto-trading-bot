# SMART EA BOT COMPANY — Blueprint
**Status:** DESIGN PHASE — NO TRADING  
**Branch:** `ea-simple-reset` (to be renamed `smart-ea-bot`)  
**Date:** Friday, May 22, 2026 — 12:52 CEST  
**CEO:** Jitesh Kumar  
**Junior CEO:** Jarvis (Second Brain)

---

## A. SMART EA BOT COMPANY ARCHITECTURE

### Core Principle
**Agents research and build. Code executes. Risk controls protect. GitHub remembers. Jarvis manages. CEO sets boundaries.**

### Company Structure
```
CEO (Jitesh Kumar)
  └── Junior CEO (Jarvis — Second Brain)
      ├── Strategy Research Department
      ├── Backtest Department
      ├── Risk Management Department
      ├── Execution Engineering Department
      ├── QA Department
      ├── Observability Department
      ├── GitHub Management Department
      └── Architecture Department
          └── Multiple Isolated Trading Bots
```

### Execution Path (Deterministic — No Agents)
```
Market Data (Alpaca API)
  ↓
Bot Strategy Signal (deterministic code)
  ↓
Risk Manager (hard-coded limits)
  ↓
Broker Reconciliation (Alpaca truth)
  ↓
Duplicate Prevention (order ID tracking)
  ↓
Position Sizer (0.25% equity per trade)
  ↓
Alpaca Paper Execution
  ↓
Position Manager (SL/TP tracking)
  ↓
Watchdog Report (simple text/JSON)
```

### Research Path (Agent-Advisory)
```
Market Data
  ↓
Strategy Research Agent (analyzes, proposes)
  ↓
Backtest Agent (tests, validates)
  ↓
Risk Manager Agent (reviews limits)
  ↓
QA Agent (tests code)
  ↓
Architect Agent (reviews design)
  ↓
GitHub Manager Agent (creates issues/PRs)
  ↓
Output: Research reports, code proposals, PRs
```

**RULE:** Research agents may NEVER touch live execution. Their output is code proposals and reports only.

---

## B. JARVIS ROLE — JUNIOR CEO

### Authority Model

**Jarvis has FULL AUTONOMY for:**
- Planning and roadmap creation
- Coding and architecture
- Testing and QA
- Backtesting and research
- Creating and assigning agents
- Creating GitHub issues, branches, PRs
- Reviewing internal PRs
- Tracking validation status
- Writing documentation
- Fixing bugs
- Improving logs and reporting
- Creating new bots
- Managing bot lifecycle (up to PAPER TEST)
- Technical decisions within risk boundaries

**Jarvis MUST ASK CEO for:**
- Live-money trading enablement
- Increasing risk limits above current bounds
- Increasing order size
- Enabling leverage
- Adding new real-money broker
- Deleting project files permanently
- Disabling Risk Governor
- Disabling Broker Reconciliation
- Promoting any bot to LIVE status
- Any action materially increasing financial risk

### Decision Framework
```
Is it inside approved risk boundaries?
├── YES → Act autonomously, report after
└── NO  → Ask CEO before acting
```

### Reporting Cadence
- **Daily:** Simple text report (bot status, positions, P/L)
- **Weekly:** Comprehensive report (backtests, bot progress, risks)
- **Immediate:** Escalate if risk boundary crossed or unexpected loss

---

## C. SPECIALIST AGENT TEAM DESIGN

### Agent A — Strategy Research Agent
**Role:** Design trading strategies with exact, testable rules
**Skills:** Technical analysis, market structure, indicator design
**May NOT:** Place trades, bypass risk controls, enable live trading
**Output:** `research/strategy_notes.md`, code proposals
**Current Task:** Design first 3 bot strategies

### Agent B — Backtest Agent
**Role:** Run historical tests, validate edge, reject weak strategies
**Skills:** Vectorized backtesting, statistical analysis, bias detection
**May NOT:** Execute trades, approve strategies for live
**Output:** `reports/backtests/<bot_name>.md`
**Current Task:** Define backtest methodology and thresholds

### Agent C — Risk Manager Agent
**Role:** Define and enforce risk limits for every bot
**Skills:** Position sizing, drawdown analysis, risk modeling
**May NOT:** Disable risk controls, increase limits without CEO
**Output:** `reports/risk/<bot_name>_risk_review.md`
**Current Task:** Define per-bot risk limits

### Agent D — Execution Engineer Agent
**Role:** Build deterministic execution code, order management
**Skills:** API integration, order validation, reconciliation
**May NOT:** Bypass duplicate prevention, remove ENTRY_LOCK
**Output:** `reports/execution/execution_review.md`
**Current Task:** Design execution layer architecture

### Agent E — QA Agent
**Role:** Unit tests, integration tests, failure scenarios
**Skills:** Test automation, edge case detection, regression testing
**May NOT:** Approve code for production without evidence
**Output:** `reports/qa/qa_report.md`
**Current Task:** Define test suite for all bots

### Agent F — Observability Agent
**Role:** Logging, watchdog, dashboards, CEO reports
**Skills:** Log aggregation, health monitoring, alerting
**May NOT:** Hide errors, suppress risk alerts
**Output:** `reports/observability/system_health.md`
**Current Task:** Design simple reporting format

### Agent G — GitHub Manager Agent
**Role:** Issue tracking, branch management, PR workflow, labels
**Skills:** Git workflow, project management, documentation
**May NOT:** Delete branches without approval, bypass review
**Output:** `reports/github/project_board.md`
**Current Task:** Set up GitHub project structure

### Agent H — Architect Agent
**Role:** Keep system clean, prevent over-complexity, enforce separation
**Skills:** System design, coupling analysis, technical debt tracking
**May NOT:** Allow agents into execution path
**Output:** `architecture/architecture_review.md`
**Current Task:** Design bot isolation architecture

---

## D. GITHUB WORKFLOW

### Repository Structure
```
smart-ea-bot/ (GitHub repo)
├── main (protected branch — stable only)
├── develop (integration branch)
├── bot/mean-reversion-scalper (bot development)
├── bot/trend-pullback (bot development)
├── bot/breakout-retest (bot development)
├── fix/position-record-bug (bug fixes)
├── research/vwap-strategy (research)
└── release/v1.0.0 (stable candidate)
```

### Branch Rules
| Branch | Purpose | Merge Requirement |
|--------|---------|-------------------|
| `main` | Production-stable | PR + QA pass + Architect review + Risk review |
| `develop` | Integration | PR + QA pass |
| `bot/*` | Bot development | PR to develop |
| `fix/*` | Bug fixes | PR to develop |
| `research/*` | Research | PR to develop or bot branch |
| `release/*` | Stable candidate | PR to main with full review |

### Issue Labels
```
bug — Something is broken
strategy — Strategy design or improvement
backtest — Backtesting task or result
risk — Risk limit or safety issue
execution — Order execution problem
qa — Testing or quality issue
agent — Agent behavior or improvement
urgent — Requires immediate attention
blocked — Cannot proceed, needs help
documentation — Docs or reports
architecture — System design issue
```

### PR Template
```markdown
## What Changed
- [ ] Description of change

## Why Changed
- [ ] Business/technical justification

## Tests Run
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Backtest run (if strategy logic changed)

## Backtest Result (if applicable)
- Strategy: [name]
- Asset: [BTC/USD, ETH/USD]
- Period: [dates]
- Profit factor: [value]
- Max drawdown: [value]
- Link to full report: [path]

## Risk Impact
- [ ] No risk limit changes
- [ ] Risk limit changed (requires CEO approval)

## Rollback Plan
- [ ] Revert commit [hash]
- [ ] Or: [specific rollback steps]
```

### GitHub Actions (Future)
- Run unit tests on every PR
- Run backtests on strategy changes
- Lint code on every commit
- Generate report on every merge to develop

---

## E. MULTI-BOT LIFECYCLE

### Bot Lifecycle Stages

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│   IDEA   │ → │ RESEARCH │ → │ BACKTEST │ → │    QA    │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
     ↑                                              ↓
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│   LIVE   │ ← │  REVIEW  │ ← │   PAPER  │ ← │  PROMOTE │
│  (CEO)   │    │          │    │  TEST    │    │ CANDIDATE│
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

### Stage Definitions

**IDEA**
- Agent: Strategy Research Agent
- Output: Strategy proposal document
- Requirements: Exact entry/exit rules, indicators, timeframe
- Gate: Rules must be deterministic and testable

**RESEARCH**
- Agent: Strategy Research Agent + Architect Agent
- Output: Research report, architecture review
- Requirements: Market condition analysis, expected weakness, edge hypothesis
- Gate: Strategy must have logical edge, not curve-fitted

**BACKTEST**
- Agent: Backtest Agent
- Output: Backtest report with metrics
- Requirements: 1+ year data, fees included, no lookahead bias
- Gate: Profit factor > 1.2, drawdown < 10%, 100+ trades

**QA**
- Agent: QA Agent
- Output: Test report
- Requirements: Unit tests pass, integration tests pass, edge cases covered
- Gate: All tests passing, no critical bugs

**PROMOTION CANDIDATE**
- Agent: Risk Manager Agent + Architect Agent
- Output: Risk review, architecture sign-off
- Requirements: Risk limits defined, isolation verified
- Gate: Risk review passed, architecture sound

**PAPER TEST**
- Agent: Execution Engineer Agent + Observability Agent
- Output: Paper trading results, daily reports
- Requirements: Run 1-2 weeks, compare to backtest
- Gate: Results within 20% of backtest expectation

**REVIEW**
- Agent: All agents
- Output: Comprehensive review document
- Requirements: Performance analysis, risk review, lessons learned
- Gate: Stable performance, no unexpected behavior

**LIVE**
- **CEO APPROVAL REQUIRED**
- Agent: Execution Engineer Agent (deterministic only)
- Output: Live trading results
- Requirements: CEO explicit approval, tiny position size
- Gate: CEO says "yes"

---

## F. FIRST 3 BOT CANDIDATES

### Bot 1 — Mean Reversion Scalper (MRS)
**Assets:** BTC/USD, ETH/USD
**Timeframe:** 5-minute
**Indicators:** RSI(14), SMA(20), ATR(14)
**Entry:** RSI < 30 + price > SMA(20) + ATR > threshold
**Exit:** RSI > 50 OR +1% profit OR -0.5% stop OR 30 min hold
**Risk:** 0.25% equity per trade
**Expected weakness:** Strong trends (RSI stays oversold)
**Best condition:** Range-bound, moderate volatility
**Status:** IDEA → ready for RESEARCH

### Bot 2 — Trend Pullback Scalper (TPS)
**Assets:** BTC/USD, ETH/USD
**Timeframe:** 5-minute (primary), 15-minute (confirmation)
**Indicators:** VWAP, SMA(20), RSI(14)
**Entry:** Price touches VWAP in trend + RSI confirms
**Exit:** +0.8% profit OR -0.4% stop OR 20 min hold
**Risk:** 0.25% equity per trade
**Expected weakness:** Choppy markets (no clear trend)
**Best condition:** Strong intraday trend
**Status:** IDEA → ready for RESEARCH

### Bot 3 — Breakout Retest Scalper (BRS)
**Assets:** BTC/USD, ETH/USD
**Timeframe:** 5-minute
**Indicators:** ATR(14), volume, support/resistance levels
**Entry:** Breakout above range + retest confirmation + volume spike
**Exit:** +1.2% profit OR -0.6% stop OR 25 min hold
**Risk:** 0.25% equity per trade
**Expected weakness:** False breakouts (no follow-through)
**Best condition:** Low volatility compression before expansion
**Status:** IDEA → ready for RESEARCH

### Bot 4 — Volatility Filter (VF) — Not a trading bot
**Assets:** BTC/USD, ETH/USD
**Role:** Decide if market is safe for other bots
**Indicators:** ATR(14), historical volatility
**Output:** Trade / No-Trade signal for bot fleet
**Status:** IDEA → ready for RESEARCH

---

## G. RISK AND PROMOTION RULES

### Per-Bot Risk Limits (Hard-Coded)
```python
MAX_POSITIONS_TOTAL = 2          # Across all bots
MAX_POSITIONS_PER_ASSET = 1      # Per asset per bot
RISK_PER_TRADE_PCT = 0.25        # 0.25% equity
DAILY_MAX_LOSS_PCT = 1.0         # Stop all bots after 1% loss
WEEKLY_MAX_LOSS_PCT = 3.0        # Stop all bots after 3% loss
MAX_HOLD_TIME_MINUTES = 30       # Force exit
COOLDOWN_MINUTES = 15            # Between trades
NO_MARTINGALE = True
NO_AVERAGING_DOWN = True
NO_REVENGE_TRADING = True
```

### Promotion Requirements

**To PAPER TEST:**
- [ ] Strategy rules exact and deterministic
- [ ] Backtest passes all thresholds
- [ ] QA tests pass
- [ ] Risk review approved
- [ ] Architecture review approved
- [ ] GitHub PR merged to develop

**To LIVE (CEO REQUIRED):**
- [ ] Paper test 1-2 weeks complete
- [ ] Results within 20% of backtest
- [ ] No unexpected behavior
- [ ] CEO explicit approval
- [ ] Tiny position size for first live trades

### Backtest Thresholds
| Metric | Minimum | Target |
|--------|---------|--------|
| Profit factor | > 1.2 | > 1.5 |
| Max drawdown | < 10% | < 5% |
| Win rate | > 45% | > 50% |
| Sharpe ratio | > 0.5 | > 1.0 |
| Total trades | ≥ 100 | ≥ 300 |
| Avg win / avg loss | > 1.2 | > 1.5 |

---

## H. FILE STRUCTURE

```
smart-ea-bot/
├── README.md                          # Project overview
├── AGENTS.md                          # Agent definitions and rules
├── ROADMAP.md                         # Development roadmap
├── GOVERNANCE.md                      # Risk boundaries and approval rules
├── CEO_BOUNDARIES.md                  # What requires CEO approval
│
├── bots/                              # INDEPENDENT BOT MODULES
│   ├── mean_reversion_scalper/
│   │   ├── config.yaml               # Bot-specific config
│   │   ├── strategy.py               # Signal generation (pure function)
│   │   ├── backtest_report.md        # Backtest results
│   │   ├── risk_review.md            # Risk analysis
│   │   ├── status.md                 # Current lifecycle stage
│   │   └── paper_results/            # Paper trading logs
│   │
│   ├── trend_pullback_scalper/
│   │   ├── config.yaml
│   │   ├── strategy.py
│   │   ├── backtest_report.md
│   │   ├── risk_review.md
│   │   ├── status.md
│   │   └── paper_results/
│   │
│   ├── breakout_retest_scalper/
│   │   ├── config.yaml
│   │   ├── strategy.py
│   │   ├── backtest_report.md
│   │   ├── risk_review.md
│   │   ├── status.md
│   │   └── paper_results/
│   │
│   └── volatility_filter/
│       ├── config.yaml
│       ├── strategy.py
│       └── status.md
│
├── core/                              # SHARED DETERMINISTIC ENGINE
│   ├── data_fetcher.py               # Alpaca 5m bar fetcher
│   ├── backtest_engine.py            # Vectorized backtest
│   ├── risk_governor.py              # Hard risk limits
│   ├── execution.py                  # Paper order submission
│   ├── position_manager.py           # SL/TP/entry tracking
│   ├── broker_reconciliation.py      # Alpaca truth verification
│   ├── duplicate_prevention.py       # Order ID deduplication
│   └── reporting.py                  # Simple text/JSON reports
│
├── agents/                            # AGENT DOCUMENTATION
│   ├── strategy_researcher.md
│   ├── backtest_agent.md
│   ├── risk_manager.md
│   ├── execution_engineer.md
│   ├── qa_agent.md
│   ├── observability_agent.md
│   ├── github_manager.md
│   └── architect_agent.md
│
├── reports/                           # OUTPUT REPORTS
│   ├── backtests/
│   ├── risk/
│   ├── qa/
│   ├── execution/
│   ├── observability/
│   ├── github/
│   └── daily/
│
├── tests/                             # TEST SUITE
│   ├── unit/
│   ├── integration/
│   └── regression/
│
├── github/                            # GITHUB TEMPLATES
│   ├── issue_templates/
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── strategy_proposal.md
│   ├── pr_template.md
│   └── labels.md
│
├── logs/                              # TRADE LOGS
│   ├── trades.jsonl                   # All trades
│   ├── daily_reports/                 # Daily summaries
│   └── errors/                        # Error logs
│
├── validation/                        # VALIDATION EVIDENCE
│   └── (backtest proofs, QA results)
│
├── archive/                           # OLD PROJECT PRESERVED
│   └── recovery-validation-v3/        # Old code snapshot
│
└── .env                               # API keys (NEVER COMMIT)
```

---

## I. DEVELOPMENT ROADMAP

### Phase 1 — Foundation (Week 1)
- [x] Create `ea-simple-reset` branch (done)
- [ ] Rename branch to `smart-ea-bot`
- [ ] Create file structure (dirs, README, AGENTS.md)
- [ ] Write `core/config.py` (hard-coded risk constants)
- [ ] Write `core/data_fetcher.py` (5m bars)
- [ ] Write `core/trade_logger.py` (CSV + JSONL)
- [ ] Write `core/position_manager.py` (SL/TP tracking)
- [ ] Write `core/duplicate_prevention.py`
- [ ] Commit Phase 1

### Phase 2 — Agent Setup (Week 1)
- [ ] Write agent documentation (`agents/*.md`)
- [ ] Define agent responsibilities and boundaries
- [ ] Set up GitHub labels and templates
- [ ] Create first GitHub issues for each bot
- [ ] Create bot branches
- [ ] Commit Phase 2

### Phase 3 — Bot 1 Research (Week 2)
- [ ] Strategy Research Agent: Design MRS exact rules
- [ ] Architect Agent: Review bot isolation
- [ ] Write `bots/mean_reversion_scalper/strategy.py`
- [ ] Write `bots/mean_reversion_scalper/config.yaml`
- [ ] Commit to `bot/mean-reversion-scalper`

### Phase 4 — Backtest Bot 1 (Week 2)
- [ ] Backtest Agent: Run 1-year backtest on BTC/USD
- [ ] Backtest Agent: Run 1-year backtest on ETH/USD
- [ ] Generate `bots/mean_reversion_scalper/backtest_report.md`
- [ ] Risk Manager Agent: Review and approve limits
- [ ] QA Agent: Write and run tests
- [ ] If passes → merge to develop

### Phase 5 — Bot 2 Research (Week 3)
- [ ] Strategy Research Agent: Design TPS exact rules
- [ ] Write `bots/trend_pullback_scalper/strategy.py`
- [ ] Backtest on BTC/USD and ETH/USD
- [ ] If passes → merge to develop

### Phase 6 — Bot 3 Research (Week 3-4)
- [ ] Strategy Research Agent: Design BRS exact rules
- [ ] Write `bots/breakout_retest_scalper/strategy.py`
- [ ] Backtest on BTC/USD and ETH/USD
- [ ] If passes → merge to develop

### Phase 7 — Paper Trading (Week 5+)
- [ ] Execution Engineer: Wire core to bots
- [ ] Observability Agent: Simple daily reporting
- [ ] Run paper mode for Bot 1 (1-2 weeks)
- [ ] Compare to backtest
- [ ] CEO review of paper results
- [ ] If approved → Bot 2 paper, then Bot 3

### Phase 8 — Review and Live (CEO Decision)
- [ ] Comprehensive review after 4-6 weeks paper
- [ ] CEO decides on tiny live test
- [ ] If approved → tiny live positions with strict limits

---

## J. CONFIRMATION: TRADING REMAINS OFF

| Control | Status | Evidence |
|---------|--------|----------|
| **Daemon** | 🔴 STOPPED | No process running |
| **Cron jobs** | 🔴 DELETED | None scheduled |
| **ENTRY_LOCK** | 🟢 ACTIVE | `src/entry_lock.json` present |
| **Paper trading** | 🔴 PAUSED | No daemon + lock |
| **Live trading** | 🔴 BLOCKED | Paper-only mode |
| **Old code** | 🟢 PRESERVED | `recovery-validation-v3` branch |
| **New code** | 🟡 NOT STARTED | Blueprint only |
| **Git branch** | `ea-simple-reset` | To be renamed |

**This is a planning document. No trading code has been written. No orders will be placed. The system is safely halted while we design the Smart EA Bot Company.**

---

## NEXT ACTIONS (Autonomous)

1. Rename branch to `smart-ea-bot`
2. Create file structure (Phase 1)
3. Write core foundation files
4. Write agent documentation
5. Create GitHub issues for first 3 bots
6. Report back with Phase 1 completion

**Agents research and build. Code executes. Risk controls protect. GitHub remembers. Jarvis manages. CEO sets boundaries.**

🦊 **Jarvis — Junior CEO. Smart EA Bot Company blueprint complete. Ready to build.**
