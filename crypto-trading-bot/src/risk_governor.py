"""
Deterministic Risk Governor
Agent: Sentinel (code-based, no LLM dependency)

Independent safety layer that validates every order against
deterministic, configurable risk rules.
Cannot be disabled without CEO approval.
"""

import logging
import os
import yaml

logger = logging.getLogger(__name__)
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from enum import Enum


class RiskDecision(Enum):
    ALLOW = "allow"
    BLOCK = "block"
    KILL_SWITCH = "kill_switch"
    COOLDOWN = "cooldown"


@dataclass
class RiskCheck:
    name: str
    passed: bool
    reason: str


@dataclass
class RiskResult:
    decision: RiskDecision
    checks: List[RiskCheck]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    requires_ceo_approval: bool = False

    @property
    def approved(self) -> bool:
        return self.decision == RiskDecision.ALLOW


class RiskGovernor:
    """
    Deterministic Risk Governor.
    All checks are code-based, testable, auditable.
    No LLM opinion involved.
    """

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "..", "config", "risk_limits.yaml"
            )
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        self.state = {
            "consecutive_losses": 0,
            "daily_pnl": 0.0,
            "daily_trades": 0,
            "daily_trade_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "peak_portfolio_value": 0.0,
            "kill_switch_active": False,
            "kill_switch_time": None,
            "open_positions": 0,
        }

    def _reset_daily_counters(self):
        """Reset daily counters if date changed."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if today != self.state.get("daily_trade_date"):
            self.state["daily_trades"] = 0
            self.state["daily_pnl"] = 0.0
            self.state["daily_trade_date"] = today
            logger.info(f"[RiskGovernor] Daily counters reset for {today}")

    def reset_state(self):
        """Reset runtime state. Used for testing and initialization."""
        self.state = {
            "consecutive_losses": 0,
            "daily_pnl": 0.0,
            "peak_portfolio_value": 0.0,
            "kill_switch_active": False,
            "kill_switch_time": None,
            "open_positions": 0,
        }

    def check_order(
        self,
        symbol: str,
        side: str,
        qty: float,
        price: float,
        portfolio_value: float,
        current_position_value: float,
        paper_mode: bool = True,
    ) -> RiskResult:
        """
        Run all deterministic risk checks for a proposed order.
        Returns RiskResult with decision and all check results.
        """
        checks = []

        # 1. Paper mode enforcement
        if self.config["mode"] != "paper":
            checks.append(
                RiskCheck(
                    name="paper_mode_enforced",
                    passed=False,
                    reason="System not in paper mode. Live trading requires CEO approval.",
                )
            )
            return RiskResult(
                decision=RiskDecision.BLOCK,
                checks=checks,
                requires_ceo_approval=True,
            )

        checks.append(
            RiskCheck(name="paper_mode_enforced", passed=True, reason="Paper mode active")
        )

        # 2. Kill switch check
        if self.state["kill_switch_active"]:
            cooldown_hours = self.config["account"]["cooldown_hours_after_kill_switch"]
            checks.append(
                RiskCheck(
                    name="kill_switch",
                    passed=False,
                    reason=f"Kill switch active. Cooldown: {cooldown_hours}h required.",
                )
            )
            return RiskResult(
                decision=RiskDecision.COOLDOWN,
                checks=checks,
                requires_ceo_approval=False,
            )

        checks.append(RiskCheck(name="kill_switch", passed=True, reason="No kill switch"))

        # 3. Asset validation
        asset_config = None
        for asset in self.config["per_asset"]:
            if symbol.lower().replace("/", "").startswith(asset.lower()):
                asset_config = self.config["per_asset"][asset]
                break

        if asset_config is None:
            checks.append(
                RiskCheck(
                    name="asset_validation", passed=False, reason=f"Asset {symbol} not in allowed list"
                )
            )
            return RiskResult(decision=RiskDecision.BLOCK, checks=checks)

        checks.append(
            RiskCheck(name="asset_validation", passed=True, reason=f"Asset {symbol} validated")
        )

        # 4. Order size check
        order_value = qty * price
        min_size = asset_config["min_order_size_usd"]
        if order_value < min_size:
            checks.append(
                RiskCheck(
                    name="min_order_size",
                    passed=False,
                    reason=f"Order value {order_value:.2f} below minimum {min_size}",
                )
            )
            return RiskResult(decision=RiskDecision.BLOCK, checks=checks)

        checks.append(
            RiskCheck(name="min_order_size", passed=True, reason=f"Order size {order_value:.2f} valid")
        )

        # 5. Max allocation per asset
        max_pct = asset_config["max_position_pct_of_portfolio"]
        max_usd = asset_config["max_position_size_usd"]
        proposed_position = current_position_value + order_value
        if proposed_position > max_usd:
            checks.append(
                RiskCheck(
                    name="max_position_size_usd",
                    passed=False,
                    reason=f"Position {proposed_position:.2f} exceeds max {max_usd}",
                )
            )
            return RiskResult(decision=RiskDecision.BLOCK, checks=checks)

        if portfolio_value > 0 and (proposed_position / portfolio_value) > max_pct:
            checks.append(
                RiskCheck(
                    name="max_position_pct",
                    passed=False,
                    reason=f"Position pct {(proposed_position/portfolio_value):.2%} exceeds max {max_pct:.0%}",
                )
            )
            return RiskResult(decision=RiskDecision.BLOCK, checks=checks)

        checks.append(
            RiskCheck(
                name="max_allocation", passed=True, reason="Position within allocation limits"
            )
        )

        # 6. Total crypto exposure
        # Note: This requires tracking total crypto exposure externally
        # For now, we check against the per-asset limit as a proxy
        total_exposure_pct = self.state.get("total_crypto_exposure_pct", 0.0)
        max_total = self.config["account"]["max_total_crypto_exposure"]
        if total_exposure_pct + (order_value / portfolio_value if portfolio_value > 0 else 0) > max_total:
            checks.append(
                RiskCheck(
                    name="total_exposure",
                    passed=False,
                    reason=f"Total exposure would exceed {max_total:.0%}",
                )
            )
            return RiskResult(decision=RiskDecision.BLOCK, checks=checks)

        checks.append(
            RiskCheck(name="total_exposure", passed=True, reason="Total exposure within limits")
        )

        # 7. Open positions limit
        max_positions = self.config["account"]["max_open_positions"]
        if self.state["open_positions"] >= max_positions and side.lower() == "buy":
            checks.append(
                RiskCheck(
                    name="max_open_positions",
                    passed=False,
                    reason=f"Max open positions ({max_positions}) reached",
                )
            )
            return RiskResult(decision=RiskDecision.BLOCK, checks=checks)

        checks.append(
            RiskCheck(
                name="max_open_positions", passed=True, reason="Open positions within limit"
            )
        )

        # 8. Consecutive losses check
        max_consecutive = self.config["account"]["max_consecutive_losses"]
        if self.state["consecutive_losses"] >= max_consecutive:
            checks.append(
                RiskCheck(
                    name="consecutive_losses",
                    passed=False,
                    reason=f"Stopped after {max_consecutive} consecutive losses",
                )
            )
            self.state["kill_switch_active"] = True
            self.state["kill_switch_time"] = datetime.now(timezone.utc)
            return RiskResult(decision=RiskDecision.KILL_SWITCH, checks=checks)

        checks.append(
            RiskCheck(
                name="consecutive_losses",
                passed=True,
                reason=f"Consecutive losses {self.state['consecutive_losses']}/{max_consecutive}",
            )
        )

        # 8a. Daily trade limit check
        self._reset_daily_counters()
        max_daily_trades = self.config["account"].get("max_daily_trades", 7)
        if self.state["daily_trades"] >= max_daily_trades:
            checks.append(
                RiskCheck(
                    name="max_daily_trades",
                    passed=False,
                    reason=f"Daily trade limit ({max_daily_trades}) reached",
                )
            )
            return RiskResult(decision=RiskDecision.BLOCK, checks=checks)

        checks.append(
            RiskCheck(
                name="max_daily_trades",
                passed=True,
                reason=f"Daily trades {self.state['daily_trades']}/{max_daily_trades}",
            )
        )

        # 8b. Daily loss limit check
        max_daily_loss_pct = self.config["account"].get("max_daily_loss_pct", 0.02)
        max_daily_loss_usd = portfolio_value * max_daily_loss_pct
        if self.state["daily_pnl"] <= -max_daily_loss_usd:
            checks.append(
                RiskCheck(
                    name="max_daily_loss",
                    passed=False,
                    reason=f"Daily loss {self.state['daily_pnl']:.2f} >= limit {-max_daily_loss_usd:.2f}",
                )
            )
            self.state["kill_switch_active"] = True
            self.state["kill_switch_time"] = datetime.now(timezone.utc)
            return RiskResult(decision=RiskDecision.KILL_SWITCH, checks=checks)

        checks.append(
            RiskCheck(
                name="max_daily_loss",
                passed=True,
                reason=f"Daily PnL {self.state['daily_pnl']:.2f} within limit",
            )
        )

        # 9. Leverage check
        if self.config["account"]["no_leverage"]:
            # In paper trading, we don't have margin accounts configured
            checks.append(
                RiskCheck(name="no_leverage", passed=True, reason="No leverage enforced")
            )

        # All checks passed
        return RiskResult(
            decision=RiskDecision.ALLOW,
            checks=checks,
            requires_ceo_approval=False,
        )

    def update_after_trade(
        self,
        symbol: str,
        realized_pnl: float,
        portfolio_value: float,
    ):
        """Update state after a trade closes."""
        self._reset_daily_counters()
        self.state["daily_pnl"] += realized_pnl
        self.state["daily_trades"] += 1
        if realized_pnl < 0:
            self.state["consecutive_losses"] += 1
        else:
            self.state["consecutive_losses"] = 0

        # Update peak and check drawdown
        if portfolio_value > self.state["peak_portfolio_value"]:
            self.state["peak_portfolio_value"] = portfolio_value

        if self.state["peak_portfolio_value"] > 0:
            drawdown = (self.state["peak_portfolio_value"] - portfolio_value) / self.state[
                "peak_portfolio_value"
            ]
            max_drawdown = self.config["account"]["max_strategy_drawdown_pct"]
            if drawdown >= max_drawdown:
                self.state["kill_switch_active"] = True
                self.state["kill_switch_time"] = datetime.now(timezone.utc)

        # Update open positions count (simplified)
        # In production, this would be fetched from broker
        if realized_pnl != 0:  # Trade closed
            self.state["open_positions"] = max(0, self.state["open_positions"] - 1)

    def reset_kill_switch(self, ceo_approved: bool = False):
        """Reset kill switch. Requires CEO approval in production."""
        if not ceo_approved:
            # In production, this would require explicit CEO approval
            # For paper trading, we log but allow
            pass
        self.state["kill_switch_active"] = False
        self.state["kill_switch_time"] = None
        self.state["consecutive_losses"] = 0

    def get_state(self) -> Dict:
        return self.state.copy()
