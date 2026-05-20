# CEO Reporting Watchdog

## Problem Detected
Cron jobs were configured with `delivery.mode="announce"` but no channel was configured.
Result: Reports generated but delivery failed silently with "Channel is required".

## Fix Applied
1. Changed `sessionTarget` from "isolated" to "current" for both cron jobs
2. Changed `delivery.mode` from "announce" to "none" — reports now fire as system events in the current session
3. Both jobs will now trigger visible events that Jarvis can respond to

## Jobs Fixed
| Job | Schedule | Status |
|-----|----------|--------|
| jarvis-autonomous-heartbeat | Every 30 min | ✅ Fixed |
| jarvis-ceo-30min-report | Every 30 min (:00, :30) | ✅ Fixed |

## Watchdog Rules
1. If a heartbeat fires and Jarvis is in a session, respond with status
2. If a CEO report fires and Jarvis is in a session, generate the full report
3. If any agent/model hangs, skip it and report the failure — never block the report
4. If delivery fails, log the failure and retry on next cycle
5. Always write reports to `memory/YYYY-MM-DD.md` as backup
6. If 2+ reports are missed, send a fallback minimal report immediately

## Fallback Report Trigger
If full report cannot be generated within 60 seconds:
- Send minimal fallback with: equity, positions, daemon status, error reason
- Never let reporting silently fail
