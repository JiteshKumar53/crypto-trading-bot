# CAPSULE-004: Broker-First Reconciliation

**Purpose:** Ensure Alpaca broker state is the source of truth for positions. Prevent stale local state from misleading position monitoring and Risk Governor.

**Origin:** Evolution Event EV-20260520-004 (Local state disagreed with Alpaca)
**Severity:** HIGH
**Owner:** Position Monitor + Risk Governor

---

## ENFORCEMENT RULES

### Rule 1: Alpaca is Source of Truth (GENE-006)
- Broker API (`get_all_positions()`) overrides local cache
- Local state is a cache, not the source of truth
- Every cycle must start with broker position check

### Rule 2: Auto-Correction
- If Alpaca shows 0 positions but local shows >0 → clear local state
- If Alpaca shows positions not in local state → add them
- If quantities differ → use Alpaca quantities
- If entry prices differ → use Alpaca entry prices

### Rule 3: Mismatch Alert
- Any broker/local mismatch creates an alert
- Alert includes: expected positions, actual positions, diff
- Alert logged to `logs/broker_reconciliation_alerts.jsonl`
- If 3+ mismatches in 1 hour → escalate to CEO

### Rule 4: No Trades on Stale State
- If reconciliation fails → block new trades
- Risk Governor must verify state is fresh before approving
- If state age > 10 minutes → request fresh reconciliation

### Rule 5: Empty Position List Handling
- If Alpaca returns empty positions → local state must be `{}`
- `_save_state({})` must be called to clear stale data
- Early return from `monitor_once()` is NOT enough — must save empty state

---

## RECONCILIATION ALGORITHM

```python
def reconcile_positions(local_state: Dict, broker_positions: List[Dict]) -> ReconciliationResult:
    """Reconcile local state with broker truth."""
    
    result = ReconciliationResult()
    broker_symbols = {p['symbol'] for p in broker_positions}
    local_symbols = set(local_state.keys())
    
    # Find mismatches
    missing_in_local = broker_symbols - local_symbols
    extra_in_local = local_symbols - broker_symbols
    qty_mismatches = []
    
    for p in broker_positions:
        sym = p['symbol']
        if sym in local_state:
            local_qty = local_state[sym].get('qty', 0)
            broker_qty = p['qty']
            if abs(local_qty - broker_qty) > 0.00001:
                qty_mismatches.append({
                    'symbol': sym,
                    'local_qty': local_qty,
                    'broker_qty': broker_qty
                })
    
    # Auto-correct
    if extra_in_local:
        for sym in extra_in_local:
            del local_state[sym]
            result.removed.append(sym)
    
    if missing_in_local:
        for sym in missing_in_local:
            # Add from broker
            p = next(pos for pos in broker_positions if pos['symbol'] == sym)
            local_state[sym] = {
                'qty': p['qty'],
                'avg_entry_price': p['avg_entry_price'],
                'current_price': p['current_price'],
                'unrealized_pl': p['unrealized_pl'],
                'entry_time': datetime.now(timezone.utc).isoformat(),
            }
            result.added.append(sym)
    
    if qty_mismatches:
        for mismatch in qty_mismatches:
            sym = mismatch['symbol']
            p = next(pos for pos in broker_positions if pos['symbol'] == sym)
            local_state[sym]['qty'] = p['qty']
            result.updated.append(sym)
    
    result.has_mismatch = bool(result.removed or result.added or result.updated)
    result.state = local_state
    
    return result
```

---

## POSITION MONITOR INTEGRATION

```python
def monitor_once(self) -> List[Dict]:
    """Run one monitoring pass with broker-first reconciliation."""
    
    # Step 1: Get broker truth
    broker_positions = self.client.get_positions()
    
    # Step 2: Load local state
    local_state = self._load_state()
    
    # Step 3: RECONCILE (broker overrides local)
    if local_state:
        result = reconcile_positions(local_state, broker_positions)
        if result.has_mismatch:
            logger.warning(f"[RECONCILIATION] Mismatches found: {result}")
            self._log_reconciliation_alert(result)
        local_state = result.state
    
    # Step 4: Build position states from reconciled data
    states = self._build_states_from_broker(broker_positions, local_state)
    
    # Step 5: Check positions and execute exits
    actions_taken = []
    for state in states:
        action = self.check_position(state)
        if action:
            success = self.execute_exit(action)
            if success:
                actions_taken.append(action)
    
    # Step 6: Save reconciled state
    self._save_state(local_state)
    
    return actions_taken
```

---

## TESTS REQUIRED

1. `test_broker_zero_positions_clears_local_state`
2. `test_broker_position_added_to_local_state`
3. `test_broker_qty_override_local_qty`
4. `test_mismatch_creates_alert`
5. `test_three_mismatches_escalates_to_ceo`
6. `test_stale_state_blocks_new_trades`
7. `test_reconciliation_runs_every_cycle`

---

## AUDIT TRAIL

- Creation: 2026-05-20 22:35 CEST
- Evolution Event: EV-20260520-004
- Genes: GENE-006
- Tests: tests/test_broker_first_reconciliation.py
- File: src/position_monitor_v2.py (modified)
