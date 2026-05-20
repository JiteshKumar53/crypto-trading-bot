"""Strategy Leaderboard — Track, rank, and filter strategies by performance.

Mandatory before any strategy is allowed to trade live.
"""
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

LEADERBOARD_FILE = Path("/data/.openclaw/workspace/crypto-trading-bot/logs/strategy_leaderboard.json")

# Minimum thresholds for a strategy to be eligible for live trading
MIN_BACKTEST_RETURN = 0.05      # +5%
MIN_SHARPE = 2.0
MIN_PROFIT_FACTOR = 1.5
MIN_TRADES = 10
MAX_DRAWDOWN = 0.15           # 15%


@dataclass
class StrategyRecord:
    """Performance record for a single strategy."""
    name: str
    asset: str
    timeframe: str = "1h"
    status: str = "testing"  # testing, active, disabled, promoted, rejected

    # Backtest metrics
    backtest_return: float = 0.0
    backtest_sharpe: float = 0.0
    backtest_drawdown: float = 0.0
    backtest_num_trades: int = 0
    backtest_lookahead_clean: bool = False

    # Live paper metrics
    live_trades: int = 0
    live_wins: int = 0
    live_losses: int = 0
    live_total_pnl: float = 0.0
    live_avg_win: float = 0.0
    live_avg_loss: float = 0.0
    live_profit_factor: float = 0.0
    live_win_rate: float = 0.0
    live_max_drawdown: float = 0.0
    live_expected_value: float = 0.0

    # Regime performance
    regime_uptrend_pnl: float = 0.0
    regime_downtrend_pnl: float = 0.0
    regime_ranging_pnl: float = 0.0

    # Metadata
    first_trade_time: Optional[str] = None
    last_trade_time: Optional[str] = None
    rejection_reason: Optional[str] = None
    promotion_reason: Optional[str] = None

    @property
    def live_win_loss_ratio(self) -> float:
        if self.live_avg_loss != 0:
            return abs(self.live_avg_win / self.live_avg_loss)
        return float('inf') if self.live_avg_win > 0 else 0.0

    @property
    def is_eligible(self) -> bool:
        """Check if strategy meets minimum criteria for live trading."""
        if self.status in ("disabled", "rejected"):
            return False
        if self.backtest_return < MIN_BACKTEST_RETURN:
            return False
        if self.backtest_sharpe < MIN_SHARPE:
            return False
        if self.backtest_drawdown > MAX_DRAWDOWN:
            return False
        if self.backtest_num_trades < MIN_TRADES:
            return False
        if not self.backtest_lookahead_clean:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["live_win_loss_ratio"] = self.live_win_loss_ratio
        d["is_eligible"] = self.is_eligible
        return d

    @classmethod
    def from_dict(cls, d: Dict) -> "StrategyRecord":
        # Remove computed fields
        d.pop("live_win_loss_ratio", None)
        d.pop("is_eligible", None)
        return cls(**d)


class StrategyLeaderboard:
    """Central registry for strategy performance tracking and filtering."""

    def __init__(self, file_path: Path = LEADERBOARD_FILE):
        self.file_path = file_path
        self.strategies: Dict[str, StrategyRecord] = {}
        self._load()

    def _load(self):
        if self.file_path.exists():
            try:
                with open(self.file_path) as f:
                    data = json.load(f)
                for key, record in data.get("strategies", {}).items():
                    self.strategies[key] = StrategyRecord.from_dict(record)
            except (json.JSONDecodeError, IOError):
                pass

    def _save(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "strategies": {k: v.to_dict() for k, v in self.strategies.items()},
        }
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _make_key(self, name: str, asset: str, timeframe: str = "1h") -> str:
        return f"{name}::{asset}::{timeframe}"

    def register_backtest(
        self,
        name: str,
        asset: str,
        timeframe: str,
        total_return: float,
        sharpe: float,
        max_drawdown: float,
        num_trades: int,
        lookahead_clean: bool = True,
    ):
        """Register or update backtest results for a strategy."""
        key = self._make_key(name, asset, timeframe)
        if key not in self.strategies:
            self.strategies[key] = StrategyRecord(
                name=name, asset=asset, timeframe=timeframe, status="testing"
            )

        record = self.strategies[key]
        record.backtest_return = total_return
        record.backtest_sharpe = sharpe
        record.backtest_drawdown = max_drawdown
        record.backtest_num_trades = num_trades
        record.backtest_lookahead_clean = lookahead_clean

        # Auto-evaluate status
        self._evaluate_status(key)
        self._save()

    def record_live_trade(
        self,
        name: str,
        asset: str,
        pnl: float,
        regime: str = "unknown",
    ):
        """Record a completed live paper trade."""
        key = self._make_key(name, asset)
        if key not in self.strategies:
            self.strategies[key] = StrategyRecord(
                name=name, asset=asset, status="testing"
            )

        record = self.strategies[key]
        record.live_trades += 1
        record.live_total_pnl += pnl

        if pnl > 0:
            record.live_wins += 1
        else:
            record.live_losses += 1

        # Recalculate averages
        wins = [0]  # We don't store individual trades, just counts
        # For proper avg_win/avg_loss we need individual trade data
        # Simplified: use running average approximation
        if pnl > 0:
            if record.live_wins == 1:
                record.live_avg_win = pnl
            else:
                record.live_avg_win = (
                    record.live_avg_win * (record.live_wins - 1) + pnl
                ) / record.live_wins
        else:
            if record.live_losses == 1:
                record.live_avg_loss = pnl
            else:
                record.live_avg_loss = (
                    record.live_avg_loss * (record.live_losses - 1) + pnl
                ) / record.live_losses

        # Profit factor
        total_wins = record.live_wins * record.live_avg_win if record.live_wins > 0 else 0
        total_losses = abs(record.live_losses * record.live_avg_loss) if record.live_losses > 0 else 0.0001
        record.live_profit_factor = total_wins / total_losses

        # Win rate
        record.live_win_rate = record.live_wins / record.live_trades if record.live_trades > 0 else 0

        # Expected value
        wr = record.live_win_rate
        record.live_expected_value = (wr * record.live_avg_win) - ((1 - wr) * abs(record.live_avg_loss))

        # Regime tracking
        if regime == "uptrend":
            record.regime_uptrend_pnl += pnl
        elif regime == "downtrend":
            record.regime_downtrend_pnl += pnl
        elif regime == "ranging":
            record.regime_ranging_pnl += pnl

        now = datetime.now(timezone.utc).isoformat()
        if record.first_trade_time is None:
            record.first_trade_time = now
        record.last_trade_time = now

        # Auto-evaluate
        self._evaluate_status(key)
        self._save()

    def _evaluate_status(self, key: str):
        """Auto-promote or reject based on performance."""
        record = self.strategies[key]

        # If backtest is bad, reject immediately
        if record.backtest_return < 0:
            record.status = "rejected"
            record.rejection_reason = f"Backtest negative: {record.backtest_return:.2%}"
            return

        if not record.backtest_lookahead_clean:
            record.status = "rejected"
            record.rejection_reason = "Lookahead bias detected"
            return

        # Check live performance if we have enough data
        if record.live_trades >= 5:
            if record.live_win_rate < 0.3:
                record.status = "disabled"
                record.rejection_reason = f"Live win rate too low: {record.live_win_rate:.1%}"
                return
            if record.live_expected_value < 0:
                record.status = "disabled"
                record.rejection_reason = f"Negative expected value: ${record.live_expected_value:.2f}"
                return

        # Promote if eligible
        if record.is_eligible:
            if record.status == "testing":
                record.status = "active"
                record.promotion_reason = (
                    f"Backtest: {record.backtest_return:.2%} return, "
                    f"Sharpe {record.backtest_sharpe:.2f}, "
                    f"{record.backtest_num_trades} trades"
                )

    def get_active_strategies(self, asset: Optional[str] = None) -> List[StrategyRecord]:
        """Get all strategies eligible for live trading."""
        active = [
            r for r in self.strategies.values()
            if r.status == "active" and r.is_eligible
        ]
        if asset:
            active = [r for r in active if r.asset == asset]
        # Sort by live expected value, then backtest return
        active.sort(key=lambda r: (
            r.live_expected_value if r.live_trades >= 3 else r.backtest_return,
            r.backtest_sharpe,
        ), reverse=True)
        return active

    def get_top_strategy(self, asset: str) -> Optional[StrategyRecord]:
        """Get the best strategy for a given asset."""
        active = self.get_active_strategies(asset)
        return active[0] if active else None

    def disable_strategy(self, name: str, asset: str, reason: str):
        """Manually disable a strategy."""
        key = self._make_key(name, asset)
        if key in self.strategies:
            self.strategies[key].status = "disabled"
            self.strategies[key].rejection_reason = reason
            self._save()

    def get_leaderboard(self) -> Dict:
        """Get full leaderboard for reporting."""
        return {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "filters": {
                "min_backtest_return": MIN_BACKTEST_RETURN,
                "min_sharpe": MIN_SHARPE,
                "min_profit_factor": MIN_PROFIT_FACTOR,
                "min_trades": MIN_TRADES,
                "max_drawdown": MAX_DRAWDOWN,
            },
            "active": [r.to_dict() for r in self.get_active_strategies()],
            "testing": [
                r.to_dict() for r in self.strategies.values()
                if r.status == "testing"
            ],
            "disabled": [
                r.to_dict() for r in self.strategies.values()
                if r.status == "disabled"
            ],
            "rejected": [
                r.to_dict() for r in self.strategies.values()
                if r.status == "rejected"
            ],
        }

    def generate_report(self) -> str:
        """Generate CEO-ready strategy leaderboard report."""
        board = self.get_leaderboard()
        lines = [
            "=" * 70,
            "STRATEGY LEADERBOARD",
            f"Updated: {board['last_updated'][:19]} UTC",
            "=" * 70,
            "",
            f"Minimum filters: Return >{MIN_BACKTEST_RETURN:.0%}, Sharpe >{MIN_SHARPE:.1f}, "
            f"Trades >={MIN_TRADES}, Drawdown <{MAX_DRAWDOWN:.0%}",
            "",
            f"ACTIVE STRATEGIES: {len(board['active'])}",
        ]

        for i, s in enumerate(board["active"][:10], 1):
            live_ev = s.get("live_expected_value", 0)
            live_trades = s.get("live_trades", 0)
            ev_str = f"EV=${live_ev:.2f}" if live_trades >= 3 else "No live data"
            lines.append(
                f"  {i}. {s['name']} ({s['asset']}): "
                f"backtest={s['backtest_return']:.2%}, "
                f"sharpe={s['backtest_sharpe']:.2f}, "
                f"live={live_trades} trades, "
                f"wr={s.get('live_win_rate', 0):.0%}, "
                f"{ev_str}"
            )

        if not board["active"]:
            lines.append("  (No active strategies meet filters)")

        lines.extend([
            "",
            f"TESTING: {len(board['testing'])}",
            f"DISABLED: {len(board['disabled'])}",
            f"REJECTED: {len(board['rejected'])}",
            "",
            "=" * 70,
        ])

        return "\n".join(lines)


# Singleton instance
_leaderboard: Optional[StrategyLeaderboard] = None


def get_leaderboard() -> StrategyLeaderboard:
    global _leaderboard
    if _leaderboard is None:
        _leaderboard = StrategyLeaderboard()
    return _leaderboard


if __name__ == "__main__":
    lb = get_leaderboard()
    print(lb.generate_report())
