"""
Runtime State Cache - Lightweight local state file for watchdog independence.

The main trading system writes this file every cycle.
The reporting watchdog reads it - no dependency on agents, Ollama, or slow APIs.
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict, field

logger = logging.getLogger(__name__)

# Default path - can be overridden
DEFAULT_STATE_FILE = Path("logs/runtime_state.json")


@dataclass
class RuntimeState:
    """Complete system state snapshot for watchdog consumption."""
    
    # Timing
    last_state_update_time: str = ""
    
    # Daemon status
    daemon_status: str = "unknown"
    daemon_pid: Optional[int] = None
    daemon_uptime_seconds: Optional[float] = None
    
    # Reporting
    reporting_watchdog_status: str = "unknown"
    reporting_watchdog_pid: Optional[int] = None
    last_successful_report_time: Optional[str] = None
    next_expected_report_time: Optional[str] = None
    consecutive_missed_reports: int = 0
    
    # Scheduler
    scheduler_status: str = "unknown"
    last_scheduler_tick: Optional[str] = None
    
    # Account
    account_equity: Optional[float] = None
    buying_power: Optional[float] = None
    reserve_capital: Optional[float] = None
    
    # Positions
    open_positions: List[Dict] = field(default_factory=list)
    open_position_count: int = 0
    
    # PnL
    realized_pnl_today: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    daily_total_pnl: Optional[float] = None
    
    # Risk
    current_exposure: Optional[float] = None
    exposure_percent: Optional[float] = None
    risk_governor_status: str = "unknown"
    risk_governor_last_check: Optional[str] = None
    risk_blocks_today: int = 0
    
    # Kill switch
    kill_switch_status: str = "unknown"
    kill_switch_triggered_at: Optional[str] = None
    
    # Activity timestamps
    last_trade: Optional[str] = None
    last_exit: Optional[str] = None
    last_error: Optional[str] = None
    last_agent_activity: Optional[str] = None
    last_position_monitor_cycle: Optional[str] = None
    last_chart_monitor_cycle: Optional[str] = None
    
    # Cycle counts
    total_cycles_today: int = 0
    total_trades_today: int = 0
    total_exits_today: int = 0
    
    # Strategy leaderboard
    active_strategies: int = 0
    testing_strategies: int = 0
    rejected_strategies: int = 0
    
    # Chart monitor
    chart_monitor_status: str = "unknown"
    chart_monitor_last_observation: Optional[str] = None
    
    # Market regime
    current_regime: str = "unknown"
    regime_confidence: Optional[float] = None
    
    @classmethod
    def from_file(cls, path: Path = None) -> Optional["RuntimeState"]:
        """Read state from disk."""
        path = path or DEFAULT_STATE_FILE
        try:
            if not path.exists():
                return None
            with open(path) as f:
                data = json.load(f)
            return cls(**data)
        except Exception as e:
            logger.warning(f"Failed to read runtime state: {e}")
            return None
    
    def to_file(self, path: Path = None):
        """Write state to disk atomically."""
        path = path or DEFAULT_STATE_FILE
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".tmp")
            with open(tmp, "w") as f:
                json.dump(asdict(self), f, indent=2, default=str)
            tmp.rename(path)
            logger.debug(f"Runtime state written: {path}")
        except Exception as e:
            logger.error(f"Failed to write runtime state: {e}")


def write_runtime_state(
    *,
    daemon_status: str = "unknown",
    daemon_pid: int = None,
    account_equity: float = None,
    buying_power: float = None,
    open_positions: List[Dict] = None,
    realized_pnl_today: float = None,
    unrealized_pnl: float = None,
    current_exposure: float = None,
    risk_governor_status: str = "unknown",
    kill_switch_status: str = "unknown",
    last_trade: str = None,
    last_exit: str = None,
    last_error: str = None,
    last_position_monitor_cycle: str = None,
    last_chart_monitor_cycle: str = None,
    reporting_watchdog_status: str = "unknown",
    chart_monitor_status: str = "unknown",
    path: Path = None,
    **kwargs
) -> RuntimeState:
    """Convenience function to write runtime state from main daemon."""
    
    now = datetime.now(timezone.utc).isoformat()
    
    state = RuntimeState(
        last_state_update_time=now,
        daemon_status=daemon_status,
        daemon_pid=daemon_pid,
        account_equity=account_equity,
        buying_power=buying_power,
        reserve_capital=buying_power - current_exposure if buying_power and current_exposure else None,
        open_positions=open_positions or [],
        open_position_count=len(open_positions) if open_positions else 0,
        realized_pnl_today=realized_pnl_today,
        unrealized_pnl=unrealized_pnl,
        daily_total_pnl=(realized_pnl_today or 0) + (unrealized_pnl or 0),
        current_exposure=current_exposure,
        exposure_percent=(current_exposure / account_equity * 100) if account_equity and current_exposure else None,
        risk_governor_status=risk_governor_status,
        kill_switch_status=kill_switch_status,
        last_trade=last_trade,
        last_exit=last_exit,
        last_error=last_error,
        last_position_monitor_cycle=last_position_monitor_cycle,
        last_chart_monitor_cycle=last_chart_monitor_cycle,
        reporting_watchdog_status=reporting_watchdog_status,
        chart_monitor_status=chart_monitor_status,
        **kwargs
    )
    
    state.to_file(path)
    return state


def read_runtime_state(path: Path = None) -> Optional[Dict]:
    """Read runtime state as dict (for watchdog)."""
    state = RuntimeState.from_file(path)
    if state:
        return asdict(state)
    return None
