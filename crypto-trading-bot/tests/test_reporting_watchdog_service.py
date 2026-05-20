"""Tests for ReportingWatchdogService."""
import pytest
import json
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0, 'src')

from reporting_watchdog_service import ReportingWatchdogService


class TestReportingWatchdogService:

    def test_run_once_generates_full_report(self, tmp_path):
        with patch('reporting_watchdog_service.REPORT_HISTORY_FILE', tmp_path / "history.jsonl"), \
             patch('reporting_watchdog_service.HEALTH_FILE', tmp_path / "health.json"):
            service = ReportingWatchdogService()
            result = service.run_once()
            assert result["success"] is True
            assert result["type"] == "full"
            assert len(result.get("errors", [])) == 0

    def test_report_saved_to_history(self, tmp_path):
        history_file = tmp_path / "history.jsonl"
        with patch('reporting_watchdog_service.REPORT_HISTORY_FILE', history_file), \
             patch('reporting_watchdog_service.HEALTH_FILE', tmp_path / "health.json"):
            service = ReportingWatchdogService()
            service.run_once()
            assert history_file.exists()
            lines = history_file.read_text().strip().split("\n")
            entry = json.loads(lines[-1])
            assert entry["type"] == "full"
            assert entry["success"] is True

    def test_fallback_on_failure(self, tmp_path):
        with patch('reporting_watchdog_service.wd.generate_full_report', side_effect=Exception("down")), \
             patch('reporting_watchdog_service.REPORT_HISTORY_FILE', tmp_path / "history.jsonl"), \
             patch('reporting_watchdog_service.HEALTH_FILE', tmp_path / "health.json"):
            service = ReportingWatchdogService()
            result = service.run_once()
            assert result["success"] is True
            assert result["type"] == "fallback"

    def test_critical_alert_on_consecutive_failures(self, tmp_path):
        with patch('reporting_watchdog_service.wd.generate_full_report', side_effect=Exception("down")), \
             patch('reporting_watchdog_service.wd.generate_fallback_report', side_effect=Exception("fail")), \
             patch('reporting_watchdog_service.REPORT_HISTORY_FILE', tmp_path / "history.jsonl"), \
             patch('reporting_watchdog_service.HEALTH_FILE', tmp_path / "health.json"):
            service = ReportingWatchdogService()
            r1 = service.run_once()
            assert r1["success"] is False
            assert service._consecutive_failures == 1
            r2 = service.run_once()
            assert r2["success"] is False
            assert service._consecutive_failures == 2

    def test_health_file_updated(self, tmp_path):
        with patch('reporting_watchdog_service.REPORT_HISTORY_FILE', tmp_path / "history.jsonl"), \
             patch('reporting_watchdog_service.HEALTH_FILE', tmp_path / "health.json"):
            service = ReportingWatchdogService()
            service.run_once()
            health = json.loads((tmp_path / "health.json").read_text())
            assert health["status"] in ("healthy", "degraded")
            assert "details" in health
            assert "last_report_type" in health["details"]
            assert "next_report_in_seconds" in health

    def test_seconds_until_next_report(self, tmp_path):
        with patch('reporting_watchdog_service.REPORT_HISTORY_FILE', tmp_path / "history.jsonl"), \
             patch('reporting_watchdog_service.HEALTH_FILE', tmp_path / "health.json"):
            service = ReportingWatchdogService()
            s = service._seconds_until_next_report()
            assert 1 <= s <= 1800

    def test_report_contains_required_fields(self, tmp_path):
        with patch('reporting_watchdog_service.REPORT_HISTORY_FILE', tmp_path / "history.jsonl"), \
             patch('reporting_watchdog_service.HEALTH_FILE', tmp_path / "health.json"):
            service = ReportingWatchdogService()
            result = service.run_once()
            report = result["report"]
            assert "CEO 30-MINUTE STATUS REPORT" in report
            assert "Account equity" in report

    def test_stockholm_timezone(self, tmp_path):
        with patch('reporting_watchdog_service.REPORT_HISTORY_FILE', tmp_path / "history.jsonl"), \
             patch('reporting_watchdog_service.HEALTH_FILE', tmp_path / "health.json"):
            service = ReportingWatchdogService()
            result = service.run_once()
            assert "CEST" in result["report"] or "Stockholm" in result["report"]

    def test_pid_file_handling(self, tmp_path):
        with patch('reporting_watchdog_service.REPORT_HISTORY_FILE', tmp_path / "history.jsonl"), \
             patch('reporting_watchdog_service.HEALTH_FILE', tmp_path / "health.json"), \
             patch('reporting_watchdog_service.PID_FILE', tmp_path / "watchdog.pid"):
            service = ReportingWatchdogService()
            service._write_pid()
            assert (tmp_path / "watchdog.pid").exists()
            service._remove_pid()
            assert not (tmp_path / "watchdog.pid").exists()
