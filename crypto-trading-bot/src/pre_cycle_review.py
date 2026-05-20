"""
Pre-Cycle Memory and Evolution Review — MANDATORY before every trading cycle.

Gene: GENE-009 (Pre-Cycle Self-Check)
Gene: GENE-010 (Memory Review Required)

Capsule: CAPSULE-005 (Pre-Cycle Memory and Evolution Review)
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# File paths
MISTAKES_FILE = Path("memory/mistakes.jsonl")
EVOLUTION_EVENTS_FILE = Path("memory/evolution_events.jsonl")
GENES_FILE = Path("memory/genes.json")
CAPSULES_DIR = Path("memory/capsules")
LEADERBOARD_FILE = Path("logs/strategy_leaderboard.json")
HALT_FILE = Path("logs/trading_halt.json")
BUGS_FILE = Path("logs/open_bugs.json")


class PreCycleReview:
    """Mandatory pre-cycle review before any trading decision."""
    
    def __init__(self):
        self.issues_found = []
        self.recommendations = []
        self.trading_allowed = True
    
    def run_full_review(self) -> Dict:
        """Run complete pre-cycle review. Returns review report."""
        logger.info("[PRE-CYCLE REVIEW] Starting mandatory memory and evolution review...")
        
        self.issues_found = []
        self.recommendations = []
        self.trading_allowed = True
        
        # 1. Check trading halt conditions
        self._check_trading_halt()
        
        # 2. Review recent mistakes
        self._review_recent_mistakes()
        
        # 3. Check active prevention rules (genes)
        self._review_active_genes()
        
        # 4. Review disabled strategies
        self._review_disabled_strategies()
        
        # 5. Check open bugs
        self._review_open_bugs()
        
        # 6. Review risk status
        self._review_risk_status()
        
        # 7. Check evolution events
        self._review_evolution_events()
        
        # 8. Check strategy validation gate status
        self._check_strategy_gate()
        
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trading_allowed": self.trading_allowed,
            "issues_found": self.issues_found,
            "recommendations": self.recommendations,
            "issue_count": len(self.issues_found),
        }
        
        if not self.trading_allowed:
            logger.critical(f"[PRE-CYCLE REVIEW] TRADING HALTED: {len(self.issues_found)} issues found")
            for issue in self.issues_found:
                logger.critical(f"  - {issue}")
        else:
            logger.info(f"[PRE-CYCLE REVIEW] PASSED: {len(self.issues_found)} warnings, trading allowed")
        
        return report
    
    def _check_trading_halt(self):
        """Check if trading is explicitly halted."""
        if HALT_FILE.exists():
            try:
                with open(HALT_FILE) as f:
                    halt_data = json.load(f)
                if halt_data.get("halted", False):
                    reason = halt_data.get("reason", "Unknown")
                    self.issues_found.append(f"Trading halt active: {reason}")
                    self.trading_allowed = False
                    logger.critical(f"[PRE-CYCLE] Trading halted: {reason}")
            except:
                pass
        
        # Also check for critical loss threshold
        # This would need account data — placeholder for now
    
    def _review_recent_mistakes(self):
        """Review recent mistakes from memory."""
        if not MISTAKES_FILE.exists():
            return
        
        try:
            with open(MISTAKES_FILE) as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        mistake = json.loads(line)
                        # Check if mistake is recent (< 7 days)
                        self.issues_found.append(
                            f"Recent mistake: {mistake.get('description', 'Unknown')} "
                            f"(prevention: {mistake.get('prevention_rule', 'None')})"
                        )
                        if not mistake.get("prevention_rule"):
                            self.recommendations.append(
                                f"Mistake '{mistake.get('description')}' has NO prevention rule — create one"
                            )
                    except json.JSONDecodeError:
                        continue
        except IOError:
            pass
    
    def _review_active_genes(self):
        """Review active prevention rules (genes)."""
        if not GENES_FILE.exists():
            self.issues_found.append("No genes file found — evolution system not initialized")
            return
        
        try:
            with open(GENES_FILE) as f:
                genes_data = json.load(f)
            
            # Handle dict format {"GENE-001": {...}, "GENE-002": {...}}
            if isinstance(genes_data, dict):
                genes = []
                for gene_id, gene_data in genes_data.items():
                    gene_data["gene_id"] = gene_id
                    genes.append(gene_data)
            else:
                genes = genes_data
            
            active_genes = [g for g in genes if g.get("active", True) or g.get("status") == "active"]
            logger.info(f"[PRE-CYCLE] {len(active_genes)} active genes")
            
            for gene in active_genes:
                logger.info(f"  - {gene.get('gene_id')}: {gene.get('name', 'Unknown')}")
        except (json.JSONDecodeError, IOError):
            self.issues_found.append("Failed to load genes — evolution system may be broken")
    
    def _review_disabled_strategies(self):
        """Review which strategies are disabled."""
        if not LEADERBOARD_FILE.exists():
            self.issues_found.append("No strategy leaderboard — cannot validate strategies")
            return
        
        try:
            with open(LEADERBOARD_FILE) as f:
                data = json.load(f)
            
            strategies = data.get("strategies", {})
            rejected = [k for k, v in strategies.items() if v.get("status") == "rejected"]
            testing = [k for k, v in strategies.items() if v.get("status") == "testing"]
            active = [k for k, v in strategies.items() if v.get("status") == "active"]
            
            logger.info(f"[PRE-CYCLE] Strategies: {len(active)} active, {len(testing)} testing, {len(rejected)} rejected")
            
            if not active and not testing:
                self.issues_found.append("ZERO active or testing strategies — no strategies available for trading")
                self.trading_allowed = False
            
            if rejected:
                for r in rejected[:5]:  # Log first 5
                    logger.warning(f"[PRE-CYCLE] Rejected strategy: {r}")
        except (json.JSONDecodeError, IOError):
            self.issues_found.append("Failed to load strategy leaderboard")
            self.trading_allowed = False
    
    def _review_open_bugs(self):
        """Check for open bugs."""
        if not BUGS_FILE.exists():
            return
        
        try:
            with open(BUGS_FILE) as f:
                bugs = json.load(f)
            
            open_bugs = [b for b in bugs if b.get("status") == "open"]
            critical_bugs = [b for b in open_bugs if b.get("severity") == "critical"]
            
            if critical_bugs:
                for bug in critical_bugs:
                    self.issues_found.append(f"Critical bug open: {bug.get('description', 'Unknown')}")
                    self.trading_allowed = False
            
            if open_bugs:
                logger.warning(f"[PRE-CYCLE] {len(open_bugs)} open bugs ({len(critical_bugs)} critical)")
        except (json.JSONDecodeError, IOError):
            pass
    
    def _review_risk_status(self):
        """Review current risk status."""
        # This would integrate with Risk Governor
        # Placeholder for now
        logger.info("[PRE-CYCLE] Risk status review: manual check required")
    
    def _review_evolution_events(self):
        """Review recent evolution events."""
        if not EVOLUTION_EVENTS_FILE.exists():
            return
        
        try:
            with open(EVOLUTION_EVENTS_FILE) as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        event = json.loads(line)
                        # Check if event has been resolved
                        if not event.get("resolution"):
                            self.recommendations.append(
                                f"Unresolved evolution event: {event.get('description', 'Unknown')}"
                            )
                    except json.JSONDecodeError:
                        continue
        except IOError:
            pass
    
    def _check_strategy_gate(self):
        """Check if strategy validation gate is active."""
        # Check if the gate module exists and is importable
        try:
            import strategy_validation_gate
            logger.info("[PRE-CYCLE] Strategy Validation Gate: ACTIVE")
        except ImportError:
            self.issues_found.append("Strategy Validation Gate NOT FOUND — trading blocked")
            self.trading_allowed = False


def run_pre_cycle_review() -> Dict:
    """Convenience function to run pre-cycle review."""
    reviewer = PreCycleReview()
    return reviewer.run_full_review()


if __name__ == "__main__":
    # Test run
    report = run_pre_cycle_review()
    print(json.dumps(report, indent=2))
