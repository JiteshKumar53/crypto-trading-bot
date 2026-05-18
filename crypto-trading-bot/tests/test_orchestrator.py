"""
Tests for Trading Orchestrator
Agent: Jarvis
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from orchestrator import TradingOrchestrator
from risk_governor import RiskGovernor


@pytest.fixture
def orchestrator():
    rg = RiskGovernor(str(Path(__file__).parent.parent / "config" / "risk_limits.yaml"))
    rg.reset_state()
    return TradingOrchestrator(rg)


def test_reject_insufficient_recommendations(orchestrator):
    result = orchestrator.run_pipeline(
        symbol="BTC/USD", side="buy", qty=0.1, price=50000,
        portfolio_value=100000, current_position_value=0,
        recommendations=[{"agent": "tech"}],  # Only 1, need 5
        strategy_backtest_passed=True, qa_passed=True,
    )
    assert result["status"] == "REJECTED"
    assert "Insufficient agent recommendations" in result["reason"]


def test_reject_backtest_failed(orchestrator):
    result = orchestrator.run_pipeline(
        symbol="BTC/USD", side="buy", qty=0.1, price=50000,
        portfolio_value=100000, current_position_value=0,
        recommendations=[{"agent": "tech"}, {"agent": "fund"}, {"agent": "sent"}, {"agent": "risk"}, {"agent": "thesis"}],
        strategy_backtest_passed=False, qa_passed=True,
    )
    assert result["status"] == "REJECTED"
    assert "backtest" in result["reason"].lower()


def test_reject_qa_failed(orchestrator):
    result = orchestrator.run_pipeline(
        symbol="BTC/USD", side="buy", qty=0.1, price=50000,
        portfolio_value=100000, current_position_value=0,
        recommendations=[{"agent": "tech"}, {"agent": "fund"}, {"agent": "sent"}, {"agent": "risk"}, {"agent": "thesis"}],
        strategy_backtest_passed=True, qa_passed=False,
    )
    assert result["status"] == "REJECTED"
    assert "QA" in result["reason"]


def test_approve_with_full_pipeline(orchestrator):
    result = orchestrator.run_pipeline(
        symbol="BTC/USD", side="buy", qty=0.1, price=50000,
        portfolio_value=100000, current_position_value=0,
        recommendations=[
            {"agent": "Candles", "warnings": "High volatility"},
            {"agent": "Ledger", "warnings": "Unlock event soon"},
            {"agent": "Pulse", "warnings": "Mixed sentiment"},
            {"agent": "Shield", "warnings": "Normal risk"},
            {"agent": "Compass", "warnings": "Wait for confirmation"},
        ],
        strategy_backtest_passed=True, qa_passed=True,
    )
    assert result["status"] == "APPROVED"
    assert result["requires_ceo_approval"] is False
