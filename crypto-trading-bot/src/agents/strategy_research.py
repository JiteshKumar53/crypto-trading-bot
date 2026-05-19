"""
Strategy Research Agent
Agent: Researcher
Model: ollama/deepseek-v4-pro:cloud

Continuously researches trading strategies from public sources,
extracts structured rules, and adds them to the strategy library.
"""

import json
import logging
import re
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class StrategyResearchAgent:
    """
    Researches trading strategies from public sources using LLM.
    Extracts structured entry/exit/risk rules.
    Stores in strategy library.
    """

    def __init__(self, ollama_base_url: str = "http://187.124.18.55:32768"):
        self.ollama_url = ollama_base_url
        self.model = "deepseek-v4-pro:cloud"
        self.timeout = 120
        self.name = "Researcher"

    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API with timeout."""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except Exception as e:
            logger.error(f"[{self.name}] Ollama error: {e}")
            return ""

    def research_strategies(
        self,
        market_type: str = "crypto",
        timeframe: str = "hourly",
        regime: str = "any",
        max_results: int = 3,
    ) -> List[Dict]:
        """
        Research proven trading strategies for given market conditions.

        Returns list of strategy dicts with structured rules.
        """
        prompt = f"""You are a quantitative strategy researcher with 20 years of experience.

Your task: Research and extract {max_results} proven trading strategies suitable for {market_type} markets on {timeframe} timeframe, optimized for {regime} market regime.

For each strategy, provide:
1. Strategy name and source (book, paper, famous trader, academic)
2. Complete entry rules (exact conditions)
3. Complete exit rules (exact conditions)
4. Stop-loss rules
5. Take-profit rules
6. Position sizing rules
7. Required indicators and their exact parameters
8. Expected market regime (trending, ranging, volatile)
9. Risk/reward ratio
10. Why this strategy works (market structure explanation)

Format as JSON array:
[
  {{
    "name": "Strategy Name",
    "source": "Source (e.g., 'John Bollinger, Bollinger Bands book')",
    "market_type": "{market_type}",
    "timeframe": "{timeframe}",
    "regime": "trending|ranging|volatile|any",
    "entry_rules": "Exact entry conditions",
    "exit_rules": "Exact exit conditions",
    "stop_loss_rules": "Stop loss placement logic",
    "take_profit_rules": "Take profit placement logic",
    "position_sizing": "How much capital per trade",
    "indicators": ["Indicator1(param1, param2)", "Indicator2(param)"],
    "risk_reward": "1:2 or similar",
    "why_it_works": "Market structure explanation",
    "python_class_name": "SuggestedPythonClassName"
  }}
]

Only include strategies that are:
- Well-documented by established traders/researchers
- Have clear, testable rules
- Do not require look-ahead (no future data)
- Suitable for backtesting

Return ONLY the JSON array. No markdown, no explanation outside JSON."""

        logger.info(f"[{self.name}] Researching {max_results} strategies for {market_type}/{timeframe}/{regime}")
        start = time.time()
        raw = self._call_ollama(prompt)
        elapsed = time.time() - start
        logger.info(f"[{self.name}] Research complete in {elapsed:.1f}s")

        strategies = self._parse_strategies(raw)
        logger.info(f"[{self.name}] Extracted {len(strategies)} strategies")
        return strategies

    def _parse_strategies(self, raw: str) -> List[Dict]:
        """Parse JSON strategy array from LLM output."""
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', raw, re.DOTALL)
        if json_match:
            raw = json_match.group(1)

        # Try direct JSON parse
        try:
            strategies = json.loads(raw)
            if isinstance(strategies, list):
                for s in strategies:
                    s["discovered_at"] = datetime.now(timezone.utc).isoformat()
                    s["discovered_by"] = "Researcher"
                    s["backtested"] = False
                    s["paper_enabled"] = False
                    s["implemented"] = False
                return strategies
        except json.JSONDecodeError:
            pass

        # Fallback: try to extract JSON array more aggressively
        array_match = re.search(r'\[.*\]', raw, re.DOTALL)
        if array_match:
            try:
                strategies = json.loads(array_match.group(0))
                for s in strategies:
                    s["discovered_at"] = datetime.now(timezone.utc).isoformat()
                    s["discovered_by"] = "Researcher"
                    s["backtested"] = False
                    s["paper_enabled"] = False
                    s["implemented"] = False
                return strategies
            except json.JSONDecodeError:
                pass

        logger.warning(f"[{self.name}] Failed to parse strategies from LLM output")
        return []

    def parameter_optimize(
        self,
        strategy_name: str,
        symbol: str,
        data,  # pd.DataFrame
        param_grid: Dict[str, List],
    ) -> List[Dict]:
        """
        Run grid search over strategy parameters.
        Returns sorted list of (params, backtest_result) tuples.
        """
        logger.info(f"[{self.name}] Parameter optimization for {strategy_name} on {symbol}")

        from strategy.strategy_engine import (
            SimpleMAStrategy, RSIStrategy, MACDStrategy, BollingerBandsStrategy
        )
        from backtest.backtest_engine import BacktestEngine

        strategy_map = {
            "ma_crossover": SimpleMAStrategy,
            "rsi": RSIStrategy,
            "macd": MACDStrategy,
            "bollinger_bands": BollingerBandsStrategy,
        }

        strategy_class = strategy_map.get(strategy_name)
        if not strategy_class:
            logger.warning(f"[{self.name}] Unknown strategy: {strategy_name}")
            return []

        results = []
        # Simple grid search for key parameters
        if strategy_name == "ma_crossover" and "ma_window" in param_grid:
            for window in param_grid["ma_window"]:
                strategy = strategy_class(symbol, ma_window=window)

                def wrapper(engine, timestamp, prices, data_slice):
                    return strategy.on_bar(engine, timestamp, prices, data_slice)

                engine = BacktestEngine(initial_capital=10000)
                result = engine.run(wrapper, data, symbol)
                result.strategy_name = f"{strategy.name}_{window}"

                results.append({
                    "params": {"ma_window": window},
                    "return": result.total_return,
                    "drawdown": result.max_drawdown,
                    "sharpe": result.sharpe_ratio,
                    "trades": result.num_trades,
                    "passed": result.max_drawdown <= 0.05,
                })

        elif strategy_name == "rsi" and "period" in param_grid:
            for period in param_grid["period"]:
                for oversold in param_grid.get("oversold", [30]):
                    for overbought in param_grid.get("overbought", [70]):
                        strategy = strategy_class(symbol, period=period, oversold=oversold, overbought=overbought)

                        def wrapper(engine, timestamp, prices, data_slice):
                            return strategy.on_bar(engine, timestamp, prices, data_slice)

                        engine = BacktestEngine(initial_capital=10000)
                        result = engine.run(wrapper, data, symbol)
                        result.strategy_name = f"{strategy.name}_{period}_{oversold}_{overbought}"

                        results.append({
                            "params": {"period": period, "oversold": oversold, "overbought": overbought},
                            "return": result.total_return,
                            "drawdown": result.max_drawdown,
                            "sharpe": result.sharpe_ratio,
                            "trades": result.num_trades,
                            "passed": result.max_drawdown <= 0.05,
                        })

        # Sort by: passed first, then highest return
        results.sort(key=lambda r: (r["passed"], r["return"]), reverse=True)
        return results

    def regime_detect(self, data) -> str:
        """
        Detect current market regime from price data.
        Returns: "trending_up", "trending_down", "ranging", "volatile"
        """
        import numpy as np

        returns = data["close"].pct_change().dropna()
        volatility = returns.std() * np.sqrt(len(returns))  # Rough annualization
        trend = (data["close"].iloc[-1] - data["close"].iloc[0]) / data["close"].iloc[0]

        # ADX-like proxy using rolling ranges
        high_low = (data["high"] - data["low"]).rolling(14).mean()
        adx_proxy = high_low.iloc[-1] / data["close"].iloc[-1] if not high_low.empty else 0

        if abs(trend) > 0.05 and adx_proxy > 0.02:
            return "trending_up" if trend > 0 else "trending_down"
        elif volatility > 0.8:  # High volatility threshold
            return "volatile"
        else:
            return "ranging"
