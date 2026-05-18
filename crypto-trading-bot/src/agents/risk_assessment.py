"""
Portfolio Risk + Execution Risk Assessment Agent
Agent: Shield
Model: ollama/deepseek-v4-pro:cloud
"""

import re
import logging
from typing import Dict, Optional
from datetime import datetime

from .base_agent import BaseRecommendationAgent, AgentRecommendation

logger = logging.getLogger(__name__)


class RiskAssessmentAgent(BaseRecommendationAgent):
    """Provides portfolio and execution risk assessment recommendations."""

    def __init__(self, ollama_base_url: str = "http://187.124.18.55:32768"):
        super().__init__("deepseek-v4-pro:cloud", "Shield", ollama_base_url)

    def build_prompt(self, asset: str, market_data: Optional[Dict] = None, **kwargs) -> str:
        portfolio_value = kwargs.get("portfolio_value", 10000)
        current_position = kwargs.get("current_position_value", 0)

        return f"""You are Shield, a Portfolio Risk and Execution Risk Assessment Agent.

Your task: Provide a comprehensive risk recommendation for {asset}.

CONTEXT:
- Portfolio value: ${portfolio_value}
- Current position in {asset}: ${current_position}
- Max allocation per asset: 10%
- Max total crypto exposure: 30%
- Max daily loss: 2%
- Max drawdown before pause: 5%
- Max open positions: 3
- No leverage
- Paper trading only

Analyze the following and provide your recommendation in the EXACT format below:

PORTFOLIO RISK + EXECUTION RISK RECOMMENDATION:
Asset: {asset}
Strategy or signal: [description]
Volatility profile: [assessment]
Correlation profile: [to BTC/ETH/market]
Max drawdown scenario: [analysis]
Liquidity risk: [assessment]
Slippage risk: [assessment]
Execution risk: [assessment]
Data risk: [assessment]
Model risk: [assessment]
Overfitting risk: [assessment]
Portfolio concentration risk: [assessment]
Risk matrix:
  - Threat: [name]
    Probability: [High/Medium/Low]
    Impact: [High/Medium/Low]
    Mitigation: [description]
    Owner: [agent/team]
    Trigger: [condition]
Recommended position size: [USD or %]
Recommended action: [Proceed | Reduce | Wait | Reject]
Required mitigation: [list]
Warnings: [any concerns]

The Risk Governor has final blocking authority. Your role is advisory.
Be conservative. Better to recommend "Wait" than risk capital.
NEVER make a final trade decision.
"""

    def parse_output(self, raw_output: str, asset: str) -> AgentRecommendation:
        timestamp = datetime.utcnow().isoformat() + "Z"
        recommendation = self._extract_field(raw_output, "Recommended action")
        confidence = self._extract_field(raw_output, "Confidence")
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
