# CAPSULE-001: Strategy Validation Gate

**Purpose:** Prevent unvalidated strategies from trading. Block strategies that are not in the leaderboard, are rejected, or have not been backtested.

**Origin:** Evolution Event EV-20260520-001 (Unvalidated strategies traded)
**Severity:** CRITICAL
**Owner:** Risk Governor + Strategy Research Team

---

## ENFORCEMENT RULES

### Rule 1: Leaderboard Membership (GENE-001)
- Before ANY trade approval, verify strategy exists in `strategy_leaderboard.json`
- If strategy name is NOT in leaderboard → **BLOCK trade immediately**
- Log rejection with reason: "Strategy not in leaderboard"

### Rule 2: Leaderboard Status Gate (GENE-002)
- Strategy status must be:
  - `active` → Full-size trades allowed (with Risk Governor approval)
  - `testing` → Experimental size only (max $100, max 1 position)
  - `rejected` → **BLOCK trade immediately**
  - `missing` → **BLOCK trade immediately**

### Rule 3: No Leaderboard = Trading Halted
- If `strategy_leaderboard.json` cannot be loaded or is empty → **HALT all trading**
- Log: "Strategy leaderboard unavailable — trading halted"
- Alert CEO

### Rule 4: Backtest Required for Active Status
- Strategy must have backtest with:
  - Minimum 10 trades
  - Positive return (> 0%)
  - Sharpe > 2.0
  - Max drawdown < 15%
  - Lookahead clean = true
- If any check fails → status remains `testing` or `rejected`

---

## RUNTIME CHECKS

```python
def validate_strategy(strategy_name: str, asset: str) -> ValidationResult:
    """Validate strategy before trade approval."""
    
    # Check 1: Load leaderboard
    leaderboard = load_strategy_leaderboard()
    if not leaderboard:
        return ValidationResult(
            approved=False,
            reason="Strategy leaderboard unavailable"
        )
    
    # Check 2: Strategy exists
    key = f"{strategy_name}::{asset}::1h"
    if key not in leaderboard:
        return ValidationResult(
            approved=False,
            reason=f"Strategy {strategy_name} not in leaderboard"
        )
    
    # Check 3: Status check
    strategy = leaderboard[key]
    status = strategy.get("status")
    
    if status == "rejected":
        return ValidationResult(
            approved=False,
            reason=f"Strategy {strategy_name} is rejected: {strategy.get('rejection_reason')}"
        )
    
    if status == "testing":
        return ValidationResult(
            approved=True,
            reason="Strategy in testing — experimental size only",
            max_position_size=100.0,
            max_open_positions=1
        )
    
    if status == "active":
        return ValidationResult(
            approved=True,
            reason="Strategy active — full size allowed with Risk Governor approval"
        )
    
    return ValidationResult(
        approved=False,
        reason=f"Unknown strategy status: {status}"
    )
```

---

## PIPELINE INTEGRATION

**Location:** `src/pipeline_controller.py`, Stage 4 (Risk Governor)
**Action:** Add strategy validation check BEFORE Risk Governor position sizing

```python
# In pipeline cycle:
strategy_validation = validate_strategy(strategy_name, symbol)
if not strategy_validation.approved:
    return CycleResult(
        status="blocked",
        reason=strategy_validation.reason,
        stage="strategy_validation_gate"
    )
```

---

## TESTS REQUIRED

1. `test_strategy_not_in_leaderboard_blocked`
2. `test_rejected_strategy_blocked`
3. `test_testing_strategy_limited_size`
4. `test_active_strategy_allowed`
5. `test_missing_leaderboard_halts_trading`
6. `test_optimized_variant_not_in_leaderboard_blocked`

---

## AUDIT TRAIL

- Creation: 2026-05-20 22:35 CEST
- Evolution Event: EV-20260520-001
- Genes: GENE-001, GENE-002
- Tests: tests/test_strategy_validation_gate.py
- Pipeline block: src/pipeline_controller.py
