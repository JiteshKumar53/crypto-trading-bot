"""
Base Agent Class
All recommendation agents inherit from this.
Provides Ollama API integration, structured output parsing, caching, and model routing.
"""

import json
import logging
import re
import requests
import hashlib
import time
from typing import Dict, Optional, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Model performance profiles
MODEL_TIMEOUTS = {
    "kimi-k2.6:cloud": 180,       # 1T params — needs 3 min
    "deepseek-v4-pro:cloud": 120,  # Deep reasoning — 2 min
    "qwen3.5:cloud": 60,          # Fast — 1 min
    "default": 60,
}

MODEL_TEMPERATURES = {
    "kimi-k2.6:cloud": 0.2,       # Lower temp for consistency
    "deepseek-v4-pro:cloud": 0.3,
    "qwen3.5:cloud": 0.3,
    "default": 0.3,
}

# In-memory response cache: key -> {output, timestamp}
_response_cache: Dict[str, Dict] = {}
CACHE_TTL_SECONDS = 300  # 5 minute cache for agent responses


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
    cached: bool = False  # Whether response came from cache


class BaseRecommendationAgent(ABC):
    """Base class for all recommendation agents with caching and model routing."""

    def __init__(self, model: str, agent_name: str, ollama_base_url: str = "http://187.124.18.55:32768"):
        self.model = model
        self.agent_name = agent_name
        self.ollama_url = ollama_base_url
        self.api_key = "ollama"
        self.timeout = MODEL_TIMEOUTS.get(model, MODEL_TIMEOUTS["default"])
        self.temperature = MODEL_TEMPERATURES.get(model, MODEL_TEMPERATURES["default"])

    def _get_cache_key(self, prompt: str) -> str:
        """Generate cache key from prompt + model."""
        return hashlib.md5(f"{self.model}:{prompt}".encode()).hexdigest()

    def _get_cached(self, cache_key: str) -> Optional[str]:
        """Get cached response if still valid."""
        entry = _response_cache.get(cache_key)
        if entry and (time.time() - entry["timestamp"]) < CACHE_TTL_SECONDS:
            logger.info(f"[{self.agent_name}] Cache HIT")
            return entry["output"]
        return None

    def _cache_response(self, cache_key: str, output: str):
        """Store response in cache."""
        _response_cache[cache_key] = {
            "output": output,
            "timestamp": time.time(),
        }
        logger.info(f"[{self.agent_name}] Cached response (TTL: {CACHE_TTL_SECONDS}s)")

    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API with the given prompt. Caches successful responses."""
        cache_key = self._get_cache_key(prompt)
        
        # Check cache first
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        logger.info(f"[{self.agent_name}] Calling Ollama ({self.model}, timeout={self.timeout}s)...")
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                    }
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}"
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            raw_output = data.get("response", "")
            
            elapsed = time.time() - start_time
            logger.info(f"[{self.agent_name}] Ollama responded in {elapsed:.1f}s")
            
            # Cache successful response
            self._cache_response(cache_key, raw_output)
            return raw_output
            
        except requests.exceptions.Timeout:
            elapsed = time.time() - start_time
            logger.error(f"[{self.agent_name}] Ollama API timeout after {elapsed:.1f}s (limit: {self.timeout}s)")
            raise  # Re-raise for run() to catch
        except requests.exceptions.RequestException as e:
            logger.error(f"[{self.agent_name}] Ollama API error: {e}")
            raise  # Re-raise for run() to catch
        except Exception as e:
            logger.error(f"[{self.agent_name}] Unexpected error: {e}")
            raise  # Re-raise for run() to catch

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
        Execute the agent: build prompt, call LLM (with cache), parse output.
        Catches all exceptions and returns ERROR recommendation.
        """
        logger.info(f"[{self.agent_name}] Running for {asset}")
        start_time = time.time()

        try:
            prompt = self.build_prompt(asset, market_data, **kwargs)
            
            # Check if we have a cached response for this exact prompt
            cache_key = self._get_cache_key(prompt)
            cached_output = self._get_cached(cache_key)
            
            if cached_output is not None:
                # Use cached response
                result = self.parse_output(cached_output, asset)
                result.cached = True
                result.timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                elapsed = time.time() - start_time
                logger.info(f"[{self.agent_name}] Completed in {elapsed:.1f}s (CACHED)")
                return result
            
            # Call Ollama (will cache on success)
            raw_output = self._call_ollama(prompt)
            result = self.parse_output(raw_output, asset)
            result.cached = False
            result.timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            elapsed = time.time() - start_time
            logger.info(f"[{self.agent_name}] Completed in {elapsed:.1f}s (LIVE)")
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"[{self.agent_name}] Failed after {elapsed:.1f}s: {e}")
            return AgentRecommendation(
                agent_name=self.agent_name,
                asset=asset,
                recommendation="ERROR",
                confidence="Low",
                warnings=str(e),
                raw_output=f"ERROR: {e}",
                timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                model_used=self.model,
                cached=False,
            )

    def _extract_field(self, text: str, field_name: str) -> Optional[str]:
        """Extract a field value from structured text."""
        escaped = re.escape(field_name)
        pattern = rf"(?:^|\n){escaped}:\s*(.+?)(?=\n[A-Z][^:\n]*:\s*|$)"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None
