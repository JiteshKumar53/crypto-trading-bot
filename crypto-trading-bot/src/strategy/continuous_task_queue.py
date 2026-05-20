"""
Continuous Task Queue — Team Performance Improvement
Agent: Jarvis (Junior CEO)

Every team must have continuous work. No idle teams.
Tasks are assigned, tracked, and escalated automatically.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

TASK_QUEUE_FILE = "logs/task_queue.json"

# Priority levels: CRITICAL=1, HIGH=2, MEDIUM=3, LOW=4
PRIORITY_ORDER = {"CRITICAL": 1, "HIGH": 2, "MEDIUM": 3, "LOW": 4}


class ContinuousTaskQueue:
    """
    CEO-level task queue. Every team has tasks. No idle teams.
    """

    TEAM_TASKS: Dict[str, List[Dict]] = {
        "COO_Coda": [
            {"id": "coo-1", "name": "Track active tasks", "description": "Review all team task queues. Identify idle teams. Reassign.", "priority": "HIGH", "status": "PENDING", "recurring": True, "interval_hours": 1},
            {"id": "coo-2", "name": "Validate CEO reports", "description": "Ensure 30-min CEO reports are complete and sent.", "priority": "HIGH", "status": "PENDING", "recurring": True, "interval_hours": 0.5},
            {"id": "coo-3", "name": "Escalate blockers", "description": "Escalate any team blocked >1 hour to Jarvis.", "priority": "CRITICAL", "status": "PENDING", "recurring": True, "interval_hours": 1},
            {"id": "coo-4", "name": "Maintain execution board", "description": "Update execution board with current team status.", "priority": "MEDIUM", "status": "PENDING", "recurring": True, "interval_hours": 2},
        ],
        "Chief_Architect": [
            {"id": "arch-1", "name": "Review chart intelligence connection", "description": "Verify LiveChartMonitor is fully wired into pipeline and position monitor.", "priority": "CRITICAL", "status": "IN_PROGRESS", "recurring": False},
            {"id": "arch-2", "name": "Review daemon design", "description": "Ensure daemon handles restarts cleanly and position monitor recovers.", "priority": "HIGH", "status": "PENDING", "recurring": False},
            {"id": "arch-3", "name": "Review data-source plugin interface", "description": "Ensure pluggable data sources work (Alpaca, TradingView, etc.).", "priority": "MEDIUM", "status": "PENDING", "recurring": False},
            {"id": "arch-4", "name": "Propose architecture improvements", "description": "When useful, propose modular improvements.", "priority": "LOW", "status": "PENDING", "recurring": True, "interval_hours": 24},
        ],
        "Strategy_Research": [
            {"id": "strat-1", "name": "Research ranging-market strategies", "description": "Find strategies that profit in sideways BTC/ETH/SOL markets.", "priority": "CRITICAL", "status": "IN_PROGRESS", "recurring": False},
            {"id": "strat-2", "name": "Research momentum-reversal strategies", "description": "Find strategies that catch reversals after overextensions.", "priority": "HIGH", "status": "PENDING", "recurring": False},
            {"id": "strat-3", "name": "Research breakout + failed-breakout strategies", "description": "Find strategies that handle both confirmed breakouts and fakeouts.", "priority": "HIGH", "status": "PENDING", "recurring": False},
            {"id": "strat-4", "name": "Research partial-profit / runner-exit strategies", "description": "Optimize scaling out and trailing runners.", "priority": "HIGH", "status": "PENDING", "recurring": False},
            {"id": "strat-5", "name": "Investigate TradingView MCP", "description": "Can we connect TradingView MCP for strategy research?", "priority": "MEDIUM", "status": "PENDING", "recurring": False},
            {"id": "strat-6", "name": "Backlog: mean reversion strategies", "description": "Research RSI/Bollinger mean reversion for crypto.", "priority": "MEDIUM", "status": "PENDING", "recurring": False},
            {"id": "strat-7", "name": "Backlog: multi-timeframe strategies", "description": "Research strategies combining 1h + 4h + daily signals.", "priority": "MEDIUM", "status": "PENDING", "recurring": False},
            {"id": "strat-8", "name": "Backlog: low-latency non-LLM strategies", "description": "Research strategies using only indicator math (no LLM calls).", "priority": "HIGH", "status": "PENDING", "recurring": False},
        ],
        "Technical_Analysis_Candles": [
            {"id": "ta-1", "name": "Scan BTC/USD hourly", "description": "Detect S/R, trend, breakout, reversal on BTC 1h.", "priority": "HIGH", "status": "PENDING", "recurring": True, "interval_hours": 1},
            {"id": "ta-2", "name": "Scan ETH/USD hourly", "description": "Detect S/R, trend, breakout, reversal on ETH 1h.", "priority": "HIGH", "status": "PENDING", "recurring": True, "interval_hours": 1},
            {"id": "ta-3", "name": "Scan SOL/USD hourly", "description": "Detect S/R, trend, breakout, reversal on SOL 1h.", "priority": "HIGH", "status": "PENDING", "recurring": True, "interval_hours": 1},
            {"id": "ta-4", "name": "Review open positions", "description": "Check if open positions face S/R breakdown.", "priority": "CRITICAL", "status": "PENDING", "recurring": True, "interval_hours": 1},
            {"id": "ta-5", "name": "Identify missed opportunities", "description": "Log clean setups that pipeline rejected or missed.", "priority": "MEDIUM", "status": "PENDING", "recurring": True, "interval_hours": 4},
        ],
        "Sentiment_Narrative_Pulse": [
            {"id": "sent-1", "name": "Monitor BTC narrative", "description": "Track catalysts, narratives, risk events for BTC.", "priority": "MEDIUM", "status": "PENDING", "recurring": True, "interval_hours": 4},
            {"id": "sent-2", "name": "Monitor ETH narrative", "description": "Track catalysts, narratives, risk events for ETH.", "priority": "MEDIUM", "status": "PENDING", "recurring": True, "interval_hours": 4},
            {"id": "sent-3", "name": "Monitor SOL narrative", "description": "Track catalysts, narratives, risk events for SOL.", "priority": "MEDIUM", "status": "PENDING", "recurring": True, "interval_hours": 4},
            {"id": "sent-4", "name": "Alert on sentiment conflicts", "description": "If sentiment contradicts open position direction, escalate.", "priority": "HIGH", "status": "PENDING", "recurring": True, "interval_hours": 4},
        ],
        "Risk_Shield": [
            {"id": "risk-1", "name": "Monitor position sizing", "description": "Review if sizing is too restrictive or too aggressive.", "priority": "HIGH", "status": "PENDING", "recurring": True, "interval_hours": 4},
            {"id": "risk-2", "name": "Verify 50% reserve maintained", "description": "Confirm reserve capital is protected.", "priority": "CRITICAL", "status": "PENDING", "recurring": True, "interval_hours": 1},
            {"id": "risk-3", "name": "Review max 5 position policy", "description": "Ensure limit enforced. Recommend adjustment if needed.", "priority": "MEDIUM", "status": "PENDING", "recurring": True, "interval_hours": 4},
            {"id": "risk-4", "name": "Review exit rules", "description": "Do exits protect profits effectively? Recommend improvements.", "priority": "HIGH", "status": "PENDING", "recurring": True, "interval_hours": 4},
            {"id": "risk-5", "name": "Recommend safer expected-return improvements", "description": "Propose ways to increase return without increasing risk.", "priority": "MEDIUM", "status": "PENDING", "recurring": True, "interval_hours": 24},
        ],
        "Backtesting": [
            {"id": "bt-1", "name": "Backtest researched strategies", "description": "Run backtests on new strategies from Strategy Research.", "priority": "HIGH", "status": "PENDING", "recurring": True, "interval_hours": 8},
            {"id": "bt-2", "name": "Backtest exit improvements", "description": "Test new exit rules (partial profit, runner, reversal).", "priority": "HIGH", "status": "PENDING", "recurring": True, "interval_hours": 8},
            {"id": "bt-3", "name": "Compare strategies by regime", "description": "Rank strategies by trending vs ranging vs volatile performance.", "priority": "MEDIUM", "status": "PENDING", "recurring": True, "interval_hours": 24},
            {"id": "bt-4", "name": "Walk-forward validation", "description": "Validate top strategies on unseen data.", "priority": "MEDIUM", "status": "PENDING", "recurring": True, "interval_hours": 24},
            {"id": "bt-5", "name": "Maintain strategy leaderboard", "description": "Update ranked list of strategies by Sharpe, win rate, max drawdown.", "priority": "MEDIUM", "status": "PENDING", "recurring": True, "interval_hours": 24},
        ],
        "Execution_Monitoring_Sentinel": [
            {"id": "exec-1", "name": "Daemon health check", "description": "Confirm daemon running, no stale PID, cycles executing.", "priority": "CRITICAL", "status": "DONE", "recurring": True, "interval_hours": 0.5},
            {"id": "exec-2", "name": "Position monitor check", "description": "Confirm PositionMonitorV2 running every 5 min.", "priority": "CRITICAL", "status": "IN_PROGRESS", "recurring": True, "interval_hours": 0.5},
            {"id": "exec-3", "name": "Chart monitor activation", "description": "Confirm LiveChartMonitor active in PositionMonitorV2.", "priority": "CRITICAL", "status": "IN_PROGRESS", "recurring": False},
            {"id": "exec-4", "name": "Confirm partial sell logic", "description": "Verify ETH/SOL partial sells still work correctly.", "priority": "HIGH", "status": "PENDING", "recurring": False},
            {"id": "exec-5", "name": "Confirm alerts and logs", "description": "Verify logs written, alerts sent, no silent failures.", "priority": "HIGH", "status": "PENDING", "recurring": True, "interval_hours": 1},
        ],
        "Self_Evolution": [
            {"id": "evo-1", "name": "Review failed trades", "description": "Analyze losing trades. Extract lessons.", "priority": "HIGH", "status": "PENDING", "recurring": True, "interval_hours": 4},
            {"id": "evo-2", "name": "Review missed trades", "description": "Log clean setups that were missed or rejected.", "priority": "HIGH", "status": "PENDING", "recurring": True, "interval_hours": 4},
            {"id": "evo-3", "name": "Review unprofitable exits", "description": "Did we exit too early or too late? Improve.", "priority": "HIGH", "status": "PENDING", "recurring": True, "interval_hours": 4},
            {"id": "evo-4", "name": "Review agent latency", "description": "Track Ollama model response times. Flag timeouts.", "priority": "MEDIUM", "status": "PENDING", "recurring": True, "interval_hours": 4},
            {"id": "evo-5", "name": "Record lessons learned", "description": "Write to memory files. Prevent repeated mistakes.", "priority": "MEDIUM", "status": "PENDING", "recurring": True, "interval_hours": 4},
            {"id": "evo-6", "name": "Recommend improvements", "description": "Propose prompt, strategy, risk, workflow improvements.", "priority": "MEDIUM", "status": "PENDING", "recurring": True, "interval_hours": 24},
        ],
        "Dashboard_Market_Intelligence": [
            {"id": "dash-1", "name": "Activate LiveChartMonitor", "description": "Confirm chart intelligence feeding into pipeline.", "priority": "CRITICAL", "status": "DONE", "recurring": False},
            {"id": "dash-2", "name": "Track chart-based exit warnings", "description": "Log when chart observations trigger or prevent exits.", "priority": "HIGH", "status": "PENDING", "recurring": True, "interval_hours": 1},
            {"id": "dash-3", "name": "Log chart decision impact", "description": "Record when chart intelligence affects a trade decision.", "priority": "HIGH", "status": "PENDING", "recurring": True, "interval_hours": 1},
            {"id": "dash-4", "name": "Build human dashboard", "description": "Low-priority HTML/JS dashboard for CEO viewing.", "priority": "LOW", "status": "PENDING", "recurring": False},
        ],
    }

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root or "."
        self.queue_file = Path(self.project_root) / TASK_QUEUE_FILE
        self._ensure_file()

    def _ensure_file(self):
        if not self.queue_file.parent.exists():
            self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.queue_file.exists():
            self.reset_queue()

    def reset_queue(self):
        """Reset queue to initial state. Call at project start or daily."""
        data = {
            "last_reset": datetime.now(timezone.utc).isoformat(),
            "teams": self.TEAM_TASKS,
        }
        self._save(data)
        logger.info("[TASK QUEUE] Reset to initial state — all teams assigned tasks")

    def _load(self) -> Dict:
        try:
            return json.loads(self.queue_file.read_text())
        except Exception:
            return {"teams": {}}

    def _save(self, data: Dict):
        self.queue_file.write_text(json.dumps(data, indent=2, default=str))

    def get_team_tasks(self, team: str) -> List[Dict]:
        """Get all tasks for a team."""
        data = self._load()
        return data.get("teams", {}).get(team, [])

    def get_pending_tasks(self, team: Optional[str] = None) -> List[Dict]:
        """Get pending tasks, optionally filtered by team."""
        data = self._load()
        tasks = []
        teams = [team] if team else data.get("teams", {}).keys()
        for t in teams:
            for task in data.get("teams", {}).get(t, []):
                if task.get("status") in ("PENDING", "IN_PROGRESS"):
                    task["_team"] = t
                    tasks.append(task)
        tasks.sort(key=lambda x: PRIORITY_ORDER.get(x.get("priority", "LOW"), 99))
        return tasks

    def get_idle_teams(self) -> List[str]:
        """Return teams with no pending/in-progress tasks."""
        data = self._load()
        idle = []
        for team, tasks in data.get("teams", {}).items():
            active = [t for t in tasks if t.get("status") in ("PENDING", "IN_PROGRESS")]
            if not active:
                idle.append(team)
        return idle

    def update_task_status(self, team: str, task_id: str, status: str, note: str = ""):
        """Update task status."""
        data = self._load()
        for task in data.get("teams", {}).get(team, []):
            if task["id"] == task_id:
                task["status"] = status
                task["updated_at"] = datetime.now(timezone.utc).isoformat()
                if note:
                    task["notes"] = task.get("notes", "") + f"\n[{datetime.now(timezone.utc).isoformat()}] {note}"
                logger.info(f"[TASK QUEUE] {team}/{task_id} → {status}: {note}")
                self._save(data)
                return True
        return False

    def add_task(self, team: str, task: Dict):
        """Add a new task to a team."""
        data = self._load()
        if team not in data.get("teams", {}):
            data["teams"][team] = []
        task.setdefault("status", "PENDING")
        task.setdefault("priority", "MEDIUM")
        data["teams"][team].append(task)
        self._save(data)
        logger.info(f"[TASK QUEUE] Added task {task['id']} to {team}")

    def generate_ceo_report(self) -> str:
        """Generate summary for CEO report."""
        lines = ["--- TEAM TASK QUEUE ---"]
        data = self._load()
        for team, tasks in sorted(data.get("teams", {}).items()):
            pending = [t for t in tasks if t.get("status") in ("PENDING", "IN_PROGRESS")]
            critical = [t for t in pending if t.get("priority") == "CRITICAL"]
            high = [t for t in pending if t.get("priority") == "HIGH"]
            lines.append(f"  {team}: {len(pending)} pending ({len(critical)} critical, {len(high)} high)")
        idle = self.get_idle_teams()
        if idle:
            lines.append(f"\n  IDLE TEAMS (no active tasks): {', '.join(idle)}")
        else:
            lines.append("\n  All teams have active tasks.")
        return "\n".join(lines)


if __name__ == "__main__":
    queue = ContinuousTaskQueue()
    queue.reset_queue()
    print(queue.generate_ceo_report())
