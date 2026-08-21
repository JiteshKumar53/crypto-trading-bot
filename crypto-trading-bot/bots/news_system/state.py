"""
Persistent ledger of already-delivered headlines.

Without this, every run would re-send the same stories. The ledger maps item
uid -> ISO timestamp of when it was sent, and is pruned by age on every save.
"""

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, Optional, Set


def load_seen(path: str) -> Dict[str, str]:
    """
    Load the ledger. A missing or corrupt file yields an empty ledger rather
    than an exception — losing de-dup history costs one repeated digest, while
    crashing costs every future digest.
    """
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items()}


def prune(seen: Dict[str, str], retention_days: int, now: Optional[datetime] = None) -> Dict[str, str]:
    """Drop entries older than the retention window; keep unparseable ones."""
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=retention_days)
    kept = {}

    for uid, stamp in seen.items():
        try:
            recorded = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            if recorded.tzinfo is None:
                recorded = recorded.replace(tzinfo=timezone.utc)
        except ValueError:
            kept[uid] = stamp
            continue
        if recorded >= cutoff:
            kept[uid] = stamp

    return kept


def save_seen(path: str, seen: Dict[str, str], retention_days: int, now: Optional[datetime] = None) -> None:
    """Prune and write the ledger atomically, so a crash cannot truncate it."""
    pruned = prune(seen, retention_days, now)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    directory = os.path.dirname(path) or "."
    fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".news_seen.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(pruned, f, indent=2, sort_keys=True)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def mark_sent(seen: Dict[str, str], uids: Iterable[str], now: Optional[datetime] = None) -> Dict[str, str]:
    """Record uids as delivered, stamped with the current UTC time."""
    now = now or datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    for uid in uids:
        seen[uid] = stamp
    return seen


def seen_uids(path: str) -> Set[str]:
    """Convenience accessor for the filter pipeline."""
    return set(load_seen(path).keys())
