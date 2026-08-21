"""
Relevance filtering, scoring and de-duplication for headlines.

Everything here is pure: no network, no clock beyond an injectable `now`, so
the ranking rules stay directly testable.
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from sources import NewsItem

KEYWORD_WEIGHTS = {"high": 3, "medium": 2, "low": 1}

# A headline arriving on a per-ticker feed is about that ticker by construction.
PER_TICKER_FEED_BONUS = 2
FRESH_BONUS_HOURS = {2: 2, 6: 1}


def _symbol_pattern(symbol: str) -> "re.Pattern":
    """Whole-word, case-sensitive match for a ticker, with optional $ prefix."""
    return re.compile(rf"(?<![A-Za-z0-9]){re.escape(symbol)}(?![A-Za-z0-9])")


def _name_pattern(name: str) -> "re.Pattern":
    """
    Whole-word, case-sensitive match for a company name or alias.

    Case-sensitivity is deliberate: names like "Meta" and "Apple" double as
    ordinary words, and headlines capitalize the company. Matching "meta
    description tips" as META news is worse than missing an all-lowercase
    headline, which is rare.
    """
    return re.compile(rf"(?<![A-Za-z0-9]){re.escape(name)}(?![A-Za-z0-9])")


def build_matchers(watchlist: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Pre-compile symbol/name patterns once per run."""
    matchers = []
    for entry in watchlist:
        symbol = entry["symbol"]
        names = [entry.get("name") or ""] + list(entry.get("aliases") or [])
        matchers.append(
            {
                "symbol": symbol,
                "symbol_re": _symbol_pattern(symbol),
                "name_res": [_name_pattern(n) for n in names if n],
            }
        )
    return matchers


def match_symbols(item: NewsItem, matchers: List[Dict[str, Any]]) -> List[str]:
    """
    Return every watchlist symbol the headline refers to.

    Both tickers and names are matched case-sensitively so that lowercase
    English words ("meta", "spy") do not masquerade as watchlist hits.
    """
    haystack = f"{item.title} {item.summary}"
    matched = []

    for matcher in matchers:
        if matcher["symbol_re"].search(haystack):
            matched.append(matcher["symbol"])
            continue
        if any(pattern.search(haystack) for pattern in matcher["name_res"]):
            matched.append(matcher["symbol"])

    if item.symbol and item.symbol not in matched:
        matched.insert(0, item.symbol)

    return matched


def is_blocked(item: NewsItem, blocklist: Iterable[str]) -> bool:
    """True when the headline contains a blocklisted phrase."""
    haystack = f"{item.title} {item.summary}".lower()
    return any(phrase.lower() in haystack for phrase in blocklist if phrase)


def score_item(item: NewsItem, keywords: Dict[str, List[str]], now: Optional[datetime] = None) -> int:
    """
    Score a headline for ranking and alerting.

    Keyword hits carry the most weight, a per-ticker feed origin adds a small
    bonus, and fresh news outranks stale news at equal keyword weight. Reasons
    are recorded on the item so a digest can explain why something surfaced.
    """
    now = now or datetime.now(timezone.utc)
    score = 0
    reasons: List[str] = []
    haystack = f"{item.title} {item.summary}".lower()

    for tier, weight in KEYWORD_WEIGHTS.items():
        for keyword in keywords.get(tier) or []:
            if keyword.lower() in haystack:
                score += weight
                reasons.append(keyword)

    # Kept apart from the total: freshness and feed-origin bonuses must not let
    # an off-topic headline clear the relevance gate below.
    item.keyword_score = score

    if item.symbol:
        score += PER_TICKER_FEED_BONUS

    age = item.age_hours(now)
    if age is not None and age >= 0:
        for hours in sorted(FRESH_BONUS_HOURS):
            if age <= hours:
                score += FRESH_BONUS_HOURS[hours]
                break

    item.score = score
    item.reasons = reasons
    return score


def filter_and_score(
    items: List[NewsItem],
    cfg: Dict[str, Any],
    seen_uids: Iterable[str] = (),
    now: Optional[datetime] = None,
) -> List[NewsItem]:
    """
    Apply the full pipeline: drop seen/blocked/stale/irrelevant items, attach
    matched symbols and scores, and return them ranked best-first.

    De-duplication happens both against the persisted ledger (`seen_uids`) and
    within the batch, since the same story commonly arrives on several feeds.
    """
    now = now or datetime.now(timezone.utc)
    filters = cfg["filters"]
    matchers = build_matchers(cfg["watchlist"])
    max_age = filters["max_age_hours"]
    blocklist = filters["blocklist"]
    require_relevance = filters["require_relevance_for_market_feeds"]
    keywords = filters["keywords"]

    seen = set(seen_uids)
    kept: List[NewsItem] = []

    for item in items:
        if item.uid in seen:
            continue
        seen.add(item.uid)

        if is_blocked(item, blocklist):
            continue

        age = item.age_hours(now)
        if age is not None and age > max_age:
            continue

        item.symbols = match_symbols(item, matchers)
        score_item(item, keywords, now)

        if not item.symbols:
            # A market-wide headline naming no watchlist company is only kept
            # when it carries at least one scoring keyword.
            if require_relevance and item.keyword_score <= 0:
                continue

        kept.append(item)

    kept.sort(key=_rank_key, reverse=True)
    return kept


def _rank_key(item: NewsItem):
    """Rank by score, then recency; undated items sort last within a score."""
    published = item.published or datetime.min.replace(tzinfo=timezone.utc)
    return (item.score, published)


def cap_per_symbol(items: List[NewsItem], max_per_symbol: int) -> List[NewsItem]:
    """
    Limit how many headlines any single ticker contributes, so one busy name
    cannot crowd out the rest of the watchlist. Order is preserved.
    """
    if max_per_symbol <= 0:
        return items

    counts: Dict[str, int] = {}
    kept = []

    for item in items:
        primary = item.symbols[0] if item.symbols else None
        if primary is None:
            kept.append(item)
            continue
        if counts.get(primary, 0) >= max_per_symbol:
            continue
        counts[primary] = counts.get(primary, 0) + 1
        kept.append(item)

    return kept


def select_for_digest(items: List[NewsItem], cfg: Dict[str, Any]) -> List[NewsItem]:
    """Apply the per-symbol and total caps to a ranked list."""
    filters = cfg["filters"]
    capped = cap_per_symbol(items, filters["max_items_per_symbol"])
    return capped[: filters["max_items_per_digest"]]


def select_for_alerts(items: List[NewsItem], cfg: Dict[str, Any]) -> List[NewsItem]:
    """Return only headlines urgent enough to interrupt, highest score first."""
    threshold = cfg["filters"]["alert_threshold"]
    return [item for item in items if item.score >= threshold]


def group_by_symbol(items: List[NewsItem]) -> Dict[str, List[NewsItem]]:
    """
    Group ranked items under their primary symbol for display.

    Items matching no watchlist symbol land under the "MARKET" heading. Python
    dicts preserve insertion order, so groups appear in rank order.
    """
    groups: Dict[str, List[NewsItem]] = {}
    for item in items:
        key = item.symbols[0] if item.symbols else "MARKET"
        groups.setdefault(key, []).append(item)
    return groups
