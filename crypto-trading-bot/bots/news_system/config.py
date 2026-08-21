"""
Config loading for the news system.

Reads config/news.yaml and the Telegram credentials from the environment.
Secrets never live in the YAML file.
"""

import os
from typing import Any, Dict, List

import yaml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
DEFAULT_CONFIG_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "..", "..", "config", "news.yaml")
)


class ConfigError(Exception):
    """Raised when the config file or environment is unusable."""


def load_config(path: str = None) -> Dict[str, Any]:
    """Load news.yaml and apply defaults for anything omitted."""
    path = path or DEFAULT_CONFIG_PATH
    if not os.path.exists(path):
        raise ConfigError(f"Config not found: {path}")

    with open(path) as f:
        cfg = yaml.safe_load(f) or {}

    cfg.setdefault("telegram", {})
    cfg.setdefault("schedule", {})
    cfg.setdefault("watchlist", [])
    cfg.setdefault("feeds", {})
    cfg.setdefault("filters", {})
    cfg.setdefault("state", {})
    cfg.setdefault("network", {})

    cfg["telegram"].setdefault("disable_web_page_preview", True)
    cfg["telegram"].setdefault("max_message_chars", 3800)
    cfg["telegram"].setdefault("quiet_hours", [])
    # None means "use the schedule timezone". Set it when you do not live in
    # the market's timezone, so quiet hours follow your clock, not the NYSE's.
    cfg["telegram"].setdefault("quiet_hours_timezone", None)

    cfg["schedule"].setdefault("timezone", "America/New_York")
    cfg["schedule"].setdefault("digest_times", ["08:30", "16:30"])
    cfg["schedule"].setdefault("alert_poll_minutes", 15)
    cfg["schedule"].setdefault("weekdays_only", True)

    cfg["feeds"].setdefault("per_ticker", [])
    cfg["feeds"].setdefault("market", [])

    cfg["filters"].setdefault("max_age_hours", 24)
    cfg["filters"].setdefault("max_items_per_digest", 12)
    cfg["filters"].setdefault("max_items_per_symbol", 3)
    cfg["filters"].setdefault("require_relevance_for_market_feeds", True)
    cfg["filters"].setdefault("blocklist", [])
    cfg["filters"].setdefault("alert_threshold", 6)
    cfg["filters"].setdefault("keywords", {})

    cfg["state"].setdefault("seen_file", "logs/news_seen.json")
    cfg["state"].setdefault("retention_days", 7)

    cfg["network"].setdefault("timeout_seconds", 15)
    cfg["network"].setdefault("retries", 3)
    cfg["network"].setdefault("user_agent", "stocks-news-bot/1.0")

    if not cfg["watchlist"]:
        raise ConfigError("watchlist is empty — nothing to track")

    return cfg


def seen_file_path(cfg: Dict[str, Any]) -> str:
    """Absolute path to the seen-item ledger."""
    rel = cfg["state"]["seen_file"]
    if os.path.isabs(rel):
        return rel
    return os.path.join(BASE_DIR, rel)


def enabled_feeds(feed_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter a feed list down to entries with enabled: true."""
    return [f for f in feed_list if f.get("enabled", True)]


def resolve_feed_urls(cfg: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Expand configured feeds into concrete {name, url, symbol} fetch targets.

    Per-ticker feeds are expanded once per watchlist symbol; market feeds are
    emitted once with symbol=None.
    """
    targets = []

    for feed in enabled_feeds(cfg["feeds"]["per_ticker"]):
        for entry in cfg["watchlist"]:
            symbol = entry["symbol"]
            targets.append(
                {
                    "name": f"{feed['name']} · {symbol}",
                    "url": feed["url"].replace("{symbol}", symbol),
                    "symbol": symbol,
                }
            )

    for feed in enabled_feeds(cfg["feeds"]["market"]):
        targets.append({"name": feed["name"], "url": feed["url"], "symbol": None})

    return targets


def telegram_credentials(require_chat_id: bool = True) -> Dict[str, str]:
    """
    Read TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID from the environment.

    Raises ConfigError with actionable text when something is missing, so the
    daemon fails loudly at startup rather than silently sending nothing.

    `require_chat_id` is False for the chatid discovery mode, whose whole
    purpose is to find the chat id the caller does not have yet.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    required = [("TELEGRAM_BOT_TOKEN", token)]
    if require_chat_id:
        required.append(("TELEGRAM_CHAT_ID", chat_id))

    missing = [name for name, value in required if not value]
    if missing:
        raise ConfigError(
            f"Missing environment variable(s): {', '.join(missing)}. "
            "See bots/news_system/README.md for how to obtain them."
        )

    return {"token": token, "chat_id": chat_id}
