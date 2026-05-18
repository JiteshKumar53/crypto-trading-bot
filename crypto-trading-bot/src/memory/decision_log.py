"""
Decision Log System
Agent: Memory + Self-Evolution Team

Persistent, auditable records of all crucial decisions.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class DecisionRecord:
    timestamp: str
    decision_id: str
    decision_type: str  # "autonomous_jarvis", "ceo_approval_required", "risk_governor_block"
    decision_maker: str
    title: str
    description: str
    recommendations_reviewed: List[str]
    agreement: str
    disagreement: Optional[str]
    files_changed: List[str]
    tests_run: List[str]
    result: str
    risks: str
    next_step: str
    ceo_approval_needed: bool
    ceo_informed: bool
    ceo_response: Optional[str] = None


class DecisionLog:
    """Persistent decision log stored as JSONL."""

    def __init__(self, log_dir: Optional[str] = None):
        if log_dir is None:
            log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs", "decisions")
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "decisions.jsonl"

    def log(self, record: DecisionRecord) -> str:
        """Log a decision. Returns the decision_id."""
        record.timestamp = datetime.utcnow().isoformat() + "Z"
        with open(self.log_file, "a") as f:
            f.write(json.dumps(asdict(record), indent=None) + "\n")
        return record.decision_id

    def get_all(self) -> List[Dict]:
        """Get all decisions."""
        decisions = []
        if self.log_file.exists():
            with open(self.log_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        decisions.append(json.loads(line))
        return decisions

    def get_recent(self, n: int = 10) -> List[Dict]:
        """Get recent decisions."""
        all_decisions = self.get_all()
        return all_decisions[-n:]

    def get_by_id(self, decision_id: str) -> Optional[Dict]:
        """Get a specific decision."""
        for decision in self.get_all():
            if decision["decision_id"] == decision_id:
                return decision
        return None

    def log_ceo_response(self, decision_id: str, response: str):
        """Update a decision with CEO response."""
        decisions = self.get_all()
        updated = False
        for d in decisions:
            if d["decision_id"] == decision_id:
                d["ceo_response"] = response
                updated = True
                break

        if updated:
            with open(self.log_file, "w") as f:
                for d in decisions:
                    f.write(json.dumps(d, indent=None) + "\n")
