# Self-Evolution Policy

**Version:** 1.0.0  
**Date:** 2026-05-18  
**Owner:** Jarvis + Memory + Self-Evolution Team

## Philosophy
Improve continuously, but safely. No uncontrolled changes. No weakening of safety.

## Allowed Without CEO Approval
1. Create hypotheses
2. Create experiments
3. Modify research code
4. Improve prompts
5. Improve agent recommendation formats
6. Improve backtests
7. Improve strategy modules after validation
8. Improve risk detection
9. Improve documentation
10. Improve tests
11. Improve team structure
12. Replace weak agents
13. Create new specialist agents
14. Make crucial project decisions and inform CEO afterward

## Forbidden Without CEO Approval
1. Live trading
2. Increasing live-trading risk limits
3. Disabling deterministic risk controls
4. Sending secrets outside the system
5. Deleting production data
6. Any legal/financial/irreversible action

## Always Forbidden
1. Directly modifying execution logic without tests
2. Removing risk checks
3. Deploying untested strategies
4. Ignoring failed experiments
5. Repeating recorded mistakes
6. Hiding uncertainty from CEO
7. Hiding decisions from CEO
8. Treating agent recommendation as guaranteed truth
9. Bypassing hierarchy
10. Bypassing Risk Governor

## Self-Evolution Loop

```
1. Read previous mistakes and lessons
2. Identify one weakness
3. Assign to correct team per hierarchy
4. Create one hypothesis
5. Create one small experiment
6. Run tests
7. Run backtest or paper-trading simulation
8. Compare with baseline
9. Keep only if:
   - Tests pass
   - Risk-adjusted performance improves
   - Drawdown does not worsen
   - Trade count sufficient
   - No safety rule violated
10. Record result
11. Update lessons
12. If failed: revert and record why
13. Inform CEO of important successful and failed evolution decisions
```

## Experiment Log Format

```json
{
  "experiment_id": "exp-20260518-001",
  "timestamp": "2026-05-18T12:00:00Z",
  "hypothesis": "Adding RSI divergence detection improves entry timing",
  "team": "Technical Analysis (Candles)",
  "changes": ["Added divergence detection to technical agent"],
  "tests_run": ["unit tests", "backtest 2023-2024"],
  "baseline_metrics": {"sharpe": 1.2, "max_drawdown": 0.04},
  "experiment_metrics": {"sharpe": 1.35, "max_drawdown": 0.038},
  "result": "KEEP",
  "reason": "Sharpe improved, drawdown reduced, all tests passed",
  "ceo_informed": true
}
```

## Memory Maintenance
- Review daily logs periodically
- Distill learnings into MEMORY.md
- Update mistakes with root cause and prevention
- Archive old experiments after 90 days
