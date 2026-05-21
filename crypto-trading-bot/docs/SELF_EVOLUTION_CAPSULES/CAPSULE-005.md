# SELF_EVOLUTION_CAPSULES/CAPSULE-005.md
**Capsule ID:** CAPSULE-005
**Name:** EA Core Engine
**Status:** ACTIVE
**Created:** 2026-05-21
**Evolution Event:** MASTER-PLAN-20260521
**Gene:** GENE-011

---

## Purpose

Deterministic trading execution engine that integrates all safety systems.
No LLM opinion may directly place a trade.

---

## Trigger

Every trading cycle (daemon loop).

## Action

1. Load runtime state
2. Fetch broker truth from Alpaca
3. Reconcile positions
4. Check trading halt status
5. Load Strategy Leaderboard
6. Fetch market data
7. Generate strategy signals
8. Validate strategy permission
9. Check open positions and open orders
10. Run Risk Governor
11. Block duplicate orders
12. Submit Alpaca paper order (only if allowed)
13. Manage exits
14. Log decisions
15. Update runtime state
16. Report to CEO
17. Repeat

## Guardrail

**EA CORE HARD RULES:**
1. Never trade a strategy not in the leaderboard.
2. Never trade a REJECTED strategy.
3. Never trade an UNVALIDATED strategy.
4. TESTING strategies: experimental size only.
5. ACTIVE strategies: trade only if Risk Governor approves.
6. Never place duplicate orders.
7. Never exceed position limit.
8. Never exceed exposure limit.
9. Never ignore open orders.
10. Never trust local state over Alpaca.
11. Reduce-only exits allowed during halt.
12. Always log entry/exit reason.

## Implementation

- src/core/ea_core_engine.py
- Integrates all other capsules and guardrails

## Tests

1. Complete cycle runs successfully
2. Halted trading blocks new orders
3. Strategy gate blocks non-approved strategies
4. Risk Governor blocks over-limit orders
5. Duplicate order guard blocks duplicates
6. Exit manager generates exit signals
7. Broker reconciliation corrects mismatches

## Verification

Run: python3 -m pytest tests/test_ea_core_engine.py

## Status

ACTIVE — Implemented, needs integration into PipelineController

---

*Capsule is enforced at runtime. Updates require Junior CEO decision.*
