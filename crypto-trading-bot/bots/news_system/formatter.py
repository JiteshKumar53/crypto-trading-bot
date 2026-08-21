"""
Message rendering for Telegram (HTML parse mode).
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from filters import group_by_symbol
from sources import NewsItem
from telegram_client import escape

ALERT_EMOJI = "\U0001F6A8"      # 🚨
DIGEST_EMOJI = "\U0001F4C8"     # 📈
MARKET_EMOJI = "\U0001F310"     # 🌐
MARKET_GROUP = "MARKET"


def local_now(timezone_name: str) -> datetime:
    """Current time in the configured display timezone."""
    return datetime.now(ZoneInfo(timezone_name))


def relative_age(published: Optional[datetime], now: Optional[datetime] = None) -> str:
    """Render a publication time as a compact relative age."""
    if published is None:
        return "undated"

    now = now or datetime.now(timezone.utc)
    minutes = int((now - published).total_seconds() // 60)

    if minutes < 0:
        return "just now"
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    return f"{hours // 24}d ago"


def _symbol_names(watchlist: List[Dict[str, Any]]) -> Dict[str, str]:
    return {entry["symbol"]: entry.get("name") or entry["symbol"] for entry in watchlist}


def _headline_line(item: NewsItem, now: datetime) -> str:
    """One bullet: linked title above a dim source/age/keyword line."""
    title = escape(item.title)
    link = escape(item.link)
    meta = f"{escape(item.source)} · {relative_age(item.published, now)}"
    if item.reasons:
        meta += f" · {escape(', '.join(sorted(set(item.reasons))[:3]))}"
    return f"• <a href=\"{link}\">{title}</a>\n  <i>{meta}</i>"


def format_digest(
    items: List[NewsItem],
    cfg: Dict[str, Any],
    label: str = "Market Digest",
    now: Optional[datetime] = None,
) -> str:
    """
    Render a grouped digest: one section per ticker, market-wide news last.

    Returns an empty string when there is nothing to report, so the caller can
    skip sending rather than delivering an empty message.
    """
    if not items:
        return ""

    now = now or datetime.now(timezone.utc)
    tz_name = cfg["schedule"]["timezone"]
    stamp = now.astimezone(ZoneInfo(tz_name)).strftime("%a %d %b, %H:%M %Z")
    names = _symbol_names(cfg["watchlist"])

    groups = group_by_symbol(items)
    ticker_count = len([key for key in groups if key != MARKET_GROUP])

    lines = [
        f"{DIGEST_EMOJI} <b>{escape(label)} — {escape(stamp)}</b>",
        f"<i>{len(items)} headline{'s' if len(items) != 1 else ''} · "
        f"{ticker_count} ticker{'s' if ticker_count != 1 else ''}</i>",
    ]

    market_items = groups.pop(MARKET_GROUP, [])

    for symbol, group in groups.items():
        name = names.get(symbol, symbol)
        heading = f"<b>${escape(symbol)}</b>"
        if name and name != symbol:
            heading += f" · {escape(name)}"
        lines.append("")
        lines.append(heading)
        lines.extend(_headline_line(item, now) for item in group)

    if market_items:
        lines.append("")
        lines.append(f"{MARKET_EMOJI} <b>Market</b>")
        lines.extend(_headline_line(item, now) for item in market_items)

    return "\n".join(lines)


def format_alert(item: NewsItem, cfg: Dict[str, Any], now: Optional[datetime] = None) -> str:
    """Render a single breaking headline as a standalone alert."""
    now = now or datetime.now(timezone.utc)
    names = _symbol_names(cfg["watchlist"])

    if item.symbols:
        symbol = item.symbols[0]
        name = names.get(symbol, symbol)
        heading = f"${escape(symbol)}"
        if name and name != symbol:
            heading += f" · {escape(name)}"
    else:
        heading = "Market"

    meta = f"{escape(item.source)} · {relative_age(item.published, now)} · score {item.score}"
    if item.reasons:
        meta += f" · {escape(', '.join(sorted(set(item.reasons))[:3]))}"

    return (
        f"{ALERT_EMOJI} <b>{heading}</b>\n"
        f"<a href=\"{escape(item.link)}\">{escape(item.title)}</a>\n"
        f"<i>{meta}</i>"
    )


def format_test_message(bot_name: str, cfg: Dict[str, Any]) -> str:
    """Connectivity check sent by `--mode test`."""
    tz_name = cfg["schedule"]["timezone"]
    stamp = local_now(tz_name).strftime("%Y-%m-%d %H:%M %Z")
    symbols = ", ".join(entry["symbol"] for entry in cfg["watchlist"])
    times = ", ".join(cfg["schedule"]["digest_times"])

    return (
        f"✅ <b>Stocks news bot connected</b>\n"
        f"<i>{escape(bot_name)} · {escape(stamp)}</i>\n\n"
        f"<b>Watchlist:</b> {escape(symbols)}\n"
        f"<b>Digests:</b> {escape(times)} {escape(tz_name)}\n"
        f"<b>Alert threshold:</b> score ≥ {cfg['filters']['alert_threshold']}"
    )


def is_quiet_hour(cfg: Dict[str, Any], now: Optional[datetime] = None) -> bool:
    """
    True when the current local hour falls in the configured quiet window.

    Quiet hours suppress the notification sound, not the message. The window
    may wrap midnight, e.g. [22, 7] means 22:00-06:59.
    """
    window = cfg["telegram"].get("quiet_hours") or []
    if len(window) != 2:
        return False

    start, end = window
    now = now or local_now(cfg["schedule"]["timezone"])
    hour = now.hour

    if start == end:
        return False
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end
