"""
Pipeline Controller — End-to-End Trading Pipeline (EA Core Integrated)

CRITICAL ARCHITECTURE:
1. EA Core is the PRIMARY decision engine
2. All order execution flows through EA Core first
3. Old gates (Strategy Validation, Risk Governor) are secondary/backup only
4. If EA Core is not active, ALL new entries are HARD BLOCKED
"""

import os
import sys
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone
import pandas as pd

from broker.alpaca_client import AlpacaPaperClient
from data.data_fetcher import DataFetcher
from agents.agent_runner import AgentRunner
from backtest.backtest_engine import BacktestEngine
from strategy.strategy_engine import Strategy, BuyAndHoldStrategy, SimpleMAStrategy
from risk_governor import RiskGovernor, RiskDecision
from orchestrator import TradingOrchestrator
from memory.decision_log import DecisionLog
from chart_monitor.data_sources.alpaca_source import AlpacaDataSource
from chart_monitor.live_chart_monitor import LiveChartMonitor, ChartObservationReporter

# EA Core Engine — MANDATORY for all order execution
from core.ea_core_engine import EACoreEngine
from core.position_manager import PositionManager
from broker.broker_first_reconciliation import BrokerFirstReconciliation
from strategy_validation_gate import validate_strategy as validate_strategy_gate
from evolver_runtime import check_strategy

logger = logging.getLogger(__name__)


class PipelineController:
    """
    End-to-end trading pipeline controller.
    
    CRITICAL SAFETY ARCHITECTURE:
    - All order execution MUST flow through EA Core Engine FIRST
    - EA Core checks: broker-first, strategy validation, risk governor, duplicate prevention
    - Old execution path is DEPRECATED but retained as fallback only
    - Hard block prevents any order if EA Core is not active
    """

    def __init__(
        self,
        use_agents: bool = False,
        use_backtest: bool = True,
        use_risk_governor: bool = True,
        paper_only: bool = True,
    ):
        self.use_agents = use_agents
        self.use_backtest = use_backtest
        self.use_risk_governor = use_risk_governor
        self.paper_only = paper_only
        
        # Order cooldown: prevent multiple orders for same asset within interval
        self.order_cooldown_seconds = 3600
        self.last_order_time: Dict[str, float] = {}

        # Initialize components
        self.alpaca = AlpacaPaperClient()
        self.data_fetcher = DataFetcher(self.alpaca)
        self.agent_runner = AgentRunner()
        self.risk_governor = RiskGovernor()
        self.orchestrator = TradingOrchestrator(self.risk_governor)
        self.decision_log = DecisionLog()
        
        # EA Core Engine — CRITICAL: All orders MUST flow through here
        try:
            self.position_manager = PositionManager(self.alpaca)
            self.broker_recon = BrokerFirstReconciliation(self.alpaca)
            
            self.ea_core = EACoreEngine(
                alpaca_client=self.alpaca,
                data_fetcher=self.data_fetcher,
                risk_governor=self.risk_governor,
                strategy_validation_gate=check_strategy,
                position_manager=self.position_manager,
                broker_reconciliation=self.broker_recon,
                order_idempotency_guard=self,
            )
            logger.info("[PipelineController] EA Core Engine INITIALIZED")
            self.ea_core_active = True
        except Exception as e:
            logger.critical(f"[PipelineController] EA Core Engine FAILED: {e}")
            self.ea_core = None
            self.ea_core_active = False
            self.position_manager = None
            self.broker_recon = None
        
        # Initialize Live Chart Monitor
        self.chart_monitor = LiveChartMonitor()
        logger.info("[PipelineController] LiveChartMonitor initialized")
        
        # Load assets from config
        import yaml
        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "assets.yaml")
        with open(config_path, "r") as f:
            assets_config = yaml.safe_load(f)
        self.assets = [a["symbol"] for a in assets_config["assets"] if a.get("active", True)]

        logger.info(f"PipelineController initialized")

    def run_cycle(self, symbol: Optional[str] = None) -> Dict:
        """Run a complete trading decision cycle."""
        cycle_start = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        results = {
            "cycle_start": cycle_start,
            "symbol": symbol,
            "stages": {},
            "success": False,
            "errors": [],
        }
        
        # HARD SAFETY BLOCK: EA Core must be active
        if not self.ea_core_active:
            logger.critical("[HARD BLOCK] EA Core is NOT ACTIVE. Trading BLOCKED.")
            return {
                'success': False,
                'blocked_reason': 'CRITICAL_EA_CORE_BYPASS: EA Core not active',
                'ea_core_active': False,
            }
        
        symbols = [symbol] if symbol else self.assets
        
        for sym in symbols:
            logger.info(f"=== Starting cycle for {sym} ===")
            try:
                result = self._run_single_asset(sym)
                results["stages"][sym] = result
                if result.get("approved"):
                    results["success"] = True
            except Exception as e:
                logger.error(f"Cycle failed for {sym}: {e}")
                results["errors"].append(f"{sym}: {e}")
                results["stages"][sym] = {"error": str(e)}
        
        return results

    def _run_single_asset(self, symbol: str) -> Dict:
        """Run pipeline for a single asset with EA Core as primary decision engine."""
        result = {
            "symbol": symbol,
            "approved": False,
            "stages": {},
        }
        
        # Stage 1: Fetch market data
        logger.info(f"[Stage 1] Fetching market data for {symbol}")
        data = self.data_fetcher.fetch_hourly_bars(symbol, limit=168)
        if data is None or data.empty:
            raise ValueError(f"Failed to fetch data for {symbol}")
        
        current_price = self.data_fetcher.get_latest_price(symbol)
        if not current_price:
            raise ValueError(f"Failed to get current price for {symbol}")
        
        result["stages"]["data"] = {
            "bars": len(data),
            "current_price": current_price,
            "status": "success",
        }
        
        # Stage 2: EA Core — PRIMARY DECISION ENGINE
        # All gates checked inside EA Core: broker-first, strategy, risk, duplicate
        logger.info(f"[Stage 2] EA Core: Primary decision check for {symbol}")
        
        ea_result = self.ea_core.run_cycle(symbol)
        
        result["stages"]["ea_core"] = {
            "status": ea_result.get("status", "unknown"),
            "approved": ea_result.get("approved", False),
            "stages": ea_result.get("stages", {}),
            "ea_core_routed": True,
        }
        
        if not ea_result.get("approved", False):
            logger.warning(f"[Stage 2] EA Core BLOCKED order for {symbol}")
            result["approved"] = False
            return result
        
        logger.info(f"[Stage 2] EA Core APPROVED order for {symbol}")
        
        # Extract EA Core constraints for execution
        ea_stages = ea_result.get("stages", {})
        gate_status = ea_stages.get("strategy_validation", {}).get("status", "unknown")
        gate_max_size = ea_stages.get("strategy_validation", {}).get("max_position_size", 500.0)
        
        # Stage 3: Backtest (optional, for signal generation)
        if self.use_backtest:
            logger.info(f"[Stage 3] Running backtest for {symbol}")
            backtest_result = self._run_backtest(symbol, data)
            result["stages"]["backtest"] = {
                "strategy": backtest_result.get("strategy_name", "unknown"),
                "total_return": backtest_result.get("total_return", 0),
                "max_drawdown": backtest_result.get("max_drawdown", 0),
                "sharpe": backtest_result.get("sharpe_ratio", 0),
                "num_trades": backtest_result.get("num_trades", 0),
                "status": "success",
            }
        else:
            result["stages"]["backtest"] = {"status": "skipped"}
        
        # Stage 4: Orchestrator (signal to action conversion)
        logger.info(f"[Stage 4] Running orchestrator for {symbol}")
        
        # Calculate order size
        account = self.alpaca.get_account()
        portfolio_value = account["portfolio_value"] if account else 10000
        positions = self.alpaca.get_positions()
        current_pos = next((p for p in positions if p["symbol"] == symbol.replace("/", "")), None)
        current_position_value = current_pos["market_value"] if current_pos else 0
        
        order_value = portfolio_value * 0.05
        qty = order_value / current_price
        
        # Enforce limits from EA Core
        if gate_status == "active":
            active_limit = gate_max_size
            if order_value > active_limit:
                order_value = min(order_value, active_limit)
                qty = order_value / current_price
                logger.info(f"[Stage 4] ACTIVE limit: ${order_value:.2f} (max ${active_limit})")
        elif gate_status == "testing":
            order_value = min(order_value, 100.0)
            qty = order_value / current_price
            logger.info(f"[Stage 4] TESTING limit: ${order_value:.2f}")
        
        side = "buy"  # EA Core already validated signal direction
        
        orchestrator_result = self.orchestrator.run_pipeline(
            symbol=symbol,
            side=side,
            qty=qty,
            price=current_price,
            portfolio_value=portfolio_value,
            current_position_value=current_position_value,
            recommendations=[],
            strategy_backtest_passed=True,
            qa_passed=True,
        )
        
        result["stages"]["orchestrator"] = {
            "status": orchestrator_result["status"],
            "reason": orchestrator_result.get("reason"),
        }
        
        if orchestrator_result["status"] != "APPROVED":
            logger.warning(f"Orchestrator REJECTED order for {symbol}")
            return result
        
        # Stage 5: Execute paper order (EA Core already approved)
        if self.paper_only and not self.alpaca.is_paper():
            raise ValueError("Paper mode required but not in paper mode!")
        
        # Order cooldown
        import time
        now = time.time()
        last_time = self.last_order_time.get(symbol, 0)
        time_since_last = now - last_time
        if time_since_last < self.order_cooldown_seconds:
            cooldown_remaining = self.order_cooldown_seconds - time_since_last
            logger.warning(f"[Stage 5] COOLDOWN for {symbol}: {cooldown_remaining:.0f}s")
            result["stages"]["execution"] = {
                "status": "cooldown",
                "reason": f"Cooldown: {cooldown_remaining:.0f}s",
            }
            return result
        
        self.last_order_time[symbol] = now
        
        logger.info(f"[Stage 5] Executing paper order for {symbol}: {side} {qty:.6f}")
        
        strategy_limit = None
        if gate_status == "active":
            strategy_limit = gate_max_size
        elif gate_status == "testing":
            strategy_limit = 100.0
        
        order_result = self.alpaca.submit_order(
            symbol=symbol,
            side=side,
            qty=round(qty, 6),
            strategy_limit=strategy_limit,
        )
        
        result["stages"]["execution"] = {
            "status": "success" if order_result.success else "failed",
            "order_id": order_result.order_id,
            "error": order_result.error,
            "ea_core_routed": True,
        }
        
        if order_result.success:
            result["approved"] = True
            logger.info(f"Paper order executed: {order_result.order_id}")
        else:
            logger.error(f"Order execution failed: {order_result.error}")
        
        return result

    def _run_backtest(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Run backtest for best strategy."""
        from strategy.strategy_engine import (
            SimpleMAStrategy, RSIStrategy, MACDStrategy, BollingerBandsStrategy
        )
        
        # Use Grid Trading if available, else fallback
        try:
            from strategies.grid_trading_strategy import GridTradingStrategy
            strategies = [GridTradingStrategy(symbol)]
        except ImportError:
            strategies = [
                SimpleMAStrategy(symbol, ma_window=20),
                RSIStrategy(symbol),
                MACDStrategy(symbol),
                BollingerBandsStrategy(symbol),
            ]
        
        best_result = None
        best_return = float('-inf')
        
        for strategy in strategies:
            try:
                engine = BacktestEngine(strategy, symbol)
                result = engine.run(data)
                if result.get("total_return", 0) > best_return:
                    best_return = result.get("total_return", 0)
                    best_result = result
            except Exception as e:
                logger.warning(f"Backtest failed for {strategy.get_name()}: {e}")
        
        if best_result is None:
            return {"strategy_name": "none", "total_return": 0, "max_drawdown": 0, "sharpe_ratio": 0, "num_trades": 0}
        
        return best_result
