"""Tests for StrategyLeaderboard."""
import pytest
import json
from pathlib import Path
from datetime import datetime, timezone
import sys
sys.path.insert(0, 'src')

from strategy_leaderboard import StrategyLeaderboard, StrategyRecord, MIN_BACKTEST_RETURN, MIN_SHARPE


class TestStrategyLeaderboard:

    def test_register_backtest_creates_record(self, tmp_path):
        lb = StrategyLeaderboard(file_path=tmp_path / "lb.json")
        lb.register_backtest(
            name="rsi_range",
            asset="BTCUSD",
            timeframe="1h",
            total_return=0.12,
            sharpe=3.5,
            max_drawdown=0.08,
            num_trades=25,
            lookahead_clean=True,
        )
        key = "rsi_range::BTCUSD::1h"
        assert key in lb.strategies
        assert lb.strategies[key].backtest_return == 0.12
        assert lb.strategies[key].status == "active"

    def test_negative_backtest_gets_rejected(self, tmp_path):
        lb = StrategyLeaderboard(file_path=tmp_path / "lb.json")
        lb.register_backtest(
            name="ma_crossover",
            asset="BTCUSD",
            timeframe="1h",
            total_return=-0.03,
            sharpe=-2.0,
            max_drawdown=0.20,
            num_trades=15,
            lookahead_clean=True,
        )
        key = "ma_crossover::BTCUSD::1h"
        assert lb.strategies[key].status == "rejected"
        assert "negative" in lb.strategies[key].rejection_reason.lower()

    def test_low_sharpe_gets_rejected(self, tmp_path):
        lb = StrategyLeaderboard(file_path=tmp_path / "lb.json")
        lb.register_backtest(
            name="low_sharpe",
            asset="BTCUSD",
            timeframe="1h",
            total_return=0.06,
            sharpe=1.0,  # Below MIN_SHARPE=2.0
            max_drawdown=0.05,
            num_trades=20,
            lookahead_clean=True,
        )
        key = "low_sharpe::BTCUSD::1h"
        # Status stays testing because is_eligible is False but not explicitly rejected
        assert not lb.strategies[key].is_eligible

    def test_lookahead_bias_gets_rejected(self, tmp_path):
        lb = StrategyLeaderboard(file_path=tmp_path / "lb.json")
        lb.register_backtest(
            name="cheating",
            asset="BTCUSD",
            timeframe="1h",
            total_return=0.50,
            sharpe=10.0,
            max_drawdown=0.02,
            num_trades=100,
            lookahead_clean=False,
        )
        key = "cheating::BTCUSD::1h"
        assert lb.strategies[key].status == "rejected"
        assert "lookahead" in lb.strategies[key].rejection_reason.lower()

    def test_live_trade_updates_stats(self, tmp_path):
        lb = StrategyLeaderboard(file_path=tmp_path / "lb.json")
        lb.register_backtest(
            name="rsi_range",
            asset="BTCUSD",
            timeframe="1h",
            total_return=0.12,
            sharpe=3.5,
            max_drawdown=0.08,
            num_trades=25,
            lookahead_clean=True,
        )
        lb.record_live_trade("rsi_range", "BTCUSD", pnl=5.0, regime="uptrend")
        lb.record_live_trade("rsi_range", "BTCUSD", pnl=-2.0, regime="uptrend")
        lb.record_live_trade("rsi_range", "BTCUSD", pnl=3.0, regime="uptrend")

        key = "rsi_range::BTCUSD::1h"
        record = lb.strategies[key]
        assert record.live_trades == 3
        assert record.live_wins == 2
        assert record.live_losses == 1
        assert record.live_win_rate == 2/3
        assert record.live_total_pnl == 6.0
        assert record.live_avg_win == 4.0  # (5+3)/2
        assert record.live_avg_loss == -2.0
        assert record.live_profit_factor == (2 * 4.0) / (1 * 2.0)  # 4.0

    def test_get_active_strategies_filters_correctly(self, tmp_path):
        lb = StrategyLeaderboard(file_path=tmp_path / "lb.json")

        # Good strategy
        lb.register_backtest(
            name="good",
            asset="BTCUSD",
            timeframe="1h",
            total_return=0.15,
            sharpe=4.0,
            max_drawdown=0.05,
            num_trades=30,
            lookahead_clean=True,
        )

        # Bad strategy (negative return)
        lb.register_backtest(
            name="bad",
            asset="BTCUSD",
            timeframe="1h",
            total_return=-0.05,
            sharpe=1.0,
            max_drawdown=0.20,
            num_trades=15,
            lookahead_clean=True,
        )

        active = lb.get_active_strategies()
        assert len(active) == 1
        assert active[0].name == "good"

    def test_top_strategy_returns_best(self, tmp_path):
        lb = StrategyLeaderboard(file_path=tmp_path / "lb.json")
        lb.register_backtest(
            name="better",
            asset="BTCUSD",
            timeframe="1h",
            total_return=0.20,
            sharpe=5.0,
            max_drawdown=0.03,
            num_trades=40,
            lookahead_clean=True,
        )
        lb.register_backtest(
            name="worse",
            asset="BTCUSD",
            timeframe="1h",
            total_return=0.10,
            sharpe=3.0,
            max_drawdown=0.08,
            num_trades=25,
            lookahead_clean=True,
        )
        top = lb.get_top_strategy("BTCUSD")
        assert top.name == "better"

    def test_disable_strategy(self, tmp_path):
        lb = StrategyLeaderboard(file_path=tmp_path / "lb.json")
        lb.register_backtest(
            name="test",
            asset="BTCUSD",
            timeframe="1h",
            total_return=0.15,
            sharpe=4.0,
            max_drawdown=0.05,
            num_trades=30,
            lookahead_clean=True,
        )
        lb.disable_strategy("test", "BTCUSD", "CEO directive")
        assert lb.strategies["test::BTCUSD::1h"].status == "disabled"
        assert lb.strategies["test::BTCUSD::1h"].rejection_reason == "CEO directive"

    def test_generate_report_format(self, tmp_path):
        lb = StrategyLeaderboard(file_path=tmp_path / "lb.json")
        lb.register_backtest(
            name="rsi_range",
            asset="BTCUSD",
            timeframe="1h",
            total_return=0.12,
            sharpe=3.5,
            max_drawdown=0.08,
            num_trades=25,
            lookahead_clean=True,
        )
        report = lb.generate_report()
        assert "STRATEGY LEADERBOARD" in report
        assert "rsi_range" in report
        assert "12.00%" in report or "0.12" in report
        assert "ACTIVE STRATEGIES: 1" in report
