"""
Investment Thesis + Strategy Synthesis Agent
Agent: Compass
Model: ollama/kimi-k2.6:cloud
"""

import re
import logging
from typing import Dict, Optional, List
from datetime import datetime, timezone

from .base_agent import BaseRecommendationAgent, AgentRecommendation

logger = logging.getLogger(__name__)


class ThesisSynthesisAgent(BaseRecommendationAgent):
    """Synthesizes all recommendations into a unified trading thesis."""

    def __init__(self, ollama_base_url: str = "http://187.124.18.55:32768"):
        # Switched from qwen3.5 (times out on thesis at 90s) to deepseek-v4-pro
        super().__init__("deepseek-v4-pro:cloud", "Compass", ollama_base_url)
        # Thesis synthesis needs more time than standard
        self.timeout = 120

    def build_prompt(self, asset: str, market_data: Optional[Dict] = None, **kwargs) -> str:
        # Collect all 4 agent recommendations
        tech_rec = kwargs.get("technical_recommendation", "N/A")
        fund_rec = kwargs.get("fundamental_recommendation", "N/A")
        sent_rec = kwargs.get("sentiment_recommendation", "N/A")
        risk_rec = kwargs.get("risk_recommendation", "N/A")

        return f"""You are Compass, an Investment Thesis and Strategy Synthesis Agent.

Your task: Synthesize multiple recommendations into one clear trading thesis for {asset}.

INPUT RECOMMENDATIONS:

1. TECHNICAL ANALYSIS (Candles):
{tech_rec}

2. FUNDAMENTAL ANALYSIS (Ledger):
{fund_rec}

3. SENTIMENT ANALYSIS (Pulse):
{sent_rec}

4. RISK ASSESSMENT (Shield):
{risk_rec}

SYNTHESIS INSTRUCTIONS:
- Combine all inputs into a unified thesis
- Create an un-sugarcoated bull case
- Create an un-sugarcoated bear case
- Be honest about conflicting signals
- If signals conflict heavily, recommend WAIT or DO NOT TRADE

Provide your recommendation in the EXACT format below:

INVESTMENT THESIS + STRATEGY SYNTHESIS RECOMMENDATION:
Asset: {asset}
Final recommendation: [BUY | SELL | HOLD | WAIT | EXIT | DO NOT TRADE]
Timeframe: [Intraday | Swing | Position | Long-term]
Summary: [2-3 sentences]
Bull case: [un-sugarcoated]
Bear case: [un-sugarcoated]
Catalyst timeline: [events and dates]
Suggested entry zone: [price range]
Suggested stop-loss: [price]
Suggested profit target 1: [price]
Suggested profit target 2: [price]
Suggested profit target 3: [price]
Suggested position sizing: [% or USD]
Risk/reward: [ratio]
Invalidation conditions: [what kills the thesis]
What would change the thesis: [specific data/events]
Risk recommendation summary: [from Shield]
Backtesting requirement: [what backtest must show]
Confidence by timeframe:
  - Intraday: [High/Medium/Low]
  - Swing: [High/Medium/Low]
  - Position: [High/Medium/Low]
  - Long-term: [High/Medium/Low]
Warnings: [any concerns]
Jarvis decision recommendation: [APPROVE / REJECT / WAIT / ESCALATE]

NEVER execute trades. NEVER write final order instructions.
Thesis must be validated through strategy logic, backtesting, QA, and Risk Governor.
"""

    def parse_output(self, raw_output: str, asset: str) -> AgentRecommendation:
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        recommendation = self._extract_field(raw_output, "Final recommendation")
        confidence = self._extract_field(raw_output, "Confidence")
        if not confidence:
            # Try to extract from confidence by timeframe section
            confidence = self._extract_field(raw_output, "Confidence by timeframe")
        warnings = self._extract_field(raw_output, "Warnings")

        return AgentRecommendation(
            agent_name=self.agent_name,
            asset=asset,
            recommendation=recommendation or "UNKNOWN",
            confidence=confidence or "Low",
            warnings=warnings or "No warnings parsed",
            raw_output=raw_output,
            timestamp=timestamp,
            model_used=self.model,
            cached=False,
        )

    def _extract_field(self, text: str, field_name: str) -> Optional[str]:
        pattern = rf"{re.escape(field_name)}:\s*(.+?)(?=\n\w|$)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return None
