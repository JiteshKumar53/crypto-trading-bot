import sys
sys.path.insert(0, 'src')

import json
import os
import tempfile
import pytest
from datetime import datetime

from dashboard.dashboard_generator import (
    generate_dashboard_html,
    write_dashboard,
    load_decisions,
    get_account_state_from_alpaca,
)


class TestDashboardGenerator:

    def test_load_decisions_with_mock_data(self, tmp_path):
        """Test loading decisions from JSONL files."""
        # Create temp decision log
        log_dir = tmp_path / "logs" / "decisions"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "test.jsonl"
        
        decisions = [
            {
                "timestamp": "2026-05-18T10:00:00Z",
                "decision_type": "autonomous_jarvis",
                "decision_maker": "Jarvis",
                "title": "Test Decision 1",
                "result": "APPROVED",
            },
            {
                "timestamp": "2026-05-18T11:00:00Z",
                "decision_type": "ceo_approval_required",
                "decision_maker": "Jitesh Kumar",
                "title": "Test Decision 2",
                "result": "AUTHORIZED",
            },
        ]
        with open(log_file, 'w') as f:
            for d in decisions:
                f.write(json.dumps(d) + '\n')
        
        # Monkeypatch DECISION_LOG_DIR
        import dashboard.dashboard_generator as dg
        old_dir = dg.DECISION_LOG_DIR
        dg.DECISION_LOG_DIR = str(log_dir)
        
        try:
            loaded = load_decisions()
            assert len(loaded) == 2
            assert loaded[0]["title"] == "Test Decision 2"  # Newest first
            assert loaded[1]["title"] == "Test Decision 1"
        finally:
            dg.DECISION_LOG_DIR = old_dir

    def test_generate_dashboard_html_basic(self):
        """Test HTML generation without data."""
        html = generate_dashboard_html()
        assert "Jarvis Trading Dashboard" in html
        assert "PAPER" in html
        assert "Decision Log" in html
        assert "<table>" in html
        assert "</style>" in html

    def test_generate_dashboard_with_account(self):
        """Test HTML with account state."""
        account = {
            "portfolio_value": 10000.00,
            "cash": 10000.00,
            "buying_power": 20000.00,
            "open_positions": 0,
        }
        html = generate_dashboard_html(account_state=account)
        assert "$10,000.00" in html
        assert "Portfolio Value" in html
        assert "Open Positions" in html

    def test_generate_dashboard_with_agents(self):
        """Test HTML with agent status."""
        agents = {
            "Candles": "operational",
            "Ledger": "operational",
            "Pulse": "error",
            "Shield": "operational",
            "Compass": "operational",
        }
        html = generate_dashboard_html(agent_status=agents)
        assert "Agent Status" in html
        assert "Candles" in html
        assert "error" in html

    def test_write_dashboard_creates_file(self, tmp_path):
        """Test writing dashboard to file."""
        import dashboard.dashboard_generator as dg
        old_dir = dg.DASHBOARD_DIR
        dg.DASHBOARD_DIR = str(tmp_path / "dashboard")
        
        try:
            filepath = write_dashboard()
            assert os.path.exists(filepath)
            with open(filepath, 'r') as f:
                content = f.read()
            assert "<!DOCTYPE html>" in content
        finally:
            dg.DASHBOARD_DIR = old_dir

    def test_account_state_from_alpaca_mock(self):
        """Test fetching account state with mock client."""
        class MockClient:
            def get_account(self):
                return {
                    "portfolio_value": "15000.00",
                    "cash": "5000.00",
                    "buying_power": "20000.00",
                }
            def get_positions(self):
                return [
                    {"symbol": "BTCUSD", "qty": "0.1", "market_value": "5000.00"},
                ]
        
        mock_client = MockClient()
        state = get_account_state_from_alpaca(mock_client)
        assert state["portfolio_value"] == "15000.00"
        assert state["cash"] == "5000.00"
        assert state["open_positions"] == 1
        assert len(state["position_details"]) == 1

    def test_account_state_error_handling(self):
        """Test error handling when Alpaca client fails."""
        class FailingClient:
            def get_account(self):
                raise Exception("API Error")
            def get_positions(self):
                return []
        
        state = get_account_state_from_alpaca(FailingClient())
        assert state["portfolio_value"] == 0
        assert state["error"] == "API Error"

    def test_load_decisions_empty_directory(self, tmp_path):
        """Test loading decisions from empty directory."""
        import dashboard.dashboard_generator as dg
        old_dir = dg.DECISION_LOG_DIR
        dg.DECISION_LOG_DIR = str(tmp_path / "empty_logs")
        os.makedirs(dg.DECISION_LOG_DIR, exist_ok=True)
        
        try:
            loaded = load_decisions()
            assert loaded == []
        finally:
            dg.DECISION_LOG_DIR = old_dir

    def test_load_decisions_invalid_json(self, tmp_path):
        """Test loading decisions with invalid JSON lines."""
        log_dir = tmp_path / "logs" / "decisions"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "mixed.jsonl"
        
        with open(log_file, 'w') as f:
            f.write('{"valid": true}\n')
            f.write('invalid json here\n')
            f.write('{"another": "valid"}\n')
        
        import dashboard.dashboard_generator as dg
        old_dir = dg.DECISION_LOG_DIR
        dg.DECISION_LOG_DIR = str(log_dir)
        
        try:
            loaded = load_decisions()
            assert len(loaded) == 2
        finally:
            dg.DECISION_LOG_DIR = old_dir
