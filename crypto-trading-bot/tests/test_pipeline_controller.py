"""
Tests for Pipeline Controller
Agent: QA + Testing Team

Note: Requires ALPACA_API_KEY and ALPACA_SECRET_KEY env vars to be set.
Tests mock the actual API calls.
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pipeline_controller import PipelineController


@pytest.fixture
def controller():
    """Create a PipelineController with mocked Alpaca client."""
    with patch('pipeline_controller.AlpacaPaperClient') as MockAlpaca:
        mock_client = MagicMock()
        mock_client.is_paper.return_value = True
        mock_client.get_account.return_value = {
            'portfolio_value': 10000.0,
            'cash': 10000.0,
        }
        mock_client.get_positions.return_value = []
        mock_client.get_open_orders.return_value = []
        MockAlpaca.return_value = mock_client

        ctrl = PipelineController(
            use_agents=False,
            use_backtest=True,
            use_risk_governor=True,
            paper_only=True,
        )
        return ctrl


def test_pipeline_controller_initialization(controller):
    """Test PipelineController initializes correctly."""
    assert controller.use_agents is False
    assert controller.use_backtest is True
    assert controller.use_risk_governor is True
    assert controller.paper_only is True
    assert len(controller.assets) == 3  # BTC, ETH, SOL


def test_run_cycle_with_mock_data(controller):
    """Test full pipeline cycle with mocked data and execution."""
    # Mock data fetcher
    mock_data = MagicMock()
    mock_data.empty = False
    mock_data.__len__ = lambda self: 100

    with patch.object(controller.data_fetcher, 'fetch_hourly_bars', return_value=mock_data):
        with patch.object(controller.data_fetcher, 'get_latest_price', return_value=50000.0):
            with patch.object(controller.alpaca, 'is_paper', return_value=True):
                with patch.object(controller.orchestrator, 'run_pipeline', return_value={
                    "status": "APPROVED",
                    "decision_id": "dec-test-123",
                    "reason": "Test approval",
                    "requires_ceo_approval": False,
                    "ceo_informed": False,
                }):
                    with patch.object(controller.alpaca, 'submit_order') as mock_submit:
                        mock_order_result = MagicMock()
                        mock_order_result.success = True
                        mock_order_result.order_id = "test-order-123"
                        mock_order_result.error = None
                        mock_submit.return_value = mock_order_result

                        result = controller.run_cycle("BTC/USD")

    assert "BTC/USD" in result["stages"]
    btc_result = result["stages"]["BTC/USD"]

    # Verify all stages ran
    assert btc_result["stages"]["data"]["status"] == "success"
    assert btc_result["stages"]["agents"]["status"] == "skipped"
    assert btc_result["stages"]["backtest"]["status"] == "success"
    assert btc_result["stages"]["risk_governor"]["approved"] is True
    assert btc_result["stages"]["orchestrator"]["status"] == "APPROVED"
    assert btc_result["stages"]["execution"]["status"] == "success"
    assert btc_result["approved"] is True


def test_pipeline_rejected_by_risk_governor(controller):
    """Test pipeline when Risk Governor blocks the order."""
    mock_data = MagicMock()
    mock_data.empty = False
    mock_data.__len__ = lambda self: 100

    with patch.object(controller.data_fetcher, 'fetch_hourly_bars', return_value=mock_data):
        with patch.object(controller.data_fetcher, 'get_latest_price', return_value=50000.0):
            with patch.object(controller.alpaca, 'is_paper', return_value=True):
                # Override risk governor to block
                with patch.object(controller.risk_governor, 'check_order') as mock_risk:
                    from risk_governor import RiskDecision
                    mock_risk_result = MagicMock()
                    mock_risk_result.decision = RiskDecision.BLOCK
                    mock_risk_result.checks = []
                    mock_risk_result.requires_ceo_approval = False
                    mock_risk.return_value = mock_risk_result

                    result = controller.run_cycle("BTC/USD")

    btc_result = result["stages"]["BTC/USD"]
    assert btc_result["stages"]["risk_governor"]["approved"] is False
    assert btc_result["approved"] is False


def test_pipeline_status(controller):
    """Test system status retrieval."""
    with patch.object(controller.alpaca, 'is_paper', return_value=True):
        status = controller.get_status()

    assert status["paper_mode"] is True
    assert status["account"]["portfolio_value"] == 10000.0
    assert len(status["positions"]) == 0
    assert len(status["open_orders"]) == 0
    assert "BTC/USD" in status["assets"]
