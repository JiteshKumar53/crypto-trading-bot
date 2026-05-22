# Validation Evidence Pack — Template

**Prepared:** Friday, May 22, 2026 — 07:38 CEST
**Status:** WAITING FOR NEXT CYCLE (08:49 UTC)
**Cycle count:** 1/3 complete

---

## Section 1: Account Snapshot

| Field | Value | Timestamp |
|-------|-------|-----------|
| Account equity | $9,923.64 | 07:38 UTC |
| Cash reserve | $9,428.59 | 07:38 UTC |
| Buying power | $18,857.18 | 07:38 UTC |
| Open positions | 1 | 07:38 UTC |
| Open orders | 0 | 07:38 UTC |

---

## Section 2: Open Positions

| Symbol | Qty | Entry | Current | PnL | SL | TP |
|--------|-----|-------|---------|-----|----|----|
| BTCUSD | 0.006381 | $77,607.00 | $77,479.50 | -$0.81 | $76,054.86 | $81,487.35 |

---

## Section 3: Per-Asset Decision Table (Last Cycle)

| Asset | Decision | Order Size | SL | TP | Max Loss | Error |
|-------|----------|------------|----|----|----------|-------|
| BTC/USD | APPROVED | $495.21 (grandfathered) | $76,054.86 | $81,487.35 | $9.90 | None |
| ETH/USD | FAILED | N/A | N/A | N/A | N/A | Position limit $3,612 > $100 |
| SOL/USD | BLOCKED | N/A | N/A | N/A | N/A | PositionRecord bug |

---

## Section 4: Validation Checklist

| Requirement | Required | Current | Status | Evidence |
|-------------|----------|---------|--------|----------|
| 3 clean daemon cycles | 3 | 1 | 🟡 IN PROGRESS | Cycle at 04:49 UTC |
| 1 complete entry-to-exit | 1 | 0 | 🟡 IN PROGRESS | BTC position open |
| ETH sizing fixed | 1 | 0 | ⏳ PENDING | force_testing_mode deployed |
| SOL EA Core fixed | 1 | 0 | ⏳ PENDING | PositionRecord fix deployed |
| No duplicate orders | 1 | 1 | ✅ DONE | Confirmed |
| No broker mismatch | 1 | 1 | ✅ DONE | Confirmed |
| No unexpected open orders | 1 | 1 | ✅ DONE | 0 open orders |
| Watchdog no unknown fields | 1 | 1 | ✅ DONE | v3 deployed |
| Strategy quality report | 1 | 0 | ⏳ PENDING | After 3 cycles |

**Score: 5/10 complete, 5 pending**

---

## Section 5: BTC Legacy Position Recommendation

**Status:** HOLD with grandfathered exception

**Rationale:**
- Max loss: $9.90 (0.10% of portfolio)
- Completes entry-to-exit lifecycle validation
- SL/TP actively tracked
- No systemic risk

**Full analysis:** `validation/BTC_LEGACY_RECOMMENDATION.md`

---

## Section 6: Next Cycle Expectations (08:49 UTC)

| Asset | Expected | Reason |
|-------|----------|--------|
| BTC/USD | HOLD / NO NEW ORDER | Already have position, cooldown active |
| ETH/USD | APPROVED (capped at $100) | force_testing_mode=True deployed |
| SOL/USD | APPROVED | PositionRecord bug fixed |

---

## Section 7: Evidence Files

| File | Path |
|------|------|
| Latest cycle log | `logs/cycle_20260522_044937.json` |
| Daemon log | `logs/daemon.log` |
| Position tracker | `logs/position_tracker.json` |
| QA tests | `qa_test_suite.py` |
| BTC recommendation | `validation/BTC_LEGACY_RECOMMENDATION.md` |

---

**This pack will be updated after the 08:49 UTC cycle.**

🦊 Jarvis (Junior CEO)
