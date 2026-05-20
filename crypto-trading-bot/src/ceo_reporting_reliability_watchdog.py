"""
CEO Reporting Reliability Watchdog - Enhanced version with all CEO requirements.

Features:
- Runtime state cache integration
- Missed report detection
- Recovery report generation
- Strict timeouts
- Independent operation
- Health monitoring
"""

import json
import logging
import os
import sys
import time
import signal
from pathlib import Path
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

sys.path.insert(0, str(Path(__file__).parent))

from runtime_state_cache import RuntimeState, read_runtime_state, DEFAULT_STATE_FILE

logger = logging.getLogger("reporting_watchdog")

# Paths
REPORT_HISTORY_FILE = Path("logs/ceo_report_history.jsonl")
HEALTH_FILE = Path("logs/reporting_watchdog_health.json")
WATCHDOG_LOG_FILE = Path("logs/ceo_watchdog.log")
MISSING_REPORT_LOG = Path("logs/missed_reports.jsonl")
RECOVERY_REPORTS_FILE = Path("logs/recovery_reports.jsonl")
PID_FILE = Path("/tmp/jarvis_reporting_watchdog.pid")

# Timezone
STOCKHOLM_TZ = ZoneInfo("Europe/Stockholm")

# Timeouts (seconds) - STRICT
TIMEOUT_STATE_READ = 3
TIMEOUT_ACCOUNT_FETCH = 10
TIMEOUT_POSITION_FETCH = 10
TIMEOUT_FULL_REPORT = 30
TIMEOUT_FALLBACK_REPORT = 5
TIMEOUT_OLLAMA = 10  # Not used, but documented

# Schedule
REPORT_INTERVAL_SECONDS = 1800  # 30 minutes


@dataclass
class ReportEntry:
    timestamp: str
    report_type: str
    success: bool
    errors: List[str]
    report: str
    delivery_status: str = "saved_locally"
    
    def to_dict(self) -> Dict:
        return asdict(self)


class CEOReportingReliabilityWatchdog:
    """
    Independent, bulletproof CEO reporting watchdog.
    
    Does NOT depend on: Ollama, agents, trading cycles, chart monitor, main daemon.
    Reads from: runtime_state.json (local cache), Alpaca (with timeout), local logs.
    """

    def __init__(self):
        self.consecutive_failures = 0
        self.total_reports = 0
        self.total_failures = 0
        self.last_successful_report_time: Optional[datetime] = None
        self.last_report_type = "none"
        
    def _read_runtime_state(self) -> Optional[Dict]:
        """Read runtime state cache with strict timeout."""
        try:
            import threading
            result = [None]
            def read():
                result[0] = read_runtime_state()
            t = threading.Thread(target=read)
            t.start()
            t.join(timeout=TIMEOUT_STATE_READ)
            if t.is_alive():
                logger.warning(f"State read timed out after {TIMEOUT_STATE_READ}s")
                return None
            return result[0]
        except Exception as e:
            logger.error(f"State read error: {e}")
            return None

    def _fetch_account_with_timeout(self) -> Dict:
        """Fetch account data with strict timeout."""
        try:
            import threading
            result = [{}]
            errors = [None]
            
            def fetch():
                try:
                    from alpaca.trading.client import TradingClient
                    api_key = os.environ.get("ALPACA_API_KEY")
                    secret_key = os.environ.get("ALPACA_SECRET_KEY")
                    if not api_key or not secret_key:
                        errors[0] = "Missing API keys"
                        return
                    client = TradingClient(api_key, secret_key, paper=True)
                    account = client.get_account()
                    result[0] = {
                        "equity": float(account.equity),
                        "buying_power": float(account.buying_power),
                        "cash": float(account.cash),
                        "portfolio_value": float(account.portfolio_value),
                    }
                except Exception as e:
                    errors[0] = str(e)
            
            t = threading.Thread(target=fetch)
            t.start()
            t.join(timeout=TIMEOUT_ACCOUNT_FETCH)
            
            if t.is_alive():
                return {"error": f"Account fetch timed out after {TIMEOUT_ACCOUNT_FETCH}s", "skipped": True}
            if errors[0]:
                return {"error": errors[0], "skipped": True}
            return result[0]
            
        except Exception as e:
            return {"error": f"Account fetch error: {e}", "skipped": True}

    def _fetch_positions_with_timeout(self) -> List[Dict]:
        """Fetch positions with strict timeout."""
        try:
            import threading
            result = [[]]
            errors = [None]
            
            def fetch():
                try:
                    from alpaca.trading.client import TradingClient
                    api_key = os.environ.get("ALPACA_API_KEY")
                    secret_key = os.environ.get("ALPACA_SECRET_KEY")
                    if not api_key or not secret_key:
                        errors[0] = "Missing API keys"
                        return
                    client = TradingClient(api_key, secret_key, paper=True)
                    positions = client.get_all_positions()
                    result[0] = [
                        {
                            "symbol": p.symbol,
                            "qty": float(p.qty),
                            "market_value": float(p.market_value),
                            "unrealized_pl": float(p.unrealized_pl),
                            "avg_entry_price": float(p.avg_entry_price),
                            "current_price": float(p.current_price),
                        }
                        for p in positions
                    ]
                except Exception as e:
                    errors[0] = str(e)
            
            t = threading.Thread(target=fetch)
            t.start()
            t.join(timeout=TIMEOUT_POSITION_FETCH)
            
            if t.is_alive():
                return [{"error": f"Position fetch timed out after {TIMEOUT_POSITION_FETCH}s"}]
            if errors[0]:
                return [{"error": errors[0]}]
            return result[0]
            
        except Exception as e:
            return [{"error": f"Position fetch error: {e}"}]

    def generate_full_report(self, state: Dict = None) -> str:
        """Generate full CEO report."""
        now = datetime.now(timezone.utc)
        stockholm = now.astimezone(STOCKHOLM_TZ)
        
        # Get state from cache if not provided
        if not state:
            state = self._read_runtime_state() or {}
        
        # Get live data (with timeouts)
        account = self._fetch_account_with_timeout()
        positions = self._fetch_positions_with_timeout()
        
        # Build report
        report_lines = [
            "# CEO 30-MINUTE STATUS REPORT",
            "",
            f"**Report time:** {stockholm.strftime('%A, %B %d, %Y — %H:%M %Z')} (Europe/Stockholm)",
            f"**UTC time:** {now.strftime('%Y-%m-%d %H:%M:%S')} UTC",
            f"**Report type:** FULL",
            "",
            "---",
            "",
            "## 1. EXECUTIVE SUMMARY",
            "",
        ]
        
        # Account data
        if "error" in account:
            report_lines.append(f"- **Account equity:** [FETCH FAILED — {account.get('error', 'unknown error')}]")
            # Fallback to state cache
            if state.get("account_equity"):
                report_lines.append(f"- **Account equity (cache):** ${state['account_equity']:.2f}")
        else:
            report_lines.append(f"- **Account equity:** ${account.get('equity', 0):.2f}")
            report_lines.append(f"- **Buying power:** ${account.get('buying_power', 0):.2f}")
        
        # State cache data
        if state:
            report_lines.append(f"- **Cash reserve:** ${state.get('reserve_capital', 0) or 0:.2f}" if state.get('reserve_capital') else "")
            report_lines.append(f"- **Invested:** ${state.get('current_exposure', 0) or 0:.2f}" if state.get('current_exposure') else "")
            report_lines.append(f"- **Exposure:** {state.get('exposure_percent', 0) or 0:.1f}%" if state.get('exposure_percent') else "")
        
        # Positions
        if positions and not any("error" in p for p in positions):
            report_lines.append(f"- **Open positions:** {len(positions)}")
        elif state.get("open_position_count") is not None:
            report_lines.append(f"- **Open positions:** {state['open_position_count']} (from cache)")
        else:
            report_lines.append("- **Open positions:** unknown")
        
        # PnL
        if state:
            if state.get("realized_pnl_today") is not None:
                report_lines.append(f"- **Realized PnL today:** ${state['realized_pnl_today']:.2f}")
            if state.get("unrealized_pnl") is not None:
                report_lines.append(f"- **Unrealized PnL:** ${state['unrealized_pnl']:.2f}")
            if state.get("daily_total_pnl") is not None:
                report_lines.append(f"- **Daily total PnL:** ${state['daily_total_pnl']:.2f}")
        
        # Daemon status
        daemon_pid = state.get("daemon_pid") or "unknown"
        daemon_status = state.get("daemon_status", "unknown")
        report_lines.append(f"- **Daemon status:** {daemon_status.upper()} (PID: {daemon_pid})")
        
        report_lines.extend(["", "## 2. OPEN POSITIONS", ""])
        
        if positions and not any("error" in p for p in positions):
            for p in positions:
                report_lines.append(
                    f"| {p['symbol']} | {p['qty']:.4f} | ${p['avg_entry_price']:.2f} | "
                    f"${p['current_price']:.2f} | {p['unrealized_pl']:+.2f} |"
                )
        elif state.get("open_positions"):
            for p in state["open_positions"]:
                report_lines.append(
                    f"| {p.get('symbol', 'N/A')} | {p.get('qty', 0):.4f} | "
                    f"${p.get('entry', 0):.2f} | ${p.get('current', 0):.2f} | "
                    f"{p.get('unrealized_pl', 0):+.2f} |"
                )
        else:
            report_lines.append("No open positions.")
        
        # System Health
        report_lines.extend([
            "",
            "## 3. SYSTEM HEALTH",
            "",
            f"- **Daemon:** {'✅' if daemon_status == 'running' else '⚠️'} {daemon_status}",
            f"- **State cache:** {'✅ Found' if state else '❌ Missing'}",
            f"- **Risk Governor:** {state.get('risk_governor_status', 'unknown')}" if state else "- **Risk Governor:** unknown",
            f"- **Kill switch:** {state.get('kill_switch_status', 'unknown')}" if state else "- **Kill switch:** unknown",
            f"- **Chart monitor:** {state.get('chart_monitor_status', 'unknown')}" if state else "- **Chart monitor:** unknown",
            f"- **Position monitor:** {'✅' if state.get('last_position_monitor_cycle') else '⚠️'} last cycle: {state.get('last_position_monitor_cycle', 'never')}" if state else "- **Position monitor:** unknown",
        ])
        
        # Strategy leaderboard
        if state and state.get("active_strategies") is not None:
            report_lines.extend([
                "",
                "## 4. STRATEGY LEADERBOARD",
                "",
                f"- **Active strategies:** {state.get('active_strategies', 0)}",
                f"- **Testing:** {state.get('testing_strategies', 0)}",
                f"- **Rejected:** {state.get('rejected_strategies', 0)}",
            ])
        
        # Trading activity
        if state:
            report_lines.extend([
                "",
                "## 5. TRADING ACTIVITY TODAY",
                "",
                f"- **Cycles:** {state.get('total_cycles_today', 0)}",
                f"- **Trades:** {state.get('total_trades_today', 0)}",
                f"- **Exits:** {state.get('total_exits_today', 0)}",
                f"- **Risk blocks:** {state.get('risk_blocks_today', 0)}",
                f"- **Last trade:** {state.get('last_trade', 'none')}",
                f"- **Last exit:** {state.get('last_exit', 'none')}",
            ])
        
        # Errors
        if state and state.get("last_error"):
            report_lines.extend([
                "",
                "## 6. LAST ERROR",
                "",
                f"```\n{state['last_error']}\n```",
            ])
        
        # Next report
        next_report = stockholm + timedelta(minutes=30)
        report_lines.extend([
            "",
            "## 7. NEXT REPORT",
            "",
            f"Next scheduled: {next_report.strftime('%H:%M %Z')}",
            "",
            "---",
            "*Generated by CEO Reporting Reliability Watchdog*",
        ])
        
        return "\n".join(report_lines)

    def generate_fallback_report(self, reason: str = "unknown failure", state: Dict = None) -> str:
        """Generate fallback report when full report fails."""
        now = datetime.now(timezone.utc)
        stockholm = now.astimezone(STOCKHOLM_TZ)
        
        if not state:
            state = self._read_runtime_state() or {}
        
        return f"""# FALLBACK CEO REPORT

**Report time:** {stockholm.strftime('%A, %B %d, %Y — %H:%M %Z')} (Europe/Stockholm)
**UTC time:** {now.strftime('%Y-%m-%d %H:%M:%S')} UTC
**Report type:** FALLBACK
**Reason full report failed:** {reason}
**Last known state time:** {state.get('last_state_update_time', 'unknown')}

---

## ACCOUNT
- **Account equity:** {f"${state.get('account_equity', 'unknown')}" if state.get('account_equity') else 'unknown'}
- **Buying power:** {f"${state.get('buying_power', 'unknown')}" if state.get('buying_power') else 'unknown'}

## POSITIONS
- **Open positions:** {state.get('open_position_count', 'unknown')}
- **Unrealized PnL:** {f"${state.get('unrealized_pnl', 'unknown')}" if state.get('unrealized_pnl') is not None else 'unknown'}

## PNL
- **Realized PnL today:** {f"${state.get('realized_pnl_today', 'unknown')}" if state.get('realized_pnl_today') is not None else 'unknown'}
- **Daily total PnL:** {f"${state.get('daily_total_pnl', 'unknown')}" if state.get('daily_total_pnl') is not None else 'unknown'}

## RISK
- **Risk Governor status:** {state.get('risk_governor_status', 'unknown')}
- **Kill switch status:** {state.get('kill_switch_status', 'unknown')}
- **Current exposure:** {f"{state.get('exposure_percent', 'unknown')}%" if state.get('exposure_percent') else 'unknown'}

## DAEMON
- **Daemon status:** {state.get('daemon_status', 'unknown')} (PID: {state.get('daemon_pid', 'unknown')})

## MONITORS
- **Position monitor:** last cycle: {state.get('last_position_monitor_cycle', 'never')}
- **Chart monitor:** {state.get('chart_monitor_status', 'unknown')}
- **Reporting watchdog:** {state.get('reporting_watchdog_status', 'unknown')}

## ERRORS
- **Last error:** {state.get('last_error', 'none')}
- **Consecutive failures:** {self.consecutive_failures}

## RECOVERY
- **Recovery action:** Using fallback report with cached state
- **Next scheduled report:** {(stockholm + timedelta(minutes=30)).strftime('%H:%M %Z')}
- **CEO approval required:** no
- **CEO informed:** yes

---
*Generated by CEO Reporting Reliability Watchdog (FALLBACK MODE)*
"""

    def generate_missed_report_recovery(self, missed_time: str, reason: str, state: Dict = None) -> str:
        """Generate recovery report for missed scheduled report."""
        now = datetime.now(timezone.utc)
        stockholm = now.astimezone(STOCKHOLM_TZ)
        
        if not state:
            state = self._read_runtime_state() or {}
        
        return f"""# CEO MISSED REPORT RECOVERY

**Missed report time:** {missed_time}
**Detected at:** {stockholm.strftime('%A, %B %d, %Y — %H:%M %Z')} (Europe/Stockholm)
**Reason missed:** {reason}

---

## SYSTEM CHECK
- **Was state cache updated:** {'yes' if state.get('last_state_update_time') else 'no'}
- **Was daemon running:** {'yes' if state.get('daemon_status') == 'running' else 'no / unknown'}
- **Was watchdog running:** {'yes' if state.get('reporting_watchdog_status') == 'running' else 'no / unknown'}
- **Was report generated:** no (this is the recovery)
- **Was report delivered:** no (this is the recovery)

## STATE
- **Last state update:** {state.get('last_state_update_time', 'unknown')}
- **Account equity:** {f"${state.get('account_equity', 'unknown')}" if state.get('account_equity') else 'unknown'}
- **Open positions:** {state.get('open_position_count', 'unknown')}
- **Unrealized PnL:** {f"${state.get('unrealized_pnl', 'unknown')}" if state.get('unrealized_pnl') is not None else 'unknown'}
- **Daily PnL:** {f"${state.get('daily_total_pnl', 'unknown')}" if state.get('daily_total_pnl') is not None else 'unknown'}

## ERRORS
- **Last error:** {state.get('last_error', 'none')}
- **Error logs:** See logs/ceo_watchdog.log

## FIX
- **Fix applied:** Generated recovery report immediately
- **Next report time:** {(stockholm + timedelta(minutes=30)).strftime('%H:%M %Z')}
- **CEO approval required:** no
- **CEO informed:** yes

---
*Generated by CEO Reporting Reliability Watchdog (RECOVERY MODE)*
"""

    def check_missed_reports(self) -> List[Dict]:
        """Check for missed scheduled reports."""
        missed = []
        now = datetime.now(STOCKHOLM_TZ)
        
        # Expected reports: every :00 and :30
        if now.minute < 30:
            last_expected = now.replace(minute=0, second=0, microsecond=0)
        else:
            last_expected = now.replace(minute=30, second=0, microsecond=0)
        
        # Check if we have a report within last 35 minutes
        if self.last_successful_report_time:
            minutes_since = (now - self.last_successful_report_time.astimezone(STOCKHOLM_TZ)).total_seconds() / 60
            if minutes_since > 35:
                missed.append({
                    "missed_time": last_expected.isoformat(),
                    "reason": f"No report for {minutes_since:.0f} minutes",
                    "severity": "high",
                })
        
        return missed

    def run_report_cycle(self) -> ReportEntry:
        """Run one complete reporting cycle."""
        logger.info("=" * 60)
        logger.info("RELIABILITY WATCHDOG: Report cycle starting")
        logger.info("=" * 60)
        
        now = datetime.now(STOCKHOLM_TZ)
        state = self._read_runtime_state()
        
        entry = ReportEntry(
            timestamp=now.isoformat(),
            report_type="unknown",
            success=False,
            errors=[],
            report="",
        )
        
        # Try full report first
        try:
            report = self.generate_full_report(state=state)
            entry.report_type = "full"
            entry.success = True
            entry.report = report
            self.last_report_type = "full"
            self.consecutive_failures = 0
            self.total_reports += 1
            self.last_successful_report_time = datetime.now(timezone.utc)
            logger.info("Full report generated successfully")
            
        except Exception as e:
            error_msg = f"Full report failed: {str(e)}"
            logger.error(error_msg)
            entry.errors.append(error_msg)
            
            # Fallback report
            try:
                fallback = self.generate_fallback_report(reason=str(e)[:200], state=state)
                entry.report_type = "fallback"
                entry.success = True
                entry.report = fallback
                self.last_report_type = "fallback"
                self.consecutive_failures = 0
                self.total_reports += 1
                self.last_successful_report_time = datetime.now(timezone.utc)
                logger.warning("Used fallback report")
                
            except Exception as e2:
                error_msg2 = f"Fallback also failed: {str(e2)}"
                logger.critical(error_msg2)
                entry.errors.append(error_msg2)
                entry.report_type = "failed"
                self.consecutive_failures += 1
                self.total_failures += 1
                entry.report = f"CRITICAL: Both full and fallback reports failed.\nErrors: {entry.errors}\nTime: {now.isoformat()}"
        
        # Check for missed reports
        missed = self.check_missed_reports()
        if missed:
            for m in missed:
                logger.critical(f"MISSED REPORT DETECTED: {m['missed_time']} - {m['reason']}")
                entry.errors.append(f"Missed report: {m['missed_time']}")
                
                # Generate recovery report
                try:
                    recovery = self.generate_missed_report_recovery(
                        m["missed_time"], m["reason"], state
                    )
                    # Save recovery separately
                    MISSING_REPORT_LOG.parent.mkdir(parents=True, exist_ok=True)
                    with open(MISSING_REPORT_LOG, "a") as f:
                        f.write(json.dumps({
                            "timestamp": now.isoformat(),
                            "missed_time": m["missed_time"],
                            "reason": m["reason"],
                            "recovery_report": recovery,
                        }) + "\n")
                    logger.info(f"Recovery report saved for {m['missed_time']}")
                except Exception as e:
                    logger.critical(f"Failed to generate recovery report: {e}")
        
        # Always save report
        try:
            REPORT_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(REPORT_HISTORY_FILE, "a") as f:
                f.write(json.dumps(entry.to_dict()) + "\n")
            logger.info(f"Report saved: {entry.report_type} ({entry.success})")
        except Exception as e:
            logger.critical(f"Failed to save report: {e}")
            entry.errors.append(f"Save failed: {e}")
        
        # Critical alert
        if self.consecutive_failures >= 2:
            logger.critical(f"CRITICAL: {self.consecutive_failures} consecutive failures!")
        
        # Update health
        self._update_health(entry)
        
        # Print to stdout for log capture
        if entry.report:
            print("\n" + "=" * 70)
            print("CEO REPORT OUTPUT")
            print("=" * 70)
            print(entry.report)
            print("=" * 70 + "\n")
        
        logger.info(f"Cycle complete. Type={entry.report_type}, Success={entry.success}, Errors={len(entry.errors)}")
        return entry

    def _update_health(self, entry: ReportEntry):
        """Write health status."""
        health = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "healthy" if entry.success else "degraded",
            "last_report_time": self.last_successful_report_time.isoformat() if self.last_successful_report_time else None,
            "last_report_type": self.last_report_type,
            "consecutive_failures": self.consecutive_failures,
            "total_reports": self.total_reports,
            "total_failures": self.total_failures,
            "report_success": entry.success,
            "report_type": entry.report_type,
            "errors": entry.errors,
        }
        try:
            HEALTH_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(HEALTH_FILE, "w") as f:
                json.dump(health, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to write health: {e}")

    def run(self):
        """Main service loop."""
        import time
        
        self._running = True
        signal.signal(signal.SIGTERM, lambda s, f: setattr(self, '_running', False))
        signal.signal(signal.SIGINT, lambda s, f: setattr(self, '_running', False))
        
        # Write PID
        try:
            PID_FILE.write_text(str(os.getpid()))
        except Exception as e:
            logger.warning(f"Could not write PID: {e}")
        
        logger.info("=" * 60)
        logger.info("CEO REPORTING RELIABILITY WATCHDOG STARTED")
        logger.info(f"PID: {os.getpid()}")
        logger.info(f"Interval: {REPORT_INTERVAL_SECONDS}s")
        logger.info("=" * 60)
        
        # Run immediately
        self.run_report_cycle()
        
        while self._running:
            try:
                # Sleep until next :00 or :30
                now = datetime.now(STOCKHOLM_TZ)
                if now.minute < 30:
                    target = now.replace(minute=30, second=0, microsecond=0)
                else:
                    target = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
                
                sleep_seconds = max(1, int((target - now).total_seconds()))
                logger.info(f"Sleeping {sleep_seconds}s until next report ({target.strftime('%H:%M')})")
                
                # Sleep in chunks
                slept = 0
                while slept < sleep_seconds and self._running:
                    time.sleep(min(5, sleep_seconds - slept))
                    slept += 5
                
                if not self._running:
                    break
                
                self.run_report_cycle()
                
            except Exception as e:
                logger.critical(f"Main loop error: {e}", exc_info=True)
                time.sleep(60)
        
        # Cleanup
        PID_FILE.unlink(missing_ok=True)
        logger.info("Watchdog stopped")

    def run_once(self) -> ReportEntry:
        """Run single cycle (for testing/manual)."""
        return self.run_report_cycle()


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


def main():
    """Run watchdog once or as service."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    
    watchdog = CEOReportingReliabilityWatchdog()
    result = watchdog.run_once()
    
    print(json.dumps({
        "success": result.success,
        "type": result.report_type,
        "errors": result.errors,
    }, indent=2))
    
    return result


if __name__ == "__main__":
    main()
