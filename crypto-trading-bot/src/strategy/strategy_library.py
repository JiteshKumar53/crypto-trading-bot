"""
Strategy Library
Central storage for all discovered and tested strategies with metadata.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

LIBRARY_FILE = Path(__file__).parent / "strategies" / "strategy_library.json"


class StrategyLibrary:
    """
    Persistent storage for trading strategies.
    Tracks: discovered -> implemented -> backtested -> paper_enabled
    """

    def __init__(self, library_file: Optional[Path] = None):
        self.library_file = library_file or LIBRARY_FILE
        self.library_file.parent.mkdir(parents=True, exist_ok=True)
        self.strategies = self._load()

    def _load(self) -> List[Dict]:
        """Load strategy library from disk."""
        if self.library_file.exists():
            try:
                with open(self.library_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load strategy library: {e}")
        return []

    def _save(self):
        """Save strategy library to disk."""
        try:
            with open(self.library_file, "w") as f:
                json.dump(self.strategies, f, indent=2, default=str)
        except IOError as e:
            logger.error(f"Failed to save strategy library: {e}")

    def add(self, strategy: Dict) -> bool:
        """
        Add a new strategy to the library.
        Returns True if added, False if duplicate.
        """
        # Check for duplicate by name
        if any(s["name"] == strategy.get("name") for s in self.strategies):
            logger.info(f"Strategy '{strategy.get('name')}' already in library")
            return False

        strategy["added_at"] = datetime.now(timezone.utc).isoformat()
        strategy["status"] = "discovered"  # discovered -> implemented -> backtested -> approved -> active
        self.strategies.append(strategy)
        self._save()
        logger.info(f"Strategy '{strategy.get('name')}' added to library")
        return True

    def update(self, name: str, updates: Dict) -> bool:
        """Update strategy metadata."""
        for s in self.strategies:
            if s["name"] == name:
                s.update(updates)
                s["updated_at"] = datetime.now(timezone.utc).isoformat()
                self._save()
                return True
        return False

    def get(self, name: str) -> Optional[Dict]:
        """Get strategy by name."""
        return next((s for s in self.strategies if s["name"] == name), None)

    def list_all(self) -> List[Dict]:
        """List all strategies."""
        return self.strategies

    def list_by_status(self, status: str) -> List[Dict]:
        """List strategies by status."""
        return [s for s in self.strategies if s.get("status") == status]

    def list_by_regime(self, regime: str) -> List[Dict]:
        """List strategies suitable for a market regime."""
        return [s for s in self.strategies if s.get("regime") == regime or s.get("regime") == "any"]

    def get_active_strategies(self) -> List[Dict]:
        """Get strategies approved for paper trading."""
        return [s for s in self.strategies if s.get("status") == "active"]

    def get_summary(self) -> Dict:
        """Get library summary stats."""
        statuses = {}
        for s in self.strategies:
            st = s.get("status", "unknown")
            statuses[st] = statuses.get(st, 0) + 1

        return {
            "total": len(self.strategies),
            "by_status": statuses,
            "by_regime": {},
            "active": len(self.get_active_strategies()),
            "last_updated": max((s.get("updated_at", "") for s in self.strategies), default="never"),
        }

    def record_backtest_result(self, name: str, result: Dict):
        """Record backtest result for a strategy."""
        for s in self.strategies:
            if s["name"] == name:
                if "backtests" not in s:
                    s["backtests"] = []
                s["backtests"].append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    **result,
                })
                # Auto-promote if backtest passes
                if result.get("passed") and s.get("status") == "backtested":
                    s["status"] = "approved"
                    logger.info(f"Strategy '{name}' promoted to APPROVED")
                self._save()
                return True
        return False
