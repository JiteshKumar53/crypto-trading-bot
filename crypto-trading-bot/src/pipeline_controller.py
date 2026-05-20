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
        
        # Initialize Live Chart Monitor (Market Intelligence)
        self.chart_monitor = LiveChartMonitor()
        logger.info("[PipelineController] LiveChartMonitor initialized")
        
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
        cycle_start = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        results = {
            "cycle_start": cycle_start,
            "symbol": symbol,
            "stages": {},
            "success": False,
            "errors": [],
        }

        # Determine which assets to process
        symbols = [symbol] if symbol else self.assets

        # STAGE 0: PRE-CYCLE MEMORY AND EVOLUTION REVIEW (MANDATORY)
        # Gene: GENE-009, GENE-010 | Capsule: CAPSULE-005
        # This MUST run before any trading decision
        try:
            from pre_cycle_review import run_pre_cycle_review
            review = run_pre_cycle_review()
            results["pre_cycle_review"] = review
            
            if not review.get("trading_allowed", True):
                logger.critical("[STAGE 0] PRE-CYCLE REVIEW BLOCKED TRADING")
                results["success"] = False
                results["blocked_reason"] = "Pre-cycle review found critical issues"
                return results
            else:
                logger.info(f"[STAGE 0] Pre-cycle review passed: {review.get('issue_count', 0)} warnings")
        except Exception as e:
            logger.critical(f"[STAGE 0] PRE-CYCLE REVIEW FAILED: {e}")
            results["success"] = False
            results["blocked_reason"] = f"Pre-cycle review failed: {e}"
            return results
        
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

        # Stage 1.5: Live Chart Monitor (Market Intelligence)
        chart_obs = None
        try:
            logger.info(f"[Stage 1.5] Running Live Chart Monitor for {symbol}")
            from chart_monitor.data_sources.base import Candle
            
            # Convert DataFrame to Candle objects
            chart_candles = []
            for idx, row in data.iterrows():
                ts = idx[1] if isinstance(idx, tuple) else idx
                chart_candles.append(Candle(
                    timestamp=ts,
                    open=row["open"],
                    high=row["high"],
                    low=row["low"],
                    close=row["close"],
                    volume=row["volume"],
                    symbol=symbol,
                    timeframe="1h",
                ))
            
            # Get current position for context-aware analysis
            positions = self.alpaca.get_positions()
            current_pos = next((p for p in positions if p["symbol"] == symbol.replace("/", "")), None)
            position_context = None
            if current_pos:
                position_context = {
                    "side": "long",
                    "entry_price": float(current_pos["avg_entry_price"]),
                    "qty": float(current_pos["qty"]),
                }
            
            # Run chart analysis
            chart_obs = self.chart_monitor.analyzer.analyze(
                chart_candles, symbol, "1h", position_context
            )
            
            result["stages"]["chart_monitor"] = {
                "trend": chart_obs.trend_state.value if chart_obs.trend_state else "unknown",
                "volatility": chart_obs.volatility_state.value if chart_obs.volatility_state else "unknown",
                "momentum": chart_obs.momentum_status.value if chart_obs.momentum_status else "unknown",
                "rsi": round(chart_obs.rsi_value, 1) if chart_obs.rsi_value else None,
                "support": round(chart_obs.nearest_support, 2) if chart_obs.nearest_support else None,
                "resistance": round(chart_obs.nearest_resistance, 2) if chart_obs.nearest_resistance else None,
                "breakout": chart_obs.breakout_detected,
                "breakdown": chart_obs.breakdown_detected,
                "reversal": chart_obs.reversal_warning,
                "reversal_type": chart_obs.reversal_type,
                "confidence": round(chart_obs.confidence, 2),
                "recommendation": chart_obs.recommended_review_action,
                "reason": chart_obs.reason,
                "risk_warning": chart_obs.risk_warning,
                "position_affected": chart_obs.open_position_affected,
                "position_pnl_pct": round(chart_obs.position_pnl_pct, 2) if chart_obs.position_pnl_pct else None,
                "status": "success",
            }
            
            rsi_str = f"{float(chart_obs.rsi_value):.1f}" if chart_obs.rsi_value is not None else 'N/A'
            logger.info(
                f"[ChartMonitor] {symbol}: trend={chart_obs.trend_state.value}, "
                f"RSI={rsi_str}, "
                f"action={chart_obs.recommended_review_action}, "
                f"confidence={float(chart_obs.confidence):.0%}"
            )
            
        except Exception as e:
            logger.warning(f"[ChartMonitor] Analysis failed for {symbol}: {e}")
            result["stages"]["chart_monitor"] = {
                "status": "failed",
                "error": str(e),
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

        # Stage 3.5: STRATEGY VALIDATION GATE (CRITICAL — prevents unvalidated strategies)
        # Gene: GENE-001, GENE-002 | Capsule: CAPSULE-001
        from strategy_validation_gate import validate_strategy_for_pipeline, get_strategy_constraints
        
        # Get strategy name from backtest or agent recommendation
        strategy_name = result["stages"]["backtest"].get("strategy_name", "unknown")
        if strategy_name == "unknown" and self.use_agents:
            strategy_name = result["stages"]["agents"].get("recommended_strategy", "unknown")
        
        # Validate strategy against leaderboard
        validation_error = validate_strategy_for_pipeline(strategy_name, symbol)
        
        if validation_error:
            logger.critical(f"[STAGE 3.5] STRATEGY VALIDATION GATE BLOCKED: {validation_error}")
            result["stages"]["strategy_validation"] = {
                "status": "blocked",
                "approved": False,
                "reason": validation_error,
                "strategy_name": strategy_name,
            }
            result["approved"] = False
            return result
        else:
            constraints = get_strategy_constraints(strategy_name, symbol)
            logger.info(f"[STAGE 3.5] Strategy validation PASSED: {strategy_name} — constraints: {constraints}")
            result["stages"]["strategy_validation"] = {
                "status": "approved",
                "approved": True,
                "strategy_name": strategy_name,
                "constraints": constraints,
            }
            
            # Apply testing-mode constraints
            if constraints.get("max_position_size"):
                order_value = min(order_value, constraints["max_position_size"])
                qty = order_value / current_price
                logger.info(f"[STAGE 3.5] Testing mode: order size limited to ${order_value:.2f}")
        
        # Stage 4: Risk Governor check
        if self.use_risk_governor:
            logger.info(f"[Stage 4] Running Risk Governor for {symbol}")

            # Get account info
            account = self.alpaca.get_account()
            portfolio_value = account["portfolio_value"] if account else 10000
            positions = self.alpaca.get_positions()
            current_pos = next((p for p in positions if p["symbol"] == symbol.replace("/", "")), None)
            current_position_value = current_pos["market_value"] if current_pos else 0

            # Determine order size (50/50 capital rule aware)
            # Conservative: 10% of equity per trade when 5 positions max
            order_value = portfolio_value * 0.05  # 5% default, will be adjusted by risk governor
            qty = order_value / current_price

            # Calculate total crypto exposure from all positions
            total_crypto_exposure = sum(
                float(p["market_value"]) for p in positions
            ) if positions else 0.0
            self.risk_governor.state["total_crypto_exposure_usd"] = total_crypto_exposure
            logger.info(f"Total crypto exposure: ${total_crypto_exposure:.2f} / ${portfolio_value:.2f} ({(total_crypto_exposure/portfolio_value)*100:.1f}%)")

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

        # Stage 5: Orchestrator decision (BUY or SELL based on signal)
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
            
            # Add Live Chart Monitor observation to recommendations
            if chart_obs:
                chart_warnings = []
                if chart_obs.breakout_detected:
                    chart_warnings.append(f"Breakout detected above ${float(chart_obs.nearest_resistance):,.2f}")
                if chart_obs.breakdown_detected:
                    chart_warnings.append(f"Breakdown detected below ${float(chart_obs.nearest_support):,.2f}")
                if chart_obs.reversal_warning:
                    chart_warnings.append(f"Reversal warning: {chart_obs.reversal_type}")
                if chart_obs.momentum_status.value in ["strong_bullish", "strong_bearish"]:
                    chart_warnings.append(f"Momentum: {chart_obs.momentum_status.value} (RSI: {float(chart_obs.rsi_value):.1f})")
                if chart_obs.volume_anomaly:
                    chart_warnings.append(f"Volume anomaly: {float(chart_obs.volume_vs_avg):.1f}x average")
                if chart_obs.open_position_affected and chart_obs.position_pnl_pct is not None:
                    chart_warnings.append(f"Position PnL: {float(chart_obs.position_pnl_pct):+.2f}%")
                
                recommendations.append({
                    "agent": "LiveChartMonitor",
                    "warnings": "; ".join(chart_warnings) if chart_warnings else chart_obs.reason,
                })
                
                logger.info(f"[Pipeline] Chart observations added to recommendations for {symbol}")
            
            # Determine side from agent consensus
            thesis_rec = agent_results["thesis"].recommendation.lower()
            if "sell" in thesis_rec or "exit" in thesis_rec or "short" in thesis_rec:
                side = "sell"
            elif "buy" in thesis_rec or "long" in thesis_rec:
                side = "buy"
            else:
                side = "buy"  # Default if agents say WAIT/HOLD
        else:
            # Provide placeholder recommendations when agents disabled
            recommendations = [
                {"agent": "Candles (disabled)", "warnings": "Agent recommendations disabled in config"},
                {"agent": "Ledger (disabled)", "warnings": "Agent recommendations disabled in config"},
                {"agent": "Pulse (disabled)", "warnings": "Agent recommendations disabled in config"},
                {"agent": "Shield (disabled)", "warnings": "Agent recommendations disabled in config"},
                {"agent": "Compass (disabled)", "warnings": "Agent recommendations disabled in config"},
            ]
            side = "buy"  # Default when agents disabled

        # If we have a position and agents say SELL, evaluate sell opportunity
        if side == "sell" and current_position_value > 0:
            logger.info(f"[Stage 5] Sell signal detected for {symbol} with open position")
        elif side == "sell" and current_position_value == 0:
            logger.info(f"[Stage 5] Sell signal for {symbol} but no position — skipping")
            side = "buy"  # Can't sell what we don't have

        # Determine if backtest passed
        backtest_passed = True
        if backtest_result and backtest_result.get("max_drawdown", 0) > 0.05:  # >5% drawdown
            backtest_passed = False
            logger.warning(f"Backtest failed: max drawdown {backtest_result['max_drawdown']:.2%} > 5%")

        orchestrator_result = self.orchestrator.run_pipeline(
            symbol=symbol,
            side=side,
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

        logger.info(f"[Stage 6] Executing paper order for {symbol}: {side} {qty:.6f}")
        order_result = self.alpaca.submit_order(
            symbol=symbol,
            side=side,
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
        """
        Run backtest for ALL implemented strategies and return the best result.
        Includes regime detection and parameter optimization (only on real data).
        A strategy passes if max_drawdown <= 5%.
        """
        from strategy.strategy_engine import (
            SimpleMAStrategy, RSIStrategy, MACDStrategy, BollingerBandsStrategy
        )

        # Detect market regime (only on real data with OHLC columns)
        regime = "unknown"
        has_real_data = hasattr(data, 'columns') and 'close' in data.columns
        if has_real_data:
            try:
                from agents.strategy_research import StrategyResearchAgent
                researcher = StrategyResearchAgent()
                regime = researcher.regime_detect(data)
                logger.info(f"[Backtest] {symbol}: Detected regime = {regime}")
            except Exception as e:
                logger.warning(f"[Backtest] {symbol}: Regime detection failed: {e}")

        strategies = [
            SimpleMAStrategy(symbol, ma_window=20),
            RSIStrategy(symbol, period=14, oversold=30, overbought=70),
            MACDStrategy(symbol, fast=12, slow=26, signal=9),
            BollingerBandsStrategy(symbol, period=20, std_dev=2.0),
        ]

        results = []
        for strategy in strategies:
            def strategy_wrapper(engine, timestamp, prices, data_slice):
                return strategy.on_bar(engine, timestamp, prices, data_slice)

            engine = BacktestEngine(initial_capital=10000)
            result = engine.run(strategy_wrapper, data, symbol)
            result.strategy_name = strategy.name

            results.append({
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
                "passed": result.max_drawdown <= 0.05,
            })

        # Parameter optimization for top 2 strategies (only on real data)
        if has_real_data:
            try:
                from agents.strategy_research import StrategyResearchAgent
                researcher = StrategyResearchAgent()
                param_results = []
                for strat_result in sorted(results, key=lambda r: r["total_return"], reverse=True)[:2]:
                    if "ma_crossover" in strat_result["strategy_name"]:
                        grid = {"ma_window": [10, 15, 20, 30, 50]}
                        param_results.extend(researcher.parameter_optimize("ma_crossover", symbol, data, grid))
                    elif "rsi" in strat_result["strategy_name"]:
                        grid = {"period": [7, 14, 21], "oversold": [20, 30, 40], "overbought": [60, 70, 80]}
                        param_results.extend(researcher.parameter_optimize("rsi", symbol, data, grid))

                if param_results:
                    best_param = param_results[0]
                    logger.info(f"[Backtest] {symbol}: Best optimized params = {best_param['params']}, "
                                f"return={best_param['return']:.2%}, drawdown={best_param['drawdown']:.2%}, "
                                f"passed={best_param['passed']}")
                    # Add optimized version to results
                    results.append({
                        "strategy_name": f"{strat_result['strategy_name']}_optimized",
                        "total_return": best_param["return"],
                        "max_drawdown": best_param["drawdown"],
                        "sharpe_ratio": best_param["sharpe"],
                        "num_trades": best_param["trades"],
                        "passed": best_param["passed"],
                        "annualized_return": 0,
                        "sortino_ratio": 0,
                        "calmar_ratio": 0,
                        "win_rate": 0,
                        "profit_factor": 0,
                        "exposure_time": 0,
                        "worst_day": 0,
                    })
            except Exception as e:
                logger.warning(f"[Backtest] {symbol}: Parameter optimization failed: {e}")

        # Sort by: passed first, then highest return
        results.sort(key=lambda r: (r["passed"], r["total_return"]), reverse=True)
        best = results[0]

        logger.info(f"[Backtest] {symbol}: Regime={regime}, Best={best['strategy_name']}, "
                    f"return={best['total_return']:.2%}, drawdown={best['max_drawdown']:.2%}, "
                    f"passed={best['passed']}")
        for r in results[1:]:
            logger.info(f"[Backtest] {symbol}:   {r['strategy_name']}: "
                        f"return={r['total_return']:.2%}, drawdown={r['max_drawdown']:.2%}, "
                        f"passed={r['passed']}")

        return best

    def get_status(self) -> Dict:
        """Get current system status."""
        account = self.alpaca.get_account()
        positions = self.alpaca.get_positions()
        orders = self.alpaca.get_open_orders()

        return {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "paper_mode": self.alpaca.is_paper(),
            "account": account,
            "positions": positions,
            "open_orders": orders,
            "assets": self.assets,
        }
