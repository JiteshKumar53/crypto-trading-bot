# TRAINING_MAP.md

**Purpose:** Map every GitHub training repository to specific project files, tests, and guardrails.
**Created:** 2026-05-20 22:50 CEST
**Status:** ACTIVE — must be updated as operationalization progresses

---

## Repository 1: HKUDS/AI-Trader

**Expected use:** Agent-native trading workflow
**Current status:** NOT OPERATIONALIZED
**Target integration:** `src/agent_trading_workflow.py`

| Concept | Repository | Project File | Status |
|---------|-----------|-------------|--------|
| Agent-native decisions | AI-Trader | `src/pipeline_controller.py` (currently code-based) | NOT DONE |
| Research→signal pipeline | AI-Trader | `src/agents/strategy_research.py` | PARTIAL |
| Risk→execution pipeline | AI-Trader | `src/risk_governor.py` | PARTIAL |
| Agent consensus voting | AI-Trader | NOT IMPLEMENTED | NOT DONE |

**Files to create:**
- `src/agent_trading_workflow.py` — Agent-native decision architecture
- `src/agent_consensus.py` — Agent voting mechanism
- `AGENTS.md` — Agent roles and authority

---

## Repository 2: google-research/timesfm

**Expected use:** Time-series forecasting
**Current status:** NOT OPERATIONALIZED
**Target integration:** `src/forecasting/` (optional module)

| Concept | Repository | Project File | Status |
|---------|-----------|-------------|--------|
| Price forecasting | TimesFM | NOT IMPLEMENTED | NOT DONE |
| Forecasting team | TimesFM | NOT IMPLEMENTED | NOT DONE |
| Forecast-based sizing | TimesFM | NOT IMPLEMENTED | NOT DONE |

**Decision:** Optional — add after strategy validation is working

---

## Repository 3: github/spec-kit

**Expected use:** Spec-driven development
**Current status:** NOT OPERATIONALIZED
**Target integration:** `SPECS/` directory

| Concept | Repository | Project File | Status |
|---------|-----------|-------------|--------|
| Feature specs | spec-kit | `SPECS/` directory | NOT CREATED |
| Acceptance criteria | spec-kit | Per spec file | NOT CREATED |
| Spec review | spec-kit | Chief Architect workflow | NOT DONE |
| Spec→test mapping | spec-kit | Test file per spec | NOT DONE |

**Files to create:**
- `SPECS/strategy_validation_gate.md`
- `SPECS/reporting_watchdog.md`
- `SPECS/broker_reconciliation.md`
- `SPECS/template.md` — Spec template

---

## Repository 4: addyosmani/agent-skills

**Expected use:** Production engineering skills
**Current status:** NOT OPERATIONALIZED
**Target integration:** `skills/` directory

| Concept | Repository | Project File | Status |
|---------|-----------|-------------|--------|
| Deployment checklist | agent-skills | `skills/deployment.md` | NOT CREATED |
| Code review gate | agent-skills | `skills/code_review.md` | NOT CREATED |
| Testing requirements | agent-skills | `skills/testing.md` | NOT CREATED |
| Ship-it gate | agent-skills | `skills/shipping.md` | NOT CREATED |

**Files to create:**
- `skills/deployment.md` — Deployment skill
- `skills/code_review.md` — Code review skill
- `skills/testing.md` — Testing skill
- `skills/shipping.md` — Ship-it gate

---

## Repository 5: obra/superpowers

**Expected use:** Reusable agent workflows
**Current status:** NOT OPERATIONALIZED
**Target integration:** `skills/` directory (executable)

| Concept | Repository | Project File | Status |
|---------|-----------|-------------|--------|
| Reusable skills | superpowers | `skills/*.py` | NOT CREATED |
| Skill triggers | superpowers | Per skill | NOT DONE |
| Skill tests | superpowers | `tests/test_skills.py` | NOT DONE |

**Files to create:**
- `skills/deploy_watchdog.py` — Deploy watchdog skill
- `skills/validate_strategy.py` — Strategy validation skill
- `skills/reconcile_broker.py` — Broker reconciliation skill
- `skills/generate_report.py` — Report generation skill

---

## Repository 6: EvoMap/evolver

**Expected use:** Self-evolution system
**Current status:** PARTIAL — documentation created, not integrated
**Target integration:** `src/evolver.py`

| Concept | Repository | Project File | Status |
|---------|-----------|-------------|--------|
| Evolution events | evolver | `memory/evolution_events.jsonl` | ✅ CREATED |
| Genes | evolver | `memory/genes.json` | ✅ CREATED |
| Capsules | evolver | `memory/capsules/*.md` | ✅ CREATED |
| Automated evolution | evolver | `src/evolver.py` | NOT CREATED |
| Selection/rejection | evolver | `src/evolver.py` | NOT DONE |

**Files to create:**
- `src/evolver.py` — Automated evolution pipeline
- `src/evolution_engine.py` — Event→gene→capsule→enforce workflow

---

## Repository 7: HKUDS/OpenSpace

**Expected use:** Agent skill improvement
**Current status:** NOT OPERATIONALIZED
**Target integration:** `docs/AGENT_SKILL_REGISTRY.md`

| Concept | Repository | Project File | Status |
|---------|-----------|-------------|--------|
| Skill registry | OpenSpace | `docs/AGENT_SKILL_REGISTRY.md` | NOT CREATED |
| Agent performance | OpenSpace | `logs/agent_performance.jsonl` | NOT CREATED |
| Skill creation | OpenSpace | `skills/` directory | NOT DONE |

**Files to create:**
- `docs/AGENT_SKILL_REGISTRY.md`
- `logs/agent_performance.jsonl`

---

## Repository 8: danielmiessler/Personal_AI_Infrastructure

**Expected use:** Persistent memory and lessons
**Current status:** PARTIAL — memory files exist, not enforced
**Target integration:** Pre-cycle memory review

| Concept | Repository | Project File | Status |
|---------|-----------|-------------|--------|
| Memory files | PAI | `MEMORY.md`, `memory/*.md` | ✅ EXISTS |
| Structured memory | PAI | `memory/structured/` | NOT CREATED |
| Pre-decision review | PAI | `docs/PRE_CYCLE_MEMORY_REVIEW.md` | NOT CREATED |
| Lesson enforcement | PAI | Runtime checks | NOT DONE |

**Files to create:**
- `docs/PRE_CYCLE_MEMORY_REVIEW.md`
- `memory/lessons_learned.json`
- `memory/mistakes.jsonl`

---

## Repository 9: karpathy/autoresearch

**Expected use:** Experiment discipline
**Current status:** NOT OPERATIONALIZED
**Target integration:** `docs/RESEARCH_QUEUE.md`

| Concept | Repository | Project File | Status |
|---------|-----------|-------------|--------|
| Research queue | autoresearch | `docs/RESEARCH_QUEUE.md` | NOT CREATED |
| Experiment log | autoresearch | `logs/experiments.jsonl` | NOT CREATED |
| One-variable changes | autoresearch | Per experiment | NOT DONE |
| Revert mechanism | autoresearch | `src/experiment_manager.py` | NOT CREATED |

**Files to create:**
- `docs/RESEARCH_QUEUE.md`
- `logs/experiments.jsonl`
- `src/experiment_manager.py`

---

## Repository 10: chrisworsey55/atlas-gic

**Expected use:** Self-improving trading agents (conceptual)
**Current status:** NOT OPERATIONALIZED
**Decision:** Research reference only — do not implement without full validation

---

## Repository 11: ruvnet/ruflo

**Expected use:** Orchestration
**Current status:** NOT OPERATIONALIZED
**Decision:** Not needed — OpenClaw provides orchestration

---

## Repository 12: gsd-build/get-shit-done

**Expected use:** Execution discipline
**Current status:** NOT OPERATIONALIZED
**Target integration:** Task queue enforcement

| Concept | Repository | Project File | Status |
|---------|-----------|-------------|--------|
| Task tracking | gsd | `src/strategy/continuous_task_queue.py` | ✅ EXISTS |
| Task enforcement | gsd | Task execution workflow | NOT DONE |
| Blocked escalation | gsd | Escalation rules | NOT DONE |
| Action-oriented reports | gsd | Report template | NOT DONE |

**Files to create:**
- `docs/TASK_ENFORCEMENT.md`
- `src/task_executor.py`

---

## OPERATIONALIZATION METRICS

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Repos with code files | 12 | 1 (evolver docs) | 8% |
| Repos with tests | 12 | 1 (evolver tests) | 8% |
| Repos with guardrails | 12 | 0 | 0% |
| Repos with agent skills | 12 | 0 | 0% |
| Repos with specs | 12 | 0 | 0% |
| Total files created from training | 50+ | 15 | 30% |

---

**Last updated:** 2026-05-20 22:50 CEST  
**Next update:** After each repository is operationalized
