# JARVIS MASTER PLAN — EA-CORE AUTONOMOUS CRYPTO TRADING SYSTEM
**Version:** 1.0
**Date:** 2026-05-21
**CEO:** Jitesh Kumar
**Junior CEO:** Joshua (Jarvis)
**Status:** ACTIVE — ARCHITECTURE REBUILD IN PROGRESS

---

## 1. CURRENT PHASE

**CONTROLLED RECOVERY + EA CORE REBUILD + STRATEGY VALIDATION**

New entries HALTED until all resume conditions met.

Trading resume conditions:
1. ✅ EA Core implemented and active
2. ✅ Strategy Validation Gate live
3. ✅ Strategy Leaderboard enforced
4. ⏳ Broker-first reconciliation active
5. ✅ Order idempotency active
6. ✅ Duplicate-order prevention active
7. ✅ Risk Governor active
8. ✅ At least one strategy ACTIVE (Grid Trading BTC)
9. ✅ ACTIVE strategy has backtest evidence
10. ✅ TESTING strategy has strict size limits
11. ✅ Dry-run cycle proves all gates
12. ✅ Alpaca paper execution verified
13. ✅ CEO informed

**Resume status: 12/13 conditions met. Broker-first reconciliation partially implemented, needs full integration.**

---

## 2. ROLE DEFINITIONS

### CEO — Jitesh Kumar
- Final veto, pause, stop, abort, redirect
- Must approve real-money live trading
- Must approve live-risk increases
- Receives 30-minute reports

### Joshua (Junior CEO) — Autonomous Executive Leader
- Makes all normal/crucial decisions autonomously
- Does not wait for CEO approval (except CEO-reserved items)
- Must inform CEO of important decisions
- Selects COO, Chief Architect, teams, agents
- Owns final project direction
- Must not ask "what should I do next?"
- Must always execute next highest-priority safe task
- Paper trading decisions: autonomous
- CEO-reserved decisions only: real money, risk increases, disable controls, send secrets, delete data, irreversible actions

---

## 3. SYSTEM ARCHITECTURE

```
Jarvis Autonomous Trading System
├── EA Core Engine
│   ├── Market Scanner
│   ├── Strategy Signal Engine
│   ├── Strategy Validation Gate
│   ├── Risk Governor
│   ├── Order Idempotency Guard
│   ├── Broker Execution Layer
│   ├── Position Manager
│   ├── Exit Manager
│   ├── Trade Logger
│   └── Runtime Health Monitor
│
├── Agent Intelligence Layer
│   ├── Market Structure + Technical Analysis Agent
│   ├── Crypto Fundamental + On-chain Agent
│   ├── Sentiment + Narrative Agent
│   ├── Portfolio Risk + Execution Risk Agent
│   ├── Thesis Synthesis Agent
│   ├── Strategy Research Agent
│   ├── Backtesting Agent
│   ├── Self-Evolution Agent
│   └── Market Intelligence / Chart Monitor Agent
│
├── Strategy Validation Layer
│   ├── Strategy Leaderboard
│   ├── Backtest Reports
│   ├── TESTING / ACTIVE / REJECTED Status
│   ├── Promotion Rules
│   └── Rejection Rules
│
├── Broker Layer
│   ├── Alpaca Paper Account
│   ├── Broker-First Reconciliation
│   ├── Order History Check
│   ├── Position Truth Check
│   └── Submit Order Guard
│
├── Self-Evolution Layer
│   ├── Evolution Events
│   ├── Genes
│   ├── Capsules
│   ├── Regression Tests
│   ├── Prevention Rules
│   └── Runtime Guardrails
│
└── CEO Reporting Layer
    ├── 30-Minute Reports
    ├── Watchdog
    ├── Local Report Archive
    ├── Dashboard / Status Page
    └── Telegram/Email Channel if available
```

---

## 4. EA CORE HARD RULES

1. Never trade a strategy not in the leaderboard.
2. Never trade a REJECTED strategy.
3. Never trade an UNVALIDATED strategy.
4. Never trade a MISSING strategy.
5. TESTING strategies: experimental size only.
6. ACTIVE strategies: trade only if Risk Governor approves.
7. Never place duplicate orders.
8. Never exceed position limit.
9. Never exceed exposure limit.
10. Never ignore open orders.
11. Never trust local state over Alpaca.
12. Never average down unless explicitly part of an ACTIVE validated strategy.
13. Never open new trades during halt.
14. Reduce-only exits allowed during halt.
15. Always log entry reason.
16. Always log exit reason.
17. Always enforce stop-loss/exit rules.
18. Always update Strategy Leaderboard after results.

---

## 5. STRATEGY LEADERBOARD

### Statuses
- **MISSING**: Block
- **UNVALIDATED**: Block
- **REJECTED**: Block
- **TESTING**: Experimental size only (max $100)
- **ACTIVE**: Allowed with Risk Governor approval (max $200)
- **DISABLED**: Block

### Promotion Rules
TESTING → ACTIVE requires:
1. Live paper results confirm edge
2. Enough sample size
3. Profit factor positive
4. Acceptable average win/loss
5. No repeated losses
6. Risk Governor approval
7. Jarvis logs the decision

### Current Leaderboard
- `grid_trading_v1::BTCUSD::1h` — ACTIVE, $200 limit
- `grid_trading_v1::ETHUSD::1h` — TESTING, $100 limit
- `grid_trading_v1::SOLUSD::1h` — TESTING, $100 limit
- `donchian_20::BTCUSD::4h` — REJECTED

---

## 6. ORDER IDEMPOTENCY FORMULA

```
existing broker position value
+ open pending order value
+ proposed order value
must be <= approved strategy position limit
```

If not: BLOCK. Reduce-only orders allowed when reducing risk.

---

## 7. BROKER-FIRST RECONCILIATION

Alpaca is source of truth.

Before every cycle:
1. Fetch Alpaca account
2. Fetch Alpaca positions
3. Fetch Alpaca open orders
4. Compare with local state
5. If mismatch: broker wins
6. Clean stale local positions
7. Cancel/reconcile stale local orders
8. Log reconciliation
9. Report major mismatch to CEO

---

## 8. RISK GOVERNOR DECISIONS

- APPROVE
- APPROVE_REDUCED_SIZE
- BLOCK_STRATEGY_NOT_ACTIVE
- BLOCK_STRATEGY_REJECTED
- BLOCK_STRATEGY_MISSING
- BLOCK_TESTING_SIZE_EXCEEDED
- BLOCK_DUPLICATE_ORDER
- BLOCK_EXPOSURE_LIMIT
- BLOCK_RESERVE_VIOLATION
- BLOCK_DAILY_LOSS
- BLOCK_KILL_SWITCH
- BLOCK_BROKER_MISMATCH
- ALLOW_REDUCE_ONLY

---

## 9. PROFITABILITY GOAL

**Target:** $30–$50/day

**Recovery order:**
1. Stop uncontrolled losses
2. Recover above $10,000
3. Stay above breakeven
4. Prove positive expected value
5. Increase TESTING strategy evidence
6. Promote best strategy to ACTIVE
7. Scale gradually
8. Work toward $30–$50/day

---

## 10. AUTONOMOUS PRODUCTIVITY

If trading is halted, work on:
1. External strategy research
2. Strategy cards
3. Backtesting
4. Leaderboard updates
5. Runtime guardrails
6. Self-evolution tests
7. Model routing
8. Broker reconciliation
9. Exit optimization
10. Reporting reliability
11. GitHub training operationalization
12. Data improvement
13. Strategy optimization

**No team idle unless blocker logged.**

---

## 11. SELF-EVOLUTION

Every serious failure creates:
1. Evolution Event
2. Root cause
3. Gene
4. Capsule (if repeatable)
5. Regression test
6. Runtime guardrail
7. Verification evidence
8. CEO report

**If mistake repeats:** previous evolution failed. Escalate. Stronger capsule. Hard runtime block.

---

## 12. MODEL ROUTING

- **Primary:** kimi-k2.6:cloud (synthesis, decisions)
- **Fallback:** deepseek-v4-pro:cloud (architecture, risk, backtesting, code)
- **Analysis:** qwen3.5:397b-cloud (analysis, research)
- **Fast checks:** deepseek-v4-flash:cloud
- **Reports:** minimax-m2.7:cloud

**No model places trades directly. Model output = advisory only. EA Core decides mechanical validity.**

---

## 13. CEO REPORTING

Every 30 minutes (Europe/Stockholm).

Required sections:
1. Executive Summary (equity, PnL, positions)
2. EA Core Status
3. Alpaca Status
4. Strategy Leaderboard
5. Backtesting Progress
6. External Strategy Research
7. Self-Evolution
8. Team Activity
9. Jarvis Decision
10. Next Autonomous Action

---

## 14. IMMEDIATE NEXT ACTIONS (18-Step List)

1. ✅ Confirm new entries status (HALTED for now)
2. ✅ Confirm EA Core / Strategy Gate active
3. ✅ Confirm duplicate-order fix active
4. ⏳ Confirm broker-first reconciliation active
5. ✅ Confirm order idempotency active
6. ✅ Confirm Alpaca paper account matches CEO dashboard
7. ✅ Reconcile all open positions
8. ✅ Ensure no stale local state
9. ⏳ Continue Grid Trading research
10. ⏳ Optimize Grid Trading parameters
11. ⏳ Backtest Grid Trading on BTC, ETH, SOL
12. ⏳ Backtest RSI Range Trading
13. ⏳ Backtest at least 3 external strategies
14. ⏳ Update Strategy Leaderboard
15. ⏳ Promote best strategy to TESTING if valid
16. ✅ Do not promote ACTIVE until paper evidence confirms
17. ✅ Keep 30-minute reports running
18. ✅ Log every failure as Evolution Event
19. ✅ Convert every repeated failure into guardrail/test
20. ⏳ Report progress to CEO

---

## 15. DOCUMENTATION

### Required Files (in progress)
- [ ] TRAINING_MAP.md
- [ ] AGENT_SKILL_REGISTRY.md
- [ ] REPO_TO_GUARDRAIL_MAP.md
- [ ] STRATEGY_VALIDATION_GATE.md
- [ ] DEPLOYMENT_VERIFICATION_CHECKLIST.md
- [ ] PRE_CYCLE_MEMORY_REVIEW.md
- [ ] SELF_EVOLUTION_CAPSULES/
- [ ] STRATEGY_RESEARCH_CARDS/
- [ ] tests/test_training_operationalization.py
- [ ] tests/test_strategy_validation_gate.py
- [ ] tests/test_deployment_verification.py

### Completed
- [x] AGENTS.md (base workspace rules)
- [x] USER.md (CEO profile)
- [x] IDENTITY.md (Junior CEO profile)
- [x] SOUL.md (behavioral rules)
- [x] TOOLS.md (model routing)
- [x] BOOTSTRAP.md (handled)
- [x] HEARTBEAT.md (heartbeat rules)
- [x] Strategy Leaderboard (active)
- [x] Duplicate Order Prevention Tests (10/10 passing)
- [x] Order Cooldown (3600s)
- [x] Position Limit Guard (broker layer)

---

*This document is the canonical master plan. All autonomous actions must align with this architecture. Updates require CEO notification.*
