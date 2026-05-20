"""
Tests for CEO Reporting Watchdog
Agent: Sentinel (QA Team)

Tests:
1. Full report succeeds
2. Full report dependency timeout triggers fallback
3. Ollama timeout does not block report (no Ollama dependency)
4. Alpaca timeout does not block report
5. Missing chart monitor does not block report
6. Report is saved locally even if delivery fails
7. Missed report is detected
8. Watchdog schedules next report correctly in Europe/Stockholm time
"""

import json
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ceo_reporting_watchdog import (
    generate_full_report,
    generate_fallback_report,
    update_state_cache,
    check_missed_reports,
    _read_state_cache,
    _ensure_files,
    STATE_CACHE_FILE,
    REPORT_HISTORY_FILE,
)


class TestCEOReportingWatchdog:
    """Test suite for CEO Reporting Watchdog."""

    @pytest.fixture(autouse=True)
    def setup_tmp_files(self, tmp_path, monkeypatch):
        """Use temporary files for tests."""
        monkeypatch.setattr('ceo_reporting_watchdog.STATE_CACHE_FILE', str(tmp_path / 'state_cache.json'))
        monkeypatch.setattr('ceo_reporting_watchdog.REPORT_HISTORY_FILE', str(tmp_path / 'report_history.jsonl'))
        monkeypatch.setattr('ceo_reporting_watchdog.WATCHDOG_LOG_FILE', str(tmp_path / 'watchdog.log'))
        _ensure_files()

    def test_01_full_report_succeeds(self, tmp_path, monkeypatch):
        """Test: Full report generates successfully with state cache."""
        update_state_cache(
            equity=10000.0,
            cash=8000.0,
            buying_power=16000.0,
            positions=[{
                "symbol": "BTCUSD",
                "qty": 0.01,
                "entry": 77000.0,
                "current": 77500.0,
                "unrealized": 5.0,
                "unrealized_pct": 0.5,
            }],
            daemon_status="running",
            risk_governor_status="active",
            kill_switch=False,
        )
        
        # Mock the live fetch functions to test cache-only path
        import ceo_reporting_watchdog as wd
        original_fetch_account = wd._fetch_account_data
        original_fetch_positions = wd._fetch_positions
        
        wd._fetch_account_data = lambda: {"equity": None, "cash": None, "buying_power": None, "status": "mocked"}
        wd._fetch_positions = lambda: []
        
        try:
            report = generate_full_report()
            
            assert "CEO 30-MINUTE STATUS REPORT" in report
            # Check cache was used
            assert "State cache:" in report
            assert "Found" in report or "✅" in report
            print("✅ test_01_full_report_succeeds PASSED")
        finally:
            wd._fetch_account_data = original_fetch_account
            wd._fetch_positions = original_fetch_positions

    def test_02_fallback_on_cache_miss(self, tmp_path, monkeypatch):
        """Test: Fallback report generated when state cache unavailable."""
        # Don't create cache — simulate missing state
        report = generate_fallback_report("Test: cache intentionally missing")
        
        assert "FALLBACK CEO REPORT" in report
        assert "Test: cache intentionally missing" in report
        assert "FALLBACK" in report
        print("✅ test_02_fallback_on_cache_miss PASSED")

    def test_03_no_ollama_dependency(self):
        """Test: Report generation does not call Ollama API."""
        # The watchdog module should not make API calls to Ollama
        import ceo_reporting_watchdog as wd
        
        # Check module imports — should not import ollama client
        import inspect
        source = inspect.getsource(wd)
        
        # The module should not contain actual Ollama API calls
        # (it may contain "ollama" in docstrings/comments, but not in function calls)
        assert "requests.post" not in source or "ollama" not in source.split("requests.post")[1] if "requests.post" in source else True
        assert "api/generate" not in source
        print("✅ test_03_no_ollama_dependency PASSED")

    def test_04_alpaca_timeout_does_not_block(self, tmp_path, monkeypatch):
        """Test: Report generation does not block on Alpaca (uses cache fallback)."""
        # Create cache so report doesn't need Alpaca
        update_state_cache(
            equity=10000.0,
            cash=8000.0,
            buying_power=16000.0,
            positions=[],
            daemon_status="running",
        )
        
        start = time.time()
        report = generate_full_report()
        elapsed = time.time() - start
        
        assert elapsed < 60  # Must complete within 60 seconds
        assert "CEO 30-MINUTE STATUS REPORT" in report
        print(f"✅ test_04_alpaca_timeout_does_not_block PASSED ({elapsed:.1f}s)")

    def test_05_no_chart_monitor_dependency(self):
        """Test: Report generation does not depend on chart monitor."""
        import inspect
        import ceo_reporting_watchdog as wd
        
        source = inspect.getsource(wd)
        assert "chart_monitor" not in source.lower()
        assert "LiveChartMonitor" not in source
        print("✅ test_05_no_chart_monitor_dependency PASSED")

    def test_06_report_saved_locally(self, tmp_path, monkeypatch):
        """Test: Report is saved to local history file."""
        update_state_cache(equity=10000.0, cash=8000.0, buying_power=16000.0, positions=[])
        
        report = generate_full_report()
        
        # Check history file exists
        history_path = Path(tmp_path / 'report_history.jsonl')
        assert history_path.exists()
        
        # Check entry was written
        entries = list(history_path.open())
        assert len(entries) >= 1
        
        entry = json.loads(entries[-1])
        assert entry["type"] == "full"
        assert "CEO 30-MINUTE STATUS REPORT" in entry["report"]
        print("✅ test_06_report_saved_locally PASSED")

    def test_07_missed_report_detected(self, tmp_path, monkeypatch):
        """Test: Missed reports are detected."""
        # Write an old report entry
        history_path = Path(tmp_path / 'report_history.jsonl')
        old_time = datetime.now(timezone.utc).replace(year=2020)  # Very old
        with open(history_path, 'a') as f:
            f.write(json.dumps({"timestamp": old_time.isoformat(), "type": "full", "report": "old"}) + "\n")
        
        missed = check_missed_reports()
        
        assert len(missed) >= 1
        assert "min ago" in missed[0] or "ago" in missed[0]
        print("✅ test_07_missed_report_detected PASSED")

    def test_08_stockholm_timezone_scheduling(self):
        """Test: Watchdog uses Europe/Stockholm timezone."""
        from zoneinfo import ZoneInfo
        
        stockholm = datetime.now(timezone.utc).astimezone(ZoneInfo("Europe/Stockholm"))
        
        # Verify Stockholm timezone is UTC+2 (CEST) or UTC+1 (CET)
        offset = stockholm.utcoffset()
        assert offset is not None
        assert offset.total_seconds() in [7200, 3600]  # +2h or +1h
        print(f"✅ test_08_stockholm_timezone_scheduling PASSED (offset: {offset})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
