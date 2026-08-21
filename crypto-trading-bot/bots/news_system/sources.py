"""
RSS/Atom fetching and parsing.

Parsing is done with the standard library (xml.etree) so the news system adds
no dependency beyond `requests`, which the project already uses.
"""

import hashlib
import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

import requests

# Namespaces seen in the wild. Atom is the only one we need to address by name.
ATOM_NS = "{http://www.w3.org/2005/Atom}"

_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")
_ENTITY_RE = re.compile(r"&(#\d+|#x[0-9a-fA-F]+|[a-zA-Z]+);")

_ENTITIES = {
    "amp": "&",
    "lt": "<",
    "gt": ">",
    "quot": '"',
    "apos": "'",
    "nbsp": " ",
    "#39": "'",
}


@dataclass
class NewsItem:
    """A single headline, normalized across feed formats."""

    title: str
    link: str
    source: str
    published: Optional[datetime] = None
    summary: str = ""
    symbol: Optional[str] = None
    symbols: List[str] = field(default_factory=list)
    score: int = 0
    keyword_score: int = 0
    reasons: List[str] = field(default_factory=list)

    @property
    def uid(self) -> str:
        """Stable id used for de-duplication across runs and across feeds."""
        basis = _normalize_link(self.link) or self.title.strip().lower()
        return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:16]

    def age_hours(self, now: Optional[datetime] = None) -> Optional[float]:
        """Hours since publication, or None when the feed omitted a date."""
        if self.published is None:
            return None
        now = now or datetime.now(timezone.utc)
        return (now - self.published).total_seconds() / 3600.0


def _normalize_link(link: str) -> str:
    """
    Reduce a URL to a comparable form: drop scheme, tracking query params and
    trailing slashes, so the same story from two feeds collapses to one id.
    """
    if not link:
        return ""
    url = link.strip().lower()
    url = re.sub(r"^https?://", "", url)
    url = re.sub(r"^www\.", "", url)
    url = url.split("#", 1)[0]
    if "?" in url:
        base, query = url.split("?", 1)
        kept = [
            part
            for part in query.split("&")
            if part and not part.split("=", 1)[0].startswith(("utm_", "fbclid", "gclid", "ref"))
        ]
        url = base + ("?" + "&".join(sorted(kept)) if kept else "")
    return url.rstrip("/")


def clean_text(raw: str) -> str:
    """Strip HTML tags, decode common entities and collapse whitespace."""
    if not raw:
        return ""
    text = _TAG_RE.sub(" ", raw)

    def _sub(match: "re.Match") -> str:
        name = match.group(1)
        if name.startswith("#x") or name.startswith("#X"):
            try:
                return chr(int(name[2:], 16))
            except ValueError:
                return match.group(0)
        if name.startswith("#"):
            try:
                return chr(int(name[1:]))
            except ValueError:
                return match.group(0)
        return _ENTITIES.get(name.lower(), match.group(0))

    text = _ENTITY_RE.sub(_sub, text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def parse_date(raw: str) -> Optional[datetime]:
    """
    Parse a feed date into a timezone-aware UTC datetime.

    Handles RFC 2822 (RSS `pubDate`) and ISO 8601 (Atom `updated`). Returns
    None rather than raising, since a missing date is not a reason to drop a
    headline.
    """
    if not raw:
        return None
    raw = raw.strip()

    try:
        parsed = parsedate_to_datetime(raw)
        if parsed is not None:
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        pass

    iso = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(iso)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _text_of(element, *tags: str) -> str:
    """Return the text of the first matching child tag, RSS or Atom."""
    for tag in tags:
        child = element.find(tag)
        if child is None:
            child = element.find(ATOM_NS + tag)
        if child is not None and child.text:
            return child.text
    return ""


def _link_of(element) -> str:
    """Extract a link from either an RSS <link>text</link> or an Atom href."""
    child = element.find("link")
    if child is not None:
        if child.text and child.text.strip():
            return child.text.strip()
        href = child.get("href")
        if href:
            return href.strip()

    for child in element.findall(ATOM_NS + "link"):
        rel = child.get("rel", "alternate")
        href = child.get("href")
        if href and rel == "alternate":
            return href.strip()

    guid = element.find("guid")
    if guid is not None and guid.text and guid.text.strip().startswith("http"):
        return guid.text.strip()

    return ""


def parse_feed(xml_text: str, source: str, symbol: Optional[str] = None) -> List[NewsItem]:
    """
    Parse RSS 2.0 or Atom XML into NewsItems.

    Malformed XML yields an empty list — one bad feed must not take down a run.
    """
    if not xml_text or not xml_text.strip():
        return []

    try:
        root = ElementTree.fromstring(xml_text.strip())
    except ElementTree.ParseError:
        return []

    entries = root.findall(".//item")
    if not entries:
        entries = root.findall(f".//{ATOM_NS}entry")

    items = []
    for entry in entries:
        title = clean_text(_text_of(entry, "title"))
        link = _link_of(entry)
        if not title or not link:
            continue

        published = parse_date(
            _text_of(entry, "pubDate", "published", "updated", "date")
        )
        summary = clean_text(
            _text_of(entry, "description", "summary", "content")
        )

        items.append(
            NewsItem(
                title=title,
                link=link,
                source=source,
                published=published,
                summary=summary[:400],
                symbol=symbol,
            )
        )

    return items


def fetch_feed(url: str, network: Dict[str, Any]) -> "tuple[Optional[str], str]":
    """
    GET a feed with retries and exponential backoff.

    Returns (body, "") on success, or (None, reason) when every attempt failed.
    The reason is carried back rather than swallowed so an operator can tell a
    blocked proxy from a dead feed from a rate limit.
    """
    headers = {
        "User-Agent": network.get("user_agent", "stocks-news-bot/1.0"),
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
    }
    timeout = network.get("timeout_seconds", 15)
    retries = max(1, int(network.get("retries", 3)))
    reason = "no attempt made"

    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                return response.text, ""
            reason = f"HTTP {response.status_code}"
            # 4xx other than rate limiting will not fix themselves — stop early.
            if 400 <= response.status_code < 500 and response.status_code != 429:
                return None, reason
        except requests.RequestException as exc:
            reason = f"{type(exc).__name__}: {str(exc)[:120]}"

        if attempt < retries - 1:
            time.sleep(2 ** attempt)

    return None, reason


def collect(
    targets: List[Dict[str, str]],
    network: Dict[str, Any],
    logger=None,
    max_workers: int = 6,
) -> List[NewsItem]:
    """
    Fetch and parse every target feed, returning all items found.

    Fetches run on a small thread pool: a per-ticker watchlist multiplies feed
    count quickly, and the work is entirely I/O-bound. Failures are logged with
    their reason and skipped, so one dead feed cannot abort the run.
    """
    if not targets:
        return []

    def _fetch(target):
        body, reason = fetch_feed(target["url"], network)
        return target, body, reason

    collected: List[NewsItem] = []
    workers = max(1, min(max_workers, len(targets)))

    with ThreadPoolExecutor(max_workers=workers) as pool:
        # Ordered map keeps log output and item order deterministic.
        for target, body, reason in pool.map(_fetch, targets):
            if body is None:
                if logger:
                    logger(f"FEED FAIL {target['name']} — {reason}")
                continue

            items = parse_feed(body, target["name"], target.get("symbol"))
            if logger:
                logger(f"FEED OK   {target['name']} — {len(items)} items")
            collected.extend(items)

    return collected
