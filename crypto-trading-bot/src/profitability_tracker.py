"""Daily Profitability Tracker — Track progress toward $30-$50/day target."""
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

TRACKER_FILE = Path("/data/.openclaw/workspace/crypto-trading-bot/logs/profitability_tracker.json")
DAILY_TARGET_MIN = 30
DAILY_TARGET_MAX = 50


class ProfitabilityTracker:
    """Tracks daily PnL, win rate, and progress toward profit target."""

    def __init__(self, tracker_file: Path = TRACKER_FILE):
        self.tracker_file = tracker_file
        self.data = self._load()

    def _load(self) -> Dict:
        if self.tracker_file.exists():
            try:
                with open(self.tracker_file) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {
            "daily_records": [],
            "trades": [],
            "strategy_performance": {},
            "current_streak": {"wins": 0, "losses": 0},
            "best_day": None,
            "worst_day": None,
        }

    def _save(self):
        self.tracker_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.tracker_file, "w") as f:
            json.dump(self.data, f, indent=2, default=str)

    def record_trade(self, symbol: str, entry_price: float, exit_price: float,
                     qty: float, strategy: str, exit_reason: str,
                     holding_hours: float):
        """Record a completed round-trip trade."""
        pnl = (exit_price - entry_price) * qty
        pnl_pct = (exit_price - entry_price) / entry_price * 100 if entry_price > 0 else 0

        trade = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "symbol": symbol,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "qty": qty,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "strategy": strategy,
            "exit_reason": exit_reason,
            "holding_hours": holding_hours,
        }
        self.data["trades"].append(trade)

        # Update strategy performance
        if strategy not in self.data["strategy_performance"]:
            self.data["strategy_performance"][strategy] = {
                "trades": 0, "wins": 0, "total_pnl": 0, "avg_pnl": 0,
            }
        sp = self.data["strategy_performance"][strategy]
        sp["trades"] += 1
        sp["total_pnl"] += pnl
        if pnl > 0:
            sp["wins"] += 1
        sp["avg_pnl"] = sp["total_pnl"] / sp["trades"]

        # Update streak
        if pnl > 0:
            self.data["current_streak"]["wins"] += 1
            self.data["current_streak"]["losses"] = 0
        else:
            self.data["current_streak"]["losses"] += 1
            self.data["current_streak"]["wins"] = 0

        self._save()
        return trade

    def get_today_summary(self) -> Dict:
        """Get today's trading summary."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_trades = [
            t for t in self.data["trades"]
            if t["timestamp"].startswith(today)
        ]

        wins = [t for t in today_trades if t["pnl"] > 0]
        losses = [t for t in today_trades if t["pnl"] <= 0]
        total_pnl = sum(t["pnl"] for t in today_trades)

        win_rate = len(wins) / len(today_trades) * 100 if today_trades else 0
        avg_win = sum(t["pnl"] for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t["pnl"] for t in losses) / len(losses) if losses else 0

        return {
            "date": today,
            "total_trades": len(today_trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "avg_trade_pnl": total_pnl / len(today_trades) if today_trades else 0,
            "target_met": DAILY_TARGET_MIN <= total_pnl <= DAILY_TARGET_MAX,
            "distance_from_target": max(0, DAILY_TARGET_MIN - total_pnl),
        }

    def get_metrics(self) -> Dict:
        """Get all-time profitability metrics."""
        all_trades = self.data["trades"]
        if not all_trades:
            return {"error": "No trades recorded yet"}

        wins = [t for t in all_trades if t["pnl"] > 0]
        losses = [t for t in all_trades if t["pnl"] <= 0]
        total_pnl = sum(t["pnl"] for t in all_trades)

        win_rate = len(wins) / len(all_trades) * 100
        avg_win = sum(t["pnl"] for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t["pnl"] for t in losses) / len(losses) if losses else 0
        profit_factor = abs(sum(t["pnl"] for t in wins) / sum(t["pnl"] for t in losses)) if losses and sum(t["pnl"] for t in losses) != 0 else float('inf')

        # Expected value
        ev = (win_rate/100 * avg_win) - ((1 - win_rate/100) * abs(avg_loss))

        return {
            "total_trades": len(all_trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": win_rate,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "expected_value_per_trade": ev,
            "total_pnl": total_pnl,
            "trades_per_day": len(all_trades) / max(1, len(self.data["daily_records"])),
        }

    def generate_report(self) -> str:
        """Generate a CEO-ready profitability report."""
        today = self.get_today_summary()
        metrics = self.get_metrics()

        lines = [
            "=" * 60,
            "DAILY PROFITABILITY REPORT",
            f"Generated: {datetime.now(timezone.utc).isoformat()[:19]} UTC",
            "=" * 60,
            "",
            f"TODAY ({today['date']}):",
            f"  Trades: {today['total_trades']} ({today['wins']} wins, {today['losses']} losses)",
            f"  Win rate: {today['win_rate']:.1f}%",
            f"  Total PnL: ${today['total_pnl']:+.2f}",
            f"  Avg trade: ${today['avg_trade_pnl']:+.2f}",
            f"  Target: ${DAILY_TARGET_MIN}-{DAILY_TARGET_MAX}/day",
            f"  Distance from target: ${today['distance_from_target']:.2f}",
            f"  Target met: {'YES' if today['target_met'] else 'NO'}",
            "",
            "ALL-TIME METRICS:",
            f"  Total trades: {metrics.get('total_trades', 0)}",
            f"  Win rate: {metrics.get('win_rate', 0):.1f}%",
            f"  Profit factor: {metrics.get('profit_factor', 0):.2f}",
            f"  Expected value/trade: ${metrics.get('expected_value_per_trade', 0):+.2f}",
            f"  Total PnL: ${metrics.get('total_pnl', 0):+.2f}",
            "",
            "STRATEGY LEADERBOARD:",
        ]

        # Sort strategies by total PnL
        strategies = sorted(
            self.data.get("strategy_performance", {}).items(),
            key=lambda x: x[1].get("total_pnl", 0),
            reverse=True,
        )
        for name, perf in strategies[:5]:
            lines.append(f"  {name}: {perf['trades']} trades, ${perf['total_pnl']:+.2f}, {perf['wins']}/{perf['trades']} wins")

        if not strategies:
            lines.append("  No strategies recorded yet")

        lines.extend([
            "",
            "=" * 60,
        ])

        return "\n".join(lines)


if __name__ == "__main__":
    tracker = ProfitabilityTracker()
    print(tracker.generate_report())
