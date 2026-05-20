# CAPSULE-005: Exit Idempotency

**Purpose:** Prevent repeated exit actions on the same position. Block dust quantities from triggering sell orders. Ensure exit flags are set atomically.

**Origin:** Evolution Event EV-20260520-005 (Partial-sell death spiral and dust positions)
**Severity:** MEDIUM
**Owner:** Position Monitor + Risk Governor

---

## ENFORCEMENT RULES

### Rule 1: Exit Idempotency (GENE-007)
- Each exit action (partial sell, full sell, runner) can execute exactly once per position stage
- After `SELL_PARTIAL` → `partial_sold = True` must be set
- After `SELL_ALL` → `fully_exited = True` must be set
- After `SELL_RUNNER` → `trailing_stop_triggered = True` must be set
- If flag is already set → action is blocked with reason "already_executed"

### Rule 2: Dust Quantity Block (GENE-008)
- No sell order for quantity < 0.00001
- Dust positions must be silently ignored
- If `qty < 0.00001` → return `HOLD` with reason `dust_quantity`
- Dust must NOT create sell orders, failed or otherwise

### Rule 3: Atomic Flag Setting
- Exit flags must be set in the SAME transaction as the sell order
- If sell succeeds → set flag immediately
- If sell fails → do NOT set flag, allow retry
- Never set flag without confirmed execution

### Rule 4: Repeated Trigger Block
- If `partial_sold = True` → partial sell trigger must be ignored
- If `fully_exited = True` → all sell triggers must be ignored
- If `trailing_stop_triggered = True` → runner trigger must be ignored
- Guard condition at top of `check_position()`

---

## IDEMPOTENCY GUARDS

```python
def check_position(self, state: PositionState) -> Optional[Dict]:
    """Check position with idempotency guards."""
    
    # Guard 1: Dust quantity
    if state.qty < 0.00001:
        return self._make_action("HOLD", state.symbol, 0, state.current_price, "dust_quantity")
    
    # Guard 2: Already exited
    if getattr(state, 'fully_exited', False):
        return self._make_action("HOLD", state.symbol, 0, state.current_price, "already_exited")
    
    # Guard 3: Already partial sold
    if state.partial_sold and action_would_be_partial_sell:
        return self._make_action("HOLD", state.symbol, 0, state.current_price, "already_partial_sold")
    
    # Guard 4: Already runner exited
    if getattr(state, 'trailing_stop_triggered', False):
        return self._make_action("HOLD", state.symbol, 0, state.current_price, "already_runner_exited")
    
    # ... rest of exit logic ...
```

## ATOMIC EXECUTION

```python
def execute_exit(self, action: Dict, state: PositionState) -> bool:
    """Execute exit with atomic flag setting."""
    
    try:
        result = self.client.submit_order(
            symbol=action["symbol"],
            side="sell",
            qty=action["qty"],
        )
        
        if result.success:
            # ATOMIC: Set flag ONLY after confirmed success
            if action["action"] == "SELL_PARTIAL":
                state.partial_sold = True
                state.partial_sold_qty = action["qty"]
                logger.info(f"ATOMIC: partial_sold SET for {state.symbol}")
            
            elif action["action"] == "SELL_ALL":
                state.fully_exited = True
                state.stop_triggered = True
                state.take_profit_triggered = True
                logger.info(f"ATOMIC: fully_exited SET for {state.symbol}")
            
            elif action["action"] == "SELL_RUNNER":
                state.trailing_stop_triggered = True
                logger.info(f"ATOMIC: trailing_stop_triggered SET for {state.symbol}")
            
            return True
        else:
            logger.error(f"EXIT FAILED: {result.error} — flags NOT set")
            return False
            
    except Exception as e:
        logger.error(f"EXIT ERROR: {e} — flags NOT set")
        return False
```

---

## TESTS REQUIRED

1. `test_partial_sell_blocked_if_already_partial_sold`
2. `test_full_sell_blocked_if_already_fully_exited`
3. `test_runner_blocked_if_already_trailing_stop_triggered`
4. `test_dust_quantity_returns_hold`
5. `test_dust_quantity_does_not_create_order`
6. `test_flag_set_only_after_successful_order`
7. `test_flag_not_set_after_failed_order`
8. `test_repeated_partial_sell_blocked`

---

## AUDIT TRAIL

- Creation: 2026-05-20 22:35 CEST
- Evolution Event: EV-20260520-005
- Genes: GENE-007, GENE-008
- Tests: tests/test_exit_idempotency.py
- File: src/position_monitor_v2.py (modified)
