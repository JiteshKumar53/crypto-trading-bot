"""
Pipeline Controller — End-to-End Trading Pipeline
Agent: Jarvis (Junior CEO)

Connects all modules:
1. Fetch market data
2. Run agent recommendations (if enabled)
3. Run thesis synthesis
4. Convert thesis to strategy
5. Run backtest validation
6. Pass through Risk Governor
7. Execute paper order (if approved)
8. Log decision and update memory
"""

import os
import sys
import logging
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

from broker.alpaca_client import AlpacaPaperClient
from data.data_fetcher import DataFetcher
from agents.agent_runner import AgentRunner
from backtest.backtest_engine import BacktestEngine
from strategy.strategy_engine import Strategy, BuyAndHoldStrategy, SimpleMAStrategy
from risk_governor import RiskGovernor, RiskDecision
from orchestrator import TradingOrchestrator
from memory.decision_log import DecisionLog

logger = logging.getLogger(__name__)


class PipelineController:
    """
    End-to-end trading pipeline controller.
    Coordinates all modules for a single trading decision cycle.
    """

    def __init__(
        self,
        use_agents: bool = False,  # Default False due to Ollama latency
        use_backtest: bool = True,
        use_risk_governor: bool = True,
        paper_only: bool = True,
    ):
        self.use_agents = use_agents
        self.use_backtest = use_backtest
        self.use_risk_governor = use_risk_governor
        self.paper_only = paper_only

        # Initialize components
        self.alpaca = AlpacaPaperClient()
        self.data_fetcher = DataFetcher(self.alpaca)
        self.agent_runner = AgentRunner()
        self.risk_governor = RiskGovernor()
        self.orchestrator = TradingOrchestrator(self.risk_governor)
        self.decision_log = DecisionLog()

        # Load assets from config
        import yaml
        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "assets.yaml")
        with open(config_path, "r") as f:
            assets_config = yaml.safe_load(f)
        self.assets = [a["symbol"] for a in assets_config["assets"] if a.get("active", True)]

        logger.info(f"PipelineController initialized")
        logger.info(f"Assets: {self.assets}")
        logger.info(f"Use agents: {use_agents}")
        logger.info(f"Use backtest: {use_backtest}")
        logger.info(f"Use risk governor: {use_risk_governor}")
        logger.info(f"Paper only: {paper_only}")

    def run_cycle(self, symbol: Optional[str] = None) -> Dict:
        """
        Run a complete trading decision cycle.

        Args:
            symbol: Specific symbol to trade, or None to cycle through all assets

        Returns:
            Dict with full cycle results
        """
        cycle_start = datetime.utcnow().isoformat() + "Z"
        results = {
            "cycle_start": cycle_start,
            "symbol": symbol,
            "stages": {},
            "success": False,
            "errors": [],
        }

        # Determine which assets to process
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
        """Run pipeline for a single asset."""
        result = {
            "symbol": symbol,
            "approved": False,
            "stages": {},
        }

        # Stage 1: Fetch market data
        logger.info(f"[Stage 1] Fetching market data for {symbol}")
        data = self.data_fetcher.fetch_hourly_bars(symbol, limit=168)  # 1 week
        if data is None or data.empty:
            raise ValueError(f"Failed to fetch data for {symbol}")

        current_price = self.data_fetcher.get_latest_price(symbol)
        if not current_price:
            raise ValueError(f"Failed to get current price for {symbol}")

        logger.info(f"Current price for {symbol}: ${current_price:,.2f}")
        result["stages"]["data"] = {
            "bars": len(data),
            "current_price": current_price,
            "status": "success",
        }

        # Stage 2: Run agents (if enabled)
        agent_results = None
        if self.use_agents:
            logger.info(f"[Stage 2] Running agent recommendations for {symbol}")
            agent_results = self.agent_runner.run_pipeline(
                asset=symbol,
                current_price=current_price,
                portfolio_value=10000,
                current_position_value=0,
            )
            result["stages"]["agents"] = {
                "all_succeeded": agent_results["all_agents_succeeded"],
                "errors": agent_results["errors"],
                "status": "success" if agent_results["all_agents_succeeded"] else "partial",
            }
        else:
            logger.info(f"[Stage 2] Agent recommendations SKIPPED (use_agents=False)")
            result["stages"]["agents"] = {
                "status": "skipped",
                "reason": "use_agents=False",
            }

        # Stage 3: Run backtest (if enabled)
        backtest_result = None
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
            logger.info(f"[Stage 3] Backtest SKIPPED (use_backtest=False)")
            result["stages"]["backtest"] = {
                "status": "skipped",
                "reason": "use_backtest=False",
            }

        # Stage 4: Risk Governor check
        if self.use_risk_governor:
            logger.info(f"[Stage 4] Running Risk Governor for {symbol}")

            # Get account info
            account = self.alpaca.get_account()
            portfolio_value = account["portfolio_value"] if account else 10000
            positions = self.alpaca.get_positions()
            current_pos = next((p for p in positions if p["symbol"] == symbol.replace("/", "")), None)
            current_position_value = current_pos["market_value"] if current_pos else 0

            # Determine order size (conservative: 5% of portfolio per trade)
            order_value = portfolio_value * 0.05
            qty = order_value / current_price

            risk_result = self.risk_governor.check_order(
                symbol=symbol,
                side="buy",
                qty=qty,
                price=current_price,
                portfolio_value=portfolio_value,
                current_position_value=current_position_value,
            )

            result["stages"]["risk_governor"] = {
                "decision": risk_result.decision.value,
                "approved": risk_result.decision == RiskDecision.ALLOW,
                "checks": [{"name": c.name, "passed": c.passed, "reason": c.reason} for c in risk_result.checks],
                "status": "success",
            }

            if risk_result.decision != RiskDecision.ALLOW:
                logger.warning(f"Risk Governor BLOCKED order for {symbol}: {risk_result.decision.value}")
                return result
        else:
            logger.info(f"[Stage 4] Risk Governor SKIPPED")
            result["stages"]["risk_governor"] = {
                "status": "skipped",
                "reason": "use_risk_governor=False",
            }

        # Stage 5: Orchestrator decision
        logger.info(f"[Stage 5] Running orchestrator decision for {symbol}")

        # Build recommendations for orchestrator
        recommendations = []
        if agent_results:
            recommendations = [
                {"agent": "Candles", "warnings": agent_results["technical"].warnings},
                {"agent": "Ledger", "warnings": agent_results["fundamental"].warnings},
                {"agent": "Pulse", "warnings": agent_results["sentiment"].warnings},
                {"agent": "Shield", "warnings": agent_results["risk"].warnings},
                {"agent": "Compass", "warnings": agent_results["thesis"].warnings},
            ]
        else:
            # Provide placeholder recommendations when agents disabled
            recommendations = [
                {"agent": "Candles (disabled)", "warnings": "Agent recommendations disabled in config"},
                {"agent": "Ledger (disabled)", "warnings": "Agent recommendations disabled in config"},
                {"agent": "Pulse (disabled)", "warnings": "Agent recommendations disabled in config"},
                {"agent": "Shield (disabled)", "warnings": "Agent recommendations disabled in config"},
                {"agent": "Compass (disabled)", "warnings": "Agent recommendations disabled in config"},
            ]

        # Determine if backtest passed
        backtest_passed = True
        if backtest_result and backtest_result.get("max_drawdown", 0) > 0.05:  # >5% drawdown
            backtest_passed = False
            logger.warning(f"Backtest failed: max drawdown {backtest_result['max_drawdown']:.2%} > 5%")

        orchestrator_result = self.orchestrator.run_pipeline(
            symbol=symbol,
            side="buy",
            qty=qty,
            price=current_price,
            portfolio_value=portfolio_value,
            current_position_value=current_position_value,
            recommendations=recommendations,
            strategy_backtest_passed=backtest_passed,
            qa_passed=True,  # TODO: Implement QA validation
        )

        result["stages"]["orchestrator"] = {
            "status": orchestrator_result["status"],
            "decision_id": orchestrator_result.get("decision_id"),
            "reason": orchestrator_result.get("reason"),
        }

        if orchestrator_result["status"] != "APPROVED":
            logger.warning(f"Orchestrator REJECTED order for {symbol}")
            return result

        # Stage 6: Execute paper order
        if self.paper_only and not self.alpaca.is_paper():
            raise ValueError("Paper mode required but not in paper mode!")

        logger.info(f"[Stage 6] Executing paper order for {symbol}")
        order_result = self.alpaca.submit_order(
            symbol=symbol,
            side="buy",
            qty=round(qty, 6),  # Round to reasonable precision
        )

        result["stages"]["execution"] = {
            "status": "success" if order_result.success else "failed",
            "order_id": order_result.order_id,
            "error": order_result.error,
        }

        if order_result.success:
            result["approved"] = True
            logger.info(f"Paper order executed: {order_result.order_id}")
        else:
            logger.error(f"Order execution failed: {order_result.error}")

        return result

    def _run_backtest(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Run backtest and return simplified result dict."""
        # Use SimpleMAStrategy as the test strategy
        strategy = SimpleMAStrategy(symbol, ma_window=20)

        def strategy_wrapper(engine, timestamp, prices, data_slice):
            return strategy.on_bar(engine, timestamp, prices, data_slice)

        engine = BacktestEngine(initial_capital=10000)
        result = engine.run(strategy_wrapper, data, symbol)
        result.strategy_name = strategy.name

        return {
            "strategy_name": result.strategy_name,
            "total_return": result.total_return,
            "annualized_return": result.annualized_return,
            "sharpe_ratio": result.sharpe_ratio,
            "sortino_ratio": result.sortino_ratio,
            "max_drawdown": result.max_drawdown,
            "calmar_ratio": result.calmar_ratio,
            "win_rate": result.win_rate,
            "profit_factor": result.profit_factor,
            "num_trades": result.num_trades,
            "exposure_time": result.exposure_time,
            "worst_day": result.worst_day,
        }

    def get_status(self) -> Dict:
        """Get current system status."""
        account = self.alpaca.get_account()
        positions = self.alpaca.get_positions()
        orders = self.alpaca.get_open_orders()

        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "paper_mode": self.alpaca.is_paper(),
            "account": account,
            "positions": positions,
            "open_orders": orders,
            "assets": self.assets,
        }
