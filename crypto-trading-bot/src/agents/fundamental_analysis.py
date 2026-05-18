"""
Crypto Fundamental + On-chain Analysis Agent
Agent: Ledger
Model: ollama/deepseek-v4-pro:cloud
"""

import re
import logging
from typing import Dict, Optional
from datetime import datetime

from .base_agent import BaseRecommendationAgent, AgentRecommendation

logger = logging.getLogger(__name__)


class FundamentalAnalysisAgent(BaseRecommendationAgent):
    """Provides crypto fundamental and on-chain analysis recommendations."""

    def __init__(self, ollama_base_url: str = "http://187.124.18.55:32768"):
        super().__init__("deepseek-v4-pro:cloud", "Ledger", ollama_base_url)

    def build_prompt(self, asset: str, market_data: Optional[Dict] = None, **kwargs) -> str:
        return f"""You are Ledger, a Crypto Fundamental and On-chain Analysis Agent.

Your task: Provide a structured fundamental recommendation for {asset}.

Analyze the following and provide your recommendation in the EXACT format below:

CRYPTO FUNDAMENTAL + ON-CHAIN RECOMMENDATION:
Asset: {asset}
Project overview: [summary]
Tokenomics: [supply, emissions, unlocks, inflation, burn mechanics]
On-chain activity: [active addresses, tx volume, fees, TVL, staking]
Network health: [validators, decentralization, security]
Ecosystem strength: [integrations, partnerships, adoption]
Developer activity: [trends]
Liquidity: [assessment]
Competitive moat: [network effects, security, brand, utility]
Valuation view: [fair/undervalued/overvalued with reasoning]
Upcoming events: [upgrades, unlocks, governance, regulatory]
Bullish fundamentals: [list]
Bearish fundamentals: [list]
Fundamental recommendation: [BULLISH | BEARISH | NEUTRAL]
Confidence: [High | Medium | Low]
Warnings: [any concerns]

Separate verified data from speculation. Label unverified items clearly.
NEVER make a final trade decision. Recommendation only.
"""

    def parse_output(self, raw_output: str, asset: str) -> AgentRecommendation:
        timestamp = datetime.utcnow().isoformat() + "Z"
        recommendation = self._extract_field(raw_output, "Fundamental recommendation")
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
        )

    def _extract_field(self, text: str, field_name: str) -> Optional[str]:
        pattern = rf"{re.escape(field_name)}:\s*(.+?)(?=\n\w|$)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return None
