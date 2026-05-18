"""
Base Agent Class
All recommendation agents inherit from this.
Provides Ollama API integration and structured output parsing.
"""

import json
import logging
import re
import requests
from typing import Dict, Optional, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class AgentRecommendation:
    agent_name: str
    asset: str
    recommendation: str
    confidence: str
    warnings: str
    raw_output: str
    timestamp: str
    model_used: str


class BaseRecommendationAgent(ABC):
    """Base class for all recommendation agents."""

    def __init__(self, model: str, agent_name: str, ollama_base_url: str = "http://187.124.18.55:32768"):
        self.model = model
        self.agent_name = agent_name
        self.ollama_url = ollama_base_url
        self.api_key = "ollama"

    def _call_ollama(self, prompt: str, temperature: float = 0.3, timeout: int = 60) -> str:
        """Call Ollama API with the given prompt. Raises on timeout/connection errors."""
        response = requests.post(
            f"{self.ollama_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                }
            },
            headers={
                "Authorization": f"Bearer {self.api_key}"
            },
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")

    @abstractmethod
    def build_prompt(self, asset: str, market_data: Optional[Dict] = None, **kwargs) -> str:
        """Build the prompt for this agent."""
        pass

    @abstractmethod
    def parse_output(self, raw_output: str, asset: str) -> AgentRecommendation:
        """Parse raw LLM output into structured recommendation."""
        pass

    def run(self, asset: str, market_data: Optional[Dict] = None, **kwargs) -> AgentRecommendation:
        """
        Execute the agent: build prompt, call LLM, parse output.
        Catches all exceptions and returns ERROR recommendation.
        """
        import datetime

        logger.info(f"[{self.agent_name}] Running for {asset}")

        try:
            prompt = self.build_prompt(asset, market_data, **kwargs)
            raw_output = self._call_ollama(prompt)
            return self.parse_output(raw_output, asset)
        except Exception as e:
            logger.error(f"[{self.agent_name}] Failed: {e}")
            return AgentRecommendation(
                agent_name=self.agent_name,
                asset=asset,
                recommendation="ERROR",
                confidence="Low",
                warnings=str(e),
                raw_output=f"ERROR: {e}",
                timestamp=datetime.datetime.utcnow().isoformat() + "Z",
                model_used=self.model,
            )
