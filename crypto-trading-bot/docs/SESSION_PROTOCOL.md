# Session Protocol

## Session Start (every new session, FIRST thing)

```bash
cd /data/.openclaw/workspace/crypto-trading-bot
git pull origin smart-ea-bot-foundation
cat MEMORY.md
git log --oneline -20
```

- Read open GitHub issues for current tasks.
- Check daemon heartbeat: `cat smart-ea-bot/core/logs/daemon_heartbeat.json`
- Run health check: `bash scripts/check_heartbeat.sh`

## Session End (before session closes)

```bash
git add -A
git commit -m "session: [summary]"
git push origin smart-ea-bot-foundation
```

## Daily Morning Check

```bash
cat smart-ea-bot/core/logs/daemon_heartbeat.json
bash scripts/check_heartbeat.sh
python3 -m pytest smart-ea-bot/core/tests/ -v --tb=short
```

## GitHub is the source of truth. If it is not on GitHub, it did not happen.
