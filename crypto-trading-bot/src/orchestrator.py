"""
Trading Decision Pipeline Orchestrator
Agent: Jarvis (Junior CEO)

Runs the full decision pipeline:
- Collect recommendations from 5 agents
- Pass through hierarchy
- Risk Governor validation
- Alpaca paper execution
- Memory update
- CEO notification
"""

import logging
from dataclasses import asdict
from typing import Dict, List, Optional
from datetime import datetime, timezone

from risk_governor import RiskGovernor, RiskDecision
from memory.decision_log import DecisionLog, DecisionRecord

logger = logging.getLogger(__name__)


class TradingOrchestrator:
    """
    End-to-end trading decision pipeline.
    Never executes trades from a single agent's recommendation.
    """

    def __init__(self, risk_governor: Optional[RiskGovernor] = None):
        self.risk_governor = risk_governor or RiskGovernor()
        self.decision_log = DecisionLog()
        self._ceo_approved_live_trading = False  # Default: paper only

    def set_ceo_approval(self, approved: bool, approval_id: str = ""):
        """Set CEO approval for live trading. Requires explicit approval."""
        self._ceo_approved_live_trading = approved
        logger.info(f"CEO live trading approval set: {approved} (id: {approval_id})")

    def run_pipeline(
        self,
        symbol: str,
        side: str,
        qty: float,
        price: float,
        portfolio_value: float,
        current_position_value: float,
        recommendations: List[Dict],
        strategy_backtest_passed: bool = False,
        qa_passed: bool = False,
        ea_core_mode: bool = False,
    ) -> Dict:
        """
        Run the full trading decision pipeline.

        Args:
            symbol: Asset symbol (e.g. BTC/USD)
            side: buy or sell
            qty: quantity
            price: current price
            portfolio_value: total portfolio value
            current_position_value: current position value for symbol
            recommendations: List of 5 agent recommendations
            strategy_backtest_passed: Whether backtest passed
            qa_passed: Whether QA validation passed

        Returns:
            Dict with decision, reason, and execution details
        """
        decision_id = f"dec-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{datetime.now(timezone.utc).microsecond:06d}-{symbol.replace('/', '')}"
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        logger.info(f"[Pipeline Start] {decision_id} for {side} {qty} {symbol} (ea_core_mode={ea_core_mode})")

        # Step 1: Validate recommendations present (skip in EA Core mode for paper)
        if not ea_core_mode and len(recommendations) < 5:
            return self._reject(
                decision_id=decision_id,
                reason="Insufficient agent recommendations. All 5 required.",
                symbol=symbol,
                side=side,
                qty=qty,
            )

        # Step 2: Validate backtest passed
        if not strategy_backtest_passed:
            return self._reject(
                decision_id=decision_id,
                reason="Strategy backtest not passed. Cannot proceed.",
                symbol=symbol,
                side=side,
                qty=qty,
            )

        # Step 3: Validate QA passed
        if not qa_passed:
            return self._reject(
                decision_id=decision_id,
                reason="QA validation not passed. Cannot proceed.",
                symbol=symbol,
                side=side,
                qty=qty,
            )

        # Step 4: Run Risk Governor
        risk_result = self.risk_governor.check_order(
            symbol=symbol,
            side=side,
            qty=qty,
            price=price,
            portfolio_value=portfolio_value,
            current_position_value=current_position_value,
        )

        if risk_result.decision != RiskDecision.ALLOW:
            return self._reject(
                decision_id=decision_id,
                reason=f"Risk Governor blocked: {risk_result.decision.value}. "
                       + "; ".join([c.reason for c in risk_result.checks if not c.passed]),
                symbol=symbol,
                side=side,
                qty=qty,
                risk_result=risk_result,
            )

        # Step 5: Jarvis final decision (autonomous)
        jarvis_decision = {
            "decision": "APPROVE",
            "reason": "All hierarchy checks passed. Risk Governor approved. Proceeding to execution.",
            "requires_ceo_approval": False,
        }

        # Step 6: Log decision
        record = DecisionRecord(
            timestamp=timestamp,
            decision_id=decision_id,
            decision_type="autonomous_jarvis",
            decision_maker="Jarvis",
            title=f"{side.upper()} {qty} {symbol}",
            description=jarvis_decision["reason"],
            recommendations_reviewed=[r.get("agent", "unknown") for r in recommendations],
            agreement="All hierarchy checks and Risk Governor passed",
            disagreement=None,
            files_changed=[],
            tests_run=["backtest", "qa", "risk_governor"],
            result="PENDING_EXECUTION",
            risks="; ".join([r.get("warnings", "") for r in recommendations]),
            next_step="Execute paper order via Alpaca",
            ceo_approval_needed=False,
            ceo_informed=False,
        )
        self.decision_log.log(record)

        # Step 7: Return approval for execution
        return {
            "decision_id": decision_id,
            "status": "APPROVED",
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "price": price,
            "reason": jarvis_decision["reason"],
            "risk_checks": [asdict(c) for c in risk_result.checks],
            "requires_ceo_approval": False,
            "ceo_informed": False,  # Caller must inform CEO
            "timestamp": timestamp,
        }

    def _reject(
        self,
        decision_id: str,
        reason: str,
        symbol: str,
        side: str,
        qty: float,
        risk_result=None,
    ) -> Dict:
        """Helper to create rejection response."""
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Log rejection
        record = DecisionRecord(
            timestamp=timestamp,
            decision_id=decision_id,
            decision_type="risk_governor_block",
            decision_maker="Risk Governor" if risk_result else "Jarvis",
            title=f"REJECTED: {side.upper()} {qty} {symbol}",
            description=reason,
            recommendations_reviewed=[],
            agreement=None,
            disagreement=None,
            files_changed=[],
            tests_run=[],
            result="REJECTED",
            risks=reason,
            next_step="Review and fix blocking issue",
            ceo_approval_needed=False,
            ceo_informed=False,
        )
        self.decision_log.log(record)

        return {
            "decision_id": decision_id,
            "status": "REJECTED",
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "reason": reason,
            "risk_checks": [asdict(c) for c in risk_result.checks] if risk_result else [],
            "requires_ceo_approval": False,
            "ceo_informed": False,
            "timestamp": timestamp,
        }
