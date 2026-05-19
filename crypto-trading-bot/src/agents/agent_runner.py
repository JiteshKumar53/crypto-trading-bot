"""
Multi-Agent Recommendation Runner
Agent: Jarvis / COO coordination

Runs all 5 recommendation agents in sequence and produces a unified report.

Sequential execution with tuned model timeouts:
- Technical (kimi-k2.6:cloud): 180s timeout
- Fundamental (deepseek-v4-pro:cloud): 120s timeout
- Sentiment (qwen3.5:cloud): 60s timeout
- Risk (deepseek-v4-pro:cloud): 120s timeout
- Thesis (qwen3.5:cloud): 60s timeout

Note: Parallel execution was tested but caused Ollama GPU contention,
making it slower than sequential. Sequential with tuned timeouts is optimal.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone

from .technical_analysis import TechnicalAnalysisAgent
from .fundamental_analysis import FundamentalAnalysisAgent
from .sentiment_analysis import SentimentAnalysisAgent
from .risk_assessment import RiskAssessmentAgent
from .thesis_synthesis import ThesisSynthesisAgent
from .base_agent import AgentRecommendation

logger = logging.getLogger(__name__)


class AgentRunner:
    """Runs the full 5-agent recommendation pipeline sequentially."""

    def __init__(self, ollama_base_url: str = "http://187.124.18.55:32768"):
        self.technical = TechnicalAnalysisAgent(ollama_base_url)
        self.fundamental = FundamentalAnalysisAgent(ollama_base_url)
        self.sentiment = SentimentAnalysisAgent(ollama_base_url)
        self.risk = RiskAssessmentAgent(ollama_base_url)
        self.thesis = ThesisSynthesisAgent(ollama_base_url)

    def run_pipeline(
        self,
        asset: str,
        current_price: Optional[float] = None,
        recent_data: Optional[str] = None,
        portfolio_value: float = 10000,
        current_position_value: float = 0,
    ) -> Dict:
        """
        Run all 5 agents sequentially and return structured results.

        Returns dict with:
        - asset
        - timestamp
        - technical: AgentRecommendation
        - fundamental: AgentRecommendation
        - sentiment: AgentRecommendation
        - risk: AgentRecommendation
        - thesis: AgentRecommendation
        - errors: list of any errors
        """
        logger.info(f"[AgentRunner] Starting sequential pipeline for {asset}")
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        errors = []

        # Step 1: Technical Analysis
        logger.info("[AgentRunner] Running Technical Analysis (Candles)...")
        try:
            tech = self.technical.run(
                asset=asset,
                current_price=current_price,
                recent_data=recent_data,
            )
        except Exception as e:
            logger.error(f"Technical analysis failed: {e}")
            errors.append(f"Technical: {e}")
            tech = self._error_recommendation("Candles", asset, str(e))

        # Step 2: Fundamental Analysis
        logger.info("[AgentRunner] Running Fundamental Analysis (Ledger)...")
        try:
            fund = self.fundamental.run(asset=asset)
        except Exception as e:
            logger.error(f"Fundamental analysis failed: {e}")
            errors.append(f"Fundamental: {e}")
            fund = self._error_recommendation("Ledger", asset, str(e))

        # Step 3: Sentiment Analysis
        logger.info("[AgentRunner] Running Sentiment Analysis (Pulse)...")
        try:
            sent = self.sentiment.run(asset=asset)
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            errors.append(f"Sentiment: {e}")
            sent = self._error_recommendation("Pulse", asset, str(e))

        # Step 4: Risk Assessment
        logger.info("[AgentRunner] Running Risk Assessment (Shield)...")
        try:
            risk = self.risk.run(
                asset=asset,
                portfolio_value=portfolio_value,
                current_position_value=current_position_value,
            )
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            errors.append(f"Risk: {e}")
            risk = self._error_recommendation("Shield", asset, str(e))

        # Step 5: Thesis Synthesis (uses outputs from steps 1-4)
        logger.info("[AgentRunner] Running Thesis Synthesis (Compass)...")
        try:
            thesis = self.thesis.run(
                asset=asset,
                technical_recommendation=tech.raw_output,
                fundamental_recommendation=fund.raw_output,
                sentiment_recommendation=sent.raw_output,
                risk_recommendation=risk.raw_output,
            )
        except Exception as e:
            logger.error(f"Thesis synthesis failed: {e}")
            errors.append(f"Thesis: {e}")
            thesis = self._error_recommendation("Compass", asset, str(e))

        return {
            "asset": asset,
            "timestamp": timestamp,
            "technical": tech,
            "fundamental": fund,
            "sentiment": sent,
            "risk": risk,
            "thesis": thesis,
            "errors": errors,
            "all_agents_succeeded": len(errors) == 0,
        }

    def _error_recommendation(self, agent_name: str, asset: str, error: str) -> AgentRecommendation:
        return AgentRecommendation(
            agent_name=agent_name,
            asset=asset,
            recommendation="ERROR",
            confidence="Low",
            warnings=error,
            raw_output=f"ERROR: {error}",
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            model_used="N/A",
            cached=False,
        )
