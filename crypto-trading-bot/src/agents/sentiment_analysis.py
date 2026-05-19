"""
Sentiment + Narrative + Catalyst Analysis Agent
Agent: Pulse
Model: ollama/qwen3.5:cloud
"""

import re
import logging
from typing import Dict, Optional
from datetime import datetime, timezone

from .base_agent import BaseRecommendationAgent, AgentRecommendation

logger = logging.getLogger(__name__)


class SentimentAnalysisAgent(BaseRecommendationAgent):
    """Provides sentiment, narrative, and catalyst analysis recommendations."""

    def __init__(self, ollama_base_url: str = "http://187.124.18.55:32768"):
        super().__init__("qwen3.5:cloud", "Pulse", ollama_base_url)

    def build_prompt(self, asset: str, market_data: Optional[Dict] = None, **kwargs) -> str:
        return f"""You are Pulse, a Sentiment, Narrative, and Catalyst Analysis Agent.

Your task: Provide a structured sentiment recommendation for {asset}.

Analyze the following and provide your recommendation in the EXACT format below:

SENTIMENT + NARRATIVE RECOMMENDATION:
Asset: {asset}
Current news: [summary of last 24-48h]
Social/community sentiment: [assessment]
Market narrative: [bullish/bearish narrative description]
Institutional/retail mood: [assessment]
Derivatives sentiment: [funding rates, OI, liquidations if known]
Crowded trade risk: [Yes/No | assessment]
Bullish sentiment factors: [list]
Bearish sentiment factors: [list]
Catalysts: [upcoming events]
Rumors/unverified items: [list with disclaimer]
Sentiment recommendation: [BULLISH | BEARISH | NEUTRAL | EXTREME]
Confidence: [High | Medium | Low]
Warnings: [any concerns]

Label unverified information clearly.
NEVER make a final trade decision. Recommendation only.
"""

    def parse_output(self, raw_output: str, asset: str) -> AgentRecommendation:
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        recommendation = self._extract_field(raw_output, "Sentiment recommendation")
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
