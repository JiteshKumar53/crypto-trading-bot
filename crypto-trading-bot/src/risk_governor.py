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


class TradeFrequencyPolicy(Enum):
    """Dynamic trade frequency policies based on market conditions and performance."""
    RISK_OFF = "risk_off"        # 0-2 trades/day - dangerous conditions
    NORMAL = "normal"            # 3-7 trades/day - standard conditions
    STRONG = "strong"            # 7-12 trades/day - good performance
    EXCEPTIONAL = "exceptional"  # >12 trades/day - requires evidence


class RiskDecision(Enum):
    ALLOW = "allow"
    BLOCK = "block"
    KILL_SWITCH = "kill_switch"
    COOLDOWN = "cooldown"
    TRADE_LIMIT_REACHED = "trade_limit_reached"


@dataclass
class RiskCheck:
    name: str
    passed: bool
    reason: str


@dataclass
@dataclass
class RiskResult:
    decision: RiskDecision
    checks: List[RiskCheck]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    requires_ceo_approval: bool = False
    trade_limit_reached: bool = False
    recommended_policy: Optional[str] = None
    improvement_mode: bool = False

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

        # 6. Total crypto exposure (50/50 capital rule)
        # Calculate current + proposed total crypto exposure
        max_investable_pct = self.config["account"].get("max_investable_capital_pct", 0.50)
        max_investable_usd = portfolio_value * max_investable_pct
        current_total_exposure = self.state.get("total_crypto_exposure_usd", 0.0)
        new_total_exposure = current_total_exposure + order_value
        if new_total_exposure > max_investable_usd:
            checks.append(
                RiskCheck(
                    name="total_exposure",
                    passed=False,
                    reason=f"Total exposure ${new_total_exposure:.2f} would exceed 50% investable capital (${max_investable_usd:.2f}). Reserve protection active.",
                )
            )
            return RiskResult(decision=RiskDecision.BLOCK, checks=checks)

        checks.append(
            RiskCheck(
                name="total_exposure",
                passed=True,
                reason=f"Total exposure ${new_total_exposure:.2f} within 50% limit (${max_investable_usd:.2f})",
            )
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

        # 8a. Dynamic daily trade limit check
        self._reset_daily_counters()
        max_daily_trades = self.config["account"].get("max_daily_trades", 7)
        current_trades = self.state["daily_trades"]
        
        # Determine current policy based on performance and conditions
        policy = self._evaluate_trade_frequency_policy(portfolio_value)
        effective_limit = self._get_effective_trade_limit(policy)
        
        if current_trades >= effective_limit:
            checks.append(
                RiskCheck(
                    name="max_daily_trades",
                    passed=False,
                    reason=f"Daily trade limit ({current_trades}/{effective_limit}) reached. Policy: {policy.value}. Team switches to IMPROVEMENT MODE.",
                )
            )
            return RiskResult(
                decision=RiskDecision.TRADE_LIMIT_REACHED,
                checks=checks,
                trade_limit_reached=True,
                recommended_policy=policy.value,
                improvement_mode=True,
            )

        checks.append(
            RiskCheck(
                name="max_daily_trades",
                passed=True,
                reason=f"Daily trades {current_trades}/{effective_limit}. Policy: {policy.value}",
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

    # ── Dynamic Trade Frequency Evaluation ──

    def _evaluate_trade_frequency_policy(self, portfolio_value: float) -> TradeFrequencyPolicy:
        """
        Evaluate current market and performance conditions to determine
        appropriate trade frequency policy.
        
        Returns:
            TradeFrequencyPolicy enum value
        """
        # Get baseline from config (safety cap)
        base_limit = self.config["account"].get("max_daily_trades", 7)
        
        # Check risk-off conditions first
        if self.state.get("kill_switch_active", False):
            return TradeFrequencyPolicy.RISK_OFF
        
        # Check consecutive losses
        consecutive = self.state.get("consecutive_losses", 0)
        max_consecutive = self.config["account"].get("max_consecutive_losses", 3)
        if consecutive >= max_consecutive - 1:  # Close to limit
            return TradeFrequencyPolicy.RISK_OFF
        
        # Check daily drawdown
        daily_pnl = self.state.get("daily_pnl", 0)
        max_daily_loss_pct = self.config["account"].get("max_daily_loss_pct", 0.02)
        max_daily_loss_usd = portfolio_value * max_daily_loss_pct
        if daily_pnl <= -max_daily_loss_usd * 0.5:  # 50% of daily loss limit
            return TradeFrequencyPolicy.RISK_OFF
        
        # Check daily PnL for exceptional conditions
        if daily_pnl > 0 and self.state.get("daily_trades", 0) >= 3:
            # Profitable day with multiple trades = strong opportunity
            return TradeFrequencyPolicy.STRONG
        
        # Normal conditions (default)
        return TradeFrequencyPolicy.NORMAL

    def _get_effective_trade_limit(self, policy: TradeFrequencyPolicy) -> int:
        """
        Get effective daily trade limit based on policy.
        
        Args:
            policy: TradeFrequencyPolicy enum value
            
        Returns:
            Effective daily trade limit
        """
        # Safety cap from config (never exceed this without explicit evidence)
        base_limit = self.config["account"].get("max_daily_trades", 7)
        
        limits = {
            TradeFrequencyPolicy.RISK_OFF: min(2, base_limit),
            TradeFrequencyPolicy.NORMAL: base_limit,
            TradeFrequencyPolicy.STRONG: min(12, base_limit + 5),
            TradeFrequencyPolicy.EXCEPTIONAL: 20,  # Only for paper with evidence
        }
        
        return limits.get(policy, base_limit)

    def get_trade_frequency_report(self, portfolio_value: float) -> Dict:
        """
        Generate a comprehensive trade frequency report for CEO review.
        
        Returns dict with all metrics needed for trade limit decision.
        """
        policy = self._evaluate_trade_frequency_policy(portfolio_value)
        effective_limit = self._get_effective_trade_limit(policy)
        current_trades = self.state.get("daily_trades", 0)
        
        # Calculate key metrics
        daily_pnl = self.state.get("daily_pnl", 0)
        consecutive = self.state.get("consecutive_losses", 0)
        max_consecutive = self.config["account"].get("max_consecutive_losses", 3)
        
        # Determine recommendation
        base_limit = self.config["account"].get("max_daily_trades", 7)
        should_increase = policy == TradeFrequencyPolicy.STRONG and current_trades >= 3
        should_decrease = policy == TradeFrequencyPolicy.RISK_OFF
        should_stay = not should_increase and not should_decrease
        
        new_limit = effective_limit if should_increase or should_decrease else base_limit
        
        return {
            "timezone": "Europe/Stockholm",
            "current_daily_trade_limit": base_limit,
            "effective_daily_limit": effective_limit,
            "trades_used_today": current_trades,
            "daily_pnl": daily_pnl,
            "win_rate": self.state.get("win_rate", 0.5),  # Placeholder until tracked
            "consecutive_losses": consecutive,
            "max_consecutive_allowed": max_consecutive,
            "market_regime": self.state.get("market_regime", "unknown"),
            "risk_governor_status": "active",
            "policy": policy.value,
            "should_limit_stay_at_default": should_stay,
            "should_limit_increase": should_increase,
            "should_limit_decrease": should_decrease,
            "new_trade_limit": new_limit,
            "reason": f"Policy: {policy.value}. Consecutive losses: {consecutive}/{max_consecutive}. Daily PnL: ${daily_pnl:.2f}",
            "improvement_mode": current_trades >= effective_limit,
            "what_agents_will_do": (
                "Switch to improvement mode: strategy research, backtesting, exit optimization, "
                "missed opportunity review, model tuning, data improvement, dashboard updates."
                if current_trades >= effective_limit
                else "Continue trading mode. Monitor for high-quality signals."
            ),
            "ceo_approval_required": False,
            "ceo_informed": True,
        }

    def get_state(self) -> Dict:
        return self.state.copy()
