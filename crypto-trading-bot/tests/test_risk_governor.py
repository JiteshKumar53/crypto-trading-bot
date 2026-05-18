"""
Tests for Deterministic Risk Governor
Agent: Sentinel
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from risk_governor import RiskGovernor, RiskDecision


@pytest.fixture
def governor():
    config_path = Path(__file__).parent.parent / "config" / "risk_limits.yaml"
    g = RiskGovernor(str(config_path))
    g.reset_state()
    return g


def test_paper_mode_enforced(governor):
    # Modify config to simulate non-paper mode
    governor.config["mode"] = "live"
    result = governor.check_order(
        symbol="BTC/USD", side="buy", qty=0.1, price=50000,
        portfolio_value=100000, current_position_value=0
    )
    assert result.decision == RiskDecision.BLOCK
    assert result.requires_ceo_approval is True


def test_asset_validation(governor):
    result = governor.check_order(
        symbol="XYZ/USD", side="buy", qty=1, price=100,
        portfolio_value=100000, current_position_value=0
    )
    assert result.decision == RiskDecision.BLOCK
    assert any("not in allowed list" in c.reason for c in result.checks)


def test_min_order_size(governor):
    result = governor.check_order(
        symbol="BTC/USD", side="buy", qty=0.00001, price=50000,  # $0.50 order
        portfolio_value=100000, current_position_value=0
    )
    assert result.decision == RiskDecision.BLOCK
    assert any("below minimum" in c.reason for c in result.checks)


def test_max_position_size_usd(governor):
    result = governor.check_order(
        symbol="BTC/USD", side="buy", qty=1, price=50000,  # $50,000
        portfolio_value=100000, current_position_value=0
    )
    assert result.decision == RiskDecision.BLOCK
    assert any("exceeds max" in c.reason for c in result.checks)


def test_max_allocation_per_asset(governor):
    result = governor.check_order(
        symbol="BTC/USD", side="buy", qty=0.15, price=50000,  # $7,500 = 7.5%
        portfolio_value=100000, current_position_value=0
    )
    # This should pass (7.5% < 10%)
    assert result.decision == RiskDecision.ALLOW


def test_valid_order(governor):
    result = governor.check_order(
        symbol="BTC/USD", side="buy", qty=0.1, price=50000,  # $5,000 = 5%
        portfolio_value=100000, current_position_value=0
    )
    assert result.decision == RiskDecision.ALLOW
    assert all(c.passed for c in result.checks)


def test_consecutive_losses_kill_switch(governor):
    governor.state["consecutive_losses"] = 3
    result = governor.check_order(
        symbol="BTC/USD", side="buy", qty=0.1, price=50000,
        portfolio_value=100000, current_position_value=0
    )
    assert result.decision == RiskDecision.KILL_SWITCH
    assert governor.state["kill_switch_active"] is True


def test_drawdown_kill_switch(governor):
    governor.state["peak_portfolio_value"] = 100000
    # Simulate a 6% drawdown
    result = governor.update_after_trade(
        symbol="BTC/USD", realized_pnl=-6000, portfolio_value=94000
    )
    # After trade update should trigger kill switch
    assert governor.state["kill_switch_active"] is True


def test_kill_switch_cooldown(governor):
    governor.state["kill_switch_active"] = True
    result = governor.check_order(
        symbol="BTC/USD", side="buy", qty=0.1, price=50000,
        portfolio_value=100000, current_position_value=0
    )
    assert result.decision == RiskDecision.COOLDOWN


def test_total_exposure_limit(governor):
    governor.state["total_crypto_exposure_pct"] = 0.25
    result = governor.check_order(
        symbol="BTC/USD", side="buy", qty=0.1, price=50000,  # Would add 5%
        portfolio_value=100000, current_position_value=0
    )
    # 25% + 5% = 30%, which equals max. Should pass.
    # But let's test exceeding
    governor.state["total_crypto_exposure_pct"] = 0.28
    result = governor.check_order(
        symbol="BTC/USD", side="buy", qty=0.1, price=50000,
        portfolio_value=100000, current_position_value=0
    )
    # 28% + 5% = 33% > 30%
    assert result.decision == RiskDecision.BLOCK
