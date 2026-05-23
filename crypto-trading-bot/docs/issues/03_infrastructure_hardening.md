# Infrastructure Hardening

**Label:** infra
**Status:** Active
**Created:** 2026-05-23

## Current Infrastructure
- Daemon: v3.0 with heartbeat, retry, duplicate detection
- Scheduling: OpenClaw cron (00:05 UTC daily)
- Health check: every 6 hours
- Data source: Alpaca (single authoritative)
- Tests: 14/14 passing

## TODO
- [ ] GitHub Actions CI pipeline
- [ ] Automated test runs on push
- [ ] Monitoring dashboard (daemon uptime visualization)
- [ ] Alert system (email/Slack on heartbeat failure)
- [ ] Log aggregation and rotation
- [ ] Backup strategy for heartbeat and trade logs

## Notes
- OpenClaw cron survives container restarts
- Health check catches missed runs every 6 hours
- systemd migration deferred until after paper trading proven
