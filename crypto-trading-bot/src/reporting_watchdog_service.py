"""
CEO Reporting Watchdog Service — Standalone background service.

Runs independently of the main trading daemon.
- Generates CEO report every 30 minutes
- Saves report locally
- Logs delivery status
- Never silently fails
"""

import os
import sys
import json
import time
import signal
import logging
import traceback
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

import ceo_reporting_watchdog as wd
from zoneinfo import ZoneInfo

logger = logging.getLogger("reporting_watchdog")

PID_FILE = Path("/tmp/jarvis_reporting_watchdog.pid")
HEALTH_FILE = Path("/data/.openclaw/workspace/crypto-trading-bot/logs/reporting_watchdog_health.json")
STOCKHOLM_TZ = ZoneInfo("Europe/Stockholm")
REPORT_HISTORY_FILE = wd.REPORT_HISTORY_FILE


class ReportingWatchdogService:
    """Independent CEO reporting service."""

    def __init__(self):
        self._running = False
        self._last_report_time = None
        self._last_report_type = "none"
        self._consecutive_failures = 0
        self._total_reports = 0
        self._total_failures = 0

    def _write_pid(self):
        PID_FILE.write_text(str(os.getpid()))

    def _remove_pid(self):
        PID_FILE.unlink(missing_ok=True)

    def _update_health(self, status: str, details: dict = None):
        health = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "pid": os.getpid(),
            "last_report_time": self._last_report_time.isoformat() if self._last_report_time else None,
            "last_report_type": self._last_report_type,
            "consecutive_failures": self._consecutive_failures,
            "total_reports": self._total_reports,
            "total_failures": self._total_failures,
            "next_report_in_seconds": self._seconds_until_next_report(),
            "details": details or {},
        }
        HEALTH_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(HEALTH_FILE, "w") as f:
            json.dump(health, f, indent=2, default=str)

    def _seconds_until_next_report(self) -> int:
        now = datetime.now(STOCKHOLM_TZ)
        if now.minute < 30:
            target = now.replace(minute=30, second=0, microsecond=0)
        else:
            target = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        return max(1, int((target - now).total_seconds()))

    def _generate_and_save_report(self) -> dict:
        start_time = time.time()
        report_entry = {
            "timestamp": datetime.now(STOCKHOLM_TZ).isoformat(),
            "type": "unknown",
            "success": False,
            "errors": [],
            "report": None,
        }

        try:
            report = wd.generate_full_report()
            report_entry["type"] = "full"
            report_entry["success"] = True
            report_entry["report"] = report
            self._last_report_type = "full"
            self._consecutive_failures = 0
            self._total_reports += 1

        except Exception as e:
            error_msg = f"Full report failed: {str(e)}"
            logger.error(error_msg)
            report_entry["errors"].append(error_msg)

            try:
                fallback = wd.generate_fallback_report(reason=str(e)[:100])
                report_entry["type"] = "fallback"
                report_entry["success"] = True
                report_entry["report"] = fallback
                self._last_report_type = "fallback"
                self._consecutive_failures = 0
                self._total_reports += 1
                logger.warning("Used fallback report")

            except Exception as e2:
                error_msg2 = f"Fallback report also failed: {str(e2)}"
                logger.critical(error_msg2)
                report_entry["errors"].append(error_msg2)
                report_entry["type"] = "failed"
                self._consecutive_failures += 1
                self._total_failures += 1

        # Always save
        try:
            report_path = Path(REPORT_HISTORY_FILE)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(report_path, "a") as f:
                f.write(json.dumps(report_entry) + "\n")
            logger.info(f"Report saved: {report_entry['type']} ({report_entry['success']})")
        except Exception as e:
            logger.critical(f"Failed to save report: {e}")
            report_entry["errors"].append(f"Save failed: {e}")

        # Delivery status log
        delivery = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "report_type": report_entry["type"],
            "success": report_entry["success"],
            "errors": report_entry["errors"],
            "saved_to": str(REPORT_HISTORY_FILE),
        }
        logger.info(f"Delivery: {json.dumps(delivery)}")

        if self._consecutive_failures >= 2:
            logger.critical(
                f"CRITICAL: {self._consecutive_failures} consecutive failures! "
            )

        self._last_report_time = datetime.now(timezone.utc)
        logger.info(f"Report took {time.time() - start_time:.1f}s")
        return report_entry

    def _run_report_cycle(self):
        logger.info("=" * 60)
        logger.info("WATCHDOG: Report cycle starting")
        logger.info("=" * 60)

        result = self._generate_and_save_report()

        self._update_health(
            "healthy" if result["success"] else "degraded",
            {
                "last_report_type": result["type"],
                "last_report_success": result["success"],
                "errors": result.get("errors", []),
            }
        )

        if result["report"]:
            print("\n" + "=" * 70)
            print("CEO REPORT OUTPUT")
            print("=" * 70)
            print(result["report"])
            print("=" * 70 + "\n")

        logger.info(f"Cycle complete. Type={result['type']}, Success={result['success']}")
        return result

    def run(self):
        self._running = True
        self._write_pid()
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        logger.info("=" * 60)
        logger.info("CEO REPORTING WATCHDOG SERVICE STARTED")
        logger.info(f"PID: {os.getpid()}")
        logger.info("=" * 60)

        self._update_health("starting")
        self._run_report_cycle()

        while self._running:
            try:
                sleep_seconds = self._seconds_until_next_report()
                logger.info(f"Sleeping {sleep_seconds}s until next report")

                slept = 0
                while slept < sleep_seconds and self._running:
                    time.sleep(min(5, sleep_seconds - slept))
                    slept += 5

                if not self._running:
                    break

                self._run_report_cycle()

            except Exception as e:
                logger.critical(f"Loop error: {e}", exc_info=True)
                self._total_failures += 1
                self._update_health("error", {"error": str(e)})
                time.sleep(60)

        self._remove_pid()
        logger.info("Service stopped")

    def _handle_signal(self, signum, frame):
        logger.info(f"Signal {signum}, shutting down...")
        self._running = False

    def run_once(self) -> dict:
        return self._run_report_cycle()


def is_already_running() -> bool:
    if not PID_FILE.exists():
        return False
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 0)
        return True
    except (ValueError, OSError, ProcessLookupError):
        PID_FILE.unlink(missing_ok=True)
        return False


def run_once():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    service = ReportingWatchdogService()
    result = service.run_once()
    print(json.dumps({
        "success": result["success"],
        "type": result["type"],
        "errors": result.get("errors", []),
    }, indent=2))
    return result


if __name__ == "__main__":
    run_once()
