# SELF_EVOLUTION_CAPSULES/CAPSULE-003.md
**Capsule ID:** CAPSULE-003
**Name:** Broker-First Reconciliation
**Status:** ACTIVE
**Created:** 2026-05-21
**Evolution Event:** DOUBLE-ORDER-20260521-1311
**Gene:** GENE-009

---

## Purpose

Ensure Alpaca is the source of truth for all positions and orders.
Detect and resolve mismatches between broker state and local state.

---

## Trigger

Every trading cycle and position-management cycle.

## Action

1. Fetch Alpaca account
2. Fetch Alpaca positions
3. Fetch Alpaca open orders
4. Compare broker state with local state
5. If mismatch exists, broker wins
6. Clean stale local positions
7. Cancel or reconcile stale local orders
8. Log reconciliation
9. Report major mismatch to CEO

## Guardrail

Local state cannot trigger an order if Alpaca disagrees.

If Alpaca says 0 position and local says open position:
- Mark local stale
- Clean local state
- Block local exit order
- Create reconciliation event

## Implementation

- src/broker/broker_first_reconciliation.py
- Integrated into EA Core Engine (src/core/ea_core_engine.py)

## Tests

1. Broker no position + local open → local cleaned
2. Broker qty different → local updated
3. Local stale position cannot trigger sell
4. Broker open order counts toward exposure
5. Reconciliation logs event

## Verification

Run: python3 -m pytest tests/test_broker_reconciliation.py

## Status

ACTIVE — Integrated into EA Core Engine

---

*Capsule is enforced at runtime. Updates require Junior CEO decision.*
