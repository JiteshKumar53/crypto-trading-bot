# SELF_EVOLUTION_CAPSULES/CAPSULE-004.md
**Capsule ID:** CAPSULE-004
**Name:** Exit Idempotency and Position Management
**Status:** ACTIVE
**Created:** 2026-05-21
**Evolution Event:** DOUBLE-ORDER-20260521-1311
**Gene:** GENE-010

---

## Purpose

Actively manage open positions with deterministic exit rules.
Prevent passive holding and infinite partial sells.

---

## Trigger

Every position check cycle (every daemon cycle).

## Action

For every open position, check:
1. Current PnL
2. Origin strategy
3. Strategy status
4. Stop-loss
5. Take-profit
6. Time-based exit
7. Break-even stop
8. Stale-position exit

## Guardrail

- If strategy is REJECTED: default bias = reduce or close
- Exit rules must be idempotent
- Partial sell must not repeat infinitely
- Dust orders must be blocked

## Exit Rules

Default:
- Stop loss: 5% max loss
- Take profit: 10% profit target
- Time limit: 72 hours max hold
- Break-even: Move SL to BE after 3% profit

## Implementation

- src/core/position_manager.py
- Integrated into EA Core Engine (src/core/ea_core_engine.py)

## Tests

1. Stop loss triggers at correct threshold
2. Take profit triggers at correct threshold
3. Time limit triggers after 72 hours
4. Break-even stop triggers correctly
5. Rejected strategy triggers exit
6. Exit is idempotent (won't repeat)

## Verification

Run: python3 -m pytest tests/test_position_manager.py

## Status

ACTIVE — Implemented, needs full integration into PipelineController

---

*Capsule is enforced at runtime. Updates require Junior CEO decision.*
