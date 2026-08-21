#!/usr/bin/env python3
"""
Stocks News → Telegram Daemon
Three modes: digest (scheduled roundup), alerts (breaking news only), test.

Usage:
    python3 news_daemon.py --mode test
    python3 news_daemon.py --mode digest --label "Pre-Market Brief"
    python3 news_daemon.py --mode alerts
    python3 news_daemon.py --mode digest --dry-run
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# ─── Load env ───────────────────────────────────────────────────────────────
env_path = os.path.join(BASE_DIR, '..', '..', '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key, value.strip().strip('"').strip("'"))

import config
import filters
import formatter
import sources
import state
from telegram_client import TelegramClient, TelegramError

# ─── Logging ────────────────────────────────────────────────────────────────
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

log_file = os.path.join(LOGS_DIR, 'news_daemon.log')
handler = logging.FileHandler(log_file, mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[handler, logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def build_client(cfg, dry_run: bool) -> TelegramClient:
    """Construct the Telegram sender. In dry-run mode credentials are optional."""
    if dry_run:
        creds = {"token": "DRY-RUN", "chat_id": "DRY-RUN"}
        try:
            creds = config.telegram_credentials()
        except config.ConfigError:
            logger.info("No Telegram credentials set — dry run will only print")
    else:
        creds = config.telegram_credentials()

    return TelegramClient(
        token=creds["token"],
        chat_id=creds["chat_id"],
        timeout=cfg["network"]["timeout_seconds"],
        retries=cfg["network"]["retries"],
        disable_preview=cfg["telegram"]["disable_web_page_preview"],
        max_chars=cfg["telegram"]["max_message_chars"],
        dry_run=dry_run,
        logger=logger.info,
    )


def gather(cfg, use_seen: bool = True):
    """
    Fetch every configured feed and return ranked, de-duplicated headlines
    that have not been delivered before.
    """
    targets = config.resolve_feed_urls(cfg)
    logger.info(f"Fetching {len(targets)} feed(s)")

    raw = sources.collect(targets, cfg["network"], logger=logger.info)
    logger.info(f"Collected {len(raw)} raw item(s)")

    already = state.seen_uids(config.seen_file_path(cfg)) if use_seen else set()
    ranked = filters.filter_and_score(raw, cfg, seen_uids=already)
    logger.info(f"{len(ranked)} item(s) survived filtering ({len(already)} already seen)")

    return ranked


def record(cfg, items, dry_run: bool) -> None:
    """Persist delivered items so they are never sent twice."""
    if dry_run or not items:
        return
    path = config.seen_file_path(cfg)
    seen = state.load_seen(path)
    state.mark_sent(seen, [item.uid for item in items])
    state.save_seen(path, seen, cfg["state"]["retention_days"])
    logger.info(f"Recorded {len(items)} item(s) as delivered")


def run_digest(cfg, client, label: str, dry_run: bool) -> int:
    """Send one grouped digest. Exit code 0 even when there is nothing to send."""
    ranked = gather(cfg)
    selected = filters.select_for_digest(ranked, cfg)

    if not selected:
        logger.info("No new headlines — digest skipped")
        return 0

    message = formatter.format_digest(selected, cfg, label=label)
    silent = formatter.is_quiet_hour(cfg)

    if client.send(message, silent=silent):
        logger.info(f"Digest sent: {len(selected)} headline(s){' (silent)' if silent else ''}")
        record(cfg, selected, dry_run)
        return 0

    logger.error("Digest delivery FAILED — items left unmarked for the next run")
    return 1


def run_alerts(cfg, client, dry_run: bool) -> int:
    """Push only headlines at or above the alert threshold, one message each."""
    ranked = gather(cfg)
    urgent = filters.select_for_alerts(ranked, cfg)

    if not urgent:
        logger.info("No breaking headlines above threshold")
        return 0

    # Cap a single cycle so a feed glitch cannot spam the chat.
    limit = cfg["filters"]["max_items_per_digest"]
    urgent = filters.cap_per_symbol(urgent, cfg["filters"]["max_items_per_symbol"])[:limit]

    silent = formatter.is_quiet_hour(cfg)
    delivered = []

    for item in urgent:
        message = formatter.format_alert(item, cfg)
        if client.send(message, silent=silent):
            delivered.append(item)
        else:
            logger.error(f"Alert delivery FAILED: {item.title[:80]}")
            break

    record(cfg, delivered, dry_run)
    logger.info(f"{len(delivered)}/{len(urgent)} alert(s) sent")
    return 0 if len(delivered) == len(urgent) else 1


def run_test(cfg, client, dry_run: bool) -> int:
    """Verify credentials and delivery end to end."""
    bot_name = "dry-run"
    if not dry_run:
        info = client.get_me()
        bot_name = f"@{info.get('username', 'unknown')}"
        logger.info(f"Authenticated as {bot_name}")

    message = formatter.format_test_message(bot_name, cfg)
    if client.send(message):
        logger.info("Test message sent")
        return 0

    logger.error("Test message FAILED")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Stocks news → Telegram")
    parser.add_argument(
        '--mode', required=True, choices=['digest', 'alerts', 'test'],
        help="digest: grouped roundup; alerts: breaking only; test: connectivity check",
    )
    parser.add_argument('--label', default='Market Digest', help="Heading for digest mode")
    parser.add_argument('--config', default=None, help="Path to news.yaml")
    parser.add_argument(
        '--dry-run', action='store_true',
        help="Print the message instead of sending; nothing is marked as seen",
    )
    args = parser.parse_args()

    started = datetime.now(timezone.utc)
    logger.info("=" * 60)
    logger.info(f"NEWS {args.mode.upper()} START{' (dry run)' if args.dry_run else ''}")

    try:
        cfg = config.load_config(args.config)
        client = build_client(cfg, args.dry_run)

        if args.mode == 'digest':
            code = run_digest(cfg, client, args.label, args.dry_run)
        elif args.mode == 'alerts':
            code = run_alerts(cfg, client, args.dry_run)
        else:
            code = run_test(cfg, client, args.dry_run)

    except config.ConfigError as exc:
        logger.error(f"CONFIG ERROR: {exc}")
        return 2
    except TelegramError as exc:
        logger.error(f"TELEGRAM ERROR: {exc}")
        return 3
    except Exception as exc:
        logger.exception(f"UNHANDLED ERROR: {exc}")
        return 1

    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    logger.info(f"NEWS {args.mode.upper()} DONE in {elapsed:.1f}s (exit {code})")
    return code


if __name__ == '__main__':
    sys.exit(main())
