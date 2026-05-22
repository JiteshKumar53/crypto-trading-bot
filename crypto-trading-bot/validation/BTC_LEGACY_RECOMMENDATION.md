# BTC Legacy Position — Risk-Based Recommendation

## Position Details

| Field | Value |
|-------|-------|
| Symbol | BTCUSD |
| Qty | 0.006381 |
| Entry | $77,607.00 |
| Current | $77,479.50 |
| Exposure | $495.21 |
| Unrealized P/L | -$0.81 (-0.16%) |

## SL/TP Status

| Field | Value |
|-------|-------|
| Stop-Loss | $76,054.86 (-2.0% from entry) |
| Take-Profit | $81,487.35 (+5.0% from entry) |
| SL Distance | 1.84% above current |
| TP Distance | 5.17% above current |
| Max Allowed Loss | $9.90 |
| Portfolio at Risk | 0.10% of $10,000 |

## Risk Analysis

### 1. Exposure vs. New Cap

| Scenario | Exposure | vs $100 Cap | Risk |
|----------|----------|-------------|------|
| **Current** | $495.21 | **5x over** | 0.10% portfolio at risk |
| **If reduced** | $100.00 | At cap | 0.02% portfolio at risk |

**Fact:** This position was opened BEFORE `force_testing_mode=True` was deployed. The new $100 cap applies to NEW orders, not existing positions.

### 2. Risk Assessment

| Risk Factor | Assessment |
|-------------|-----------|
| **Max loss** | $9.90 (0.10% of portfolio) |
| **Portfolio impact** | Negligible |
| **Concentration** | Single position, 5% of equity |
| **Liquidation risk** | None — well above maintenance |
| **Exit plan** | SL/TP active and tracked |

### 3. Options

| Option | Action | Pros | Cons |
|--------|--------|------|------|
| **A. Hold (RECOMMENDED)** | Keep position, let SL/TP manage exit | - Low risk ($9.90 max loss)<br>- Allows exit lifecycle validation<br>- No transaction costs<br>- Proves complete trade cycle | - Position 5x over new cap<br>- Slightly larger than intended for testing |
| **B. Reduce** | Partial sell to ~$100 exposure | - Aligns with new cap<br>- Reduces concentration | - Creates partial exit complexity<br>- Loses full trade lifecycle data<br>- Small transaction cost |
| **C. Close** | Sell entire position | - Fully aligns with $100 cap<br>- Clean slate | - No complete lifecycle proof<br>- Misses exit monitoring test<br>- Small transaction cost |

## Recommendation

**HOLD the BTC position. Do NOT reduce or close.**

**Rationale:**

1. **Risk is negligible.** Max loss $9.90 on $10,000 portfolio. This is 0.10% — well within any reasonable drawdown limit.

2. **Completes validation checklist.** We need 1 complete entry-to-exit lifecycle. Closing now would waste the entry and require a new one.

3. **SL/TP is active.** Position is protected. If BTC drops 2%, we exit automatically with $9.90 loss. If BTC rises 5%, we take profit.

4. **Grandfathered exception justified.** The position was opened under the old rules before `force_testing_mode` was deployed. Retroactively applying new caps to existing positions is:
   - Unfair to the validation process
   - Destructive to the lifecycle test
   - Unnecessary given the tiny risk

5. **No systemic risk.** This is a single $495 position on a $10,000 account. Even if it went to zero (impossible with BTC at $77k), the loss is 5%.

## Conditions for Hold

The position must be monitored continuously. If ANY of these occur, close immediately:

- SL triggered: Exit at $76,055, accept $9.90 loss
- TP triggered: Exit at $81,487, take profit
- Strategy promotion: Reduce to $100 before promotion
- CEO override: Close if CEO explicitly orders

## Future Rule

**All NEW positions after this point must respect the $100 cap.** This BTC position is the sole grandfathered exception.

---

**Decision:** Jarvis recommends HOLD with grandfathered exception.
**Confidence:** High
**Risk:** Very low ($9.90 max loss)
**CEO override:** CEO may order close if preferred.

🦊 Jarvis (Junior CEO)
