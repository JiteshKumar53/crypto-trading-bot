"""
Strategy Validation Gate — LIVE pipeline enforcement.

Every trade must pass through this gate BEFORE execution.
Prevents unvalidated, rejected, or missing strategies from trading.

Gene: GENE-001 (Leaderboard Membership Check)
Gene: GENE-002 (Leaderboard Status Gate)
Gene: GENE-009 (Pre-Cycle Self-Check)

Capsule: CAPSULE-001 (Strategy Validation Gate)
"""

import json
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict

logger = logging.getLogger(__name__)

LEADERBOARD_FILE = Path("logs/strategy_leaderboard.json")


@dataclass
class ValidationResult:
    """Result of strategy validation check."""
    approved: bool
    reason: str
    max_position_size: Optional[float] = None  # None = full size with Risk Gov
    max_open_positions: Optional[int] = None     # None = default
    strategy_status: Optional[str] = None
    backtest_return: Optional[float] = None
    backtest_sharpe: Optional[float] = None


def load_strategy_leaderboard() -> Optional[Dict]:
    """Load strategy leaderboard from disk."""
    try:
        if not LEADERBOARD_FILE.exists():
            logger.error("[STRATEGY GATE] Strategy leaderboard file not found!")
            return None
        with open(LEADERBOARD_FILE) as f:
            data = json.load(f)
        return data.get("strategies", {})
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"[STRATEGY GATE] Failed to load leaderboard: {e}")
        return None


def validate_strategy(strategy_name: str, asset: str) -> ValidationResult:
    """
    Validate a strategy before trade approval.
    
    Returns ValidationResult with approval status and constraints.
    """
    # Check 1: Load leaderboard
    leaderboard = load_strategy_leaderboard()
    if leaderboard is None:
        logger.critical("[STRATEGY GATE] LEADERBOARD UNAVAILABLE — TRADING HALTED")
        return ValidationResult(
            approved=False,
            reason="Strategy leaderboard unavailable — trading halted",
            strategy_status="unknown"
        )
    
    # Check 2: Strategy exists in leaderboard
    # Handle both "BTC/USD" and "BTCUSD" asset formats
    asset_normalized = asset.replace("/", "")
    
    # Handle both base name and optimized variants
    # Strategy name might already contain "_optimized" or not
    key_forms = [
        f"{strategy_name}::{asset}::1h",
        f"{strategy_name}::{asset_normalized}::1h",
    ]
    
    # If strategy_name doesn't already have _optimized, try that form too
    if not strategy_name.endswith("_optimized"):
        key_forms.append(f"{strategy_name}_optimized::{asset}::1h")
        key_forms.append(f"{strategy_name}_optimized::{asset_normalized}::1h")
    
    # Also try without _optimized if it has it
    if strategy_name.endswith("_optimized"):
        base_name = strategy_name[:-10]  # Remove "_optimized"
        key_forms.append(f"{base_name}::{asset}::1h")
        key_forms.append(f"{base_name}::{asset_normalized}::1h")
        key_forms.append(f"{base_name}_optimized::{asset}::1h")
        key_forms.append(f"{base_name}_optimized::{asset_normalized}::1h")
    
    strategy_data = None
    matching_key = None
    
    for key in key_forms:
        if key in leaderboard:
            strategy_data = leaderboard[key]
            matching_key = key
            break
    
    # Also try partial matching for fallback
    if strategy_data is None:
        for key, data in leaderboard.items():
            if strategy_name in key and (asset in key or asset_normalized in key):
                strategy_data = data
                matching_key = key
                break
    
    if strategy_data is None:
        logger.critical(
            f"[STRATEGY GATE] BLOCKED: {strategy_name} on {asset} "
            f"NOT IN LEADERBOARD. Keys tried: {', '.join(key_forms)}"
        )
        return ValidationResult(
            approved=False,
            reason=f"Strategy '{strategy_name}' not in leaderboard for {asset}",
            strategy_status="missing"
        )
    
    # Check 3: Status validation
    status = strategy_data.get("status", "unknown")
    backtest_return = strategy_data.get("backtest_return")
    backtest_sharpe = strategy_data.get("backtest_sharpe")
    
    if status == "rejected":
        rejection_reason = strategy_data.get("rejection_reason", "Unknown")
        logger.critical(
            f"[STRATEGY GATE] BLOCKED: {strategy_name} on {asset} "
            f"is REJECTED: {rejection_reason}"
        )
        return ValidationResult(
            approved=False,
            reason=f"Strategy '{strategy_name}' is rejected: {rejection_reason}",
            strategy_status="rejected",
            backtest_return=backtest_return,
            backtest_sharpe=backtest_sharpe
        )
    
    if status == "testing":
        logger.info(
            f"[STRATEGY GATE] LIMITED: {strategy_name} on {asset} "
            f"is TESTING — experimental size only ($100 max, 1 position)"
        )
        return ValidationResult(
            approved=True,
            reason="Strategy in testing — experimental size only",
            max_position_size=100.0,
            max_open_positions=1,
            strategy_status="testing",
            backtest_return=backtest_return,
            backtest_sharpe=backtest_sharpe
        )
    
    if status == "active":
        max_size = strategy_data.get("active_limit_usd", 500.0)
        logger.info(
            f"[STRATEGY GATE] APPROVED: {strategy_name} on {asset} "
            f"is ACTIVE — full size with Risk Governor approval, limit ${max_size}"
        )
        return ValidationResult(
            approved=True,
            reason="Strategy is ACTIVE — full size with Risk Governor approval",
            max_position_size=max_size,
            max_open_positions=5,
            strategy_status="active",
            backtest_return=backtest_return,
            backtest_sharpe=backtest_sharpe
        )
        return ValidationResult(
            approved=True,
            reason="Strategy active — full size allowed with Risk Governor approval",
            strategy_status="active",
            backtest_return=backtest_return,
            backtest_sharpe=backtest_sharpe
        )
    
    # Unknown status
    logger.critical(
        f"[STRATEGY GATE] BLOCKED: {strategy_name} on {asset} "
        f"has unknown status: {status}"
    )
    return ValidationResult(
        approved=False,
        reason=f"Strategy '{strategy_name}' has unknown status: {status}",
        strategy_status=status,
        backtest_return=backtest_return,
        backtest_sharpe=backtest_sharpe
    )


def validate_strategy_for_pipeline(strategy_name: str, asset: str) -> Optional[str]:
    """
    Simplified validation for pipeline integration.
    Returns None if approved, returns error string if blocked.
    """
    result = validate_strategy(strategy_name, asset)
    if result.approved:
        return None
    return result.reason


def get_strategy_constraints(strategy_name: str, asset: str) -> Dict:
    """
    Get position constraints for a strategy.
    Returns dict with max_position_size and max_open_positions.
    """
    result = validate_strategy(strategy_name, asset)
    return {
        "max_position_size": result.max_position_size,
        "max_open_positions": result.max_open_positions,
        "approved": result.approved,
        "reason": result.reason,
        "status": result.strategy_status,
    }
