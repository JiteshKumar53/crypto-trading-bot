# TRAINING_MAP.md
**Version:** 1.0
**Date:** 2026-05-21
**Status:** ACTIVE

---

## Purpose

This document maps GitHub training repositories to operational behavior.
Every repo listed must produce runtime guardrails, tests, or implementation.

---

## Repository Map

### 1. HKUDS/AI-Trader
**Purpose:** Agent-native trading pipeline architecture
**Operationalized:** YES
**Usage:**
- PipelineController (src/pipeline_controller.py)
- Strategy Validation Gate (src/strategy_validation_gate.py)
- Broker integration (src/broker/)
- Risk Governor (src/risk/)

**Guardrails:**
- Strategy must be in leaderboard
- Paper trading only
- Risk Governor enforces limits

**Tests:**
- tests/test_pipeline_controller.py
- tests/test_strategy_validation_gate.py

---

### 2. google-research/timesfm
**Purpose:** Forecasting research module
**Operationalized:** PARTIAL
**Usage:**
- Optional signal feature (not standalone execution)
- Research module only

**Guardrails:**
- Never standalone execution
- Advisory only

**Tests:**
- Not yet implemented

---

### 3. github/spec-kit
**Purpose:** Specs and acceptance criteria
**Operationalized:** YES
**Usage:**
- Strategy Research Cards (strategies/cards/)
- Acceptance criteria for backtests
- Implementation plans

**Guardrails:**
- Every strategy must have a card
- Every card must have entry/exit rules
- Every card must have regime suitability

**Tests:**
- tests/test_strategy_cards.py

---

### 4. addyosmani/agent-skills
**Purpose:** Production engineering, testing, deployment
**Operationalized:** YES
**Usage:**
- Testing framework (tests/)
- Deployment verification
- Code review checklist
- Production readiness

**Guardrails:**
- All changes must have tests
- All tests must pass
- Deployment requires verification

**Tests:**
- tests/test_duplicate_order_prevention.py
- tests/test_training_operationalization.py

---

### 5. obra/superpowers
**Purpose:** Reusable agent skills
**Operationalized:** PARTIAL
**Usage:**
- Modular strategy patterns
- Reusable analysis components

**Guardrails:**
- Modular design
- Reusable components

**Tests:**
- Not yet implemented

---

### 6. EvoMap/evolver
**Purpose:** Self-evolution, Evolution Events, Genes, Capsules
**Operationalized:** YES
**Usage:**
- Evolution Event tracking (logs/)
- Gene definitions
- Capsule implementation
- Runtime guardrails

**Guardrails:**
- Every failure creates Evolution Event
- Every repeatable failure creates Capsule
- Repeated mistakes escalate severity

**Tests:**
- tests/test_evolution_system.py

---

### 7. HKUDS/OpenSpace
**Purpose:** Agent skill discovery, underperforming agent review
**Operationalized:** PARTIAL
**Usage:**
- Agent performance tracking
- Skill gap analysis

**Guardrails:**
- Agent performance monitoring
- Underperforming agent review

**Tests:**
- Not yet implemented

---

### 8. Personal_AI_Infrastructure
**Purpose:** Structured memory, decision logs, lessons
**Operationalized:** YES
**Usage:**
- MEMORY.md (long-term memory)
- memory/YYYY-MM-DD.md (daily logs)
- Decision logs
- Lessons learned

**Guardrails:**
- Daily memory review
- Long-term memory updates
- Decision accountability

**Tests:**
- Not applicable (human-readable files)

---

### 9. karpathy/autoresearch
**Purpose:** Hypothesis → experiment → measure → keep/reject
**Operationalized:** PARTIAL
**Usage:**
- Strategy research methodology
- Backtest validation
- Evidence-based decisions

**Guardrails:**
- Hypothesis must be testable
- Results must be measurable
- Failed hypotheses must be documented

**Tests:**
- tests/test_backtest_validation.py

---

### 10. atlas-gic
**Purpose:** Conceptual inspiration
**Operationalized:** NO
**Usage:**
- Conceptual reference only
- All claims validated independently

**Guardrails:**
- Validate everything independently
- Do not trust claims without evidence

**Tests:**
- Not applicable

---

### 11. ruflo
**Purpose:** Orchestration improvement
**Operationalized:** NO
**Usage:**
- Potential future orchestration layer
- Not currently used

**Guardrails:**
- Not yet implemented

**Tests:**
- Not yet implemented

---

### 12. get-shit-done
**Purpose:** Idle-agent prevention, continuous execution
**Operationalized:** YES
**Usage:**
- Autonomous daemon (scripts/autonomous_daemon.py)
- Continuous execution
- Blocker escalation

**Guardrails:**
- No team idle unless blocker logged
- 30-minute productivity check
- AUTONOMOUS PRODUCTIVITY FAILURE alert

**Tests:**
- tests/test_daemon_heartbeat.py

---

## Operationalization Status Summary

| Repo | Status | Guardrails | Tests |
|------|--------|-----------|-------|
| HKUDS/AI-Trader | ✅ YES | ✅ | ✅ |
| google-research/timesfm | ⚠️ PARTIAL | ⚠️ | ❌ |
| github/spec-kit | ✅ YES | ✅ | ⚠️ |
| addyosmani/agent-skills | ✅ YES | ✅ | ✅ |
| obra/superpowers | ⚠️ PARTIAL | ⚠️ | ❌ |
| EvoMap/evolver | ✅ YES | ✅ | ⚠️ |
| HKUDS/OpenSpace | ⚠️ PARTIAL | ⚠️ | ❌ |
| Personal_AI_Infrastructure | ✅ YES | ✅ | N/A |
| karpathy/autoresearch | ⚠️ PARTIAL | ⚠️ | ⚠️ |
| atlas-gic | ❌ NO | N/A | N/A |
| ruflo | ❌ NO | N/A | ❌ |
| get-shit-done | ✅ YES | ✅ | ⚠️ |

---

## Next Steps

1. Complete operationalization of PARTIAL repos
2. Add missing tests for all repos
3. Create runtime guardrails for all repos
4. Review and update monthly

---

*This document is the canonical training map. Updates require Junior CEO decision and CEO notification.*
