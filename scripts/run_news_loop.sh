#!/bin/bash
# Stocks News → Telegram Loop Wrapper
# Loads environment and runs the scheduler with logging.

set -e

NEWS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../crypto-trading-bot/bots/news_system" && pwd)"
LOG_DIR="$NEWS_DIR/logs"

mkdir -p "$LOG_DIR"

# Refuse to start without credentials rather than looping on failed sends.
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
  ENV_FILE="$NEWS_DIR/../../.env"
  if [ -f "$ENV_FILE" ]; then
    set -a
    # shellcheck disable=SC1090
    . "$ENV_FILE"
    set +a
  fi
fi

if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
  echo "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set — see $NEWS_DIR/README.md" >&2
  exit 2
fi

# Remove stale PID from a previous run
rm -f "$LOG_DIR/news_loop.pid"

echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') — Starting news loop"

cd "$NEWS_DIR"
exec python3 news_loop.py >> "$LOG_DIR/news_loop.log" 2>&1
