"""
Market Structure + Technical Analysis Agent
Agent: Candles
Model: ollama/kimi-k2.6:cloud
"""

import re
import logging
from typing import Dict, Optional
from datetime import datetime

from .base_agent import BaseRecommendationAgent, AgentRecommendation

logger = logging.getLogger(__name__)


class TechnicalAnalysisAgent(BaseRecommendationAgent):
    """Provides technical analysis recommendations."""

    def __init__(self, ollama_base_url: str = "http://187.124.18.55:32768"):
        super().__init__("kimi-k2.6:cloud", "Candles", ollama_base_url)

    def build_prompt(self, asset: str, market_data: Optional[Dict] = None, **kwargs) -> str:
        current_price = kwargs.get("current_price", "N/A")
        recent_data = kwargs.get("recent_data", "N/A")

        return f"""You are Candles, a Market Structure and Technical Analysis Agent for crypto trading.

Your task: Provide a structured technical recommendation for {asset}.

CURRENT PRICE: {current_price}

RECENT DATA (last few hourly bars if available):
{recent_data}

Analyze the following and provide your recommendation in the EXACT format below:

MARKET STRUCTURE + TECHNICAL RECOMMENDATION:
Asset: {asset}
Timeframe: [e.g. 1H, 4H, Daily]
Trend: [Bullish | Bearish | Sideways | Mixed]
Market structure: [description]
Key support: [levels]
Key resistance: [levels]
Liquidity zones: [description]
52-week high: [price]
52-week low: [price]
Fibonacci levels: [levels]
Indicator readings: [RSI, MACD, etc.]
Volume analysis: [description]
Bullish evidence: [list]
Bearish evidence: [list]
Possible entry zone: [range]
Possible invalidation level: [price]
Possible stop-loss: [price]
Possible profit target 1: [price]
Possible profit target 2: [price]
Possible profit target 3: [price]
Technical recommendation: [BUY zone | SELL zone | WAIT | NEUTRAL]
Confidence: [High | Medium | Low]
Warnings: [any concerns]

NEVER make a final trade decision. This is a recommendation only.
Be honest about uncertainty. If data is insufficient, say so.
"""

    def parse_output(self, raw_output: str, asset: str) -> AgentRecommendation:
        """Parse raw LLM output into structured recommendation."""
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Extract key fields with regex
        recommendation = self._extract_field(raw_output, "Technical recommendation")
        confidence = self._extract_field(raw_output, "Confidence")
        warnings = self._extract_field(raw_output, "Warnings")

        if not recommendation:
            recommendation = "UNKNOWN"
        if not confidence:
            confidence = "Low"
        if not warnings:
            warnings = "No warnings parsed"

        return AgentRecommendation(
            agent_name=self.agent_name,
            asset=asset,
            recommendation=recommendation,
            confidence=confidence,
            warnings=warnings,
            raw_output=raw_output,
            timestamp=timestamp,
            model_used=self.model,
            cached=False,
        )

    def _extract_field(self, text: str, field_name: str) -> Optional[str]:
        """Extract a field value from structured text."""
        # Case-sensitive, exact field match to avoid matching header text
        # Value is everything until the next field (capitalized word + colon)
        escaped = re.escape(field_name)
        pattern = rf"(?:^|\n){escaped}:\s*(.+?)(?=\n[A-Z][^:\n]*:\s*|$)"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None
